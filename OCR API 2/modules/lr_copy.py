import textwrap
from llm_utils import extract_fields_with_gemini


def extract_lr_copy_fields(image_paths: list[str]) -> dict:
    prompt = textwrap.dedent("""\
You are an expert ISO-compliant parser specialized in Indian LR Copy documents.

Task:
Extract exactly these nine fields from each LR Copy image:
1. Vehicle Number
   • Look for labels like "Vehicle No" or "Vehicle Number" or "Lorry No" or "Loffy Number".
   • Normalize to uppercase alphanumeric.
2. Date
   • Match formats DD/MM/YYYY or DD-MM-YYYY.
   • Normalize to DD-MM-YYYY.
3. No
   • Match "LR No", "Lorry Receipt No", or plain "No" labels.
4. Transporter Name
   • Extract the name next to or under the "Transporter" label.
5. Net Weight (Tons)
   • Identify "Net Weight" or "Net Wt" in kg.
   • Convert from kg → tons and round to two decimal places.
6. Consignee
   • Extract the party name labeled "Consignee".
7. Consignor
   • Extract the party name labeled "Consignor".
8. From State
   • Find the origin state name under "From".
9. To State
   • Find the destination state name under "To".

Rules:
- If a field is missing or unreadable, return `null`.
- Never invent or guess values.
- Respond with exactly one valid JSON object with these keys only:
  Vehicle Number, Date, No, Transporter Name,
  Net Weight (Tons), Consignee, Consignor, From State, To State.

Example:
```
LR No: LR123456
Date: 16/01/2025
Vehicle No: GJ01AB2345
Transporter: ABC Transports
Consignor: XYZ Industries
Consignee: PQR Traders
From State: Maharashtra
To State: Goa
Gross Weight: 12000 kg, Tare Weight: 2000 kg, Net Weight: 10000 kg
```
→
```json
{
  "Vehicle Number": "GJ01AB2345",
  "Date": "16-01-2025",
  "No": "LR123456",
  "Transporter Name": "ABC Transports",
  "Net Weight (Tons)": 10.00,
  "Consignee": "PQR Traders",
  "Consignor": "XYZ Industries",
  "From State": "Maharashtra",
  "To State": "Goa"
}
```

Now process the images and return only the JSON object.
""")

    expected_fields = [
        "Vehicle Number",
        "Date",
        "No",
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
        document_type="LR Copy"
    )
