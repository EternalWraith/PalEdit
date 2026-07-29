from typing import Any, Optional, Sequence

from loguru import logger
from palworld_save_tools.archive import (
    FArchiveReader,
    FArchiveWriter,
    coerce_bytes,
    without_custom_type,
)


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    data_bytes = value["value"]["values"]
    value["value"] = decode_bytes(reader, data_bytes)
    return value


def decode_bytes(
    parent_reader: FArchiveReader, c_bytes: Sequence[int]
) -> Optional[dict[str, Any]]:
    if len(c_bytes) == 0:
        return None
    buf = coerce_bytes(c_bytes)
    reader = parent_reader.internal_copy(buf, debug=False)
    data: dict[str, Any] = {}
    data["type"] = "unknown"
    data["id"] = {
        "created_world_id": reader.guid(),
        "local_id_in_created_world": reader.guid(),
        "static_id": reader.fstring(),
    }
    egg_data = try_read_egg(reader)
    if isinstance(egg_data, dict):
        data |= egg_data
    elif (reader.size - reader.data.tell()) == 12:
        data["type"] = "armor"
        data["leading_bytes"] = reader.byte_list(4)
        data["durability"] = reader.float()
        data["trailing_bytes"] = reader.byte_list(4)
        if not reader.eof():
            raise Exception("Warning: EOF not reached")
    else:
        cur_pos = reader.data.tell()
        temp_data: dict[str, Any] = {"type": "weapon"}
        try:
            temp_data["leading_bytes"] = reader.byte_list(4)
            temp_data["durability"] = reader.float()
            temp_data["remaining_bullets"] = reader.i32()
            temp_data["passive_skill_list"] = reader.tarray(lambda r: r.fstring())
            if (reader.size - reader.data.tell()) > 4:
                temp_data["unknown_str"] = reader.fstring()
            temp_data["trailing_bytes"] = reader.byte_list(4)
            if not reader.eof():
                raise Exception("Warning: EOF not reached")
            data |= temp_data
        except Exception as e:
            logger.debug(
                f"Failed to parse weapon data, continuing as raw data {buf!r}: {e}"
            )
            reader.data.seek(cur_pos)
            data["trailer"] = reader.read_to_end()
    return data


def try_read_egg(reader: FArchiveReader) -> Optional[dict[str, Any]]:
    cur_pos = reader.data.tell()
    try:
        data: dict[str, Any] = {"type": "egg"}
        data["leading_bytes"] = reader.byte_list(4)
        data["character_id"] = reader.fstring()
        data["object"] = reader.properties_until_end()
        data["trailing_bytes"] = reader.byte_list(28)
        if not reader.eof():
            raise Exception("Warning: EOF not reached")
        return data
    except Exception as e:
        if e.args[0] == "Warning: EOF not reached":
            raise e
        reader.data.seek(cur_pos)
        return None


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type != "ArrayProperty":
        raise Exception(f"Expected ArrayProperty, got {property_type}")
    prop_value = properties.get("value")
    if isinstance(prop_value, dict):
        encoded_bytes = encode_bytes(prop_value)
    else:
        # If value is not a dict, it might be None or raw bytes; return as-is
        encoded_bytes = encode_bytes(None)
    properties = without_custom_type(properties)
    properties["value"] = {"values": encoded_bytes}
    return writer.property_inner(property_type, properties)


def encode_bytes(p: dict[str, Any]) -> bytes:
    if p is None:
        return bytes()
    if not isinstance(p, dict):
        logger.warning(f"encode_bytes received non-dict: {type(p)}, returning empty bytes")
        return bytes()

    writer = FArchiveWriter()
    writer.guid(p.get("id", {}).get("created_world_id"))
    writer.guid(p.get("id", {}).get("local_id_in_created_world"))
    writer.fstring(p.get("id", {}).get("static_id", ""))

    item_type = p.get("type", "unknown")
    if item_type == "unknown":
        writer.write(coerce_bytes(p.get("trailer", b"")))
    elif item_type == "egg":
        writer.write(coerce_bytes(p.get("leading_bytes", b"\x00" * 4)))
        writer.fstring(p.get("character_id", ""))
        writer.properties(p.get("object", {}))
        writer.write(coerce_bytes(p.get("trailing_bytes", b"\x00" * 28)))
    elif item_type == "armor":
        writer.write(coerce_bytes(p.get("leading_bytes", b"\x00" * 4)))
        writer.float(p.get("durability", 100.0))
        writer.write(coerce_bytes(p.get("trailing_bytes", b"\x00" * 4)))
    elif item_type == "weapon":
        writer.write(coerce_bytes(p.get("leading_bytes", b"\x00" * 4)))
        writer.float(p.get("durability", 100.0))
        writer.i32(p.get("remaining_bullets", 0))
        writer.tarray(lambda w, d: (w.fstring(d), None)[1], p.get("passive_skill_list", []))
        if "unknown_str" in p:
            writer.fstring(p["unknown_str"])
        writer.write(coerce_bytes(p.get("trailing_bytes", b"\x00" * 4)))
    else:
        logger.warning(f"Unknown item type: {item_type}, treating as unknown")
        writer.write(coerce_bytes(p.get("trailer", b"")))

    encoded_bytes = writer.bytes()
    return encoded_bytes
