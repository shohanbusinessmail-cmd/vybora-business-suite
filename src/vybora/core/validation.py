"""Centralized input validation helpers (Bengali messages)."""

from __future__ import annotations

import re

from vybora.core.errors import ValidationError

_MOBILE_BD = re.compile(r"^(?:\+?88)?01[3-9]\d{8}$")


def require_non_empty(value: str | None, field_bn: str) -> str:
    if value is None or not str(value).strip():
        raise ValidationError(f"{field_bn} আবশ্যক।", field=field_bn)
    return str(value).strip()


def require_positive_int(value: int, field_bn: str, *, allow_zero: bool = False) -> int:
    if not isinstance(value, int) or (value < 0 if allow_zero else value <= 0):
        op = "ঋণাত্মক হতে পারবে না" if allow_zero else "অবশ্যই ধনাত্মক হতে হবে"
        raise ValidationError(f"{field_bn} {op}।", field=field_bn)
    return value


def require_non_negative(value: int, field_bn: str) -> int:
    if not isinstance(value, int) or value < 0:
        raise ValidationError(f"{field_bn} ঋণাত্মক হতে পারবে না।", field=field_bn)
    return value


def validate_mobile_bd(value: str | None, *, required: bool = False) -> str | None:
    if value is None or not str(value).strip():
        if required:
            raise ValidationError("মোবাইল নম্বর আবশ্যক।", field="mobile")
        return None
    v = re.sub(r"[\s-]", "", str(value))
    if not _MOBILE_BD.match(v):
        raise ValidationError("সঠিক বাংলাদেশি মোবাইল নম্বর দিন (যেমন 01XXXXXXXXX)।", field="mobile")
    return v


def validate_email(value: str | None, *, required: bool = False) -> str | None:
    if value is None or not str(value).strip():
        if required:
            raise ValidationError("ইমেইল আবশ্যক।", field="email")
        return None
    v = str(value).strip()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
        raise ValidationError("সঠিক ইমেইল ঠিকানা দিন।", field="email")
    return v


def require_in(value, allowed, field_bn: str):
    if value not in allowed:
        raise ValidationError(f"{field_bn} এর মান অবৈধ।", field=field_bn)
    return value
