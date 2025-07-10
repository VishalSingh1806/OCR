from llm_utils import extract_fields_with_gemini

def extract_e_way_bill_fields(image_paths: list[str]) -> dict:
    prompt = """You are an expert document parser for Indian transport documents.

Extract the following fields from this E-Way Bill document:
- Generated Date
- Bill No
- Net weight (in Tons)
- Valid Upto
- From State
- To State
- Categorization of Plastic

Respond ONLY in valid JSON format like this (do NOT wrap in triple backticks):

{
  "Generated Date": "...",
  "Bill No": "...",
  "Net weight (in Tons)": "...",
  "Valid Upto": "...",
  "From State": "...",
  "To State": "...",
  "Categorization of Plastic": "..."
}
"""
    expected_fields = ["Generated Date", "Bill No", "Net weight (in Tons)", "Valid Upto", "From State", "To State", "Categorization of Plastic"]
    return extract_fields_with_gemini(image_paths=image_paths, prompt=prompt, expected_fields=expected_fields, document_type="LR Copy")
