import streamlit as st
import fitz  # PyMuPDF
import easyocr
from PIL import Image
from dotenv import load_dotenv
import google.generativeai as genai
import json
import os
import base64

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def read_pdf(file):
    """Extract text from PDF file."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = "\n".join(page.get_text("text") for page in doc)
    return text

def read_image(file):
    """Extract text from image file using EasyOCR."""
    reader = easyocr.Reader(['en'])  # Initialize EasyOCR with English language
    image = Image.open(file)
    text = reader.readtext(image, detail=0)  # Extract text without bounding boxes
    return " ".join(text) if text else "No text detected"

def extract_key_value_pairs(text):
    """Extract key-value pairs using Gemini API."""
    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
    prompt = f"Extract key-value pairs from the following text and return a **valid JSON object**:\n\n{text}"
    
    response = model.generate_content(prompt)
    
    if response and response.text:
        cleaned_text = response.text.strip("`json\n").strip("```")  # Remove backticks and "json"
        try:
            return json.loads(cleaned_text)  # Parse JSON response
        except json.JSONDecodeError:
            return {"Error": "Invalid JSON format returned from Gemini", "Raw Response": cleaned_text}
    
    return {"Error": "No response from Gemini"}

def display_pdf(file):
    """Convert PDF to base64 and render it in an iframe."""
    base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def display_image(file):
    """Display uploaded image."""
    image = Image.open(file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

# 🎨 Streamlit UI
st.set_page_config(layout="wide")  # Set layout to wide mode

st.title("📄 File Key-Value Extractor with Gemini")
st.write("Upload a PDF or image (JPG, PNG) to extract key-value pairs using Gemini API.")

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "jpg", "png"])

if uploaded_file is not None:
    # Create a 2-column layout for split-screen
    col1, col2 = st.columns([1, 1])  # Equal width columns
    
    with col1:
        st.subheader("📄 Uploaded File Preview")
        if uploaded_file.type == "application/pdf":
            display_pdf(uploaded_file)
        else:
            display_image(uploaded_file)
    
    with col2:
        with st.spinner("Extracting text..."):
            if uploaded_file.type == "application/pdf":
                text = read_pdf(uploaded_file)
            else:
                text = read_image(uploaded_file)
            st.success("Text extraction completed!")

        if st.button("Extract Key-Value Pairs"):
            with st.spinner("Extracting key-value pairs..."):
                result = extract_key_value_pairs(text)
                st.subheader("📊 Extracted JSON Output")
                st.json(result)