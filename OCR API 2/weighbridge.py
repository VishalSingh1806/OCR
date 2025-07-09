# # weighbridge.py

# import re
# from ocr_utils import debug_print_lines, normalize_ascii


# textual_map = {
#     "zero": "0", "one": "1", "two": "2", 
#     "three": "3", "four": "4", "five": "5",
#     "six": "6", "seven": "7", "eight": "8", "nine": "9"
# }

# def extract_weighbridge_fields(text):
#     print("🧾 Processing: Weighbridge")
#     lines = text.splitlines()
#     debug_print_lines(text, "Weighbridge: Line-by-Line OCR Output")

#     # normalize for matching
#     norm_lines = [normalize_ascii(ln) for ln in lines]
#     full_norm = " ".join(norm_lines)

#     # initialize fields
#     date = "Not found"
#     vehicle_number = "Not found"
#     name = "Not found"
#     material = "Not found"
#     net_weight = "Not found"



#     # ── NAME ─────────────────────────────────────────────────────────────────
#     for ln in lines:
#         if "weigh bridge" in normalize_ascii(ln):
#             name = ln.strip().title()
#             break



#     # ── VEHICLE NUMBER ────────────────────────────────────────────────────────
#     # Pass 1
#     if vehicle_number == "Not found":
#         seg = lines[5:11]
#         cands = []
#         for ln in seg:
#             cl = normalize_ascii(ln)
#             if "vehicle" in cl or re.search(r"[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}", cl):
#                 cands.append(cl)
#         combo = " ".join(cands).replace(":", " ").replace("\xa0"," ")
#         combo = re.sub(r"\s{2,}", " ", combo).upper()
#         m = re.search(r"[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}", combo)
#         if m:
#             vehicle_number = m.group().replace(" ", "")

#     # Pass 2
#     if vehicle_number == "Not found":
#         for i in range(len(lines)-1):
#             l1, l2 = normalize_ascii(lines[i]), normalize_ascii(lines[i+1])
#             if "vehicle" in l1:
#                 merged = f"{l1} {l2}".replace(":", " ").replace("\xa0"," ")
#                 merged = re.sub(r"\s{2,}", " ", merged).upper()
#                 m = re.search(r"[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}", merged)
#                 if m:
#                     vehicle_number = m.group().replace(" ", "")
#                     break

#     # Pass 3
#     if vehicle_number == "Not found":
#         for ln in lines:
#             cl = normalize_ascii(ln).upper()
#             if "carrier" in cl:
#                 m = re.search(r"[A-Z]{2}\d{2}[A-Z]{1,3}\d{3,4}", cl)
#                 if m:
#                     vehicle_number = m.group()
#                     break
#             m2 = re.fullmatch(r"[A-Z]{2}\d{2}[A-Z]{1,3}\d{3,4}", cl)
#             if m2:
#                 vehicle_number = m2.group()
#                 break

#     # ── MATERIAL ─────────────────────────────────────────────────────────────
#     if material == "Not found":
#         skip = {"vehicle","operator","date","source","time","gross","tare","net","wt"}
#         for i, ln in enumerate(lines):
#             cl = normalize_ascii(ln)
#             if any(k in cl for k in ("material","commodity")):
#                 if i+1 < len(lines):
#                     cand = normalize_ascii(lines[i+1]).strip(":;")
#                     if cand and re.search(r"[A-Za-z]", cand) and not any(k in cand for k in skip):
#                         material = cand.title()
#                         break

#     # ── PASS 0: Table-driven Gross/Tare/Net ─────────────────────────────────
#     label_patterns = {
#         "gross": ["gross weight","groos","gross"],
#         "tare":  ["tare weight","tare"],
#         "net":   ["net weight","nett","net"]
#     }
#     # match 3–6 digits with optional commas/decimals, anywhere in string
#     num_re = re.compile(r"(\d{3,6}(?:,\d{3})*(?:\.\d+)?)")
#     # offsets: net first looks below (+1), then above, then further away
#     offsets = {
#         "gross": (-1, 1, 2),
#         "tare":  (-1, 1, 2),
#         "net":   (1, -1, 2)
#     }
#     weights = {}
#     for key, pats in label_patterns.items():
#         for idx, nl in enumerate(norm_lines):
#             if any(p in nl for p in pats):
#                 for off in offsets[key]:
#                     j = idx + off
#                     if j < 0 or j >= len(norm_lines):
#                         continue
#                     cand = norm_lines[j]
#                     # skip obvious date/time/currency lines
#                     if any(sym in cand for sym in ("/", ":", "$")):
#                         continue
#                     m = num_re.search(cand)
#                     if m:
#                         weights[key] = m.group(1)
#                         break
#                 break

#     if "net" in weights:
#         try:
#             v = float(weights["net"].replace(",", ""))
#             net_weight = f"{v/1000:.3f} Tons"
#         except:
#             pass

#     # ── FALLBACK PASSES ─────────────────────────────────────────────────────
#     if net_weight == "Not found":
#         # Pass 1: multi-line “net” + “wt”
#         for i, ln in enumerate(norm_lines):
#             if "net" in ln and "wt" in ln:
#                 for off in (1,2,3):
#                     j = i + off
#                     if j < len(norm_lines):
#                         m = re.search(r"\d{3,6}", norm_lines[j])
#                         if m:
#                             net_weight = f"{int(m.group())/1000:.3f} Tons"
#                             break
#                 if net_weight != "Not found":
#                     break

#         # Pass 2: vertical stack
#         if net_weight == "Not found":
#             for i in range(len(norm_lines)-2):
#                 if "net" in norm_lines[i] and "weight" in norm_lines[i+1]:
#                     m = re.search(r"\d{3,6}", norm_lines[i+2])
#                     if m:
#                         net_weight = f"{int(m.group())/1000:.3f} Tons"
#                         break

#         # Pass 3: inline
#         if net_weight == "Not found":
#             for ln in norm_lines:
#                 if "net weight" in ln:
#                     m = re.search(r"\d{3,6}(?:\.\d+)?", ln)
#                     if m:
#                         net_weight = f"{float(m.group())/1000:.3f} Tons"
#                         break

#         # Pass 4: textual fallback
#         if net_weight == "Not found":
#             for ln in norm_lines:
#                 parts = ln.split()
#                 digits = "".join(textual_map.get(w, "") for w in parts)
#                 if digits.isdigit() and len(digits) >= 4:
#                     net_weight = f"{int(digits)/1000:.3f} Tons"
#                     break

#     # ── Final Result ────────────────────────────────────────────────────────
#     return {
#         "Category": "Weighbridge",
#         "Date": date(lines),
#         "Vehicle Number": vehicle_number(vehicle_number),
#         "Name": name,
#         "Material": material_name(material),
#         "Net Weight (Tons)": net_weight(net_weight)
#     }
# weighbridge.py

import re
from ocr_utils import debug_print_lines, normalize_ascii

textual_map = {
    "zero": "0", "one": "1", "two": "2",
    "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9"
}

def extract_date(norm_lines):
    # First calendar‐style date in any line
    for ln in norm_lines:
        m = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", ln)
        if m:
            return m.group(1)
    return "Not found"

def extract_vehicle_number(lines, norm_lines):
    # Try three passes to catch the number
    # Pass 1: look in lines 5–11
    seg = lines[5:11]
    combo = []
    for ln in seg:
        cl = normalize_ascii(ln)
        if "vehicle" in cl or re.search(r"[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}", cl):
            combo.append(cl)
    joined = " ".join(combo).replace(":", " ").replace("\xa0", " ")
    joined = re.sub(r"\s{2,}", " ", joined).upper()
    m = re.search(r"[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}", joined)
    if m:
        return m.group().replace(" ", "")

    # Pass 2: split‐line “Vehicle” + next line
    for i in range(len(lines) - 1):
        l1 = normalize_ascii(lines[i])
        if "vehicle" in l1:
            l2 = normalize_ascii(lines[i + 1])
            merged = f"{l1} {l2}".replace(":", " ").replace("\xa0", " ")
            merged = re.sub(r"\s{2,}", " ", merged).upper()
            m = re.search(r"[A-Z]{2}\d{2,3}[A-Z]?\s?\d{3,4}", merged)
            if m:
                return m.group().replace(" ", "")

    # Pass 3: “Carrier No.” or standalone pattern
    for ln in lines:
        cl = normalize_ascii(ln).upper()
        if "carrier" in cl:
            m = re.search(r"[A-Z]{2}\d{2}[A-Z]{1,3}\d{3,4}", cl)
            if m:
                return m.group()
        if re.fullmatch(r"[A-Z]{2}\d{2}[A-Z]{1,3}\d{3,4}", cl):
            return cl

    return "Not found"

def extract_name(lines, norm_lines):
    # First line that mentions “weigh bridge”
    for i, ln in enumerate(norm_lines):
        if "weigh bridge" in ln:
            return lines[i].strip().title()
    return "Not found"

def extract_material(lines, norm_lines):
    # Line after “material” or “commodity”
    skip = {"vehicle", "operator", "date", "source", "time", "gross", "tare", "net", "wt"}
    for i, ln in enumerate(norm_lines):
        if any(k in ln for k in ("material", "commodity")) and i + 1 < len(lines):
            cand = normalize_ascii(lines[i + 1]).strip(":; ")
            if re.search(r"[A-Za-z]", cand) and not any(k in cand for k in skip):
                return cand.title()
            break
    return "Not found"

def extract_net_weight(lines, norm_lines):
    # ─── 1️⃣ Locate the “net weight” label ───
    net_idx = None
    for i, ln in enumerate(norm_lines):
        low = ln.lower()
        cleaned = re.sub(r"[^\w\s]", " ", low)       # strip punctuation
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if "net weight" in cleaned or "nett" in cleaned:
            net_idx = i
            break

    # ─── 2️⃣ Check up to 3 lines above and below ───
    if net_idx is not None:
        # above
        for back in range(1, 4):
            j = net_idx - back
            if j < 0:
                break
            raw = lines[j]
            if "/" in raw or ":" in raw:
                continue
            if any(w in raw.lower() for w in ("tare", "gross", "weight")):
                continue
            val = re.sub(r"[^\d\.]", "", raw).strip()
            if re.fullmatch(r"\d+(\.\d+)?", val):
                kg = float(val)
                return f"{kg/1000:.3f} Tons"
        # below
        for forward in range(1, 4):
            j = net_idx + forward
            if j >= len(lines):
                break
            raw = lines[j]
            if "/" in raw or ":" in raw:
                continue
            if any(w in raw.lower() for w in ("tare", "gross", "weight")):
                continue
            val = re.sub(r"[^\d\.]", "", raw).strip()
            if re.fullmatch(r"\d+(\.\d+)?", val):
                kg = float(val)
                return f"{kg/1000:.3f} Tons"

    # ─── Inline fallback: “net weight” on same line ───
    for ln in norm_lines:
        m = re.search(
            r"net weight[:\s\-]{0,3}(\d{3,6}(?:,\d{3})*(?:\.\d+)?)",
            ln, re.IGNORECASE
        )
        if m:
            v = float(m.group(1).replace(",", ""))
            return f"{v/1000:.3f} Tons"

    # ─── Textual fallback: spelled-out digits ───
    for ln in norm_lines:
        parts = ln.split()
        digits = "".join(textual_map.get(w.lower(), "") for w in parts)
        if digits.isdigit() and len(digits) >= 4:
            v = int(digits)
            return f"{v/1000:.3f} Tons"

    return "Not found"

def extract_weighbridge_fields(text):
    print("🧾 Processing: Weighbridge")
    lines = text.splitlines()
    debug_print_lines(text, "Weighbridge: Line-by-Line OCR Output")

    norm_lines = [normalize_ascii(ln) for ln in lines]

    return {
        "Category": "Weighbridge",
        "Date": extract_date(norm_lines),
        "Vehicle Number": extract_vehicle_number(lines, norm_lines),
        "Name": extract_name(lines, norm_lines),
        "Material": extract_material(lines, norm_lines),
        # pass both raw and normalized lines now:
        "Net Weight (Tons)": extract_net_weight(lines, norm_lines)
    }
