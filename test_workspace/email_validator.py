"""Pragmatic email validation helper.

This module provides a fast, practical validator for typical email
addresses. It avoids full RFC 5322 complexity while enforcing
commonly accepted constraints:

- Local part up to 64 chars, no leading/trailing dots, no consecutive dots
- Allowed local characters: letters, digits, and !#$%&'*+/=?^_`{|}~.-
- Domain uses label rules (letters/digits, internal hyphens), at least one dot
- TLD-style ending enforced by requiring at least one dot in domain
- Overall length up to 254 chars

Usage
-----
- Library: `is_valid_email("user@example.com") -> bool`
- CLI: `python email_validator.py user@example.com` (returns exit code 0 if all valid)
"""

from __future__ import annotations

import argparse
import re
from typing import Iterable

# Local part: atoms separated by single dots; no leading/trailing dot
# Domain: labels 1-63 chars, alnum with internal hyphens, at least one dot
EMAIL_REGEX = re.compile(
    r"^"
    # Local part
    r"(?!\.)"  # no leading dot
    r"(?:[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*)"
    r"@"
    # Domain part
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,}"  # final TLD-like label
    r"$",
)


def is_valid_email(email: str) -> bool:
    """Return True if `email` looks like a valid email address.

    This is a pragmatic check suited for most apps. For stricter needs,
    consider deliverability checks (e.g., MX lookup) separately.
    """

    if not isinstance(email, str):
        return False

    if not email or len(email) > 254:
        return False

    m = EMAIL_REGEX.fullmatch(email)
    if not m:
        return False

    local, _, domain = email.rpartition("@")

    # Enforce local part length
    if len(local) > 64:
        return False

    # Disallow consecutive dots in local part (already prevented by regex, but explicit)
    if ".." in local:
        return False

    # Enforce each domain label length <= 63
    labels = domain.split(".")
    if any(len(label) == 0 or len(label) > 63 for label in labels):
        return False

    return True


def _cli(emails: Iterable[str]) -> int:
    """Validate provided emails; print results; return exit status.

    Exit code: 0 if all valid, 1 otherwise.
    """

    all_valid = True
    for e in emails:
        valid = is_valid_email(e)
        all_valid = all_valid and valid
        print(f"{e}: {'valid' if valid else 'invalid'}")
    return 0 if all_valid else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate email addresses")
    parser.add_argument(
        "emails",
        nargs="+",
        help="One or more email addresses to validate",
    )
    args = parser.parse_args()
    return _cli(args.emails)


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["is_valid_email"]

