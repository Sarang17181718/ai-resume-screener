
import pdfplumber
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber
from resume_parser import parse_resume
skills_list = [
    "python",
    "sql",
    "machine learning",
    "deep learning",
    "aws",
    "docker",
    "kubernetes",
    "flask",
    "django",
    "pandas",
    "numpy",
    "tensorflow",
    "pytorch"
]

def extract_skills(text):

    text = text.lower()

    found_skills = []

    for skill in skills_list:
        if skill.lower() in text:
            found_skills.append(skill)

    return found_skills

model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(path):

    text = ""

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t

    return text

def extract_text(filepath):

    if filepath.endswith(".pdf"):

        text = ""

        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t
    

        return text

    elif filepath.endswith(".txt"):

        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

def compute_skill_score(resume_text, job_text):

    skills = ["python", "sql", "machine learning", "aws", "docker"]

    score = 0

    for skill in skills:
        if skill in resume_text.lower():
            score += 20

    return min(score, 100)

import re

def compute_experience_score(resume_text):

    match = re.search(r'(\d+)\s+years', resume_text.lower())

    if match:
        years = int(match.group(1))

        if years >= 5:
            return 100
        elif years >= 3:
            return 75
        elif years >= 1:
            return 50

    return 25


def compute_education_score(resume_text):

    text = resume_text.lower()

    if "phd" in text:
        return 100
    elif "master" in text or "m.tech" in text:
        return 75
    elif "bachelor" in text or "b.tech" in text:
        return 50

    return 25



def run_resume_screening(job_text, applications):
    
    job_skills = extract_skills(job_text)
    print("Job Skills:", job_skills)
    print("Job Skills:", job_skills)
    job_embedding = model.encode(job_text)
    


    results = []

    for app in applications:
        app_id = app[0]
        resume_filename = app[1]
        file_path = os.path.join("uploads", resume_filename)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            resume_text = f.read()
        

    

        if resume_filename.endswith(".pdf") or resume_filename.endswith(".txt"):
            file_path = os.path.join("uploads", resume_filename)

            # extract resume text
            resume_text = extract_text(file_path)
            candidate_info = parse_resume(resume_text)
            name = candidate_info["name"]
            email = candidate_info["email"]
            phone = candidate_info["phone"]
            skills = candidate_info["skills"]

    
            resume_skills = extract_skills(resume_text)
            matched_skills = list(set(resume_skills) & set(job_skills))
            missing_skills = list(set(job_skills) - set(resume_skills))
            



            # semantic similarity
            resume_embedding = model.encode(resume_text)
            similarity = cosine_similarity([resume_embedding], [job_embedding])[0][0]
            semantic_score = similarity * 100

            # skill score
            skill_score = compute_skill_score(resume_text, job_text)

            # experience score
            exp_score = compute_experience_score(resume_text)

            # education score
            edu_score = compute_education_score(resume_text)

            final_score = (
                0.4 * semantic_score +
                0.3 * skill_score +
                0.2 * exp_score +
                0.1 * edu_score
            )

            results.append(
                (app_id,
                 resume_filename,
                 float(semantic_score),
                 float(skill_score),
                 float(exp_score),
                 float(edu_score),
                 float(final_score),
                 matched_skills,
                 missing_skills,
                 name,
                 email,
                 phone,
                 )
                 )

      
    results.sort(key=lambda x: x[6], reverse=True)

    return results[:10]