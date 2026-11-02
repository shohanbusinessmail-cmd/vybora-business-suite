"""Centralized error types with natural Bengali user-facing messages.

Internal details are logged (redacted); users never see stack traces.
"""

from __future__ import annotations


class VyboraError(Exception):
    """Base error with a Bengali message and a stable machine code."""

    code = "error"

    def __init__(self, message_bn: str, *, detail: str | None = None):
        super().__init__(message_bn)
        self.message_bn = message_bn
        self.detail = detail


class ValidationError(VyboraError):
    code = "validation"

    def __init__(self, message_bn: str, *, field: str | None = None):
        super().__init__(message_bn)
        self.field = field


class PermissionDeniedError(VyboraError):
    code = "permission"

    def __init__(self, message_bn: str = "এই কাজটি করার অনুমতি আপনার নেই।"):
        super().__init__(message_bn)


class NotFoundError(VyboraError):
    code = "not_found"


class ConflictError(VyboraError):
    code = "conflict"


class LicenseError(VyboraError):
    code = "license"


class DatabaseError(VyboraError):
    code = "database"


class BackupError(VyboraError):
    code = "backup"


def friendly_db_message(exc: Exception) -> str:
    """Map low-level DB/storage errors to understandable Bengali messages."""
    text = str(exc).lower()
    if "locked" in text or "busy" in text:
        return "ডেটাবেস এখন ব্যস্ত। অনুগ্রহ করে কিছুক্ষণ পর আবার চেষ্টা করুন।"
    if "disk i/o" in text or "no space" in text or "full" in text:
        return "ডিস্কে সমস্যা বা পর্যাপ্ত জায়গা নেই। অনুগ্রহ করে ডিস্ক পরীক্ষা করুন।"
    if "corrupt" in text or "malformed" in text:
        return "ডেটাবেস ফাইল ক্ষতিগ্রস্ত মনে হচ্ছে। অনুগ্রহ করে ব্যাকআপ থেকে পুনরুদ্ধার করুন।"
    if "foreign key" in text:
        return "সম্পর্কিত তথ্য পাওয়া যায়নি। অনুগ্রহ করে সংশ্লিষ্ট রেকর্ড পরীক্ষা করুন।"
    if "unique" in text or "duplicate" in text:
        return "এই তথ্য ইতিমধ্যে রয়েছে। অনুগ্রহ করে ভিন্ন মান ব্যবহার করুন।"
    return "ডেটাবেস সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।"
