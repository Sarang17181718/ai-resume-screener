import spacy
import re

nlp = spacy.load("en_core_web_sm")



def extract_email(text):

    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    emails = re.findall(email_pattern, text)

    return emails[0] if emails else "Not Found"


def extract_phone(text):

    phone_pattern = r"\+?\d[\d -]{8,12}\d"

    phones = re.findall(phone_pattern, text)

    return phones[0] if phones else "Not Found"


def extract_name(text):

    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text

    return "Not Found"


def extract_skills(text):

    skills_list = [
        "python","java","sql","machine learning","aws",
        "deep learning","nlp","flask","django",
        "tensorflow","pandas","numpy","data analysis"
    ]

    text = text.lower()

    found_skills = []

    for skill in skills_list:

        if skill in text:
            found_skills.append(skill)

    return found_skills


def parse_resume(text):

    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills
    }