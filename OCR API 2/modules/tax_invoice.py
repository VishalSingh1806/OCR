import textwrap
from llm_utils import extract_fields_with_gemini


def extract_tax_invoice_fields(image_paths: list[str]) -> dict:
    prompt = textwrap.dedent("""\
You are an expert ISO-compliant parser specialized in Indian Tax Invoice documents.

Task:
Extract exactly these five fields from each Tax Invoice image:
1. Vehicle Number
   • Look for labels like "Vehicle No" or "Vehicle Number".
   • Normalize to uppercase alphanumeric.
2. Date
   • Match formats DD/MM/YYYY or DD-MM-YYYY.
   • Normalize to DD-MM-YYYY.
3. Invoice No
   • Match labels such as "Invoice No", "Inv No", or "Tax Invoice No".
4. Material Name
   • Extract the primary material or product description from the invoice line items.
5. Net Weight (Tons)
   • Identify "Net Weight" or "Net Wt" given in kilograms.
   • Convert from kg → tons and round to two decimal places.

Rules:
- If a field is missing or unreadable, return `null`.
- Never invent or guess values.
- Respond with exactly one valid JSON object with these keys only:
  Vehicle Number, Date, Invoice No, Material Name, Net Weight (Tons).

Example:
```
Tax Invoice No: INV-2025-00123
Date: 20/01/2025
Vehicle No: MH01AB2345
Item Description: PET Bottle
Gross Weight: 15000 kg, Tare Weight: 5000 kg, Net Weight: 10000 kg
```
→
```json
{
  "Vehicle Number": "MH01AB2345",
  "Date": "20-01-2025",
  "Invoice No": "INV-2025-00123",
  "Material Name": "PET Bottle",
  "Net Weight (Tons)": 10.00
}
```

Now process the images and return only the JSON object.
""")

    expected_fields = [
        "Vehicle Number",
        "Date",
        "Invoice No",
        "Material Name",
        "Net Weight (Tons)"
    ]

    return extract_fields_with_gemini(
        image_paths=image_paths,
        prompt=prompt,
        expected_fields=expected_fields,
        document_type="Tax Invoice"
    )
