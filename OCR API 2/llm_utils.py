import logging
import json
from google import genai
from google.genai import types

# ─── Logger Setup ───
logger = logging.getLogger("gemini_parser")
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
logger.addHandler(console)

# ─── Gemini Client Setup ───
genai_client = genai.Client(
    vertexai=True,
    project="ocr-training-450612",
    location="global",
)
MODEL_NAME = "gemini-2.5-flash-lite-preview-06-17"

def _img_to_part(image_path):
    logger.debug(f"📄 Converting image to part: {image_path}")
    with open(image_path, "rb") as f:
        return types.Part.from_bytes(data=f.read(), mime_type="image/jpeg")

def safe(val):
    if isinstance(val, str) and val.strip().lower() in ("null", "none"):
        return ""
    return val if isinstance(val, str) else ""

# ─── Main Gemini Runner ───
def extract_fields_with_gemini(
    image_paths: list[str],
    prompt: str,
    expected_fields: list[str],
    document_type: str = "Unknown"
) -> dict:
    logger.info(f"🚀 Running Gemini extraction for: {document_type}, files={len(image_paths)}")

    # Build content
    parts = [_img_to_part(path) for path in image_paths]
    parts.append(types.Part.from_text(text=prompt))
    contents = [types.Content(role="user", parts=parts)]

    config = types.GenerateContentConfig(
        temperature=0.2,
        top_p=0.95,
        max_output_tokens=2048,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
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

        # Remove ```json wrappers if needed
        if raw_output.startswith("```"):
            raw_output = raw_output.strip("`").strip()
            if raw_output.lower().startswith("json"):
                raw_output = raw_output[4:].strip()

        parsed = json.loads(raw_output)

        result = {
            key: safe(parsed.get(key)) for key in expected_fields
        }

        # Add metadata
        result["Category"] = document_type.title()
        result["Category Confidence"] = "1.0"
        result["Error"] = ""

        logger.info(f"✅ Parsed fields: {result}")
        return result

    except json.JSONDecodeError as je:
        logger.error(f"❌ JSON Decode Error: {je}")
        return _empty_result(expected_fields, document_type, f"JSON decode error: {str(je)}")

    except Exception as e:
        logger.exception("❌ Gemini processing failed")
        return _empty_result(expected_fields, document_type, str(e))

# ─── Fallback Builder ───
def _empty_result(fields, doc_type, error=""):
    return {
        **{key: "" for key in fields},
        "Category": doc_type.title(),
        "Category Confidence": "0.0",
        "Error": error
    }
