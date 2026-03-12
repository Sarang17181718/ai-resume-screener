from flask import send_from_directory
from flask import Flask, render_template, request
import os
import csv
import zipfile
from flask import send_file
from resume_screener import run_resume_screening


app = Flask(__name__)


@app.route("/download_top_zip")

def download_top_zip():

    results = app.config["LATEST_RESULTS"]

    zip_filename = "top_candidates.zip"

    with zipfile.ZipFile(zip_filename, "w") as zipf:

        for r in results[:5]:   
            resume_name = r[0]
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], resume_name)

            if os.path.exists(file_path):
                zipf.write(file_path, resume_name)

    return send_file(zip_filename, as_attachment=True)


def create_csv_report(results):

    filepath = "ranking_report.csv"

    with open(filepath, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow([
            "Rank",
            "Resume",
            "Semantic Score",
            "Skill Score",
            "Experience Score",
            "Education Score",
            "Final Score",
            "Matched Skills",
            "Missing Skills"
        ])

        for i, r in enumerate(results):

            writer.writerow([
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

    return filepath

@app.route("/download_report")
def download_report():

    filepath = create_csv_report(app.config["LATEST_RESULTS"])

    return send_file(filepath, as_attachment=True)

@app.route("/download/<filename>")
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    job_text = request.form["job_text"]

    for file in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, file))

    files = request.files.getlist("resumes[]")


    for file in files:
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)

    results = run_resume_screening(job_text, "uploads")

    app.config["LATEST_RESULTS"] = results

    return render_template("results.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)

