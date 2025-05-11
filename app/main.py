import os
from flask import Flask, request, jsonify, render_template
import requests
import PyPDF2
import docx
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ADZUNA_API_URL = "https://api.adzuna.com/v1/api/jobs"
APP_ID = os.environ.get("ADZUNA_API_ID")  # Get API ID from environment variable
APP_KEY = os.environ.get("ADZUNA_API_KEY")  # Get API Key from environment variable

# Upload Folder for Resume Matching
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

nltk.download('punkt')
nltk.download('stopwords')

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(file)
    return ''.join(page.extract_text() for page in pdf_reader.pages)

def extract_text_from_docx(file):
    doc = docx.Document(file)
    return ''.join(para.text for para in doc.paragraphs)

def clean_text(text):
    stop_words = set(stopwords.words('english'))
    words = word_tokenize(text.lower())
    return [w for w in words if w.isalnum() and w not in stop_words]

def ultra_loose_match(resume_words, jd_words):
    matched = 0
    for jd_word in jd_words:
        for res_word in resume_words:
            if jd_word in res_word or res_word in jd_word:
                matched += 1
                break
    return matched

# Route: Home Page (combined layout)
@app.route('/')
def home():
    return render_template('index.html')

# Route: Job Search API
@app.route('/get_jobs', methods=['POST'])
def get_jobs():
    data = request.get_json()
    location = data.get("location", "").strip()
    role = data.get("role", "").strip().lower()
    job_type = data.get("jobType", "").strip().lower()
    results_per_page = int(data.get("results_per_page", 10))

    country_codes = {
        "india": "in",
        "united states": "us",
        "united kingdom": "gb",
        "australia": "au",
        "canada": "ca",
        "germany": "de"
    }
    country = country_codes.get(location.lower(), "in")

    url = f"{ADZUNA_API_URL}/{country}/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 50,
        "what": role,
        "where": location,
        "content-type": "application/json"
    }

    if job_type == "full-time":
        params["full_time"] = 1
    elif job_type == "part-time":
        params["part_time"] = 1
    elif job_type == "remote":
        params["remote"] = 1
    elif job_type == "internship":
        params["contract"] = 1

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        jobs = response.json().get("results", [])
        filtered_jobs = [
            job for job in jobs if role in job.get("title", "").lower()
        ]
        return jsonify(filtered_jobs[:results_per_page])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route: Resume Checker API (returns JSON)
@app.route('/resume_checker', methods=['POST'])
def resume_checker():
    resume_file = request.files.get('resume')
    jd_text = request.form.get('job_description')

    if resume_file and allowed_file(resume_file.filename):
        path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
        resume_file.save(path)

        with open(path, 'rb') as file:
            resume_text = extract_text_from_pdf(file) if resume_file.filename.endswith('.pdf') else extract_text_from_docx(file)

        resume_words = clean_text(resume_text)
        jd_words = clean_text(jd_text)

        matched_count = ultra_loose_match(resume_words, jd_words)
        match_percentage = (matched_count / len(set(jd_words))) * 100 if jd_words else 0

        if match_percentage >= 70:
            match_result = 'Great Match'
            suggestions = "Great job! Consider emphasizing relevant skills more for a stronger match."
        elif match_percentage >= 60:
            match_result = 'Good Match'
            suggestions = "Good match! You could emphasize experience in machine learning or Python."
        elif match_percentage >= 50:
            match_result = 'Normal Match'
            suggestions = "Normal match. Try adding more project-based experience or skills relevant to the job."
        elif match_percentage >= 30:
            match_result = 'Worse Match'
            suggestions = "Worse match. Revise your resume to focus more on relevant experience and skills."
        else:
            match_result = 'Not a good match'
            suggestions = "Consider revising your resume to align better with the job description."

        resume_links = [
            {"name": "Zety", "url": "https://zety.com/resume-builder"},
            {"name": "Canva", "url": "https://www.canva.com/resumes/templates/"},
            {"name": "Novoresume", "url": "https://novoresume.com/"}
        ]

        return jsonify({
            "match_result": match_result,
            "match_percentage": round(match_percentage, 2),
            "suggestions": suggestions,
            "resume_links": resume_links
        })

    return jsonify({"error": "Invalid file or job description"}), 400

if __name__ == '__main__':
    app.run(debug=True)
