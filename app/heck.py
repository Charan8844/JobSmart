from flask import Flask, request, jsonify, render_template
import requests

app = Flask(__name__)

# Replace with your actual API key for the Resume Parser
API_KEY = 'HrPoZjCg69XCcHnBBn1U6q1IWwKc2YMX'

# Function to parse the resume using API
def parse_resume(file):
    url = "https://api.apilayer.com/resume_parser/parse"
    headers = {"apikey": API_KEY}
    files = {'file': file}
    
    response = requests.post(url, headers=headers, files=files)
    if response.status_code == 200:
        return response.json()  # Assuming it returns skills, education, and experience as lists
    else:
        return {"error": "Failed to parse resume"}

# Function to extract keywords from job description
def extract_keywords_from_job_desc(job_desc):
    # Simple text extraction: tokenize the job description and remove stop words
    common_stopwords = set(['the', 'and', 'a', 'an', 'in', 'on', 'for', 'to', 'of'])
    words = job_desc.lower().split()
    keywords = [word for word in words if word not in common_stopwords]
    return set(keywords)

# Function to compare resume and job description keywords
def compare_keywords(resume_keywords, job_desc_keywords):
    common_keywords = resume_keywords.intersection(job_desc_keywords)
    return common_keywords

# Function to give suggestions based on missing keywords
def generate_suggestions(resume_keywords, job_desc_keywords):
    missing_keywords = job_desc_keywords - resume_keywords
    suggestions = []
    
    if missing_keywords:
        suggestions.append(f"Consider adding these missing keywords: {', '.join(missing_keywords)}")
    else:
        suggestions.append("Your resume seems to match the job description well!")
    
    return suggestions

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    # Check if file is provided
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Call the resume parser API
    resume_data = parse_resume(file)
    
    # Extract keywords from resume (Assuming skills are returned in 'skills' field)
    resume_keywords = set(resume_data.get('skills', []))

    return jsonify(resume_keywords)

@app.route('/check_resume', methods=['POST'])
def check_resume():
    data = request.get_json()
    job_desc = data.get('job_desc', '')
    resume_data = data.get('resume_data', [])

    # Extract keywords from the job description
    job_desc_keywords = extract_keywords_from_job_desc(job_desc)

    # Compare resume and job description keywords
    common_keywords = compare_keywords(resume_data, job_desc_keywords)

    # Generate suggestions based on comparison
    suggestions = generate_suggestions(resume_data, job_desc_keywords)

    # Prepare the response based on keyword match
    if common_keywords:
        return jsonify({"message": "Resume matches job description", 
                        "common_keywords": list(common_keywords), 
                        "suggestions": suggestions})
    else:
        return jsonify({"message": "No match found", 
                        "common_keywords": [], 
                        "suggestions": suggestions})

if __name__ == '__main__':
    app.run(debug=True)
