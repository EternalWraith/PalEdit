import base64
import json
import math
import uuid

import orjson

from palworld_save_tools.archive import UUID


def _bytes_to_str(obj: bytes) -> str:
    """Encode a raw byte blob as base64 ASCII string for JSON."""
    return base64.b64encode(obj).decode("ascii")


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (bytes, bytearray)):
            return _bytes_to_str(bytes(obj))
        return super(CustomEncoder, self).default(obj)


def _orjson_default(obj):
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, (bytes, bytearray)):
        return _bytes_to_str(bytes(obj))
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _sanitize_nonfinite(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_nonfinite(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_nonfinite(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_sanitize_nonfinite(v) for v in obj)
    return obj


def dump(data, path, minify=False, allow_nan=True):
    if not allow_nan:
        data = _sanitize_nonfinite(data)
    option = orjson.OPT_NON_STR_KEYS
    if not minify:
        option |= orjson.OPT_INDENT_2
    buf = orjson.dumps(data, default=_orjson_default, option=option)
    with open(path, "wb") as f:
        f.write(buf)


def load(path):
    with open(path, "rb") as f:
        return orjson.loads(f.read())