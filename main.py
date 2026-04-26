import pdfplumber
import fitz
import re
import os
import pandas as pd
import nltk

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from sentence_transformers import SentenceTransformer


# ------------------ FUNCTIONS ------------------

def download_nltk_data():
    try:
        nltk.data.find('corpora/stopwords')
    except:
        nltk.download('stopwords')

    try:
        nltk.data.find('tokenizers/punkt')
    except:
        nltk.download('punkt')


def clean_text(text, stop_words):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = word_tokenize(text)
    tokens = [w for w in tokens if w not in stop_words]
    return " ".join(tokens)


def extract_skills(text, skills_list):
    return [skill for skill in skills_list if skill in text]


def extract_pdf_text(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    return text


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


def extract_experience(text):
    matches = re.findall(r'(\d+)\s+years', text)
    return max([int(x) for x in matches]) if matches else 0


def extract_education(text, education_keywords):
    return [edu for edu in education_keywords if edu in text]


# ------------------ MAIN ------------------

def main():

    # Setup
    download_nltk_data()
    stop_words = set(stopwords.words('english'))

    model_semantic = SentenceTransformer('all-MiniLM-L6-v2')

    skills_list = [
        "python","java","c++","sql","machine learning","deep learning",
        "pandas","numpy","scikit learn","tensorflow","pytorch",
        "flask","django","aws","docker","kubernetes","git",
        "linux","html","css","javascript",
        "terraform","ansible","jenkins","prometheus","grafana"
    ]

    education_keywords = [
        "bachelor","master","phd","btech","mtech",
        "computer science","information technology","engineering"
    ]

    ground_truth = {
        "job_1.txt": ["resume_1.txt", "resume_3.txt"],
        "job_2.txt": ["resume_4.txt", "resume_7.txt"],
        "job_3.txt": ["resume_1.txt", "resume_14.txt"],
        "job_4.txt": ["resume_12.txt"],
        "job_5.txt": ["resume_3.txt"]
    }

    resume_folder = "dataset/resumes/"
    job_folder = "dataset/jobs/"
    top_n = 3

    training_data = []

    # ------------------ LOOP ------------------

    for job_filename in os.listdir(job_folder):

        if job_filename.endswith(".txt"):

            with open(os.path.join(job_folder, job_filename), "r", encoding="utf-8") as file:
                job_text = file.read()

            cleaned_job = clean_text(job_text, stop_words)
            job_skills = extract_skills(cleaned_job, skills_list)

            print("\nRequired skills:", job_skills)

            scores = []

            for resume_filename in os.listdir(resume_folder):

                if resume_filename.endswith(".txt") or resume_filename.endswith(".pdf"):

                    resume_path = os.path.join(resume_folder, resume_filename)

                    if resume_filename.endswith(".pdf"):
                        resume_text = extract_pdf_text(resume_path)
                    else:
                        with open(resume_path, "r", encoding="utf-8") as f:
                            resume_text = f.read()

                    cleaned_resume = clean_text(resume_text, stop_words)

                    resume_skills = extract_skills(cleaned_resume, skills_list)

                    matched_skills = set(job_skills) & set(resume_skills)
                    skill_score = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0

                    resume_exp = extract_experience(cleaned_resume)
                    job_exp = extract_experience(cleaned_job)
                    exp_score = min((resume_exp / job_exp) * 100, 100) if job_exp else 50

                    resume_edu = extract_education(cleaned_resume, education_keywords)
                    job_edu = extract_education(cleaned_job, education_keywords)
                    edu_score = (len(set(resume_edu) & set(job_edu)) / len(job_edu)) * 100 if job_edu else 50

                    overall_score = (0.5 * skill_score + 0.3 * exp_score + 0.2 * edu_score)

                    # TF-IDF similarity
                    vectorizer = TfidfVectorizer()
                    tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_job])
                    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

                    label = 1 if resume_filename in ground_truth.get(job_filename, []) else 0

                    training_data.append([
                        resume_filename, job_filename, similarity,
                        skill_score, exp_score, edu_score,
                        overall_score, label
                    ])

                    scores.append((resume_filename, overall_score, skill_score, exp_score, edu_score))

            scores.sort(key=lambda x: x[1], reverse=True)

            print(f"\n===== Candidate Ranking for {job_filename} =====")

            for i, (resume, score, skill_s, exp_s, edu_s) in enumerate(scores[:top_n], 1):
                print(f"\nRank {i}: {resume}")
                print(f"Overall Score: {score:.2f}")
                print(f"Skill Score: {skill_s:.2f}")
                print(f"Experience Score: {exp_s:.2f}")
                print(f"Education Score: {edu_s:.2f}")

    # ------------------ ML ------------------

    df = pd.DataFrame(training_data, columns=[
        "resume","job","similarity","skill_score",
        "exp_score","edu_score","overall_score","label"
    ])

    X = df[["similarity","skill_score","exp_score","edu_score","overall_score"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Logistic Regression
    model = LogisticRegression()
    model.fit(X_train, y_train)
    print("\nLogistic Accuracy:", accuracy_score(y_test, model.predict(X_test)))

    # Random Forest
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)
    print("Random Forest Accuracy:", accuracy_score(y_test, rf_model.predict(X_test)))

    # ------------------ SEMANTIC ------------------

    print("\nRunning MiniLM Semantic Similarity...\n")

    job_filename = "job_1.txt"
    job_path = os.path.join(job_folder, job_filename)

    with open(job_path, "r", encoding="utf-8") as f:
        job_text = f.read()

    job_embedding = model_semantic.encode(job_text)

    hybrid_scores = []

    for resume_filename in os.listdir(resume_folder):

        if resume_filename.endswith(".txt") or resume_filename.endswith(".pdf"):

            resume_path = os.path.join(resume_folder, resume_filename)

            if resume_filename.endswith(".txt"):
                with open(resume_path, "r", encoding="utf-8") as f:
                    resume_text = f.read()
            else:
                resume_text = extract_text_from_pdf(resume_path)

            resume_embedding = model_semantic.encode(resume_text)

            similarity = cosine_similarity([resume_embedding], [job_embedding])[0][0]
            semantic_percentage = similarity * 100

            row = df[(df["resume"] == resume_filename) & (df["job"] == job_filename)]

            if not row.empty:
                skill_score = row["skill_score"].values[0]
                exp_score = row["exp_score"].values[0]
                edu_score = row["edu_score"].values[0]
            else:
                skill_score = exp_score = edu_score = 0

            final_score = (
                0.4 * semantic_percentage +
                0.3 * skill_score +
                0.2 * exp_score +
                0.1 * edu_score
            )

            hybrid_scores.append((resume_filename, final_score))

    hybrid_scores.sort(key=lambda x: x[1], reverse=True)

    result_df = pd.DataFrame(hybrid_scores, columns=["resume","final_score"])
    result_df.to_csv("final_resume_ranking.csv", index=False)

    print("\nResults saved to final_resume_ranking.csv")

    print("\n===== Final Hybrid Ranking =====\n")
    for i, (resume, score) in enumerate(hybrid_scores[:top_n], 1):
        print(f"{i}. {resume} → {score:.2f}")


# ------------------ ENTRY ------------------

if __name__ == "__main__":
    main()