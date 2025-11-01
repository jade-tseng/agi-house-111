import pytest
import tempfile
import shutil
from pathlib import Path
import uuid
import sys
from unittest.mock import Mock, patch, MagicMock

# Mock streamlit and its dependencies before importing streamlit_app
sys.modules['streamlit'] = MagicMock()

# Add the api directory to the Python path so we can import streamlit_app
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from streamlit_app import save_uploaded_bill


@pytest.fixture
def mock_mongo_collection():
    """
    Mock the MongoDB collection to avoid requiring a real MongoDB connection during tests.
    """
    with patch('streamlit_app.bills_collection') as mock_collection:
        # Configure the mock to have an insert_one method that returns a Mock result
        mock_collection.insert_one = MagicMock(return_value=Mock(inserted_id='mock_id'))
        yield mock_collection


@pytest.fixture
def temp_bills_dir():
    """
    Create a temporary directory for testing bill uploads.
    Cleans up after the test completes.
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup after test
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_pdf_file():
    """
    Create a mock PDF file content for testing.
    Returns bytes that represent a simple PDF-like content.
    """
    # This is a minimal PDF file structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Count 1
/Kids [3 0 R]
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Bill) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    return pdf_content


def test_file_upload_saves_to_bills_directory(temp_bills_dir, mock_pdf_file, mock_mongo_collection):
    """
    Test that when a file is uploaded, it is saved to ./bills/{uuid}.pdf
    and the response UUID matches the saved filename.
    """
    # Call the save function
    response = save_uploaded_bill(mock_pdf_file, temp_bills_dir)
    
    # Verify response structure
    assert "id" in response
    assert "status" in response
    assert response["status"] == "pending"
    
    # Verify the UUID is a valid UUID string
    response_uuid = response["id"]
    try:
        uuid.UUID(response_uuid)
    except ValueError:
        pytest.fail(f"Response ID '{response_uuid}' is not a valid UUID")
    
    # Verify the file was saved with the UUID as filename
    expected_file_path = temp_bills_dir / f"{response_uuid}.pdf"
    assert expected_file_path.exists(), f"File not found at expected path: {expected_file_path}"
    
    # Verify the file contents match the uploaded file
    with open(expected_file_path, "rb") as f:
        saved_content = f.read()
    
    assert saved_content == mock_pdf_file, "Saved file content does not match uploaded file"
    
    # Verify the file is saved in the correct directory structure
    assert expected_file_path.parent == temp_bills_dir
    
    # Verify the filename matches the UUID pattern
    assert expected_file_path.name == f"{response_uuid}.pdf"
    
    # Verify MongoDB insert_one was called
    mock_mongo_collection.insert_one.assert_called_once()
    
    # Verify the document structure passed to MongoDB
    call_args = mock_mongo_collection.insert_one.call_args[0][0]
    assert call_args["id"] == response_uuid
    assert call_args["status"] == "pending"
    assert call_args["path"] == f"./bills/{response_uuid}.pdf"


def test_multiple_uploads_generate_unique_uuids(temp_bills_dir, mock_pdf_file, mock_mongo_collection):
    """
    Test that multiple file uploads generate unique UUIDs.
    """
    # Upload multiple files
    response1 = save_uploaded_bill(mock_pdf_file, temp_bills_dir)
    response2 = save_uploaded_bill(mock_pdf_file, temp_bills_dir)
    response3 = save_uploaded_bill(mock_pdf_file, temp_bills_dir)
    
    # Verify all UUIDs are different
    uuids = [response1["id"], response2["id"], response3["id"]]
    assert len(set(uuids)) == 3, "UUIDs are not unique"
    
    # Verify all files exist
    for response_uuid in uuids:
        file_path = temp_bills_dir / f"{response_uuid}.pdf"
        assert file_path.exists(), f"File not found for UUID: {response_uuid}"
    
    # Verify MongoDB insert_one was called 3 times
    assert mock_mongo_collection.insert_one.call_count == 3


def test_file_content_integrity(temp_bills_dir, mock_mongo_collection):
    """
    Test that different file contents are saved correctly.
    """
    # Create two different file contents
    content1 = b"PDF content for bill 1"
    content2 = b"PDF content for bill 2"
    
    # Save both files
    response1 = save_uploaded_bill(content1, temp_bills_dir)
    response2 = save_uploaded_bill(content2, temp_bills_dir)
    
    # Verify each file has the correct content
    file1_path = temp_bills_dir / f"{response1['id']}.pdf"
    file2_path = temp_bills_dir / f"{response2['id']}.pdf"
    
    with open(file1_path, "rb") as f:
        assert f.read() == content1
    
    with open(file2_path, "rb") as f:
        assert f.read() == content2

