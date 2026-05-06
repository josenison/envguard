"""Generate a .env.example template from a schema definition."""

from dataclasses import dataclass, field
from typing import List, Optional
from envguard.schema import Schema, FieldRule


@dataclass
class TemplateResult:
    lines: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return "\n".join(self.lines)

    def write(self, path: str) -> None:
        """Write the rendered template to a file."""
        with open(path, "w") as fh:
            fh.write(str(self))
            if not str(self).endswith("\n"):
                fh.write("\n")


def _placeholder(rule: FieldRule) -> str:
    """Return a sensible placeholder value for a field."""
    if rule.default is not None:
        return str(rule.default)
    type_placeholders = {
        "str": "your_value_here",
        "int": "0",
        "float": "0.0",
        "bool": "false",
    }
    return type_placeholders.get(rule.type, "your_value_here")


def generate_template(
    schema: Schema,
    include_descriptions: bool = True,
    mark_optional: bool = True,
) -> TemplateResult:
    """Generate a .env.example template from a Schema.

    Args:
        schema: The schema to generate from.
        include_descriptions: If True, emit description comments above each key.
        mark_optional: If True, annotate optional fields with a comment.

    Returns:
        A TemplateResult whose str() is the rendered template text.
    """
    result = TemplateResult()

    for name, rule in schema.fields.items():
        if include_descriptions and rule.description:
            result.lines.append(f"# {rule.description}")

        annotations: List[str] = []
        if not rule.required:
            if mark_optional:
                annotations.append("optional")
            if rule.default is not None:
                annotations.append(f"default: {rule.default}")
        if rule.type and rule.type != "str":
            annotations.append(f"type: {rule.type}")

        if annotations:
            result.lines.append(f"# [{', '.join(annotations)}]")

        placeholder = _placeholder(rule)
        result.lines.append(f"{name}={placeholder}")
        result.lines.append("")  # blank line between fields

    # Remove trailing blank line
    while result.lines and result.lines[-1] == "":
        result.lines.pop()

    return result
