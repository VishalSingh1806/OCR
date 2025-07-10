from llm_utils import extract_fields_with_gemini

def extract_tax_invoice_fields(image_paths: list[str]) -> dict:
    prompt = """You are an expert document parser for Indian transport documents.

Extract the following fields from this Tax Invoice document:
- Vehicle Number
- Date
- Invoice No
- Net Weight (Tons)
- Material Name

Respond ONLY in valid JSON format like this (do NOT wrap in triple backticks):

{
  "Vehicle Number": "...",
  "Date": "...",
  "Invoice No": "...",
  "Net Weight (Tons)": "...",
  "Material Name": "..."
}
"""
    expected_fields = ["Date", "Vehicle Number", "Invoice No", "Net Weight (Tons)", "Material Name"]
    return extract_fields_with_gemini(image_paths=image_paths, prompt=prompt, expected_fields=expected_fields, document_type="LR Copy")
