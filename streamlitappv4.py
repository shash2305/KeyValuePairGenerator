import streamlit as st
import fitz  # PyMuPDF
import easyocr
import cv2
import numpy as np
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

def preprocess_image(image):
    """Preprocess image to correct minor orientation shifts."""
    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(largest_contour)
        angle = rect[-1]
        
        if angle < -45:
            angle += 90
        
        (h, w) = image_np.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image_np, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return Image.fromarray(rotated)
    
    return image

def read_image(file, languages=['en']):
    """Extract text from image file using EasyOCR."""
    reader = easyocr.Reader(languages)
    image = Image.open(file)
    image = preprocess_image(image)
    text = reader.readtext(np.array(image), detail=0)
    return " ".join(text) if text else "No text detected"

def extract_key_value_pairs(text):
    """Extract key-value pairs using Gemini API."""
    model = genai.GenerativeModel("gemini-2.0-pro-exp-02-05")
    prompt = f"Extract key-value pairs from the following text and return a **valid JSON object**:\n\n{text}"
    
    response = model.generate_content(prompt)
    
    if response and response.text:
        cleaned_text = response.text.strip("`json\n").strip("```")
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            return {"Error": "Invalid JSON format returned", "Raw Response": cleaned_text}
    
    return {"Error": "No response"}

def display_pdf(file):
    """Convert PDF to base64 and render it in an iframe."""
    base64_pdf = base64.b64encode(file.getvalue()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def display_image(file):
    """Display uploaded image."""
    image = Image.open(file)
    st.image(image, caption="Uploaded Image", use_column_width=True)

def manual_edit_kv_pairs(extracted_data):
    """Allow users to manually edit extracted key-value pairs without refreshing the page."""
    st.subheader("✏️ Edit Key-Value Pairs")

    if not isinstance(extracted_data, dict):
        st.error("Extracted data is not in valid JSON format.")
        return None

    # Initialize session state
    if "updated_json" not in st.session_state or not st.session_state["updated_json"]:
        st.session_state["updated_json"] = extracted_data.copy()

    updated_data = st.session_state["updated_json"]

    def update_key(old_key, new_key):
        """Update key name in session state."""
        if new_key and old_key != new_key:
            st.session_state["updated_json"][new_key] = st.session_state["updated_json"].pop(old_key)

    def update_value(key):
        """Update value in session state."""
        st.session_state["updated_json"][key] = st.session_state[f"value_{key}"]

    new_updated_data = {}

    for key, value in list(updated_data.items()):
        col1, col2 = st.columns([1, 2])

        new_key = col1.text_input(
            f"Key:", value=key, key=f"key_{key}", on_change=update_key, args=(key, f"key_{key}")
        )

        new_value = col2.text_input(
            f"Value:", value=value, key=f"value_{key}", on_change=update_value, args=(key,)
        )

        new_updated_data[new_key] = new_value

    st.session_state["updated_json"] = new_updated_data  # Persist updates

    if st.button("Save Changes"):
        st.success("Updated key-value pairs saved!")

    return st.session_state["updated_json"]





# 🎨 Streamlit UI
st.set_page_config(layout="wide")
st.title("📄 File Key-Value Extractor")
st.write("Upload a PDF or image (JPG, PNG) to extract key-value pairs")

uploaded_file = st.file_uploader("Choose a file", type=["pdf", "jpg", "png"])
selected_languages = st.multiselect("Select OCR languages", ["en", "fr", "es", "de", "hi", "zh"], default=["en"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📄 Uploaded File Preview")
        if uploaded_file.type == "application/pdf":
            display_pdf(uploaded_file)
        else:
            display_image(uploaded_file)
    
    with col2:
        with st.spinner("Extracting text..."):
            text = read_pdf(uploaded_file) if uploaded_file.type == "application/pdf" else read_image(uploaded_file, languages=selected_languages)
            st.success("Text extraction completed!")
        
        if st.button("Extract Key-Value Pairs"):
            with st.spinner("Extracting key-value pairs..."):
                result = extract_key_value_pairs(text)
                st.subheader("📊 Extracted JSON Output")
                st.json(result)
                
                st.session_state["updated_json"] = result 

                # Allow manual editing of key-value pairs
                final_json = manual_edit_kv_pairs(result)
                
                if final_json:
                    st.download_button(
                        label="📥 Download JSON",
                        data=json.dumps(final_json, indent=4),
                        file_name="updated_data.json",
                        mime="application/json"
                    )
