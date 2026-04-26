import os
import re
import pdfplumber
import nltk

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from resume_parser import parse_resume

# ------------------ NLTK SETUP (SAFE FOR RAILWAY) ------------------
nltk_path = "/tmp/nltk_data"
os.makedirs(nltk_path, exist_ok=True)
nltk.data.path.append(nltk_path)

def download_nltk():
    try:
        nltk.data.find("tokenizers/punkt")
    except:
        nltk.download("punkt", download_dir=nltk_path)

    try:
        nltk.data.find("corpora/stopwords")
    except:
        nltk.download("stopwords", download_dir=nltk_path)

download_nltk()

# ------------------ GLOBALS ------------------
skills_list = [
    "python", "sql", "machine learning", "deep learning",
    "aws", "docker", "kubernetes", "flask", "django",
    "pandas", "numpy", "tensorflow", "pytorch"
]

model = None  # lazy load


# ------------------ MODEL LOADER ------------------
def get_model():
    global model
    if model is None:
        print("🔄 Loading ML model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded")
    return model


# ------------------ HELPERS ------------------
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

    return ""


def extract_skills(text):
    text = text.lower()
    return [skill for skill in skills_list if skill in text]


def compute_skill_score(resume_text):
    score = 0
    for skill in ["python", "sql", "machine learning", "aws", "docker"]:
        if skill in resume_text.lower():
            score += 20
    return min(score, 100)


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


# ------------------ MAIN FUNCTION ------------------
def run_resume_screening(job_text, applications):

    model = get_model()  # lazy load here

    job_skills = extract_skills(job_text)
    job_embedding = model.encode(job_text)

    results = []

    for app in applications:
        app_id = app[0]
        resume_filename = app[1]

        file_path = os.path.join(os.getcwd(), "uploads", resume_filename)

        if not os.path.exists(file_path):
            print("❌ Missing file:", file_path)
            continue

        resume_text = extract_text(file_path)

        if not resume_text:
            continue

        # -------- Candidate Info --------
        candidate_info = parse_resume(resume_text)
        name = candidate_info.get("name", "N/A")
        email = candidate_info.get("email", "N/A")
        phone = candidate_info.get("phone", "N/A")

        # -------- Skills --------
        resume_skills = extract_skills(resume_text)
        matched_skills = list(set(resume_skills) & set(job_skills))
        missing_skills = list(set(job_skills) - set(resume_skills))

        # -------- Semantic --------
        resume_embedding = model.encode(resume_text)
        similarity = cosine_similarity(
            [resume_embedding], [job_embedding]
        )[0][0]
        semantic_score = similarity * 100

        # -------- Scores --------
        skill_score = compute_skill_score(resume_text)
        exp_score = compute_experience_score(resume_text)
        edu_score = compute_education_score(resume_text)

        final_score = (
            0.4 * semantic_score +
            0.3 * skill_score +
            0.2 * exp_score +
            0.1 * edu_score
        )

        results.append((
            app_id,
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
            phone
        ))

    results.sort(key=lambda x: x[6], reverse=True)

    return results[:10]