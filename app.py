from flask import Flask,render_template, request, redirect, send_file, send_from_directory
import os
import csv
import zipfile
#from resume_screener import run_resume_screening
from flask_mail import Mail, Message
from flask import session
import time
from dotenv import load_dotenv
load_dotenv()






import psycopg2

# def get_db():
#     return psycopg2.connect(
#         host=os.environ.get("DB_HOST"),
#         dbname=os.environ.get("DB_NAME"),
#         user=os.environ.get("DB_USER"),
#         password=os.environ.get("DB_PASSWORD"),
#         port=os.environ.get("DB_PORT"),
#         sslmode=os.environ.get("DB_SSLMODE")
#     )

def get_db():
    try:
        return psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            dbname=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            port=os.environ.get("DB_PORT"),
            sslmode=os.environ.get("DB_SSLMODE")
        )
    except Exception as e:
        print("DB ERROR:", e)
        return None

app = Flask(__name__)
app.secret_key="mysecrete123"
UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sarangbhokse29@gmail.com'

app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
mail=Mail(app)

app.config['MAIL_DEBUG'] = True

@app.route("/run_screening", methods=["POST"])
def run_screening():
    from resume_screener import run_resume_screening  # ✅ lazy load

@app.route("/")
def home():
    return redirect("/login")



@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
        (name,email,password,role))
        

        db.commit()
        cursor.close()
        db.close()

        return redirect("/login")

    return render_template("signup.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]


        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s",
        (email,password))
        
        

        user = cursor.fetchone()
        cursor.close()
        db.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[4]
    

            role = user[4]

            if role == "recruiter":
                return redirect("/recruiter")

            if role == "candidate":
                return redirect("/candidate")

        else:
            return "Invalid login"

    return render_template("login.html")


@app.route("/recruiter")
def recruiter_dashboard():
    return render_template("recruiter_dashboard.html")


@app.route("/post_job", methods=["GET","POST"])
def post_job():

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        recruiter_id =session["user_id"]

        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO jobs(title,description,recruiter_id) VALUES(%s,%s,%s)",
        (title,description,recruiter_id))
        

        db.commit()
        cursor.close()
        db.close()

        return redirect("/view_jobs")

    return render_template("post_job.html")


@app.route("/view_jobs")
def view_jobs():
    if "user_id" not in session or session["role"] != "recruiter":
        return "Access Denied", 403

    recruiter_id = session["user_id"]   

    db = get_db()
    cursor = db.cursor()
    cursor.execute( "SELECT * FROM jobs WHERE recruiter_id=%s",
        (session["user_id"],))
    

    jobs = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template("view_jobs.html", jobs=jobs)



@app.route("/ai_screening")
def ai_screening():
    return render_template("ai_screening.html")



@app.route("/run_screening", methods=["POST"])
def run_screening():

    job_text = request.form["job_text"]

    files = request.files.getlist("resumes")

    # clear old uploads
    for file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, file))

    applications = []
    for i, file in enumerate(files):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
    
        applications.append((i, file.filename)) 
    results = run_resume_screening(job_text, applications)

    
    app.config["LATEST_RESULTS"] = results

    return render_template("results.html", results=results)



@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.route("/download_top_zip")
def download_top_zip():

    results = app.config.get("LATEST_RESULTS", [])

    zip_filename = "top_candidates.zip"

    with zipfile.ZipFile(zip_filename, "w") as zipf:

        for r in results[:5]:

            resume_name = r[1]
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_name)

            if os.path.exists(file_path):
                zipf.write(file_path, resume_name)

    return send_file(zip_filename, as_attachment=True)


from openpyxl import Workbook
from openpyxl.styles import Font

def create_excel_report(results):

    wb = Workbook()
    ws = wb.active
    ws.title = "AI Resume Ranking"

    headers = [
        "Rank",
        "Resume Name",
        "Semantic Score",
        "Skill Score",
        "Experience Score",
        "Education Score",
        "Final Score",
        "Matched Skills",
        "Missing Skills"
    ]

    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)

    for i, r in enumerate(results):

        ws.append([
            i+1,
            r[1],
            round(r[2],2),
            round(r[3],2),
            round(r[4],2),
            round(r[5],2),
            round(r[6],2),
            ", ".join(r[7]),
            ", ".join(r[8])
        ])

    
    for column in ws.columns:

        max_length = 0
        column_letter = column[0].column_letter

        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))

        ws.column_dimensions[column_letter].width = max_length + 4

    filepath = "AI_Resume_Ranking_Report.xlsx"

    wb.save(filepath)

    return filepath

@app.route("/download_report")
def download_report():

    results = app.config.get("LATEST_RESULTS", [])

    filepath = create_excel_report(results)

    return send_file(filepath, as_attachment=True)

@app.route("/candidate")
def candidate_dashboard():

    candidate_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT jobs.title, applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.candidate_id = %s
    """, (candidate_id,))
    

    applications = cursor.fetchall()
    cursor.close()
    db.close()

    return render_template(
        "candidate_dashboard.html",
        applications=applications
    )


@app.route("/candidate_jobs")
def candidate_jobs():

    candidate_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM jobs")
    jobs = cursor.fetchall()

    
    cursor.execute("""
        SELECT job_id FROM applications
        WHERE candidate_id=%s
    """, (candidate_id,))
    
   

    applied_jobs = cursor.fetchall()
    cursor.close()
    db.close()

    applied_job_ids = [j[0] for j in applied_jobs]

    return render_template(
        "candidate_jobs.html",
        jobs=jobs,
        applied_job_ids=applied_job_ids
    )

@app.route("/apply/<int:job_id>", methods=["GET","POST"])

def apply(job_id):

    if request.method == "POST":
        candidate_id = session["user_id"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM applications
            WHERE job_id=%s AND candidate_id=%s
        """, (job_id, candidate_id))

        existing=cursor.fetchone()
        
        if existing:
            cursor.close()
            db.close()
            return "You have already applied for this job"
        

        file = request.files["resume"]
        unique_name=str(int(time.time())) + "_" + file.filename

        filepath = os.path.join("uploads", unique_name)

        file.save(filepath)


        db = get_db()
        cursor = db.cursor()

        cursor.execute(
        "INSERT INTO applications(job_id,candidate_id,resume_filename) VALUES(%s,%s,%s)",
        (job_id,candidate_id,unique_name)
        )

        db.commit()
        cursor.close()
        db.close()


        return "Application Submitted Successfully"

    return render_template("apply_job.html", job_id=job_id)




@app.route("/view_applicants/<int:job_id>")
def view_applicants(job_id):

    if "user_id" not in session or session["role"] != "recruiter":
        return "Access Denied", 403

    recruiter_id = session["user_id"]

    # 🔐 Ensure recruiter owns this job
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id FROM jobs
        WHERE id=%s AND recruiter_id=%s
    """, (job_id, recruiter_id))
    job = cursor.fetchone()
    cursor.close()
    db.close()

    

    if not job:
        return "Unauthorized Access", 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM applications
        WHERE job_id=%s
    """, (job_id,))
    applicants = cursor.fetchall()
    cursor.close()
    db.close()

    

    return render_template(
        "view_applicants.html",
        applicants=applicants,
        job_id=job_id
    )



@app.route("/screen_job/<int:job_id>")
def screen_job(job_id):
    recruiter_id = session["user_id"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute( "SELECT * FROM jobs WHERE id=%s AND recruiter_id=%s",
        (job_id, recruiter_id))
    
    job = cursor.fetchone()
    cursor.close()
    db.close()
   
   

    if not job:
        return "Unauthorized Access", 403

    import shutil

    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT description FROM jobs WHERE id=%s",
        (job_id,)
    )

    job = cursor.fetchone()
    job_text = job[0]
    cursor.close()
    db.close()
    

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT resume_filename FROM applications WHERE job_id=%s",
        (job_id,)
    )

    resumes = cursor.fetchall()
    cursor.close()
    db.close()

    temp_folder = "temp_resumes"

    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    os.makedirs(temp_folder)

    for r in resumes:

        filename = r[0]

        source = os.path.join("uploads", filename)
        destination = os.path.join(temp_folder, filename)

        if os.path.exists(source):
            shutil.copy(source, destination)

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
                   SELECT id, resume_filename
                   FROM applications
                   WHERE job_id = %s
                   """, (job_id,))
    applications = cursor.fetchall()

    cursor.close()
    db.close()
    results=run_resume_screening(job_text,applications)






    app.config["LATEST_RESULTS"] = results
    return render_template("results.html", results=results,job_id=job_id)



@app.route("/shortlist/<int:job_id>/<int:app_id>")
def shortlist(job_id, app_id):

    if "user_id" not in session or session["role"] != "recruiter":
        return "Access Denied", 403

    recruiter_id = session["user_id"]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name, email FROM users WHERE id=%s", (recruiter_id,))
    
    recruiter = cursor.fetchone()
    cursor.close()
    db.close()

    recruiter_name = recruiter[0]
    recruiter_email = recruiter[1]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id FROM jobs 
        WHERE id=%s AND recruiter_id=%s
    """, (job_id, recruiter_id))

    job = cursor.fetchone()
    cursor.close()
    db.close()

    if not job:
        return "Unauthorized Access", 403

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE applications 
        SET status='shortlisted' 
        WHERE id=%s AND job_id=%s
    """, (app_id, job_id))
    db.commit()
    cursor.close()
    db.close()

    

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT users.email, jobs.title
        FROM applications
        JOIN users ON applications.candidate_id = users.id
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = %s
    """, (app_id,))

    data = cursor.fetchone()
    

    if data:
        email = data[0]
        job_title = data[1]

        # 📧 SEND EMAIL
        msg = Message(
            subject="Congratulations! You are Shortlisted 🎉",
            sender=("AI Recruitment System",app.config['MAIL_USERNAME']),
            recipients=[email]
        )

        msg.body = f"""
        Congratulations!
        You have been shortlisted for the position: {job_title}
        Recruiter: {recruiter_name}
        Contact Email: {recruiter_email}
        Please wait for further communication.
        Regards,
        Recruitment Team
        """

        mail.send(msg)
    cursor.close()
    db.close()

    return redirect(request.referrer)



@app.route("/reject/<int:job_id>/<int:app_id>")
def reject(job_id, app_id):

    if "user_id" not in session or session["role"] != "recruiter":
        return "Access Denied", 403

    recruiter_id = session["user_id"]
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT name, email FROM users WHERE id=%s", (recruiter_id,))
    recruiter = cursor.fetchone()
    cursor.close()
    db.close()
    recruiter_name = recruiter[0]
    recruiter_email = recruiter[1]

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id FROM jobs 
        WHERE id=%s AND recruiter_id=%s
    """, (job_id, recruiter_id))

    job = cursor.fetchone()
    cursor.close()
    db.close()

    if not job:
        return "Unauthorized Access", 403
    

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE applications 
        SET status='rejected' 
        WHERE id=%s AND job_id=%s
    """, (app_id, job_id))

    db.commit()
    cursor.close()
    db.close()

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT users.email, jobs.title
        FROM applications
        JOIN users ON applications.candidate_id = users.id
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = %s AND applications.job_id = %s
    """, (app_id, job_id))

    data = cursor.fetchone()
    
    
    if data:
        email = data[0]
        job_title = data[1]

        msg = Message(
            subject="Application Update",
            sender=("AI Recruitment System",app.config['MAIL_USERNAME']),
            recipients=[email]
        )

        msg.body = f"""
        Dear Candidate,

        Thank you for applying for the position: {job_title}

        We regret to inform you that your application has not been selected at this time.
        Recruiter: {recruiter_name}
        contact Email: {recruiter_email}

        We encourage you to apply for future opportunities.

        Regards,
        Recruitment Team
        """

        mail.send(msg)
    cursor.close()
    db.close()


    return redirect(request.referrer)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


import os
if __name__ == "__main__": 
      port = int(os.environ.get("PORT", 5000))
      app.run(host="0.0.0.0", port=port)

#if __name__ == "__main__":
 #   app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))