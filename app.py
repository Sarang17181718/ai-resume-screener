from flask import Flask, render_template, request, redirect, send_file, send_from_directory
import os
import csv
import zipfile
import mysql.connector
from resume_screener import run_resume_screening

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ---------------- DATABASE CONNECTION ----------------

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Sarang@123",
    database="ai_recruitment"
)

cursor = db.cursor()

# ---------------- HOME ----------------
@app.route("/")
def home():
    return redirect("/login")


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        cursor.execute(
        "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
        (name,email,password,role)
        )

        db.commit()

        return redirect("/login")

    return render_template("signup.html")

# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor.execute(
        "SELECT * FROM users WHERE email=%s AND password=%s",
        (email,password)
        )

        user = cursor.fetchone()

        if user:

            role = user[4]

            if role == "recruiter":
                return redirect("/recruiter")

            if role == "candidate":
                return redirect("/candidate")

        else:
            return "Invalid login"

    return render_template("login.html")

# ---------------- RECRUITER DASHBOARD ----------------

@app.route("/recruiter")
def recruiter_dashboard():
    return render_template("recruiter_dashboard.html")


@app.route("/post_job", methods=["GET","POST"])
def post_job():

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]

        recruiter_id = 1   # temporary (later we use session)

        cursor.execute(
        "INSERT INTO jobs(title,description,recruiter_id) VALUES(%s,%s,%s)",
        (title,description,recruiter_id)
        )

        db.commit()

        return "Job Posted Successfully"

    return render_template("post_job.html")


@app.route("/view_jobs")
def view_jobs():

    recruiter_id = 1   # temporary

    cursor.execute(
        "SELECT * FROM jobs WHERE recruiter_id=%s",
        (recruiter_id,)
    )

    jobs = cursor.fetchall()

    return render_template("view_jobs.html", jobs=jobs)


# ---------------- AI SCREENING PAGE ----------------

@app.route("/ai_screening")
def ai_screening():
    return render_template("ai_screening.html")


# ---------------- RUN AI SCREENING ----------------

@app.route("/run_screening", methods=["POST"])
def run_screening():

    job_text = request.form["job_text"]

    files = request.files.getlist("resumes")

    # clear old uploads
    for file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, file))

    # save new resumes
    for file in files:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

    results = run_resume_screening(job_text, UPLOAD_FOLDER)

    # store results for downloads
    app.config["LATEST_RESULTS"] = results

    return render_template("results.html", results=results)


# ---------------- DOWNLOAD SINGLE RESUME ----------------

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

# ---------------- DOWNLOAD TOP CANDIDATES ZIP ----------------

@app.route("/download_top_zip")
def download_top_zip():

    results = app.config.get("LATEST_RESULTS", [])

    zip_filename = "top_candidates.zip"

    with zipfile.ZipFile(zip_filename, "w") as zipf:

        for r in results[:5]:

            resume_name = r[0]
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_name)

            if os.path.exists(file_path):
                zipf.write(file_path, resume_name)

    return send_file(zip_filename, as_attachment=True)


# ---------------- CSV REPORT ----------------
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
            r[0],
            round(r[1],2),
            round(r[2],2),
            round(r[3],2),
            round(r[4],2),
            round(r[5],2),
            ", ".join(r[6]),
            ", ".join(r[7])
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
    return render_template("candidate_dashboard.html")


@app.route("/candidate_jobs")
def candidate_jobs():

    cursor.execute("SELECT * FROM jobs")

    jobs = cursor.fetchall()

    return render_template("candidate_jobs.html", jobs=jobs)



@app.route("/apply/<int:job_id>", methods=["GET","POST"])
def apply(job_id):

    if request.method == "POST":

        file = request.files["resume"]

        filepath = os.path.join("uploads", file.filename)

        file.save(filepath)

        candidate_id = 1   # temporary

        cursor.execute(
        "INSERT INTO applications(job_id,candidate_id,resume_filename) VALUES(%s,%s,%s)",
        (job_id,candidate_id,file.filename)
        )

        db.commit()

        return "Application Submitted Successfully"

    return render_template("apply_job.html", job_id=job_id)


@app.route("/view_applicants/<int:job_id>")
def view_applicants(job_id):

    cursor.execute(
        "SELECT * FROM applications WHERE job_id=%s",
        (job_id,)
    )

    applicants = cursor.fetchall()

    return render_template(
        "view_applicants.html",
        applicants=applicants,
        job_id=job_id
    )
@app.route("/screen_job/<int:job_id>")
def screen_job(job_id):

    import shutil

    # get job description
    cursor.execute(
        "SELECT description FROM jobs WHERE id=%s",
        (job_id,)
    )

    job = cursor.fetchone()
    job_text = job[0]

    # get resumes for this job
    cursor.execute(
        "SELECT resume_filename FROM applications WHERE job_id=%s",
        (job_id,)
    )

    resumes = cursor.fetchall()

    # create temporary folder
    temp_folder = "temp_resumes"

    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    os.makedirs(temp_folder)

    # copy applicant resumes into temp folder
    for r in resumes:

        filename = r[0]

        source = os.path.join("uploads", filename)
        destination = os.path.join(temp_folder, filename)

        if os.path.exists(source):
            shutil.copy(source, destination)

    # run AI screening
    results = run_resume_screening(job_text, temp_folder)

    app.config["LATEST_RESULTS"] = results
    return render_template("results.html", results=results)

'''@app.route("/shortlist/<int:app_id>")
def shortlist(app_id):

    cursor.execute(
        "UPDATE applications SET status='shortlisted' WHERE id=%s",
        (app_id,)
    )

    db.commit()

    return redirect(request.referrer)'''
@app.route("/shortlist/<filename>")
def shortlist(filename):

    cursor.execute(
        "UPDATE applications SET status='shortlisted' WHERE resume_filename=%s",
        (filename,)
    )

    db.commit()

    return redirect(request.referrer)

'''@app.route("/reject/<int:app_id>")
def reject(app_id):

    cursor.execute(
        "UPDATE applications SET status='rejected' WHERE id=%s",
        (app_id,)
    )

    db.commit()

    return redirect(request.referrer)'''

@app.route("/reject/<filename>")
def reject(filename):

    cursor.execute(
        "UPDATE applications SET status='rejected' WHERE resume_filename=%s",
        (filename,)
    )

    db.commit()

    return redirect(request.referrer)

# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)