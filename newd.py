import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import re
import json
import csv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR\\tessdata"

# Load NLLB model
model_name = "facebook/nllb-200-1.3B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def contains_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate_text(text):
    tokenizer.src_lang = "arb"
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    eng_token_id = tokenizer.convert_tokens_to_ids("eng_Latn")
    translated = model.generate(**inputs, forced_bos_token_id=eng_token_id)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def preprocess_image(image):
    gray = image.convert('L')
    enhanced = ImageEnhance.Contrast(gray).enhance(2.0)
    sharpened = enhanced.filter(ImageFilter.SHARPEN)
    binary = sharpened.point(lambda x: 0 if x < 140 else 255, '1')
    return binary

def extract_text_blocks_with_coords(pdf_path):
    doc = fitz.open(pdf_path)
    extracted = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        blocks = page.get_text("dict")["blocks"]
        found_arabic = False
        paragraph = ""

        for block in blocks:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if contains_arabic(span["text"]):
                            found_arabic = True
                            paragraph += span["text"].strip() + " "

        if not found_arabic:
            print(f"📄 Page {page_number + 1}: No text found, using OCR.")
            pix = page.get_pixmap(dpi=300)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            processed_image = preprocess_image(image)
            processed_image_path = f"page_{page_number+1}_preprocessed.png"
            processed_image.save(processed_image_path)
            print(f"📷 Saved preprocessed image to {processed_image_path}")

            ocr_data = pytesseract.image_to_data(processed_image, lang='ara', output_type=pytesseract.Output.DICT)
            high_conf_lines = []
            current_line = ""
            for i in range(len(ocr_data['text'])):
                word = ocr_data['text'][i].strip()
                conf = int(ocr_data['conf'][i])
                if contains_arabic(word) and conf >= 80:
                    current_line += word + " "
                elif current_line:
                    high_conf_lines.append(current_line.strip())
                    current_line = ""
            if current_line:
                high_conf_lines.append(current_line.strip())

            if not high_conf_lines:
                print(f"⚠️ No high-confidence Arabic text found on Page {page_number + 1}.")
            else:
                print(f"📋 High-confidence Arabic Lines (Page {page_number + 1}):\n{high_conf_lines}")
                paragraph = " ".join(high_conf_lines)

        if paragraph.strip():
            extracted.append({
                "text": paragraph.strip(),
                "bbox": (0, 0, 0, 0),
                "page": page_number
            })
            print(f"✅ Added paragraph from Page {page_number + 1}:\n{paragraph.strip()}\n")

    return extracted, len(doc)

def write_json(data, filename="translations.json"):
    json_data = [
        {
            "page": item["page"],
            "original_text": item["text"],
            "translated_english": item.get("translated", ""),
            "bbox": item["bbox"]
        }
        for item in data if item.get("translated")
    ]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"📝 JSON saved to {filename}")

def export_table_pdf(data, pdf_file="translated_table.pdf"):
    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph("Arabic to English Translations (Table Format)", styles["Heading1"]), Spacer(1, 12)]
    table_data = [["Page", "English Translation"]]
    for row in data:
        table_data.append([str(row["page"] + 1), row.get("translated", "")])
    table = Table(table_data, repeatRows=1, colWidths=[40, 250])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(table)
    doc.build(elements)
    print(f"✅ Table PDF saved to {pdf_file}")

def export_paragraph_pdf(data, pdf_file="translatedNLLB.pdf"):
    doc = SimpleDocTemplate(pdf_file, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle('Custom', parent=styles['Normal'], fontSize=11, leading=15)
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, (A4[0] - 60) / 2, A4[1] - 60, id='col1')
    frame2 = Frame(doc.leftMargin + (A4[0] - 60) / 2, doc.bottomMargin, (A4[0] - 60) / 2, A4[1] - 60, id='col2')
    doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame1, frame2])])
    elements = [Paragraph("Arabic to English Translations (Paragraph Format)", styles["Heading1"]), Spacer(1, 12)]
    for row in data:
        elements.append(Paragraph(row.get("translated", ""), custom_style))
        elements.append(Spacer(1, 10))
    doc.build(elements)
    print(f"✅ Paragraph PDF saved to {pdf_file}")

def render_translated_text_on_images(data, pdf_file="translated_layout.pdf"):
    c = canvas.Canvas(pdf_file, pagesize=A4)
    page_height = A4[1]
    for row in data:
        x0, y0, _, _ = row["bbox"]
        text = row.get("translated", "")
        adjusted_y = page_height - y0
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.darkblue)
        c.drawString(x0, adjusted_y, text)
    c.save()
    print(f"✅ Layout PDF with overlays saved to {pdf_file}")

if __name__ == "__main__":
    input_pdf = "invoice.pdf"
    text_blocks, _ = extract_text_blocks_with_coords(input_pdf)
    print(f"🏠 Translating {len(text_blocks)} Arabic segments...")
    for i, block in enumerate(text_blocks):
        print(f"[{i+1}/{len(text_blocks)}] Translating: {block['text'][:30]}...")
        block["translated"] = translate_text(block["text"])
    write_json(text_blocks, "translations.json")
    export_table_pdf(text_blocks)
    export_paragraph_pdf(text_blocks)
    render_translated_text_on_images(text_blocks)