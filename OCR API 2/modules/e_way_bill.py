import textwrap
from llm_utils import extract_fields_with_gemini


def extract_e_way_bill_fields(image_paths: list[str]) -> dict:
    prompt = textwrap.dedent("""\
You are an expert ISO-compliant parser specialized in Indian E-Way Bill documents.

Task:
Extract exactly these seven fields from each E-Way Bill image:
1. Generated Date
   • Look for labels like "Generated Date" or "Date Generated".
   • Normalize to DD-MM-YYYY.
2. Bill No
   • Match "EWB No", "Bill No", or "E-Way Bill Number".
3. Net Weight (Tons)
   • Identify "Net Weight" or "Net Wt" given in kg.
   • Convert from kg → tons and round to two decimal places.
4. Valid Upto
   • Find the "Valid Upto" date field.
   • Normalize to DD-MM-YYYY.
5. From State
   • Extract the origin state name from the "From" section.
6. To State
   • Extract the destination state name from the "To" section.
7. Categorization of Plastic
   • Look for the line or table entry labeled "Goods Description" or "Item" and return the plastic category (e.g., "PET Bottle", "HDPE", etc.).

Rules:
- If a field is missing or unreadable, return `null`.
- Never invent or guess values.
- Respond with exactly one valid JSON object with these keys only:
  Generated Date, Bill No, Net Weight (Tons), Valid Upto,
  From State, To State, Categorization of Plastic.

Example:
```
E-Way Bill No: 2025EWB0001234
Generated Date: 14/01/2025
Valid Upto: 17/01/2025
From: Maharashtra
To: Gujarat
Item Description: PET Bottle
Gross Weight: 12000 kg, Tare Weight: 2000 kg, Net Weight: 10000 kg
```
→
```json
{
  "Generated Date": "14-01-2025",
  "Bill No": "2025EWB0001234",
  "Net Weight (Tons)": 10.00,
  "Valid Upto": "17-01-2025",
  "From State": "Maharashtra",
  "To State": "Gujarat",
  "Categorization of Plastic": "PET Bottle"
}
```

Now process the images and return only the JSON object.
""")

    expected_fields = [
        "Generated Date",
        "Bill No",
        "Net Weight (Tons)",
        "Valid Upto",
        "From State",
        "To State",
        "Categorization of Plastic"
    ]

    return extract_fields_with_gemini(
        image_paths=image_paths,
        prompt=prompt,
        expected_fields=expected_fields,
        document_type="E-Way Bill"
    )
