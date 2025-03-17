import base64
import pytest
from app.utils.barcode_utils import generate_barcode_base64

def test_generate_barcode_base64():
    code_value = "MEMBER-1"  # Example code for a member (or you can use a book copy code)
    barcode_str = generate_barcode_base64(code_value)
    
    # Ensure we get a non-empty string
    assert barcode_str, "The generated barcode string is empty."
    
    # Check that the returned string is valid base64 by attempting to decode it
    try:
        decoded_data = base64.b64decode(barcode_str)
    except Exception as e:
        pytest.fail(f"Barcode string is not valid base64: {e}")
    
    # Optionally, verify that the decoded data appears to be a PNG image.
    # PNG files start with an 8-byte signature: 89 50 4E 47 0D 0A 1A 0A
    png_signature = b'\x89PNG\r\n\x1a\n'
    assert decoded_data.startswith(png_signature), "Decoded barcode image does not have a valid PNG signature."
