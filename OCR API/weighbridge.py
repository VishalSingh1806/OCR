import re
from ocr_utils import debug_print_lines, normalize_ascii

def extract_weighbridge_fields(text):
    print(" Processing: Weighbridge")
    lines = text.splitlines()
    # debug_print_lines(text, " Weighbridge: Line-by-Line OCR Output")

    result = {"Category": "Weighbridge"}

    vehicle_number = "Not found"
    material = "Not found"
    net_weight = "Not found"
    date = "Not found"
    name = "Not found"

    textual_map = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }

    # Flatten OCR lines for full-text context matching
    full_text = " ".join([normalize_ascii(l) for l in lines])

    for i, line in enumerate(lines):
        clean = normalize_ascii(line)

        # --- VEHICLE NUMBER EXTRACTION (before per-line loop) ---
        if vehicle_number == "Not found":
            # Pass 1: scan lines 5–10
            vehicle_lines = lines[5:11]
            candidate_lines = []

            for line in vehicle_lines:
                clean = normalize_ascii(line)
                if "vehicle" in clean or re.search(r"[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}", clean):
                    candidate_lines.append(clean)

            combined = " ".join(candidate_lines)
            combined = combined.replace(":", " ").replace("\xa0", " ")
            combined = re.sub(r"\s{2,}", " ", combined).upper()

            match = re.search(r"\b[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}\b", combined)
            if match:
                vehicle_number = match.group().replace(" ", "").strip().upper()
                # print(f"✅ Found vehicle number (pass 1): {vehicle_number}")

        # Pass 2: If still not found, handle split-line case like Line 7 = "VEHICLE NO", Line 8 = ": WB738 6961"
        if vehicle_number == "Not found":
            for i in range(len(lines) - 1):
                this_line = normalize_ascii(lines[i])
                next_line = normalize_ascii(lines[i + 1])

                if "vehicle" in this_line:
                    # Merge lines and clean
                    merged = f"{this_line} {next_line}".replace(":", " ").replace("\xa0", " ").upper()
                    merged = re.sub(r"\s{2,}", " ", merged)

                    match = re.search(r"\b[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}\b", merged)
                    if match:
                        vehicle_number = match.group().replace(" ", "").strip().upper()
                        # print(f"✅ Found vehicle number (pass 2): {vehicle_number}")
                        break
        # Pass 3: Scan full document for standalone vehicle-looking patterns or "Carrier No." formats
        if vehicle_number == "Not found":
            for i, line in enumerate(lines):
                clean = normalize_ascii(line)
                # Case A: Line contains something like "Carrier No.: DD01E9074"
                if "carrier" in clean:
                    match = re.search(r"\b[A-Z]{2}\d{2}[A-Z]{1,3}\d{3,4}\b", clean.upper())
                    if match:
                        vehicle_number = match.group().replace(" ", "").strip().upper()
                        # print(f"✅ Found vehicle number (pass 3a - carrier line): {vehicle_number}")
                        break

                # Case B: Line *is* the vehicle number (standalone)
                match = re.fullmatch(r"[A-Z]{2}\d{2}[A-Z]{1,3}\d{3,4}", clean.upper())
                if match:
                    vehicle_number = match.group().strip().upper()
                    # print(f"✅ Found vehicle number (pass 3b - standalone line): {vehicle_number}")
                    break


        # MATERIAL — skip generic keywords in next line
        skip_keywords = ["vehicle", "operator", "date", "source", "time", "gross", "tare", "net", "wt"]

        if material == "Not found" and any(k in clean for k in ["material", "commodity"]):
            for offset in range(1, 3):
                if i + offset < len(lines):
                    mat_line = normalize_ascii(lines[i + offset]).strip(":;")
                    if mat_line and not any(k in mat_line for k in skip_keywords) and not re.match(r"^[\d\W\s]+$", mat_line):
                        material = mat_line.title()
                        break


        # Pass 1: label-based, multi-line format
        if net_weight == "Not found" and "net" in clean and "wt" in clean:
            for offset in range(1, 4):
                if i + offset < len(lines):
                    line_val = normalize_ascii(lines[i + offset])
                    match = re.search(r"\d{4,6}", line_val)
                    if match:
                        net_weight = f"{int(match.group()) / 1000:.3f} Tons"
                        break

        # Pass 2: vertical stacked label
        if net_weight == "Not found":
            for i in range(len(lines) - 2):
                l1 = normalize_ascii(lines[i])
                l2 = normalize_ascii(lines[i + 1])
                l3 = normalize_ascii(lines[i + 2])
                if "net" in l1 and "weight" in l2:
                    match = re.search(r"\d{4,6}", l3)
                    if match:
                        net_weight = f"{int(match.group()) / 1000:.3f} Tons"
                        # print(f"✅ Found net weight (vertical stack): {net_weight}")
                        break

        # ✅ New: inline phrase like "Total Net Weight 12210.00"
        if net_weight == "Not found":
            for line in lines:
                clean_line = normalize_ascii(line)
                if "net weight" in clean_line:
                    match = re.search(r"\b\d{4,6}(?:\.\d{1,2})?\b", clean_line)
                    if match:
                        net_weight = f"{float(match.group()):,.3f} Tons"
                        # print(f"✅ Found net weight (inline): {net_weight}")
                        break

        # Pass 4: textual fallback
        if net_weight == "Not found":
            if "one" in clean and "kg" in clean:
                words = clean.lower().split()
                digits = "".join([textual_map.get(w, "") for w in words])
                if len(digits) >= 4:
                    net_weight = f"{int(digits) / 1000:.3f} Tons"


        # --- DATE EXTRACTION (DD/MM/YYYY, DD/MM/YY, or YYYY-MM-DD) ---
        full_text = " ".join([normalize_ascii(l) for l in lines])
        date_matches = re.findall(r"\b(?:\d{2}/\d{2}/\d{2,4}|\d{4}-\d{2}-\d{2})\b", full_text)
        if date_matches:
            def sort_key(d):
                if "-" in d:
                    year, month, day = map(int, d.split("-"))
                else:
                    day, month, year = map(int, d.split("/"))
                    year += 2000 if year < 100 else 0
                return (year, month, day)
            date = sorted(date_matches, key=sort_key, reverse=True)[0]
            # print(f"✅ Found date: {date}")

        # --- NAME FIELD LOGIC ---
        if name == "Not found":
            # Case 1: If line 0 looks like a clean name (common in newer slips)
            line0 = normalize_ascii(lines[0])
            if 2 <= len(line0.split()) <= 5 and not any(kw in line0 for kw in ["rst", "no", "kg", "wt", "date", "phone", "vehicle"]):
                name = lines[0].strip().title()
                # print(f"✅ Found name (line 0): {name}")

        # Case 2: Fallback to line 4 for legacy format slips (like 'Ajanta Weigh Bridge')
        if name == "Not found" and len(lines) > 4:
            line4 = normalize_ascii(lines[4])
            if 2 <= len(line4.split()) <= 5 and not any(kw in line4 for kw in ["gross", "net", "tare", "phone", "bags", "date", "wt", "operator"]):
                name = lines[4].strip().title()
                # print(f"✅ Found name (line 4 fallback): {name}")


    result.update({
        "Date": date,
        "Vehicle Number": vehicle_number,
        "Name": name,
        "Material": material,
        "Net Weight (Tons)": net_weight
    })

    return result
