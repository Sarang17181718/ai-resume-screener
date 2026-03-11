def run_resume_screening(job_text, resume_folder):

    results = []

    for resume_filename in os.listdir(resume_folder):

        if resume_filename.endswith(".pdf") or resume_filename.endswith(".txt"):

            # extract resume text
            # compute semantic score
            # compute skill score
            # compute hybrid score

            results.append((resume_filename, final_score))

    results.sort(key=lambda x: x[1], reverse=True)

    return results[:5]