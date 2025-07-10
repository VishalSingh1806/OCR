from llm_utils import extract_fields_with_gemini

def extract_weighbridge_fields(image_paths: list[str]) -> dict:
    prompt = """You are an expert document parser for Indian transport documents.

Extract the following fields from this weighbridge document:
- Date
- Vehicle Number
- Name (Weighbridge name)
- Material
- Net Weight in Tons (convert if needed)

Respond ONLY in valid JSON format like this (do NOT wrap in triple backticks):

{
  "Date": "...",
  "Vehicle Number": "...",
  "Name": "...",
  "Material": "...",
  "Net Weight (Tons)": "..."
}
"""
    expected_fields = ["Date", "Vehicle Number", "Name", "Material", "Net Weight (Tons)"]
    return extract_fields_with_gemini(
        image_paths=image_paths, 
        prompt=prompt, 
        expected_fields=expected_fields, 
        document_type="Weighbridge"
    )
