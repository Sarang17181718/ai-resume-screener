import re
import os
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# nltk.download('punkt')
# nltk.download('stopwords')

stop_words = set(stopwords.words('english'))
skills_list = [
    "python",
    "java",
    "c++",
    "sql",
    "machine learning",
    "deep learning",
    "data analysis",
    "pandas",
    "numpy",
    "scikit learn",
    "tensorflow",
    "pytorch",
    "flask",
    "django",
    "aws",
    "docker",
    "kubernetes",
    "git",
    "linux",
    "html",
    "css",
    "javascript"
]
ground_truth = {
    "job_1.txt": ["resume_1.txt", "resume_3.txt"],
    "job_2.txt": ["resume_4.txt", "resume_7.txt"],
    "job_3.txt": ["resume_1.txt", "resume_14.txt"],
    "job_4.txt": ["resume_12.txt"],
    "job_5.txt": ["resume_3.txt"]
}

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stop_words]
    return " ".join(tokens)

def extract_skills(text):

    found_skills = []

    for skill in skills_list:
        if skill in text:
            found_skills.append(skill)

    return found_skills

resume_folder = "dataset/resumes/"
job_folder = "dataset/jobs/"

top_n = 3

for job_filename in os.listdir(job_folder):

    if job_filename.endswith(".txt"):

        with open(os.path.join(job_folder, job_filename), "r", encoding="utf-8") as file:
            job_text = file.read()

        cleaned_job = clean_text(job_text)
        job_skills = extract_skills(cleaned_job)
        print("\nrequired skills:",job_skills)

        scores = []

        for resume_filename in os.listdir(resume_folder):

            if resume_filename.endswith(".txt"):

                with open(os.path.join(resume_folder, resume_filename), "r", encoding="utf-8") as file:
                    resume_text = file.read()

                cleaned_resume = clean_text(resume_text)
                resume_skills=extract_skills(cleaned_resume)
                matched_skills = set(job_skills) &set(resume_skills)
                missing_skills = set(job_skills) - set(resume_skills)

                vectorizer = TfidfVectorizer()

                tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_job])

                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

                match_percentage = similarity[0][0] * 100

                scores.append((resume_filename, match_percentage))

        scores.sort(key=lambda x: x[1], reverse=True)
        predicted_resumes = [resume for resume, score in scores[:top_n]]
        actual_resumes = ground_truth.get(job_filename, [])
        true_positive = len(set(predicted_resumes) & set(actual_resumes))
        precision = true_positive / len(predicted_resumes) if predicted_resumes else 0
        recall = true_positive / len(actual_resumes) if actual_resumes else 0
        if precision + recall == 0:
            f1_score = 0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
    

    

        print(f"\n===== Top {top_n} resumes for {job_filename} =====\n")

        for resume, score in scores[:top_n]:
            print(f"\n{resume} --> {score:.2f}%")

            with open(os.path.join(resume_folder, resume), "r", encoding="utf-8") as file:
                resume_text = file.read()
                cleaned_resume = clean_text(resume_text)
                resume_skills = extract_skills(cleaned_resume)
                matched_skills = set(job_skills) & set(resume_skills)
                missing_skills = set(job_skills) - set(resume_skills)

                print("Matched Skills:", list(matched_skills))
                print("Missing Skills:", list(missing_skills))
        print("\nModel Evaluation:")
        print(f"Precision: {precision:.2f}")
        print(f"Recall: {recall:.2f}")
        print(f"F1 Score: {f1_score:.2f}")





    
    
    


    
    

    

        

   
    
    

    