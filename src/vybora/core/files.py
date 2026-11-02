"""Safe file operations: path validation, traversal protection, safe copies."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from vybora.core.errors import ValidationError


def safe_attachment_copy(
    source: str | Path, dest_dir: Path, *, max_bytes: int = 20_000_000
) -> Path:
    """Copy a user-selected file into dest_dir under a generated name.

    Prevents path traversal (only the file's bytes are copied, never its path),
    enforces a size limit, and never preserves executable names.
    """
    src = Path(source)
    if not src.is_file():
        raise ValidationError("ফাইলটি পাওয়া যায়নি।")
    if src.stat().st_size > max_bytes:
        raise ValidationError("ফাইলটি খুব বড় (সর্বোচ্চ ২০ মেগাবাইট)।")
    suffix = src.suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".pdf", ".webp"}:
        raise ValidationError("শুধুমাত্র JPG, PNG, PDF বা WebP ফাইল অনুমোদিত।")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{uuid.uuid4().hex}{suffix}"
    shutil.copyfile(src, dest)
    return dest


def ensure_within(path: Path, parent: Path) -> Path:
    """Resolve and ensure path stays within parent (traversal guard)."""
    rp = path.resolve()
    rparent = parent.resolve()
    if rparent != rp and rparent not in rp.parents:
        raise ValidationError("অননুমোদিত ফাইল পাথ।")
    return rp
