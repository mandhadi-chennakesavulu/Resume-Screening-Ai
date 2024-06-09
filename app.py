import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
from docx import Document
from dotenv import load_dotenv
import time
import json
from io import BytesIO

load_dotenv()  # Load environment variables

genai.configure(api_key="AIzaSyB_MfpqTjenjmCAqczJ0eoRvKiyMXxRVFM")  # Use environment variable for the API key

# Function to instantiate model and get response
def get_gemini_response(input):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(input)
    return response.text

# Function to extract text from PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page_n in range(len(reader.pages)):
        page = reader.pages[page_n]
        text += str(page.extract_text())
    return text

# Function to extract text from DOCX
def input_docx_text(uploaded_file):
    doc = Document(uploaded_file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

# Prompt template
input_prompt = """
Hey act like a skilled or very experienced ATS (Application Tracking System)
with a deep understanding of tech field, software engineering, data science, data analyst
and bit data engineer. Your task is to evaluate the resume based on the given job description.
You must consider the job market is very competitive and you should provide best assistance
for improving the resumes. Assign the percentage matching based on JD (Job Description)
and the missing keywords with high accuracy.

I want the response in json structure like
{
    "JD Match": "%",
    "Missing Keywords": [],
    "Profile Summary": ""
}
"""

# Streamlit app
st.title("Resume Screening Software (ATS)")
st.subheader("Match Your Resume Against the Job Description")
jd = st.text_area("Paste the Job Description")
uploaded_files = st.file_uploader("Upload Resumes", type=["pdf", "docx"], accept_multiple_files=True, help="Please upload the PDF or DOCX")

submit = st.button("Submit")

if submit:
    suitable_files = []
    unsuitable_files = []

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Extract text based on file type
            if uploaded_file.type == "application/pdf":
                text = input_pdf_text(uploaded_file)
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text = input_docx_text(uploaded_file)
            
            # Generate AI response
            response_text = get_gemini_response([input_prompt, "Job Description\n" + jd, "Resume\n" + text])

            # Progress bar simulation
            bar = st.progress(0)
            for percent in range(50, 101, 10):
                time.sleep(0.3)  # Simulate processing time
                bar.progress(percent)
            
            # Handle JSON parsing errors
            try:
                response = json.loads(response_text.replace('\n', ''))  # Handle JSON parsing
                st.json(response)
                
                # Extract JD match percentage and determine folder
                match_percentage = float(response.get("JD Match", "0").replace("%", ""))
                
                # Write file to in-memory BytesIO object based on match percentage
                filename = uploaded_file.name
                file_bytes = uploaded_file.getvalue()  # Get file bytes
                
                if match_percentage >= 60:  # Assuming 60% as the threshold for suitability
                    suitable_files.append((filename, file_bytes))
                else:
                    unsuitable_files.append((filename, file_bytes))
                
                st.write(f"Resume '{filename}' categorized as {'Suitable' if match_percentage >= 60 else 'Unsuitable'}.")
            except json.JSONDecodeError as e:
                st.error(f"Error parsing response: {str(e)}")
                st.error("Response text:")
                st.code(response_text)

        # Function to create a download link for multiple files as a zip
        def create_zip_download(files, zip_name):
            from zipfile import ZipFile

            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                for file_name, file_bytes in files:
                    zip_file.writestr(file_name, file_bytes)
            zip_buffer.seek(0)  # Move to the start of the BytesIO buffer

            return zip_buffer

        # Create download buttons for suitable and unsuitable files
        if suitable_files:
            suitable_zip = create_zip_download(suitable_files, "Suitable_Resumes.zip")
            st.download_button(
                label="Download Suitable Resumes",
                data=suitable_zip,
                file_name="Suitable_Resumes.zip",
                mime="application/zip"
            )
        if unsuitable_files:
            unsuitable_zip = create_zip_download(unsuitable_files, "Unsuitable_Resumes.zip")
            st.download_button(
                label="Download Unsuitable Resumes",
                data=unsuitable_zip,
                file_name="Unsuitable_Resumes.zip",
                mime="application/zip"
            )
