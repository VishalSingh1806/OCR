import textwrap
from llm_utils import extract_fields_with_gemini


def extract_delivery_challan_fields(image_paths: list[str]) -> dict:
    prompt = textwrap.dedent("""\
You are an expert ISO-compliant parser specialized in Indian Delivery Challan documents.

Task:
Extract exactly these nine fields from each Delivery Challan image:
1. Vehicle Number
   • Look for labels like "Vehicle No", "Vehicle Number".
   • Normalize to uppercase alphanumeric.
2. Date
   • Match formats DD/MM/YYYY or DD-MM-YYYY.
   • Normalize to DD-MM-YYYY.
3. Challan No
   • Match "Challan No", "DC No" or "DC Number".
4. Transporter Name
   • Extract the name printed at the Top of the document.
5. Net Weight (Tons)
   • Identify "Net Weight" or "Net Wt" in kg.
   • Convert from kg → tons and round to two decimals.
6. Consignee
   • Extract the party name labeled "Consignee".
7. Consignor
   • Extract the party name labeled "Consignor".
8. From State
   • Look for the source state field on the document.
9. To State
   • Look for the destination state field on the document.

Rules:
- If a field is missing or unreadable, return `null`.
- Never invent or guess values.
- Respond with exactly one valid JSON object with these keys only:
  Vehicle Number, Date, Challan No, Transporter Name, Net Weight (Tons),
  Consignee, Consignor, From State, To State.

Example:
```
Challan No: DC12345
Print Date: 15/01/2025
Vehicle No: MH01AB1234
Transporter: ABC Logistics
Consignor: XYZ Corp
Consignee: PQR Ltd.
From State: Maharashtra
To State: Gujarat
Gross Weight: 15000 kg, Tare Weight: 5000 kg, Net Weight: 10000 kg
```
→
```json
{
  "Vehicle Number": "MH01AB1234",
  "Date": "15-01-2025",
  "Challan No": "DC12345",
  "Transporter Name": "ABC Logistics",
  "Net Weight (Tons)": 10.00,
  "Consignee": "PQR Ltd.",
  "Consignor": "XYZ Corp",
  "From State": "Maharashtra",
  "To State": "Gujarat"
}
```

Now process the images and return only the JSON object.
""")

    expected_fields = [
        "Vehicle Number",
        "Date",
        "Challan No",
        "Transporter Name",
        "Net Weight (Tons)",
        "Consignee",
        "Consignor",
        "From State",
        "To State"
    ]

    return extract_fields_with_gemini(
        image_paths=image_paths,
        prompt=prompt,
        expected_fields=expected_fields,
        document_type="Delivery Challan"
    )
