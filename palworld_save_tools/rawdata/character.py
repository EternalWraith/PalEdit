from typing import Any, Sequence

from palworld_save_tools.archive import *


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    char_bytes = value["value"]["values"]
    value["value"] = decode_bytes(reader, char_bytes)
    return value


def decode_bytes(
    parent_reader: FArchiveReader, char_bytes: Sequence[int]
) -> dict[str, Any]:
    reader = parent_reader.internal_copy(coerce_bytes(char_bytes), debug=False)

    char_data = {
        "object": reader.properties_until_end(),
        "unknown_bytes": reader.byte_list(4),
    }

    remaining = reader.size - reader.data.tell()

    # Legacy format
    if remaining == 20:
        char_data["group_id"] = reader.guid()
        char_data["trailing_bytes"] = reader.byte_list(4)

    # Compatibility shim
    else:
        # Preserve the existing JSON due to 12 byte shift
        # Can read this GUID because incorrect bytes left
        # Preserve every byte so nothing is lost on loop write
        char_data["group_id"] = ""
        char_data["trailing_bytes"] = reader.byte_list(remaining)

    if not reader.eof():
        raise Exception("Warning: EOF not reached")

    return char_data


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {property_type}")

    encoded_bytes = encode_bytes(properties["value"])
    properties = without_custom_type(properties)
    properties["value"] = {"values": encoded_bytes}

    return writer.property_inner(property_type, properties)


def encode_bytes(p: dict[str, Any]) -> bytes:
    writer = FArchiveWriter()

    writer.properties(p["object"])
    writer.write(coerce_bytes(p["unknown_bytes"]))

    # Only emit the GUID if we actually have one
    if p.get("group_id"):
        writer.guid(p["group_id"])

    # Always write back the preserved bytes
    writer.write(coerce_bytes(p["trailing_bytes"]))

    return writer.bytes()
