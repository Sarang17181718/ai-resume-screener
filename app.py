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


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)