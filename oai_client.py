from openai import OpenAI
import os
from pathlib import Path
from pymongo import MongoClient
import PyPDF2
from typing import Optional, Dict, Any

OPENAI_API_KEY="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"

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.environ.get("MONGO_DB", "app_database")

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
bills_collection = db["bills"]

## this is basic chat completion, change once org gets access to reasoning capability
system_message = """
You are a medical insurance lawyer specializing in helping patients resolve medical billing disputes and insurance claim issues. Your expertise includes healthcare law, insurance regulations, billing practices, and patient rights.

Your role is to:
- Analyze medical bills for errors, overcharges, and billing irregularities
- Identify potential insurance coverage issues and claim denials that may be improper
- Spot coding errors, duplicate charges, and services not rendered
- Recognize balance billing violations and out-of-network billing issues
- Provide guidance on patient rights and legal protections
- Suggest specific actions to dispute incorrect charges
- Identify when bills violate state or federal healthcare billing regulations

When reviewing medical bills or insurance issues, look for:
- Incorrect CPT codes or procedure descriptions
- Charges for services not received
- Duplicate billing entries
- Out-of-network surprise billing violations
- Insurance claim processing errors
- Unreasonable or inflated charges compared to standard rates

Always provide actionable advice and explain the legal basis for any disputes you recommend.
"""

def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text content from a PDF file."""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

def get_bill_by_id(bill_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve bill document from MongoDB by ID."""
    return bills_collection.find_one({"id": bill_id})

def analyze_medical_bill(bill_id: str) -> Dict[str, Any]:
    """
    Analyze a medical bill for issues and provide legal advice.
    
    Args:
        bill_id: UUID of the bill to analyze
        
    Returns:
        Dictionary containing analysis results and recommendations
    """
    # Get bill from database
    bill_doc = get_bill_by_id(bill_id)
    if not bill_doc:
        raise Exception(f"Bill with ID {bill_id} not found")
    
    # Extract text from PDF
    file_path = Path(bill_doc["path"])
    if not file_path.exists():
        raise Exception(f"Bill file not found at {file_path}")
    
    bill_text = extract_text_from_pdf(file_path)
    
    # Create user query with bill content
    user_query = f"""
    Please analyze this medical bill for potential issues, errors, and billing irregularities:

    MEDICAL BILL CONTENT:
    {bill_text}

    Please provide:
    1. A summary of the bill
    2. Any potential issues or red flags you identify
    3. Specific recommendations for disputing incorrect charges
    4. Legal basis for any disputes you recommend
    5. Next steps the patient should take
    """
    
    # Get AI analysis
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
    )
    
    analysis_result = response.choices[0].message.content
    
    # Update bill status in database
    bills_collection.update_one(
        {"id": bill_id},
        {"$set": {"status": "analyzed", "analysis": analysis_result}}
    )
    
    return {
        "bill_id": bill_id,
        "status": "analyzed",
        "analysis": analysis_result,
        "bill_text": bill_text[:500] + "..." if len(bill_text) > 500 else bill_text  # Truncated for response
    }

# Example usage - uncomment to test with a specific bill ID
# if __name__ == "__main__":
#     bill_id = "your-bill-uuid-here"
#     try:
#         result = analyze_medical_bill(bill_id)
#         print("Analysis Result:")
#         print(result["analysis"])
#     except Exception as e:
#         print(f"Error: {e}")
