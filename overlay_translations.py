import fitz  # PyMuPDF
import json

def overlay_translations(pdf_path, json_path, output_path):
    doc = fitz.open(pdf_path)

    # Load JSON
    with open(json_path, "r", encoding="utf-8") as f:
        translations = json.load(f)

    for item in translations:
        page_number = item["page"]
        translated_text = item["translated_english"]
        x0, y0, x1, y1 = item["bbox"]

        page = doc[page_number]

        # Draw white rectangle to cover Arabic text
        rect = fitz.Rect(x0, y0, x1, y1)
        page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))  # white box

        # Overlay translated text
        page.insert_text(
            fitz.Point(x0, y0),
            translated_text,
            fontsize=10,
            fontname="helv",
            fill=(0, 0, 0)  # black text
        )

    # Save the new PDF
    doc.save(output_path)
    doc.close()
    print(f"✅ Translated PDF saved as: {output_path}")

# Run
if __name__ == "__main__":
    overlay_translations("easypd.pdf", "translations.json", "translated_overlay_output.pdf")
