# envguard

Lightweight utility to validate and lint `.env` files against a schema definition before deployment.

---

## Installation

```bash
pip install envguard
```

---

## Usage

Define a schema file (`env.schema.json`) describing your expected environment variables:

```json
{
  "DATABASE_URL": { "type": "string", "required": true },
  "PORT": { "type": "integer", "required": false, "default": 8080 },
  "DEBUG": { "type": "boolean", "required": false }
}
```

Then validate your `.env` file against it:

```bash
envguard validate --env .env --schema env.schema.json
```

Or use it programmatically in Python:

```python
from envguard import validate

result = validate(env_file=".env", schema_file="env.schema.json")

if not result.is_valid:
    for error in result.errors:
        print(f"[ERROR] {error}")
```

**Example output:**

```
✔ PORT — ok (default applied)
✘ DATABASE_URL — required variable is missing
✔ DEBUG — ok
```

Exit code `1` is returned when validation fails, making it easy to integrate into CI/CD pipelines.

---

## CI Integration

```yaml
- name: Validate environment
  run: envguard validate --env .env.production --schema env.schema.json
```

---

## License

MIT © [envguard contributors](https://github.com/your-org/envguard)