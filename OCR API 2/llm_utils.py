import logging
import json
from collections import OrderedDict
from google import genai
from google.genai import types

# ─── Logger Setup ─────────────────────────────────────────────────────────────
logger = logging.getLogger("gemini_parser")
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
logger.addHandler(console)

# ─── Gemini Client Setup ──────────────────────────────────────────────────────
genai_client = genai.Client(
    vertexai=True,
    project="ocr-training-450612",
    location="global",
)
MODEL_NAME = "gemini-2.5-flash-lite-preview-06-17"

# ─── Helpers ───────────────────────────────────────────────────────────────────
def _img_to_part(image_path: str) -> types.Part:
    logger.debug(f"📄 Converting image to part: {image_path}")
    with open(image_path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/jpeg")


def safe(val):
    """Turn any 'null'/'none' strings into empty, and non-str into empty str."""
    if isinstance(val, str) and val.strip().lower() in ("null", "none"):
        return ""
    return val if isinstance(val, str) else ""


def _empty_result(fields: list[str], doc_type: str, error: str = "") -> OrderedDict:
    """Build an empty OrderedDict result when Gemini fails to return JSON."""
    od = OrderedDict()
    # metadata first
    od["Category"] = doc_type.title()
    od["Category Confidence"] = "0.0"
    # then placeholders for every expected field
    for key in fields:
        od[key] = ""
    return od

# ─── Main Gemini Runner ────────────────────────────────────────────────────────
def extract_fields_with_gemini(
    image_paths: list[str],
    prompt: str,
    expected_fields: list[str],
    document_type: str = "Unknown"
) -> OrderedDict:
    """
    Sends images + prompt to Gemini, parses JSON, and returns an OrderedDict
    whose first keys are Category/Confidence, then your expected_fields.
    """
    logger.info(f"🚀 Running Gemini extraction for: {document_type}, files={len(image_paths)}")

    # build the request
    parts = [_img_to_part(path) for path in image_paths]
    parts.append(types.Part.from_text(text=prompt))
    contents = [types.Content(role="user", parts=parts)]

    config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=2048,
        safety_settings=[types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")],
    )

    try:
        response = genai_client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=config
        )
        raw_output = None
        if response.candidates and response.candidates[0].content.parts:
            raw_output = response.candidates[0].content.parts[0].text.strip()

        logger.debug(f"🧠 Gemini Raw Output:\n{raw_output}")
        if not raw_output:
            raise ValueError("Gemini returned empty response.")

        # strip markdown fences if present
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("`").strip()
            if raw_output.lower().startswith("json"):
                raw_output = raw_output[4:].strip()

        parsed = json.loads(raw_output)

        # build ordered result
        od = OrderedDict()
        # 1) metadata
        od["Category"] = document_type.title()
        od["Category Confidence"] = "1.0"
        # 2) your fields, in order
        for key in expected_fields:
            val = parsed.get(key)
            if isinstance(val, (int, float)):
                # preserve numeric values formatted to two decimals
                od[key] = f"{val:.2f}"
            else:
                od[key] = safe(val)

        logger.info(f"✅ Parsed fields: {od}")
        return od

    except json.JSONDecodeError as je:
        logger.error(f"❌ JSON Decode Error: {je}")
        return _empty_result(expected_fields, document_type, f"JSON decode error: {je}")

    except Exception as e:
        logger.exception("❌ Gemini processing failed")
        return _empty_result(expected_fields, document_type, str(e))
