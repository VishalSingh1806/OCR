import textwrap
from llm_utils import extract_fields_with_gemini

def extract_weighbridge_fields(image_paths: list[str]) -> dict:
    prompt = textwrap.dedent("""\
    You are an expert ISO-compliant parser specialized in Indian weighbridge documents.

    Task:
    Extract exactly these five fields from each slip image:
    1. Date
       • Look for "Print Date" or any date on the slip.  
       • Normalize to DD-MM-YYYY.
    2. Vehicle No
       • Match labels like "Vehicle No", "Vehicle Number", "Vehical No".  
       • Return as uppercase alphanumeric.
    3. Weighbridge Name
       • Use the official site name printed under the header.
    4. Material
       • If a top-of-page total is used (see #5), set Material to null.  
       • Otherwise pick the first material column header (e.g. "PET BOTTLE","GREEN") whose Net Weight is non-zero.
    5. Net Weight (Tons)
       • Round to two decimal places.
       Priority:
         a) Look for a printed **Total Net Weight** label anywhere on the slip.  
            Recognize variants like:
            - "Total Net Weight"
            - "Total Net Weigh"
            - "Total Net Wt"
            - "Total NetWeight"
            possibly followed by a number in parentheses or after a colon.
            Convert from kg → tons.
         b) Else look for "Net Wt" or "Net Weight" in the table and convert from kg → tons.
         c) Else compute (Gross – Tare) from the table and convert.

    Rules:
    - If you cannot read a field, return `null`.  
    - Never invent or guess values.  
    - Respond with exactly one valid JSON object with these keys only:
      Date, Vehicle No, Weighbridge Name, Material, Net Weight (Tons).

    Examples:

    Example A (Total Net Weight with parentheses):
    ```
    Total Net Weight(10610.00)
    Print Date: 18/01/2025 12:50:09
    Vehicle No: GJ16AW9372
    Weighbridge Name: Malad West Depot
    Gross Wt: 16640 kg, Tare Wt: 6725 kg
    ```
    →  
    ```json
    {
      "Date": "18-01-2025",
      "Vehicle No": "GJ16AB1234",
      "Weighbridge Name": "Malad West Depot",
      "Material": null,
      "Net Weight (Tons)": 10.61
    }
    ```

    Example B (Printed Net Wt shorthand):
    ```
    Date: 04/01/2025
    Vehicle No: MH47BL3322
    Pet Bottle 17185 kg, Tare Wt: 6075 kg, Net Wt: 11110 kg
    ```
    →  
    ```json
    {
      "Date": "04-01-2025",
      "Vehicle No": "MH47BL3322",
      "Weighbridge Name": null,
      "Material": "PET BOTTLE",
      "Net Weight (Tons)": 11.11
    }
    ```

    Example C (Compute Gross – Tare):
    ```
    Gross Wt: 15805 kg, Tare Wt: 7965 kg
    ```
    →  
    ```json
    {
      "Date": null,
      "Vehicle No": null,
      "Weighbridge Name": null,
      "Material": "PET BOTTLE",
      "Net Weight (Tons)": 7.84
    }
    ```

    Now process the images and return only the JSON object.
    """)

    expected_fields = [
        "Date",
        "Vehicle No",
        "Weighbridge Name",
        "Material",
        "Net Weight (Tons)"
    ]
    return extract_fields_with_gemini(
        image_paths=image_paths,
        prompt=prompt,
        expected_fields=expected_fields,
        document_type="Weighbridge"
    )
