from llm_utils import extract_fields_with_gemini

def extract_lr_copy_fields(image_paths: list[str]) -> dict:
    prompt = """You are an expert document parser for Indian transport documents.

Extract the following fields from this LR Copy document:
- Vehicle Number
- Date
- No
- Transporter Name
- Net Weight (Tons)
- Consignee
- Consignor
- From State
- To State

Respond ONLY in valid JSON format like this (do NOT wrap in triple backticks):

{
  "Vehicle Number": "...",
  "Date": "...",
  "No": "...",
  "Transporter Name": "...",
  "Net Weight (Tons)": "...",
  "Consignee": "...",
  "Consignor": "...",
  "From State": "...",
  "To State": "..."
}
"""
    expected_fields = ["Date", "Vehicle Number", "No", "Transporter Name", "Net Weight (Tons)", "Consignee", "Consignor", "From State", "To State"]
    return extract_fields_with_gemini(image_paths=image_paths, prompt=prompt, expected_fields=expected_fields, document_type="LR Copy")
