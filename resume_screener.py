import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber

model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_text_from_pdf(path):

    text = ""

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t

    return text


def run_resume_screening(job_text, resume_folder):

    job_embedding = model.encode(job_text)

    results = []

    for resume_filename in os.listdir(resume_folder):

        if resume_filename.endswith(".pdf") or resume_filename.endswith(".txt"):

            path = os.path.join(resume_folder, resume_filename)

            # READ RESUME
            if resume_filename.endswith(".pdf"):
                resume_text = extract_text_from_pdf(path)

            else:
                with open(path, "r", encoding="utf-8") as f:
                    resume_text = f.read()

            # SEMANTIC SIMILARITY
            resume_embedding = model.encode(resume_text)

            similarity = cosine_similarity(
                [resume_embedding],
                [job_embedding]
            )[0][0]

            semantic_score = similarity * 100

            # TEMPORARY SIMPLE HYBRID SCORE
            final_score = semantic_score

            results.append((resume_filename, final_score))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:5]