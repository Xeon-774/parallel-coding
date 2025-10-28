"""Email address validation utility.

This module exposes a single function, `validate_email`, which performs a
pragmatic, regex-based validation of email addresses. It aims to cover the
majority of real-world use cases while avoiding the extreme complexity of the
full RFC 5322 grammar.

Note: This checks only the syntactic form of an address; it does not verify
that the domain exists or that the mailbox can receive mail.
"""

from __future__ import annotations

import re
from typing import Final

# A pragmatic email regex:
# - Local part: one or more dot-separated atoms of allowed characters
# - Domain: one or more labels separated by dots, labels may contain hyphens
# - TLD: letters only, at least 2 characters
_EMAIL_PATTERN: Final[str] = (
    r"(?:[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*)"
    r"@"
    r"(?:(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)\.)+"
    r"(?:[A-Za-z]{2,})"
)

_EMAIL_REGEX: Final[re.Pattern[str]] = re.compile(_EMAIL_PATTERN, re.IGNORECASE)


def validate_email(email: str) -> bool:
    """Return True if the given string is a syntactically valid email.

    This function uses a carefully chosen, pragmatic regular expression that
    accepts common, standards-compliant addresses while rejecting obvious
    mistakes such as consecutive dots in the local part, invalid domain label
    characters, or a missing top-level domain.

    The validation is case-insensitive and checks only syntax — it does not
    ensure that the address can actually receive email.

    Args:
        email: The email address to validate.

    Returns:
        True if the email address is syntactically valid, False otherwise.

    Examples:
        >>> validate_email('alice@example.com')
        True
        >>> validate_email('ALICE+news@sub.example.co.uk')
        True
        >>> validate_email('a..b@example.com')  # consecutive dots invalid
        False
        >>> validate_email('.alice@example.com')  # starts with dot invalid
        False
        >>> validate_email('alice@-example.com')  # label cannot start with hyphen
        False
        >>> validate_email('alice@example')  # missing TLD
        False
        >>> validate_email('invalid@exa_mple.com')  # underscore not allowed in domain
        False
        >>> validate_email('not an email')
        False
    """
    if not isinstance(email, str):
        return False

    # Optional length sanity check (typical practical limits: 64 + 1 + 255)
    if len(email) > 320:
        return False

    return _EMAIL_REGEX.fullmatch(email) is not None

