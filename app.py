from flask import send_from_directory
from flask import Flask, render_template, request
import os
from resume_screener import run_resume_screening


app = Flask(__name__)

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

    return render_template("results.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)

