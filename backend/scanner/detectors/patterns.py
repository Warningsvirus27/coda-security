"""
SecureCoda — Sensitive Data Regex Patterns

Defines regex patterns for detecting various types of sensitive information
in table cell values and page content. Each pattern has a name, regex,
severity level, and description.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SensitivePattern:
    """Defines a sensitive data detection pattern."""
    name: str
    regex: re.Pattern
    severity: str  # critical, high, medium, low
    description: str
    category: str  # pii, credential, financial, network


# --------------------------------------------------------------------------
# Pattern Definitions
# --------------------------------------------------------------------------

PATTERNS = [
    # ── Credentials (Critical / High) ──────────────────────────────────
    SensitivePattern(
        name='password_field',
        regex=re.compile(
            r'(?i)\b(?:password|passwd|pwd|pass_?word|secret_?key)\s*[:=]\s*\S+',
            re.IGNORECASE,
        ),
        severity='critical',
        description='Password or secret key in plain text',
        category='credential',
    ),
    SensitivePattern(
        name='api_key',
        regex=re.compile(
            r'(?i)\b(?:api[_\-]?key|api[_\-]?secret|access[_\-]?token|auth[_\-]?token|bearer)\s*[:=]\s*[A-Za-z0-9_\-\.]{20,}',
            re.IGNORECASE,
        ),
        severity='high',
        description='API key or authentication token',
        category='credential',
    ),
    SensitivePattern(
        name='aws_key',
        regex=re.compile(r'(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}'),
        severity='critical',
        description='AWS Access Key ID',
        category='credential',
    ),
    SensitivePattern(
        name='private_key',
        regex=re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'),
        severity='critical',
        description='Private key block detected',
        category='credential',
    ),
    SensitivePattern(
        name='generic_secret',
        regex=re.compile(
            r'(?i)\b(?:sk[_\-]live|sk[_\-]test|rk[_\-]live|rk[_\-]test)[_\-]?[A-Za-z0-9]{20,}',
        ),
        severity='high',
        description='Stripe or service secret key',
        category='credential',
    ),

    # ── PII — Personal Identifiers (Medium) ───────────────────────────
    SensitivePattern(
        name='email_address',
        regex=re.compile(
            r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
        ),
        severity='medium',
        description='Email address detected',
        category='pii',
    ),
    SensitivePattern(
        name='phone_us',
        regex=re.compile(
            r'\b(?:\+1[\-.\s]?)?\(?\d{3}\)?[\-.\s]?\d{3}[\-.\s]?\d{4}\b'
        ),
        severity='medium',
        description='US phone number detected',
        category='pii',
    ),
    SensitivePattern(
        name='ssn',
        regex=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        severity='critical',
        description='Social Security Number (SSN) detected',
        category='pii',
    ),

    # ── Financial (Critical) ──────────────────────────────────────────
    SensitivePattern(
        name='credit_card',
        regex=re.compile(
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?'        # Visa
            r'|5[1-5][0-9]{14}'                      # MasterCard
            r'|3[47][0-9]{13}'                       # American Express
            r'|3(?:0[0-5]|[68][0-9])[0-9]{11}'      # Diners Club
            r'|6(?:011|5[0-9]{2})[0-9]{12}'          # Discover
            r'|(?:2131|1800|35\d{3})\d{11})\b'       # JCB
        ),
        severity='critical',
        description='Credit card number detected',
        category='financial',
    ),
    SensitivePattern(
        name='credit_card_formatted',
        regex=re.compile(
            r'\b\d{4}[\-\s]\d{4}[\-\s]\d{4}[\-\s]\d{4}\b'
        ),
        severity='critical',
        description='Formatted credit card number detected',
        category='financial',
    ),

    # ── Network (Low) ────────────────────────────────────────────────
    SensitivePattern(
        name='ipv4_address',
        regex=re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ),
        severity='low',
        description='IPv4 address detected',
        category='network',
    ),
]

# Column name patterns that suggest sensitive data
SENSITIVE_COLUMN_PATTERNS = re.compile(
    r'(?i)\b(?:password|passwd|pwd|secret|token|api[_\-]?key|ssn|'
    r'social[_\-]?security|credit[_\-]?card|card[_\-]?number|cvv|'
    r'private[_\-]?key|access[_\-]?key)\b'
)


def scan_text(text: str) -> list[dict]:
    """
    Scan a string for all sensitive data patterns.

    Returns:
        List of dicts with keys: pattern_name, severity, description, category, match
        The 'match' value is masked (first 4 chars shown, rest replaced with ***).
    """
    if not text or not isinstance(text, str):
        return []

    findings = []
    for pattern in PATTERNS:
        matches = pattern.regex.findall(text)
        for match in matches:
            # Mask the match for safe storage (never store raw sensitive data)
            masked = mask_value(match)
            findings.append({
                'pattern_name': pattern.name,
                'severity': pattern.severity,
                'description': pattern.description,
                'category': pattern.category,
                'masked_value': masked,
            })

    return findings


def mask_value(value: str, visible_chars: int = 4) -> str:
    """Mask a sensitive value, showing only the first few characters."""
    if len(value) <= visible_chars:
        return '***'
    return value[:visible_chars] + '***' + value[-2:] if len(value) > 6 else value[:visible_chars] + '***'


def is_sensitive_column(column_name: str) -> bool:
    """Check if a column name suggests it contains sensitive data."""
    return bool(SENSITIVE_COLUMN_PATTERNS.search(column_name))
