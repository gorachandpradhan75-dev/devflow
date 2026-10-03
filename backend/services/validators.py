"""Input validation helpers. Each returns (clean_data, errors)."""

ENVIRONMENTS = ("development", "staging", "production")
SERVICE_STATUSES = ("running", "stopped", "failed")
BUILD_STATUSES = ("success", "failed", "running")


def _clean_text(value, max_length):
    return value.strip()[:max_length] if isinstance(value, str) else None


def validate_service(data, partial=False):
    """Validate a service payload. With partial=True only given fields are checked."""
    errors = {}
    clean = {}
    if not isinstance(data, dict):
        return {}, {"body": "JSON object expected"}

    rules = {
        "name": 80,
        "version": 30,
        "environment": None,
        "status": None,
        "description": 255,
    }
    required = ("name", "version", "environment")

    for field, max_length in rules.items():
        if field not in data:
            if field in required and not partial:
                errors[field] = "This field is required"
            continue
        value = data[field]
        if field == "environment":
            value = _clean_text(value, 20)
            if value not in ENVIRONMENTS:
                errors[field] = f"Must be one of: {', '.join(ENVIRONMENTS)}"
                continue
        elif field == "status":
            value = _clean_text(value, 20)
            if value not in SERVICE_STATUSES:
                errors[field] = f"Must be one of: {', '.join(SERVICE_STATUSES)}"
                continue
        else:
            value = _clean_text(value, max_length)
            if value is None or (field in required and not value):
                errors[field] = "Must be a non-empty text value"
                continue
        clean[field] = value
    return clean, errors


def validate_pipeline_run(data):
    errors = {}
    clean = {}
    if not isinstance(data, dict):
        return {}, {"body": "JSON object expected"}

    name = _clean_text(data.get("pipeline_name"), 80)
    if not name:
        errors["pipeline_name"] = "This field is required"
    clean["pipeline_name"] = name

    build_number = data.get("build_number")
    if not isinstance(build_number, int) or isinstance(build_number, bool) or build_number < 1:
        errors["build_number"] = "Must be a positive integer"
    clean["build_number"] = build_number

    status = _clean_text(data.get("status"), 20)
    if status not in BUILD_STATUSES:
        errors["status"] = f"Must be one of: {', '.join(BUILD_STATUSES)}"
    clean["status"] = status

    duration = data.get("duration_seconds", 0)
    if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
        errors["duration_seconds"] = "Must be zero or a positive integer"
    clean["duration_seconds"] = duration

    clean["trigger"] = _clean_text(data.get("trigger", "Manual"), 40) or "Manual"
    return clean, errors
