import base64
import os
import uuid
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Dict, Union

import streamlit as st
from openai import OpenAI
from pdf2image import convert_from_path
from pymongo import MongoClient

# MongoDB connection setup
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = os.environ.get("MONGO_DB", "app_database")

# OpenAI client setup
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Initialize MongoDB client and get bills collection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[MONGO_DB]
bills_collection = db["bills"]


def summarize_bill_with_vision(file_path: Path) -> str:
    """
    Analyze a PDF bill using OpenAI Vision API and return a summary.

    Args:
        file_path: Path to the PDF file to analyze

    Returns:
        String summary of the bill content

    Raises:
        Exception: If OpenAI client is not configured or if analysis fails
    """
    if not openai_client:
        raise Exception("OpenAI API key not configured")

    try:
        # Convert PDF to images (only first page for efficiency)
        images = convert_from_path(file_path, first_page=1, last_page=1)

        if not images:
            raise Exception("Failed to convert PDF to images")

        # Convert first page to base64
        buffered = BytesIO()
        images[0].save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        # Call OpenAI Vision API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are a bill analysis assistant. Analyze the bill document and provide a concise summary including: vendor/company name, total amount, date, and key items or services. Be specific and extract exact values when visible.",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this bill and provide a summary with the following details: vendor name, total amount, date, and main items/services.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            },
                        },
                    ],
                },
            ],
            max_tokens=500,
        )

        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"Failed to summarize bill: {str(e)}")


def save_uploaded_bill(
    file_content: bytes, bills_dir: Path
) -> Dict[str, Union[str, None]]:
    """
    Save an uploaded bill file to the bills directory with a UUID filename.
    Also creates a MongoDB document with the file metadata and AI-generated summary.

    Args:
        file_content: The binary content of the file to save
        bills_dir: Path to the directory where bills should be saved

    Returns:
        Dictionary containing the UUID, status, and summary (if successful)

    Raises:
        Exception: If file save or MongoDB insertion fails
    """
    # Generate UUID
    bill_uuid = uuid.uuid4()

    # Save file with UUID as filename
    file_path = bills_dir / f"{bill_uuid}.pdf"

    try:
        # Write the file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Try to summarize the bill using OpenAI Vision API
        summary = None
        status = "pending"
        processed_at = None

        try:
            summary = summarize_bill_with_vision(file_path)
            status = "processed"
            processed_at = datetime.now()
        except Exception as e:
            # If summarization fails, log the error but continue with upload
            print(f"Warning: Failed to summarize bill: {str(e)}")
            status = "pending"

        # Create MongoDB document
        document = {
            "id": str(bill_uuid),
            "path": f"./bills/{bill_uuid}.pdf",
            "status": status,
            "summary": summary,
            "uploaded_at": datetime.now(),
            "processed_at": processed_at,
        }

        # Insert document into MongoDB
        bills_collection.insert_one(document)

        return {"id": str(bill_uuid), "status": status, "summary": summary}
    except Exception as e:
        # If MongoDB insertion fails, clean up the saved file
        if file_path.exists():
            file_path.unlink()
        raise Exception(f"Failed to save bill: {str(e)}")


# Page configuration
st.set_page_config(page_title="Bill Upload", page_icon="📄", layout="centered")

st.title("📄 Bill Submission")
st.write("Upload your bill document for processing")

# Create bills directory if it doesn't exist
bills_dir = Path("./bills")
bills_dir.mkdir(exist_ok=True)

# File uploader
uploaded_file = st.file_uploader(
    "Choose a PDF file", type=["pdf"], help="Only PDF files are supported"
)

if uploaded_file is not None:
    # Check if file is PDF
    if not uploaded_file.name.lower().endswith(".pdf"):
        st.error("❌ File not supported - Only PDF files are accepted")
    else:
        try:
            # Show processing message
            with st.spinner("📄 Uploading and analyzing bill..."):
                # Save the uploaded file using the extracted function
                response_data = save_uploaded_bill(
                    uploaded_file.getbuffer(), bills_dir
                )

            # Display success message with response data
            st.success("✅ Bill submitted successfully!")

            # Display response in JSON format matching the API spec
            st.subheader("Response")
            st.json(
                {"id": response_data["id"], "status": response_data["status"]}
            )

            # Additional info
            file_path = bills_dir / f"{response_data['id']}.pdf"
            st.info(f"📁 File saved to: `{file_path}`")

            # Display AI-generated summary if available
            if response_data.get("summary"):
                st.subheader("📝 AI-Generated Summary")
                with st.expander("View Bill Summary", expanded=True):
                    st.markdown(response_data["summary"])
            elif response_data["status"] == "pending":
                st.warning(
                    "⚠️ AI summarization failed or is pending. Bill uploaded successfully but without analysis."
                )

        except Exception as e:
            st.error(f"❌ Failed to process bill: {str(e)}")
