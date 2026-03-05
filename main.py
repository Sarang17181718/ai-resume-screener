import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download once (comment after first run)
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('punkt_tab')

stop_words = set(stopwords.words('english'))

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)   # remove punctuation
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in stop_words]
    return " ".join(tokens)


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Read resume
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

resume_folder = "dataset/resumes/"
job_folder = "dataset/jobs/"

# Loop through each job file
for job_filename in os.listdir(job_folder):
    if job_filename.endswith(".txt"):

        with open(job_folder + job_filename, "r", encoding="utf-8") as file:
            job_text = file.read()

        cleaned_job = clean_text(job_text)

        scores = []

        # Compare with all resumes
        for resume_filename in os.listdir(resume_folder):
            if resume_filename.endswith(".txt"):

                with open(resume_folder + resume_filename, "r", encoding="utf-8") as file:
                    resume_text = file.read()

                cleaned_resume = clean_text(resume_text)

                vectorizer = TfidfVectorizer()
                tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_job])
                similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
                match_percentage = similarity[0][0] * 100

                scores.append((resume_filename, match_percentage))

        # Sort results for current job
        scores.sort(key=lambda x: x[1], reverse=True)

        print(f"\n===== Ranking for {job_filename} =====\n")

        for resume, score in scores:
            print(f"{resume} --> {score:.2f}%")

# Sort resumes by highest match
scores.sort(key=lambda x: x[1], reverse=True)

print("\nResume Ranking:\n")

for resume, score in scores:
    print(f"{resume} --> {score:.2f}%")

# Read job
with open("dataset/jobs/job_1.txt", "r", encoding="utf-8") as file:
    job_text = file.read()

# Clean both
cleaned_resume = clean_text(resume_text)
cleaned_job = clean_text(job_text)

# TF-IDF Vectorization
vectorizer = TfidfVectorizer()

tfidf_matrix = vectorizer.fit_transform([cleaned_resume, cleaned_job])

# Cosine similarity
similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

# Convert to percentage
match_percentage = similarity_score[0][0] * 100

print("Match Score: {:.2f}%".format(match_percentage))