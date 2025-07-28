import fitz  # PyMuPDF
import os
import json
import re
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher

# Update these paths if you're running locally
BASE_INPUT_DIR = r"C:\Users\shasi\OneDrive\Desktop\adobe\input"
BASE_OUTPUT_DIR = r"C:\Users\shasi\OneDrive\Desktop\adobe\output"

def load_input_json(input_json_path):
    if not os.path.exists(input_json_path):
        print(f"❌ Input JSON not found: {input_json_path}")
        return None, None
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    persona = data.get("persona", {}).get("role", "Unknown Persona")
    job = data.get("job_to_be_done", {}).get("task", "Unknown Job")
    return persona, job

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_sections_with_content(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except:
        return []

    headings = []
    all_blocks = []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_SEARCH)["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    span_text = " ".join([s['text'].strip() for s in spans if s['text'].strip()])
                    if not span_text:
                        continue
                    all_blocks.append({
                        "page": page_num,
                        "bbox": block["bbox"],
                        "text": span_text,
                        "size": round(spans[0]['size']),
                        "bold": "bold" in spans[0]['font'].lower()
                    })

    if not all_blocks:
        return []

    size_counts = Counter([b['size'] for b in all_blocks])
    body_size = size_counts.most_common(1)[0][0]

    for block in all_blocks:
        if block['text'].strip() and (block['size'] > body_size or (block['size'] == body_size and block['bold'])):
            headings.append({
                "document": os.path.basename(pdf_path),
                "title": block['text'].strip(),
                "page": block['page'],
                "bbox": block['bbox'],
                "level": block['size']
            })

    for i, heading in enumerate(headings):
        content_text = []
        start_page = heading['page']
        start_y = heading['bbox'][3]
        end_y = doc[start_page].rect.height
        if i + 1 < len(headings) and headings[i + 1]['page'] == start_page:
            end_y = headings[i + 1]['bbox'][1]

        for block in all_blocks:
            if block['page'] == start_page and start_y < block['bbox'][1] < end_y:
                if not (block['size'] > body_size or (block['size'] == body_size and block['bold'])):
                    if block['text'].strip():
                        content_text.append(block['text'].strip())

        heading['content'] = " ".join(content_text).strip()

    return [h for h in headings if h['title'].strip() and h['content'].strip()]

def rank_and_select_top_sections(all_sections, job_to_be_done, num_results=5):
    keywords = re.findall(r'\b\w{4,}\b', job_to_be_done.lower())
    scored_sections = []
    for section in all_sections:
        score = 0
        title_lower = section['title'].lower()
        for keyword in keywords:
            sim = similar(keyword, title_lower)
            if sim > 0.7:
                score += int(sim * 15)
        if any(w in title_lower for w in ["guide", "activities", "restaurants", "hotels", "things to do"]):
            score += 10
        score += section.get("level", 12) * 0.5
        if score > 0:
            section["relevance_score"] = score
            scored_sections.append(section)
    return sorted(scored_sections, key=lambda x: x["relevance_score"], reverse=True)[:num_results]

def process_document_collection(collection_name):
    input_dir = os.path.join(BASE_INPUT_DIR, collection_name)
    input_json_path = os.path.join(input_dir, "input.json")
    os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

    persona, job_to_be_done = load_input_json(input_json_path)
    if persona is None:
        return

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    all_sections = []
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        print(f"\n📄 Processing: {pdf_file}")
        sections = extract_sections_with_content(pdf_path)
        if sections:
            all_sections.extend(sections)

    top_5 = rank_and_select_top_sections(all_sections, job_to_be_done, 5)
    output_data = {
        "metadata": {
            "input_documents": sorted(pdf_files),
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.utcnow().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": []
    }

    for i, section in enumerate(top_5):
        output_data["extracted_sections"].append({
            "document": section["document"],
            "section_title": section["title"],
            "importance_rank": i + 1,
            "page_number": section["page"]
        })
        clean_text = re.sub(r'\s+', ' ', f"{section['title']}: {section['content']}").strip()
        output_data["subsection_analysis"].append({
            "document": section["document"],
            "refined_text": clean_text,
            "page_number": section["page"]
        })

    output_path = os.path.join(BASE_OUTPUT_DIR, f"{collection_name}_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    try:
        collection_names = [d for d in os.listdir(BASE_INPUT_DIR) if os.path.isdir(os.path.join(BASE_INPUT_DIR, d))]
    except FileNotFoundError:
        print(f"❌ Input folder not found: {BASE_INPUT_DIR}")
        exit(1)

    if not collection_names:
        print("⚠️ No collections found.")
        exit(1)

    for collection in collection_names:
        process_document_collection(collection)
