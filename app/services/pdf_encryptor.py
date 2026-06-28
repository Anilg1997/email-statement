"""PDF encryption service using PyMuPDF for AES-256."""
from io import BytesIO
import fitz  # PyMuPDF


def encrypt_pdf(pdf_data: bytes, user_password: str) -> bytes:
    """Encrypt a PDF with AES-256 using the given password.

    Mimics the Java iText encryption: password = last 4 digits of account number.
    Uses in-memory BytesIO instead of a temp file for security.
    """
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    perm = (
        fitz.PDF_PERM_ACCESSIBILITY
        | fitz.PDF_PERM_PRINT
        | fitz.PDF_PERM_COPY
    )
    buffer = BytesIO()
    doc.save(
        buffer,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw=user_password,
        owner_pw=user_password,
        permissions=perm,
    )
    doc.close()
    return buffer.getvalue()
