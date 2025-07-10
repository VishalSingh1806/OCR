from llm_utils import extract_fields_with_gemini

def extract_delivery_challan_fields(image_paths: list[str]) -> dict:
    prompt = """You are an expert document parser for Indian transport documents.

Extract the following fields from this Delivery Challan document:
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
