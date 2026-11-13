"""Document storage — Cloudflare R2 design (starter: local metadata only).

Production design (see docs/architecture.md):
- Files are stored in Cloudflare R2 (S3-compatible) under
  ``shipments/<shipment_id>/<evidence_id>-<filename>``.
- Only the storage key, filename, content type, size, and checksum
  are stored in PostgreSQL (``evidence.storage_key``). No file bytes
  live in the database.
- Credentials come ONLY from environment variables
  (``R2_ENDPOINT``, ``R2_ACCESS_KEY_ID``, ``R2_SECRET_ACCESS_KEY``,
  ``R2_BUCKET``). No real credentials are in this repo — ever.

Starter behaviour: ``store_file()`` validates the upload, computes a
storage key and a SHA-256 checksum, and returns the metadata WITHOUT
uploading anywhere (``backend="local-stub"``). Wire the boto3 / S3
client in ``_upload_to_r2()`` when R2 is configured; the metadata
shape callers receive does not change.
"""
import hashlib
import os
from dataclasses import dataclass

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
}
MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB


@dataclass
class StoredFile:
    storage_key: str
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    backend: str = "local-stub"  # "r2" once _upload_to_r2() is wired up


def _upload_to_r2(key: str, data: bytes, content_type: str) -> None:
    """Production upload — NOT wired up in the starter.

    Implement with boto3 against R2_ENDPOINT using the R2_* env vars.
    Raising here (instead of silently pretending) is deliberate: a
    file must never be reported as stored in R2 when it was not.
    """
    raise NotImplementedError(
        "R2 upload is not configured. Set R2_ENDPOINT / R2_ACCESS_KEY_ID / "
        "R2_SECRET_ACCESS_KEY / R2_BUCKET and implement _upload_to_r2() "
        "with an S3-compatible client."
    )


def store_file(shipment_id: str, evidence_id: str, filename: str,
               content_type: str, data: bytes) -> StoredFile:
    """Validate and record a file upload. Returns metadata only."""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported file type: {content_type}. "
                         f"Allowed: PDF, JPEG, PNG, WebP, plain text.")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"File too large: {len(data)} bytes (max {MAX_FILE_BYTES}).")
    if not filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename.")
    safe_name = filename.replace(" ", "_")
    key = f"shipments/{shipment_id}/{evidence_id}-{safe_name}"
    checksum = hashlib.sha256(data).hexdigest()
    if os.environ.get("R2_BUCKET"):
        _upload_to_r2(key, data, content_type)
        backend = "r2"
    else:
        backend = "local-stub"
    return StoredFile(storage_key=key, filename=filename, content_type=content_type,
                      size_bytes=len(data), sha256=checksum, backend=backend)
