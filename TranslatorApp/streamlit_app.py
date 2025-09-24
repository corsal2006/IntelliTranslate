import streamlit as st
from PIL import Image
import pytesseract
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pdf2image import convert_from_path
import io

# --- Page Configuration (sets the title in the browser tab) ---
st.set_page_config(
    page_title="IntelliTranslate",
    page_icon="✨",
    layout="wide"
)

# --- AI Model Loading ---
# Use Streamlit's caching to load the model only once
@st.cache_resource
def load_model():
    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
    return tokenizer, model

st.title("IntelliTranslate ✨")
st.write("AI-Powered Document Translation for Nepali & Sinhalese")

# Load model with a spinner
with st.spinner("Loading AI model... This may take a moment on first startup."):
    tokenizer, model = load_model()

# --- Helper Functions ---
def translate_text(text, source_lang_code):
    if not text.strip():
        return ""
    lang_codes = {'nep': 'npi_Deva', 'sin': 'sin_Sinh'}
    tokenizer.src_lang = lang_codes[source_lang_code]
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    translated_tokens = model.generate(
        **inputs,
        forced_bos_token_id=tokenizer.convert_tokens_to_ids("eng_Latn")
    )
    return tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)[0]

def process_document(image, lang_code):
    original_text = pytesseract.image_to_string(image, lang=lang_code)
    if not original_text.strip():
        return "No text detected.", "No translation generated."
    
    translated_text = translate_text(original_text, lang_code)
    return original_text, translated_text

# --- User Interface ---
language = st.selectbox(
    "1. Select Source Language:",
    options=[('nep', 'Nepali'), ('sin', 'Sinhalese')],
    format_func=lambda x: x[1]
)

uploaded_file = st.file_uploader(
    "2. Upload Document (Image or PDF):",
    type=['png', 'jpg', 'jpeg', 'pdf']
)

if uploaded_file is not None:
    lang_code = language[0]
    
    if st.button("Translate Document"):
        with st.spinner('Processing your document... This may take a few moments.'):
            try:
                images_to_process = []
                if uploaded_file.type == "application/pdf":
                    # Convert PDF to a list of images
                    pdf_bytes = uploaded_file.read()
                    images_to_process = convert_from_path(pdf_bytes)
                else:
                    # It's an image file
                    image = Image.open(uploaded_file)
                    images_to_process.append(image)

                # Process each page/image
                for i, image in enumerate(images_to_process):
                    st.header(f"Results for Page {i+1}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Original Document")
                        st.image(image, use_column_width=True)
                    
                    with col2:
                        st.subheader("Translated Text (English)")
                        original_text, translated_text = process_document(image, lang_code)
                        st.text_area("Extracted Original Text", original_text, height=200)
                        st.text_area("Translated Text", translated_text, height=200)

            except Exception as e:
                st.error(f"An error occurred: {e}")
