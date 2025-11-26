import streamlit as st
import google.generativeai as genai
import re
import pdfplumber
import docx2txt
import base64

API_KEY = "AIzaSyCe94e7LUc6CIYOKTXVmwKdNM8Mbl-s_H0"
genai.configure(api_key=API_KEY)

st.set_page_config(
    page_title="AI Interviewer & Resume Analyzer",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
body { background-color: #0e1117; }
.big-header {
    font-size: 50px !important;
    font-weight: 900;
    text-align: center;
    color: white;
}
.card {
    background: #111418;
    padding: 25px;
    border-radius: 15px;
    border: 1px solid #30363d;
    margin-bottom: 20px;
}
textarea, input { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "interview_active" not in st.session_state:
    st.session_state.interview_active = False
if "feedback" not in st.session_state:
    st.session_state.feedback = None

def ai_model():
    return genai.GenerativeModel("gemini-2.5-flash")

def extract_text_from_pdf(uploaded_file):
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(uploaded_file):
    return docx2txt.process(uploaded_file)

def generate_questions(jd, role, level, exp, org):
    difficulty = {
        "Intern": "Ask basic and learning-focused questions",
        "Entry": "Ask core fundamental skill questions",
        "Experienced": f"Ask leadership and scenario-based questions for {exp} years"
    }[level.split()[0]]

    prompt = f"""
    Act as an expert interviewer for {org}.
    Generate exactly 5 interview questions for the role: {role}
    Level: {level}
    Job Description: {jd}
    Difficulty rule: {difficulty}

    Output format:
    1. Question
    2. Question
    3. Question
    4. Question
    5. Question
    """

    response = ai_model().generate_content(prompt)
    return re.findall(r"^\d+\.\s*(.+)", response.text, re.MULTILINE)

def generate_feedback(role, questions, answers):
    transcript = "\n".join(
        [f"Q{i+1}: {q}\nA: {answers.get(i,'No answer')}" for i, q in enumerate(questions)]
    )

    prompt = f"""
    You are HR reviewing an interview for role: {role}
    Transcript:
    {transcript}

    Provide structured evaluation:
    For each question:
        - Score (x/10)
        - What they should improve
    Final:
        - Overall score (out of 100)
        - Verdict (Hire/Reject)
        - Short summary
    """

    return ai_model().generate_content(prompt).text

def analyze_resume(text, role):
    prompt = f"""
    You are an ATS (Applicant Tracking System) + Senior HR.
    Analyze this resume for the role: {role}

    RESUME:
    {text}

    Provide:
    1. ATS Score (0–100)
    2. Strengths
    3. Weak Points
    4. Missing keywords
    5. How to improve (bullet points)
    6. Summary in 3 lines
    """

    return ai_model().generate_content(prompt).text

tabs = st.tabs(["🧠 Interview", "📄 Resume Analyzer", "About"])

with tabs[0]:

    st.markdown("<h1 class='big-header'>🧠 AskAstra</h1>", unsafe_allow_html=True)
    st.write("")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.text_input("Organization", key="org")
        st.text_input("Role", key="role")
        st.selectbox("Level", ["Intern", "Entry Level (0-2 Years)", "Experienced"], key="level")
        exp = st.text_input("Experience (years)", key="exp")

    with col2:
        jd = st.text_area("Paste Job Description", height=200, key="jd")

    if st.button("🚀 Generate Interview Questions"):
        if not jd or not st.session_state.org or not st.session_state.role:
            st.error("Fill all fields first!")
        else:
            st.session_state.questions = generate_questions(jd, st.session_state.role, st.session_state.level, exp, st.session_state.org)
            st.session_state.interview_active = True
            st.session_state.current_index = 0
            st.session_state.answers = {}
            st.session_state.feedback = None
            st.rerun()

    if st.session_state.interview_active:

        q_idx = st.session_state.current_index
        total = len(st.session_state.questions)

        if q_idx < total:
            st.markdown(f"<div class='card'><h3>❓ Question {q_idx+1}</h3><p>{st.session_state.questions[q_idx]}</p></div>", unsafe_allow_html=True)

            user_ans = st.text_area("Your Answer", key=f"ans_{q_idx}", height=180)
            if st.button("Submit Answer"):
                st.session_state.answers[q_idx] = user_ans
                st.session_state.current_index += 1
                st.rerun()
        else:
            st.success("Interview Completed!")

            if st.button("📝 Generate Feedback Report"):
                st.session_state.feedback = generate_feedback(st.session_state.role, st.session_state.questions, st.session_state.answers)
                st.rerun()

            if st.session_state.feedback:
                st.markdown(st.session_state.feedback)

with tabs[1]:

    st.markdown("<h1 class='big-header'>📄 AI Resume Analyzer + ATS Score</h1>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])

    role_resume = st.text_input("Target Role for Resume Review")

    if uploaded and role_resume:
        if st.button("🔍 Analyze Resume"):
            file_ext = uploaded.name.split(".")[-1]

            if file_ext == "pdf":
                resume_text = extract_text_from_pdf(uploaded)
            else:
                resume_text = extract_text_from_docx(uploaded)

            with st.spinner("Analyzing Resume..."):
                result = analyze_resume(resume_text, role_resume)

            st.markdown(result)


with tabs[2]:
    st.markdown("""
<style>
.big-title {
    font-size: 30px;
    font-weight: 700;
}
.big-text {
    font-size: 18px;
    line-height: 1.6;
}
</style>

<p class="big-title">⭐ AskAstra – Project Overview</p>

<p class="big-text">
AskAstra is an intelligent, personalized interview preparation system designed to help students and job seekers 
practice and master interview skills using artificial intelligence. The platform simulates real-world interview scenarios, 
analyzes user responses, and provides detailed feedback to improve confidence, communication, and performance.
</p>

<p class="big-text">
The application uses Natural Language Processing (NLP), Machine Learning, and Generative AI models to generate questions, 
evaluate answers, and guide users across different domains such as technical interviews, HR interviews, coding interviews, 
and behavioral assessments. With its interactive UI and real-time feedback system, AskAstra acts as a virtual 
mentor that is accessible anytime, anywhere.
</p>

<hr>

<h3>🎯 Purpose</h3>

<p class="big-text">
The main goal of AskAstra is to eliminate the anxiety, confusion, and lack of preparation that many candidates face 
before interviews. Instead of memorizing answers, the system helps users practice in a realistic environment and receive 
actionable feedback that improves communication skills, content structure, and confidence.
</p>
""", unsafe_allow_html=True)

footer_html = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: black;
    color: gold;
    text-align: center;
    padding: 8px;
    font-size: 16px;
    border-top: 1px solid gold;
    font-weight: bold;
}
</style>

<div class="footer">
    Made with ❤️ by Team Nismay
</div>
"""

st.markdown(footer_html, unsafe_allow_html=True)

