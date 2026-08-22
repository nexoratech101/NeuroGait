"""Raw sensor file storage. Uploaded files are never modified after being written --
they are hashed and kept forever addressable, separately from any processed output
(spec section 0.3)."""
import hashlib
import uuid
from pathlib import Path

from app.config import RAW_DATA_DIR


def save_raw_file(session_id: str, filename: str, content: bytes) -> tuple[str, str]:
    session_dir = RAW_DATA_DIR / str(session_id)
    session_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:8]}_{Path(filename).name}"
    dest = session_dir / safe_name
    dest.write_bytes(content)

    file_hash = hashlib.sha256(content).hexdigest()
    return str(dest), file_hash
