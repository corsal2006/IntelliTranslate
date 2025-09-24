import os
import csv
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import pytesseract
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pdf2image import convert_from_path

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
FEEDBACK_LOG_FILE = 'general_feedback.log'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- PRE-LOAD TRANSLATION MODEL ---
print("Loading translation model...")
model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
print("Model loaded successfully!")

# --- HELPER FUNCTIONS ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

def process_image_for_highlighting(image, lang_code):
    ocr_data = pytesseract.image_to_data(image, lang=lang_code, output_type=pytesseract.Output.DICT)
    results = []
    current_block = {"text": "", "coords": [], "translation": ""}
    last_block_num = -1
    for i in range(len(ocr_data['text'])):
        if int(ocr_data['conf'][i]) > 40:
            block_num = ocr_data['block_num'][i]
            if block_num != last_block_num and last_block_num != -1:
                if current_block["text"]:
                    current_block["translation"] = translate_text(current_block["text"], lang_code)
                    results.append(current_block)
                current_block = {"text": "", "coords": [], "translation": ""}
            current_block["text"] += ocr_data['text'][i] + " "
            current_block["coords"].append({
                "left": ocr_data['left'][i], "top": ocr_data['top'][i],
                "width": ocr_data['width'][i], "height": ocr_data['height'][i]
            })
            last_block_num = block_num
    if current_block["text"]:
        current_block["translation"] = translate_text(current_block["text"], lang_code)
        results.append(current_block)
    return results

# --- FLASK WEB ROUTES ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    language = request.form.get('language')
    if file.filename == '' or not language: return jsonify({"error": "No selected file or language"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        images = []
        if filename.lower().endswith('.pdf'):
            try: images = convert_from_path(filepath)
            except Exception as e: return jsonify({"error": f"PDF processing error: {e}"}), 500
        else:
            images.append(Image.open(filepath))
        all_pages_data = []
        for image in images:
            page_data = process_image_for_highlighting(image, language)
            all_pages_data.append(page_data)
        return jsonify({"filename": filename, "pages": all_pages_data})
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    feedback_text = data.get('feedback')
    if not feedback_text:
        return jsonify({"status": "error", "message": "Feedback cannot be empty."}), 400

    # Save the general feedback to a simple log file
    with open(FEEDBACK_LOG_FILE, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"--- FEEDBACK AT {timestamp} ---\n")
        f.write(f"{feedback_text}\n\n")
    
    return jsonify({"status": "success", "message": "Thank you for your feedback!"})

# --- MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER): os.makedirs(UPLOAD_FOLDER)
    # app.run(host='0.0.0.0', debug=True) 
# We comment this out because the production server will run the app.
