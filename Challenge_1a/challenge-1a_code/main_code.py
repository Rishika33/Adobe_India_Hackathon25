
import fitz  # PyMuPDF
import os
import json

INPUT_DIR = "input"
OUTPUT_DIR = "output"

def extract_headings(pdf_path):
    doc = fitz.open(pdf_path)

    # ---------- PASS 1: find largest font size across all spans ----------
    max_font_size = 0
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    size = round(span["size"], 1)
                    if size > max_font_size:
                        max_font_size = size

    outline = []
    title_text = None
    title_done = False

    # ---------- PASS 2: scan each line ----------
    for page_num, page in enumerate(doc, start=0):
        blocks = page.get_text("dict")["blocks"]
        line_entries = []

        # collect all lines
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                if not line["spans"]:
                    continue
                combined_text = " ".join(
                    [sp["text"] for sp in line["spans"] if sp["text"].strip()]
                ).strip()
                if not combined_text:
                    continue
                first_span = line["spans"][0]
                font_name = first_span.get("font", "")
                font_size = round(first_span["size"], 1)
                line_entries.append((combined_text, font_name, font_size))

        # process collected lines
        i = 0
        while i < len(line_entries):
            text, font_name, font_size = line_entries[i]
            is_arial = "arial" in font_name.lower()

            # ----- detect TITLE: largest font size -----
            if not title_done and font_size == max_font_size:
                combined = text
                j = i + 1
                while j < len(line_entries):
                    next_text, next_font, next_size = line_entries[j]
                    if round(next_size, 1) == max_font_size:
                        combined += " " + next_text
                        j += 1
                    else:
                        break
                title_text = combined.strip()
                title_done = True
                i = j
                continue

            # ----- detect H1: Arial size 16 -----
            if is_arial and font_size == 16:
                combined = text
                j = i + 1
                while j < len(line_entries):
                    nt, nf, ns = line_entries[j]
                    if "arial" in nf.lower() and round(ns, 1) == 16:
                        combined += " " + nt
                        j += 1
                    else:
                        break
                outline.append({
                    "level": "H1",
                    "text": combined.strip(),
                    "page": page_num
                })
                i = j
                continue

            # ----- detect H2: Arial size 14 -----
            if is_arial and font_size == 14:
                combined = text
                j = i + 1
                while j < len(line_entries):
                    nt, nf, ns = line_entries[j]
                    if "arial" in nf.lower() and round(ns, 1) == 14:
                        combined += " " + nt
                        j += 1
                    else:
                        break
                outline.append({
                    "level": "H2",
                    "text": combined.strip(),
                    "page": page_num
                })
                i = j
                continue

            i += 1

    if not title_text:
        title_text = os.path.basename(pdf_path)

    return {
        "title": title_text,
        "outline": outline
    }

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Looking in:", os.path.abspath(INPUT_DIR))
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    print("Found PDFs:", pdf_files)
    for pdf_file in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, pdf_file)
        print(f"🔎 Processing: {pdf_file}")
        result = extract_headings(pdf_path)
        json_file = pdf_file.replace(".pdf", ".json")
        json_path = os.path.join(OUTPUT_DIR, json_file)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON saved: {json_path}")

if __name__ == "__main__":
    main()