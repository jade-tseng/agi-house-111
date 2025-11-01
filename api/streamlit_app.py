import streamlit as st
import uuid
from pathlib import Path
import os

# Page configuration
st.set_page_config(
    page_title="Bill Upload",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Bill Submission")
st.write("Upload your bill document for processing")

# Create bills directory if it doesn't exist
bills_dir = Path("./bills")
bills_dir.mkdir(exist_ok=True)

# File uploader
uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"],
    help="Only PDF files are supported"
)

if uploaded_file is not None:
    # Check if file is PDF
    if not uploaded_file.name.lower().endswith('.pdf'):
        st.error("❌ File not supported - Only PDF files are accepted")
    else:
        # Generate UUID
        bill_uuid = uuid.uuid4()
        
        # Save file with UUID as filename
        file_path = bills_dir / f"{bill_uuid}.pdf"
        
        try:
            # Write the uploaded file to disk
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Display success message with response data
            st.success("✅ Bill submitted successfully!")
            
            # Display response in JSON format matching the API spec
            st.subheader("Response")
            response_data = {
                "id": str(bill_uuid),
                "status": "pending"
            }
            
            st.json(response_data)
            
            # Additional info
            st.info(f"📁 File saved to: `{file_path}`")
            
        except Exception as e:
            st.error(f"❌ Failed to process bill: {str(e)}")

