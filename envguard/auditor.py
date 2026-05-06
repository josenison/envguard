"""Audit .env files for sensitive key exposure and security best practices."""
from dataclasses import dataclass, field
from typing import List
import re

SENSITIVE_PATTERNS = [
    re.compile(r"(password|passwd|pwd)", re.IGNORECASE),
    re.compile(r"(secret|api_key|apikey|token|auth)", re.IGNORECASE),
    re.compile(r"(private_key|priv_key|credentials)", re.IGNORECASE),
]

WEAK_VALUE_PATTERNS = [
    re.compile(r"^(password|123456|admin|test|changeme|secret)$", re.IGNORECASE),
]


@dataclass
class AuditIssue:
    key: str
    message: str
    severity: str  # "error" | "warning" | "info"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class AuditResult:
    issues: List[AuditIssue] = field(default_factory=list)

    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)

    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    def add(self, issue: AuditIssue) -> None:
        self.issues.append(issue)


def audit_env(env: dict) -> AuditResult:
    """Audit a parsed env dictionary for security issues."""
    result = AuditResult()

    for key, value in env.items():
        is_sensitive = any(p.search(key) for p in SENSITIVE_PATTERNS)

        if is_sensitive:
            if not value or value.strip() == "":
                result.add(AuditIssue(
                    key=key,
                    message="Sensitive key has an empty value.",
                    severity="error",
                ))
            elif any(p.match(value.strip()) for p in WEAK_VALUE_PATTERNS):
                result.add(AuditIssue(
                    key=key,
                    message="Sensitive key appears to have a weak or placeholder value.",
                    severity="warning",
                ))

        if value and len(value) > 0 and value == value.upper() and re.search(r"[a-z]", key):
            result.add(AuditIssue(
                key=key,
                message="Key contains lowercase letters; consider using UPPER_SNAKE_CASE.",
                severity="info",
            ))

    return result
