"""Structured, redacted logging. Never logs passwords, keys or SQL values."""

from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

_REDACT_PATTERNS = [
    re.compile(r"(password|passwd|passphrase|secret|token|api[_-]?key)\s*[=:]\s*\S+", re.I),
    re.compile(r"(-----BEGIN [A-Z ]*PRIVATE KEY-----).*?(-----END [A-Z ]*PRIVATE KEY-----)", re.S),
    re.compile(r"\b[0-9a-fA-F]{64}\b"),  # long hex (fingerprints/signatures/hashes)
]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pat in _REDACT_PATTERNS:
            msg = pat.sub("[REDACTED]", msg)
        record.msg = msg
        record.args = ()
        return True


def setup_logging(log_dir: Path, level: int = logging.INFO) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("vybora")
    logger.setLevel(level)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    fh = RotatingFileHandler(
        log_dir / "vybora.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    fh.addFilter(RedactingFilter())
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    sh.addFilter(RedactingFilter())
    logger.addHandler(sh)
    logger.propagate = False
    return logger
