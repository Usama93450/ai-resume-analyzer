import streamlit as st
import pdfplumber
import docx
import io
import re
from collections import Counter
import pandas as pd

st.set_page_config(page_title="AI Resume Analyzer", layout="wide")
st.title("📄 AI Resume Analyzer")

st.write("Upload your resume and job description to get an ATS score and improvement suggestions.")

# Upload Resume and Job Description
resume_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
job_desc = st.text_area("Paste Job Description Here")

# Function to extract text from PDF
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# Function to extract text from DOCX
def extract_text_from_docx(file):
    doc = docx.Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

# Text cleaning function
def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text.split()

# ATS Score function
def ats_score(resume_text, job_desc, keyword_match_percent):
    score = 0

    # Keyword score
    score += keyword_match_percent * 0.6  # 60% weight

    # Resume length check
    word_count = len(resume_text.split())
    if 300 < word_count < 800:
        score += 20  # good length
    else:
        score += 10  # average

    # Section check
    sections = ["experience", "education", "skills", "projects"]
    for sec in sections:
        if sec in resume_text.lower():
            score += 5

    return min(score, 100)

# Process when both resume and job description are uploaded
if resume_file and job_desc:
    # Extract Resume Text
    if resume_file.name.endswith(".pdf"):
        resume_text = extract_text_from_pdf(io.BytesIO(resume_file.read()))
    elif resume_file.name.endswith(".docx"):
        resume_text = extract_text_from_docx(io.BytesIO(resume_file.read()))
    else:
        resume_text = ""

    st.subheader("📄 Extracted Resume Text")
    st.text_area("Resume Content", resume_text[:2000], height=300)

    # Clean and Compare Keywords
    resume_words = clean_text(resume_text)
    job_words = clean_text(job_desc)

    matched_keywords = set(resume_words).intersection(set(job_words))
    keyword_match_percent = (len(matched_keywords) / len(set(job_words))) * 100 if job_words else 0

    st.subheader("✅ Keyword Matching")
    st.write(f"Matched Keywords: {', '.join(list(matched_keywords))}")
    st.write(f"Match Score: **{keyword_match_percent:.2f}%**")

    # Calculate ATS Score
    score = ats_score(resume_text, job_desc, keyword_match_percent)
    st.subheader("📊 ATS Score")
    st.progress(int(score))
    st.write(f"Your ATS Score: **{score:.2f}/100**")

    # Suggestions
    suggestions = []
    if keyword_match_percent < 50:
        suggestions.append("Add more job-related keywords to your resume.")
    if "skills" not in resume_text.lower():
        suggestions.append("Include a dedicated 'Skills' section.")
    if len(resume_text.split()) < 300:
        suggestions.append("Your resume seems too short. Add more details.")

    if suggestions:
        st.subheader("💡 Suggestions for Improvement")
        for s in suggestions:
            st.write(f"- {s}")
    else:
        st.success("Your resume looks well-optimized!")

    # Download Report
    report_data = {
        "ATS Score": [score],
        "Keyword Match %": [keyword_match_percent],
        "Matched Keywords": [", ".join(matched_keywords)],
        "Suggestions": ["; ".join(suggestions)]
    }
    report_df = pd.DataFrame(report_data)

    csv = report_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Report (CSV)", csv, "ats_report.csv", "text/csv")