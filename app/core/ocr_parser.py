import re
from rapidocr import RapidOCR
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.models.document import DocumentTypeEnum

try:
    engine = RapidOCR()
except Exception as e:
    engine = None
    print(f"Failed to initialize RapidOCR: {e}")


def parse_date(date_str: str) -> Optional[datetime.date]:
    match = re.search(r'(\d{2}/\d{2}/\d{4})', date_str)
    if match:
        try:
            return datetime.strptime(match.group(1), '%d/%m/%Y').date()
        except ValueError:
            pass
    return None


def get_box_center_y(box) -> float:
    return (box[0][1] + box[2][1]) / 2


def get_box_center_x(box) -> float:
    return (box[0][0] + box[1][0]) / 2


def normalize_box(box, img_width, img_height) -> List[float]:
    cx = get_box_center_x(box) / img_width
    cy = get_box_center_y(box) / img_height
    return [cx, cy]


def find_text_near_label(ocr_items, label_keywords, direction="below", max_distance_ratio=0.06):
    label_item = None
    for item in ocr_items:
        text_upper = item["text"].upper()
        for keyword in label_keywords:
            if keyword in text_upper:
                label_item = item
                break
        if label_item:
            break

    if not label_item:
        return None, 0.0

    label_cy = get_box_center_y(label_item["box"])
    label_cx = get_box_center_x(label_item["box"])

    best = None
    best_dist = float("inf")

    for item in ocr_items:
        if item == label_item:
            continue
        cy = get_box_center_y(item["box"])
        cx = get_box_center_x(item["box"])

        if direction == "below" and cy > label_cy:
            dist = cy - label_cy
            if dist < best_dist and abs(cx - label_cx) < 150:
                best_dist = dist
                best = item
        elif direction == "right" and cx > label_cx:
            dist = abs(cy - label_cy)
            if dist < 30 and cx - label_cx < 400:
                if cx - label_cx < best_dist:
                    best_dist = cx - label_cx
                    best = item

    if best:
        return best["text"], best["score"]
    return None, 0.0


def extract_aadhaar_info_with_boxes(ocr_items: List[Dict]) -> Dict[str, Any]:
    info = {
        "doc_type": DocumentTypeEnum.AADHAR,
        "full_name": "Unknown",
        "doc_number": "Unknown",
        "dob": None,
        "gender": None,
        "issue_date": None,
        "address": None,
        "nationality": "Indian"
    }
    field_scores = []

    aadhaar_pattern = re.compile(r'(\d{4}\s\d{4}\s\d{4}|\d{12})')

    for item in ocr_items:
        text = item["text"]
        text_upper = text.upper()
        score = item["score"]
        cy = get_box_center_y(item["box"])
        cx = get_box_center_x(item["box"])

        if info["doc_number"] == "Unknown":
            match = aadhaar_pattern.search(text.strip())
            if match:
                info["doc_number"] = match.group(1).replace(' ', '')
                field_scores.append(score)
                continue

        if 'ISSUED' in text_upper:
            info["issue_date"] = parse_date(text)
            if info["issue_date"]:
                field_scores.append(score)

        if 'DOB' in text_upper or 'YOB' in text_upper or 'YEAR OF BIRTH' in text_upper:
            info["dob"] = parse_date(text)
            if info["dob"]:
                field_scores.append(score)

            dob_cy = cy
            best_name = None
            best_name_dist = float("inf")
            for candidate in ocr_items:
                c_cy = get_box_center_y(candidate["box"])
                c_text = candidate["text"].strip()
                if c_cy < dob_cy and len(c_text) > 2:
                    if not re.search(r'\d', c_text) and 'GOVERNMENT' not in c_text.upper() and 'ISSUED' not in c_text.upper() and 'AADHAAR' not in c_text.upper():
                        dist = dob_cy - c_cy
                        if dist < best_name_dist and dist < 100:
                            best_name_dist = dist
                            best_name = candidate
            if best_name and info["full_name"] == "Unknown":
                info["full_name"] = best_name["text"].strip()
                field_scores.append(best_name["score"])

        if 'MALE' in text_upper and 'FEMALE' not in text_upper:
            info["gender"] = 'Male'
            field_scores.append(score)
        elif 'FEMALE' in text_upper:
            info["gender"] = 'Female'
            field_scores.append(score)

    address_items = []
    collecting = False
    for item in ocr_items:
        text_upper = item["text"].upper()
        if 'ADDRESS' in text_upper:
            collecting = True
            continue
        if collecting:
            if 'VID:' in text_upper or 'UIDAI' in text_upper or '1947' in text_upper:
                collecting = False
            elif aadhaar_pattern.search(item["text"]):
                collecting = False
            else:
                if item["text"].strip() != 'Details' and len(item["text"].strip()) > 1:
                    address_items.append(item)

    if address_items:
        info["address"] = " ".join([a["text"].strip() for a in address_items])
        for a in address_items:
            field_scores.append(a["score"])

    info["ocr_confidence"] = round(sum(field_scores) / len(field_scores) * 100, 2) if field_scores else 0.0
    return info


def extract_passport_info_with_boxes(ocr_items: List[Dict]) -> Dict[str, Any]:
    info = {
        "doc_type": DocumentTypeEnum.PASSPORT,
        "full_name": "Unknown",
        "doc_number": "Unknown",
        "dob": None,
        "gender": None,
        "mrz_no": None,
        "issue_date": None,
        "expiry_date": None,
        "nationality": None,
        "place_of_birth": None,
        "place_of_issue": None
    }
    field_scores = []

    mrz_items = []
    for item in ocr_items:
        clean_line = item["text"].replace(" ", "").upper()
        if len(clean_line) > 30 and "<" in clean_line:
            mrz_items.append(item)

    if len(mrz_items) >= 2:
        mrz1_item = mrz_items[-2]
        mrz2_item = mrz_items[-1]
        mrz1 = mrz1_item["text"].replace(" ", "").upper()
        mrz2 = mrz2_item["text"].replace(" ", "").upper()

        info["mrz_no"] = f"{mrz1}\n{mrz2}"
        field_scores.append(mrz1_item["score"])
        field_scores.append(mrz2_item["score"])

        if mrz1.startswith("P"):
            name_parts = mrz1[5:].split("<<")
            if len(name_parts) >= 2:
                surname = name_parts[0].replace("<", " ").strip()
                given_names = name_parts[1].replace("<", " ").strip()
                info["full_name"] = f"{given_names} {surname}".strip()
            else:
                info["full_name"] = mrz1[5:].replace("<", " ").strip()

            info["doc_number"] = mrz2[0:9].replace("<", "")
            nat = mrz2[10:13].replace("<", "")
            info["nationality"] = "Indian" if nat == "IND" else nat

            dob_raw = mrz2[13:19]
            if dob_raw.isdigit():
                yy = int(dob_raw[0:2])
                yyyy = yy + 1900 if yy > 50 else yy + 2000
                info["dob"] = datetime(yyyy, int(dob_raw[2:4]), int(dob_raw[4:6])).date()

            info["gender"] = "Male" if mrz2[20] == "M" else "Female" if mrz2[20] == "F" else None

            exp_raw = mrz2[21:27]
            if exp_raw.isdigit():
                yy_exp = int(exp_raw[0:2])
                yyyy_exp = yy_exp + 2000
                info["expiry_date"] = datetime(yyyy_exp, int(exp_raw[2:4]), int(exp_raw[4:6])).date()

    surname_text, surname_score = find_text_near_label(ocr_items, ["SURNAME", "SUMAME"], direction="below")
    given_text, given_score = find_text_near_label(ocr_items, ["GIVEN NAME"], direction="below")
    if surname_text and given_text:
        info["full_name"] = f"{given_text.strip()} {surname_text.strip()}"
        field_scores.append(surname_score)
        field_scores.append(given_score)

    dob_text, dob_score = find_text_near_label(ocr_items, ["DATE OF BIRTH"], direction="below")
    if dob_text:
        parsed = parse_date(dob_text)
        if parsed:
            info["dob"] = parsed
            field_scores.append(dob_score)

    sex_text, sex_score = find_text_near_label(ocr_items, ["SEX"], direction="below")
    if sex_text:
        if sex_text.strip().upper() == "M":
            info["gender"] = "Male"
        elif sex_text.strip().upper() == "F":
            info["gender"] = "Female"
        field_scores.append(sex_score)

    pob_text, pob_score = find_text_near_label(ocr_items, ["PLACE OF BIRTH"], direction="below")
    if pob_text:
        info["place_of_birth"] = pob_text.strip()
        field_scores.append(pob_score)

    poi_text, poi_score = find_text_near_label(ocr_items, ["PLACE OF ISSUE", "PLACE AF ISSUE"], direction="below")
    if poi_text:
        info["place_of_issue"] = poi_text.strip()
        field_scores.append(poi_score)

    doi_text, doi_score = find_text_near_label(ocr_items, ["DATE OF ISSUE"], direction="below")
    if doi_text:
        parsed = parse_date(doi_text)
        if parsed:
            info["issue_date"] = parsed
            field_scores.append(doi_score)

    doe_text, doe_score = find_text_near_label(ocr_items, ["DATE OF EXPIRY", "DALE OF EXPITY", "DALE OL EXPITY", "DATE OL EXPIRY"], direction="below")
    if doe_text:
        parsed = parse_date(doe_text)
        if parsed:
            info["expiry_date"] = parsed
            field_scores.append(doe_score)

    if info["doc_number"] == "Unknown":
        passport_num_pattern = re.compile(r'^[A-Z][0-9]{7}$')
        for item in ocr_items:
            words = item["text"].upper().split()
            for word in words:
                if passport_num_pattern.match(word):
                    info["doc_number"] = word
                    field_scores.append(item["score"])
                    break

    info["ocr_confidence"] = round(sum(field_scores) / len(field_scores) * 100, 2) if field_scores else 0.0
    return info


def process_document_image(image_bytes: bytes) -> Dict[str, Any]:
    if engine is None:
        return {
            "doc_type": DocumentTypeEnum.UNKNOWN,
            "full_name": "OCR Engine Not Loaded",
            "doc_number": "Error",
            "ocr_confidence": 0.0
        }

    try:
        result = engine(image_bytes)

        if not hasattr(result, 'txts') or not result.txts:
            return {
                "doc_type": DocumentTypeEnum.UNKNOWN,
                "full_name": "No text detected",
                "doc_number": "Unknown",
                "ocr_confidence": 0.0
            }

        ocr_items = []
        for i, (text, score) in enumerate(zip(result.txts, result.scores)):
            box = result.boxes[i].tolist() if hasattr(result.boxes[i], 'tolist') else result.boxes[i]
            ocr_items.append({
                "text": text,
                "score": score,
                "box": box
            })

        full_text = " ".join([item["text"] for item in ocr_items]).upper()

        if 'AADHAAR' in full_text or ('GOVERNMENT OF INDIA' in full_text and 'REPUBLIC' not in full_text) or 'UIDAI' in full_text:
            parsed_data = extract_aadhaar_info_with_boxes(ocr_items)
        elif 'PASSPORT' in full_text or 'REPUBLIC OF INDIA' in full_text:
            parsed_data = extract_passport_info_with_boxes(ocr_items)
        else:
            parsed_data = {
                "doc_type": DocumentTypeEnum.UNKNOWN,
                "full_name": "Unknown",
                "doc_number": "Unknown",
                "ocr_confidence": 0.0
            }

        return parsed_data

    except Exception as e:
        print(f"OCR Error: {e}")
        return {
            "doc_type": DocumentTypeEnum.UNKNOWN,
            "full_name": f"Error: {str(e)}",
            "doc_number": "Error",
            "ocr_confidence": 0.0
        }
