import io
import base64
import barcode
from barcode.writer import ImageWriter

def generate_barcode_base64(code_value):
    """
    Generates a barcode image for the given code_value and returns it as a base64 string.
    """
    # Using Code128 as the barcode format.
    CODE128 = barcode.get_barcode_class('code128')
    rv = io.BytesIO()
    barcode_obj = CODE128(code_value, writer=ImageWriter())
    barcode_obj.write(rv)
    base64_str = base64.b64encode(rv.getvalue()).decode('utf-8')
    return base64_str
