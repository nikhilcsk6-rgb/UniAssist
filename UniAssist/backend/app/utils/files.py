"""File upload validation: extension, size, magic bytes, safe naming."""
import uuid
from werkzeug.utils import secure_filename

ALLOWED = {"pdf", "docx", "txt"}


def validate_upload(file_storage, max_bytes):
    """Return (ext, safe_original_name, data_bytes) or raise ValueError."""
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided.")
    name = secure_filename(file_storage.filename)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED:
        raise ValueError("Only PDF, DOCX and TXT files are allowed.")
    data = file_storage.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("File exceeds the maximum upload size.")
    if not data:
        raise ValueError("File is empty.")
    # Magic-byte check: the content must match the claimed extension.
    if ext == "pdf" and not data.startswith(b"%PDF"):
        raise ValueError("File content is not a valid PDF.")
    if ext == "docx" and not data.startswith(b"PK\x03\x04"):
        raise ValueError("File content is not a valid DOCX.")
    if ext == "txt":
        if b"\x00" in data:
            raise ValueError("File content is not plain text.")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("TXT files must be UTF-8 encoded.")
    return ext, name, data


def new_stored_name(ext):
    return f"{uuid.uuid4().hex}.{ext}"
