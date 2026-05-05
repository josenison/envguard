"""Schema definition and parsing for .env validation rules."""

from dataclasses import dataclass, field
from typing import Optional
import json
import re


@dataclass
class FieldRule:
    name: str
    required: bool = True
    type: str = "string"  # string | integer | boolean | url | email
    pattern: Optional[str] = None
    default: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self):
        valid_types = {"string", "integer", "boolean", "url", "email"}
        if self.type not in valid_types:
            raise ValueError(f"Invalid type '{self.type}' for field '{self.name}'. Must be one of {valid_types}")


@dataclass
class Schema:
    fields: list[FieldRule] = field(default_factory=list)

    def get_field(self, name: str) -> Optional[FieldRule]:
        for f in self.fields:
            if f.name == name:
                return f
        return None


def load_schema(path: str) -> Schema:
    """Load a schema from a JSON file."""
    with open(path, "r") as fh:
        raw = json.load(fh)

    if not isinstance(raw, dict) or "fields" not in raw:
        raise ValueError("Schema file must be a JSON object with a 'fields' key")

    rules = []
    for entry in raw["fields"]:
        if "name" not in entry:
            raise ValueError(f"Each field entry must have a 'name' key: {entry}")
        rules.append(
            FieldRule(
                name=entry["name"],
                required=entry.get("required", True),
                type=entry.get("type", "string"),
                pattern=entry.get("pattern"),
                default=entry.get("default"),
                description=entry.get("description"),
            )
        )

    return Schema(fields=rules)
