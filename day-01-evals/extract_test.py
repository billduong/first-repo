import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError
from typing import Literal

# 1. Define the schema with a strict regex constraint
class TriageRecord(BaseModel):
    client_name: str
    ticket_category: Literal["BILLING", "TECHNICAL_BUG", "ACCOUNT_SECURITY", "FEATURE_REQUEST"]
    urgency_score: int = Field(ge=1, le=5)
    # Strict regex: must be two uppercase letters, a dash, and three numbers (e.g., "IT-101")
    routing_code: str = Field(
        pattern=r"^[A-Z]{2}-\d{3}$", 
        description="Internal department routing code in format XX-123"
    )
    action_required: bool
    summary: str

# 2. Test 1: Simulating an invalid payload directly
print("--- SCENARIO 1: Intercepting Malformed Data Locally ---")
malformed_raw_json = json.dumps({
    "client_name": "Apex Corp",
    "ticket_category": "BILLING",
    "urgency_score": 10,                 # Fails ge=1, le=5 constraint
    "routing_code": "finance_dept_99",   # Fails regex pattern ^[A-Z]{2}-\d{3}$
    "action_required": True,
    "summary": "Urgent accounting issue."
})

try:
    # Attempting to validate invalid data
    record = TriageRecord.model_validate_json(malformed_raw_json)
    print("Record validated successfully.")
except ValidationError as e:
    print("Caught Pydantic ValidationError successfully!\n")
    # Pydantic breaks down every single field failure:
    for error in e.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        print(f"  * Field Failed: {field}")
        print(f"    Error Type:   {error['type']}")
        print(f"    Message:      {error['msg']}\n")

# 3. Test 2: Live API call without the required routing code present in text
print("--- SCENARIO 2: Live Model Call with Missing/Ambiguous Data ---")
client = genai.Client()

ambiguous_email = """
Hey, this is Dave from Alpha Partners. The login portal is giving a 500 error.
Please look into it when someone is free.
"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=f"Extract triage record:\n{ambiguous_email}",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=TriageRecord,
        temperature=0.0
    )
)

print(f"Raw Model JSON Output:\n{response.text}\n")

try:
    validated = TriageRecord.model_validate_json(response.text)
    print("Model adhered to schema correctly!")
    print(f"Generated Routing Code: {validated.routing_code}")
except ValidationError as e:
    print("Model violated schema constraints! Error details:")
    print(e.json(indent=2))