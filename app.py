# import os
# from PyPDF2 import PdfReader
# from transformers import MarianMTModel, MarianTokenizer

# # Load model from local directory
# model_path = "models/opus-mt-ar-en"
# model = MarianMTModel.from_pretrained(model_path)
# tokenizer = MarianTokenizer.from_pretrained(model_path)

# def extract_text_from_pdf(pdf_path):
#     reader = PdfReader(pdf_path)
#     # Concatenate all pages if more than one
#     return "\n".join([page.extract_text() or "" for page in reader.pages])

# def translate_arabic_to_english(text):
#     translated_output = []
#     paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

#     print(f"[INFO] Total paragraphs to translate: {len(paragraphs)}")

#     for i, para in enumerate(paragraphs):
#         print(f"[{i+1}/{len(paragraphs)}] Translating: {para[:40]}...")
#         inputs = tokenizer(para, return_tensors="pt", padding=True, truncation=True, max_length=512)
#         translated = model.generate(**inputs)
#         eng = tokenizer.decode(translated[0], skip_special_tokens=True)
#         translated_output.append(eng)

#     return "\n\n".join(translated_output)

# if __name__ == "__main__":
#     input_pdf_path = "dumdum.pdf"     # Replace with your actual file path
#     output_txt_path = "output_english.txt"  # Optional output

#     print("🔍 Extracting Arabic text from PDF...")
#     arabic_text = extract_text_from_pdf(input_pdf_path)

#     print("🔁 Translating to English...")
#     english_text = translate_arabic_to_english(arabic_text)

#     print("✅ Translation complete. Writing to file...")
#     with open(output_txt_path, "w", encoding="utf-8") as f:
#         f.write(english_text)

#     print(f"🎉 Translation saved to '{output_txt_path}'")

# import os
# import fitz  # PyMuPDF
# import pytesseract
# from PIL import Image
# from transformers import MarianMTModel, MarianTokenizer
# import io
# import re
# import json
# import csv
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet

# # Tesseract configuration
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR\\tessdata"

# # Load MarianMT model
# model_path = "models/opus-mt-ar-en"
# model = MarianMTModel.from_pretrained(model_path)
# tokenizer = MarianTokenizer.from_pretrained(model_path)

# def contains_arabic(text):
#     return bool(re.search(r'[\u0600-\u06FF]', text))

# def translate_text(text):
#     inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
#     translated = model.generate(**inputs)
#     return tokenizer.decode(translated[0], skip_special_tokens=True)

# def extract_text_blocks_with_coords(pdf_path):
#     doc = fitz.open(pdf_path)
#     extracted = []

#     for page_number in range(len(doc)):
#         page = doc[page_number]
#         has_images = len(page.get_images(full=True)) > 0

#         # 1. Extract text layer if available
#         blocks = page.get_text("dict")["blocks"]
#         if blocks:
#             for block in blocks:
#                 if block["type"] == 0:
#                     for line in block["lines"]:
#                         for span in line["spans"]:
#                             if contains_arabic(span["text"]):
#                                 x0, y0, x1, y1 = span["bbox"]
#                                 extracted.append({
#                                     "text": span["text"].strip(),
#                                     "bbox": (x0, y0, x1, y1),
#                                     "page": page_number
#                                 })
#         elif has_images:
#             # 2. Use OCR only if no selectable text but image exists
#             pix = page.get_pixmap(dpi=300)
#             image = Image.open(io.BytesIO(pix.tobytes("png")))
#             ocr_data = pytesseract.image_to_data(image, lang='ara', output_type=pytesseract.Output.DICT)

#             for i in range(len(ocr_data["text"])):
#                 word = ocr_data["text"][i].strip()
#                 if contains_arabic(word):
#                     x = ocr_data["left"][i]
#                     y = ocr_data["top"][i]
#                     w = ocr_data["width"][i]
#                     h = ocr_data["height"][i]
#                     extracted.append({
#                         "text": word,
#                         "bbox": (x, y, x + w, y + h),
#                         "page": page_number
#                     })

#     return extracted, len(doc)

# def write_json(data, filename="translations.json"):
#     json_data = [
#         {
#             "page": item["page"],
#             "original_text": item["text"],
#             "translated_english": item.get("translated", ""),
#             "bbox": item["bbox"]
#         }
#         for item in data if item.get("translated")
#     ]
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=2)
#     print(f"📝 JSON saved to {filename}")

# def export_to_table(data, pdf_file="translated_table_output.pdf", csv_file="translated_table_output.csv"):
#     # Save as CSV
#     with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)
#         writer.writerow(["Page", "Arabic Text", "English Translation"])
#         for row in data:
#             writer.writerow([row["page"] + 1, row["text"], row.get("translated", "")])
#     print(f"✅ CSV saved to {csv_file}")

#     # Save as PDF
#     doc = SimpleDocTemplate(pdf_file, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = []
#     elements.append(Paragraph("Arabic to English Translations", styles["Heading1"]))
#     elements.append(Spacer(1, 12))

#     table_data = [["Page", "Arabic Text", "English Translation"]]
#     for row in data:
#         table_data.append([
#             str(row["page"] + 1), row["text"], row.get("translated", "")
#         ])

#     table = Table(table_data, repeatRows=1, colWidths=[40, 200, 250])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
#         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#         ('ALIGN', (0, 0), (0, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#     ]))

#     elements.append(table)
#     doc.build(elements)
#     print(f"✅ Table PDF saved to {pdf_file}")

# if __name__ == "__main__":
#     input_pdf = "gardaan.pdf"
#     output_pdf = "NUB22.pdf"
#     json_path = "Nubtranslations22.json"

#     print("🔍 Extracting Arabic text with layout...")
#     text_blocks, total_pages = extract_text_blocks_with_coords(input_pdf)

#     print(f"🏠 Translating {len(text_blocks)} Arabic segments...")
#     for i, block in enumerate(text_blocks):
#         print(f"[{i+1}/{len(text_blocks)}] Translating: {block['text'][:30]}...")
#         block["translated"] = translate_text(block["text"])

#     print("📎 Saving translations to JSON...")
#     write_json(text_blocks, json_path)

#     print("🔢 Exporting to table format...")
#     export_to_table(text_blocks) 

# import os
# from PyPDF2 import PdfReader
# from transformers import MarianMTModel, MarianTokenizer

# # Load model from local directory
# model_path = "models/opus-mt-ar-en"
# model = MarianMTModel.from_pretrained(model_path)
# tokenizer = MarianTokenizer.from_pretrained(model_path)

# def extract_text_from_pdf(pdf_path):
#     reader = PdfReader(pdf_path)
#     # Concatenate all pages if more than one
#     return "\n".join([page.extract_text() or "" for page in reader.pages])

# def translate_arabic_to_english(text):
#     translated_output = []
#     paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

#     print(f"[INFO] Total paragraphs to translate: {len(paragraphs)}")

#     for i, para in enumerate(paragraphs):
#         print(f"[{i+1}/{len(paragraphs)}] Translating: {para[:40]}...")
#         inputs = tokenizer(para, return_tensors="pt", padding=True, truncation=True, max_length=512)
#         translated = model.generate(**inputs)
#         eng = tokenizer.decode(translated[0], skip_special_tokens=True)
#         translated_output.append(eng)

#     return "\n\n".join(translated_output)

# if __name__ == "__main__":
#     input_pdf_path = "dumdum.pdf"     # Replace with your actual file path
#     output_txt_path = "output_english.txt"  # Optional output

#     print("🔍 Extracting Arabic text from PDF...")
#     arabic_text = extract_text_from_pdf(input_pdf_path)

#     print("🔁 Translating to English...")
#     english_text = translate_arabic_to_english(arabic_text)

#     print("✅ Translation complete. Writing to file...")
#     with open(output_txt_path, "w", encoding="utf-8") as f:
#         f.write(english_text)

#     print(f"🎉 Translation saved to '{output_txt_path}'")
# import os
# import fitz  # PyMuPDF
# import pytesseract
# from PIL import Image
# from transformers import MarianMTModel, MarianTokenizer
# import io
# import re
# import json
# import csv
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.pdfgen import canvas
# from reportlab.lib.units import mm

# # Tesseract configuration
# pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
# os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR\\tessdata"

# # Load MarianMT model
# model_path = "models/opus-mt-ar-en"
# model = MarianMTModel.from_pretrained(model_path)
# tokenizer = MarianTokenizer.from_pretrained(model_path)

# def contains_arabic(text):
#     return bool(re.search(r'[\u0600-\u06FF]', text))

# def translate_text(text):
#     inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
#     translated = model.generate(**inputs)
#     return tokenizer.decode(translated[0], skip_special_tokens=True)

# def extract_text_blocks_with_coords(pdf_path):
#     doc = fitz.open(pdf_path)
#     extracted = []

#     for page_number in range(len(doc)):
#         page = doc[page_number]
#         has_images = len(page.get_images(full=True)) > 0
#         blocks = page.get_text("dict")["blocks"]
#         if blocks:
#             for block in blocks:
#                 if block["type"] == 0:
#                     for line in block["lines"]:
#                         for span in line["spans"]:
#                             if contains_arabic(span["text"]):
#                                 x0, y0, x1, y1 = span["bbox"]
#                                 extracted.append({
#                                     "text": span["text"].strip(),
#                                     "bbox": (x0, y0, x1, y1),
#                                     "page": page_number
#                                 })
#         elif has_images:
#             pix = page.get_pixmap(dpi=300)
#             image = Image.open(io.BytesIO(pix.tobytes("png")))
#             ocr_data = pytesseract.image_to_data(image, lang='ara', output_type=pytesseract.Output.DICT)
#             for i in range(len(ocr_data["text"])):
#                 word = ocr_data["text"][i].strip()
#                 if contains_arabic(word):
#                     x = ocr_data["left"][i]
#                     y = ocr_data["top"][i]
#                     w = ocr_data["width"][i]
#                     h = ocr_data["height"][i]
#                     extracted.append({
#                         "text": word,
#                         "bbox": (x, y, x + w, y + h),
#                         "page": page_number
#                     })
#     return extracted, len(doc)

# def write_json(data, filename="translations.json"):
#     json_data = [
#         {
#             "page": item["page"],
#             "original_text": item["text"],
#             "translated_english": item.get("translated", ""),
#             "bbox": item["bbox"]
#         }
#         for item in data if item.get("translated")
#     ]
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=2)
#     print(f"📝 JSON saved to {filename}")

# def export_table_pdf(data, pdf_file="translated_table.pdf"):
#     doc = SimpleDocTemplate(pdf_file, pagesize=A4)
#     styles = getSampleStyleSheet()
#     elements = [Paragraph("Arabic to English Translations (Table Format)", styles["Heading1"]), Spacer(1, 12)]
#     table_data = [["Page", "English Translation"]]
#     for row in data:
#         table_data.append([str(row["page"] + 1), row.get("translated", "")])
#     table = Table(table_data, repeatRows=1, colWidths=[40, 250])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
#         ('VALIGN', (0, 0), (-1, -1), 'TOP'),
#         ('ALIGN', (0, 0), (0, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#     ]))
#     elements.append(table)
#     doc.build(elements)
#     print(f"✅ Table PDF saved to {pdf_file}")

# def export_paragraph_pdf(data, pdf_file="translated_paragraph.pdf"):
#     doc = SimpleDocTemplate(pdf_file, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
#     styles = getSampleStyleSheet()
#     custom_style = ParagraphStyle('Custom', parent=styles['Normal'], fontSize=11, leading=15)
#     frame1 = Frame(doc.leftMargin, doc.bottomMargin, (A4[0] - 60) / 2, A4[1] - 60, id='col1')
#     frame2 = Frame(doc.leftMargin + (A4[0] - 60) / 2, doc.bottomMargin, (A4[0] - 60) / 2, A4[1] - 60, id='col2')
#     doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame1, frame2])])
#     elements = [Paragraph("Arabic to English Translations (Paragraph Format)", styles["Heading1"]), Spacer(1, 12)]
#     for row in data:
#         elements.append(Paragraph(row.get("translated", ""), custom_style))
#         elements.append(Spacer(1, 10))
#     doc.build(elements)
#     print(f"✅ Paragraph PDF saved to {pdf_file}")

# def render_translated_text_on_images(data, pdf_file="translated_layout.pdf"):
#     c = canvas.Canvas(pdf_file, pagesize=A4)
#     page_height = A4[1]
#     for row in data:
#         x0, y0, _, _ = row["bbox"]
#         text = row.get("translated", "")
#         # Convert bbox from image to PDF scale if needed
#         adjusted_y = page_height - y0  # invert y for PDF
#         c.setFont("Helvetica-Bold", 8)
#         c.setFillColor(colors.darkblue)
#         c.drawString(x0, adjusted_y, text)
#     c.save()
#     print(f"✅ Layout PDF with overlays saved to {pdf_file}")

# if __name__ == "__main__":
#     input_pdf = "imagearabic.pdf"
#     text_blocks, _ = extract_text_blocks_with_coords(input_pdf)
#     print(f"🏠 Translating {len(text_blocks)} Arabic segments...")
#     for i, block in enumerate(text_blocks):
#         print(f"[{i+1}/{len(text_blocks)}] Translating: {block['text'][:30]}...")
#         block["translated"] = translate_text(block["text"])
#     write_json(text_blocks, "translations.json")
#     export_table_pdf(text_blocks)
#     export_paragraph_pdf(text_blocks)
#     render_translated_text_on_images(text_blocks)



import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from transformers import MarianMTModel, MarianTokenizer
import io
import re
import json
import csv
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Frame, PageTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Tesseract configuration
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR\\tessdata"

# Load MarianMT model
model_path = "models/opus-mt-ar-en"
model = MarianMTModel.from_pretrained(model_path)
tokenizer = MarianTokenizer.from_pretrained(model_path)

def contains_arabic(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate_text(text):
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    translated = model.generate(**inputs)
    return tokenizer.decode(translated[0], skip_special_tokens=True)

def extract_text_blocks_with_coords(pdf_path):
    doc = fitz.open(pdf_path)
    extracted = []

    for page_number in range(len(doc)):
        page = doc[page_number]
        blocks = page.get_text("dict")["blocks"]
        has_images = len(page.get_images(full=True)) > 0

        # Check if Arabic is found in text blocks
        found_arabic = False
        for block in blocks:
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        if contains_arabic(span["text"]):
                            found_arabic = True
                            x0, y0, x1, y1 = span["bbox"]
                            extracted.append({
                                "text": span["text"].strip(),
                                "bbox": (x0, y0, x1, y1),
                                "page": page_number
                            })

        # If no Arabic found and images exist, fallback to OCR
        if not found_arabic and has_images:
            pix = page.get_pixmap(dpi=300)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_data = pytesseract.image_to_data(image, lang='ara', output_type=pytesseract.Output.DICT)
            for i in range(len(ocr_data["text"])):
                word = ocr_data["text"][i].strip()
                if contains_arabic(word):
                    x = ocr_data["left"][i]
                    y = ocr_data["top"][i]
                    w = ocr_data["width"][i]
                    h = ocr_data["height"][i]
                    extracted.append({
                        "text": word,
                        "bbox": (x, y, x + w, y + h),
                        "page": page_number
                    })

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

def export_paragraph_pdf(data, pdf_file="translated_paragraph.pdf"):
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
        adjusted_y = page_height - y0  # invert y for PDF
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
