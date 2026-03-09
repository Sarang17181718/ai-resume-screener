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
# nltk.download('punkt')
# nltk.download('stopwords')

training_data = []

stop_words = set(stopwords.words('english'))

skills_list = [
    "python","java","c++","sql","machine learning","deep learning",
    "data analysis","pandas","numpy","scikit learn","tensorflow",
    "pytorch","flask","django","aws","docker","kubernetes","git",
    "linux","html","css","javascript"
]
education_keywords = [
    "bachelor",
    "master",
    "phd",
    "btech",
    "mtech",
    "computer science",
    "information technology",
    "engineering"
]

ground_truth = {
    "job_1.txt": ["resume_1.txt", "resume_3.txt"],
    "job_2.txt": ["resume_4.txt", "resume_7.txt"],
    "job_3.txt": ["resume_1.txt", "resume_14.txt"],
    "job_4.txt": ["resume_12.txt"],
    "job_5.txt": ["resume_3.txt"]
}
# Text Cleaning

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = word_tokenize(text)
    tokens = [w for w in tokens if w not in stop_words]
    return " ".join(tokens)

# Skill Extraction

def extract_skills(text):
    found = []
    for skill in skills_list:
        if skill.lower() in text:
            found.append(skill)
    return found

resume_folder = "dataset/resumes/"
job_folder = "dataset/jobs/"
top_n = 3

def extract_experience(text):

    pattern = r'(\d+)\s+years'

    matches = re.findall(pattern, text)

    if matches:
        return max([int(x) for x in matches])
    else:
        return 0
    
def extract_education(text):

    found = []

    for edu in education_keywords:

        if edu in text:
            found.append(edu)

    return found
# TF-IDF Matching

for job_filename in os.listdir(job_folder):

    if job_filename.endswith(".txt"):

        with open(os.path.join(job_folder, job_filename), "r", encoding="utf-8") as file:
            job_text = file.read()

        cleaned_job = clean_text(job_text)
        job_skills = extract_skills(cleaned_job)

        print("\nRequired skills:", job_skills)

        scores = []

        for resume_filename in os.listdir(resume_folder):

            if resume_filename.endswith(".txt"):

                with open(os.path.join(resume_folder, resume_filename), "r", encoding="utf-8") as file:
                    resume_text = file.read()

                cleaned_resume = clean_text(resume_text)

                resume_skills = extract_skills(cleaned_resume)

                matched_skills = set(job_skills) & set(resume_skills)
                missing_skills = set(job_skills) - set(resume_skills)
                skill_score = (len(matched_skills) / len(job_skills)) * 100 if job_skills else 0

                resume_exp = extract_experience(cleaned_resume)
                job_exp = extract_experience(cleaned_job)
                if job_exp == 0:
                    exp_score = 50
                else:
                    exp_score = min((resume_exp / job_exp) * 100, 100)
                resume_edu = extract_education(cleaned_resume)
                job_edu = extract_education(cleaned_job)
                edu_match = set(resume_edu) & set(job_edu)
                edu_score = (len(edu_match) / len(job_edu)) * 100 if job_edu else 50

                overall_score = (0.5 * skill_score +0.3 * exp_score +0.2 * edu_score)

  

                       
                vectorizer = TfidfVectorizer()
                tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_job])

                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                similarity_score = similarity[0][0]
                match_percentage = similarity_score * 100

                skill_match = len(matched_skills)

                label = 1 if resume_filename in ground_truth.get(job_filename, []) else 0

                training_data.append([resume_filename,job_filename,similarity_score,skill_score,
                                       exp_score,edu_score,overall_score, label])

                scores.append((resume_filename, overall_score, skill_score, exp_score, edu_score))

        scores.sort(key=lambda x: x[1], reverse=True)

        predicted_resumes = [resume for resume, _, _, _, _ in scores[:top_n]]
        actual_resumes = ground_truth.get(job_filename, [])

        true_positive = len(set(predicted_resumes) & set(actual_resumes))

        precision = true_positive / len(predicted_resumes) if predicted_resumes else 0
        recall = true_positive / len(actual_resumes) if actual_resumes else 0

        if precision + recall == 0:
            f1_score = 0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)

        print(f"\n===== Candidate Ranking for {job_filename} =====")
        rank = 1
        for resume, score, skill_s, exp_s, edu_s in scores[:top_n]:
            print(f"\nRank {rank}: {resume}")
            print(f"Overall Score: {score:.2f}")
            print(f"Skill Score: {skill_s:.2f}")
            print(f"Experience Score: {exp_s:.2f}")
            print(f"Education Score: {edu_s:.2f}")
            rank += 1


            matched = set(job_skills) & set(resume_skills)
            missing = set(job_skills) - set(resume_skills)
            skill_score = (len(matched) / len(job_skills)) * 100 if job_skills else 0
            
            



        print("\nModel Evaluation:")
        print(f"Precision: {precision:.2f}")
        print(f"Recall: {recall:.2f}")
        print(f"F1 Score: {f1_score:.2f}")
        




# ML Dataset

df = pd.DataFrame(training_data,
columns=["resume","job","similarity","skill_score","exp_score","edu_score","overall_score","label"])


print("\nTraining dataset:\n")
print(df.head())


X = df[["similarity","skill_score","exp_score","edu_score","overall_score"]]
y = df["label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Logistic Regression

model = LogisticRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print("\nLogistic Regression Accuracy:", accuracy)

# Random Forest

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

rf_pred = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_pred)

print("\nRandom Forest Accuracy:", rf_accuracy)


rf_prob = rf_model.predict_proba(X)
df["rf_hiring_probability"] = rf_prob[:, 1] * 100

top_candidates = df.sort_values(
    by="rf_hiring_probability", ascending=False).reset_index(drop=True)

print("\nTop Hiring Predictions (Random Forest):\n")
print(top_candidates[["resume", "job", "rf_hiring_probability"]].head(10))

# Logistic Probability

probabilities = model.predict_proba(X)

df["hiring_probability"] = probabilities[:, 1] * 100

top_candidates = df.sort_values(
    by="hiring_probability", ascending=False).reset_index(drop=True)

df["hiring_probability"] = df["hiring_probability"].round(2)

print("\nTop Hiring Predictions (Logistic Regression):\n")
print(top_candidates[["resume", "job", "hiring_probability"]].head(10))

# MiniLM Semantic Matching

print("\nRunning MiniLM Semantic Similarity...\n")

model_semantic = SentenceTransformer('all-MiniLM-L6-v2')

resume_path = os.path.join(resume_folder, "resume_1.txt")
job_path = os.path.join(job_folder, "job_1.txt")

with open(resume_path, "r", encoding="utf-8") as f:
    resume_text = f.read()

with open(job_path, "r", encoding="utf-8") as f:
    job_text = f.read()

resume_embedding = model_semantic.encode(resume_text)
job_embedding = model_semantic.encode(job_text)

similarity = cosine_similarity(
    [resume_embedding],
    [job_embedding]
)

print("Semantic Similarity Score:", similarity[0][0])