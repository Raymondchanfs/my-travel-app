import json
import uuid


def uid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def json_text(v):
    return json.dumps(v, ensure_ascii=False)
