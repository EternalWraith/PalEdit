import json
from typing import Any, Sequence

from palworld_save_tools.archive import *
from palworld_save_tools.json_tools import CustomEncoder

# EPalMapObjectConcreteModelModuleType::None = 0,
# EPalMapObjectConcreteModelModuleType::ItemContainer = 1,
# EPalMapObjectConcreteModelModuleType::CharacterContainer = 2,
# EPalMapObjectConcreteModelModuleType::Workee = 3,
# EPalMapObjectConcreteModelModuleType::Energy = 4,
# EPalMapObjectConcreteModelModuleType::StatusObserver = 5,
# EPalMapObjectConcreteModelModuleType::ItemStack = 6,
# EPalMapObjectConcreteModelModuleType::Switch = 7,
# EPalMapObjectConcreteModelModuleType::PlayerRecord = 8,
# EPalMapObjectConcreteModelModuleType::BaseCampPassiveEffect = 9,
# EPalMapObjectConcreteModelModuleType::PasswordLock = 10,


def module_slot_indexes_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "attribute": reader.byte(),
        "indexes": reader.tarray(lambda r: r.i32()),
    }


def player_lock_info_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "player_uid": reader.guid(),
        "try_failed_count": reader.i32(),
        "try_success_cache": reader.u32(),
    }


def color_setting_entry_reader(reader: FArchiveReader) -> dict[str, Any]:
    # FPalColorSettingEntry: FName Key + FLinearColor Color.
    return {
        "key": reader.fstring(),
        "color": {
            "r": reader.float(),
            "g": reader.float(),
            "b": reader.float(),
            "a": reader.float(),
        },
    }


def decode_bytes(
    parent_reader: FArchiveReader, m_bytes: Sequence[int], module_type: str
) -> Optional[dict[str, Any]]:
    if len(m_bytes) == 0:
        return {"values": []}
    reader = parent_reader.internal_copy(coerce_bytes(m_bytes), debug=False)
    data: dict[str, Any] = {}

    match module_type:
        case "EPalMapObjectConcreteModelModuleType::ItemContainer":
            data["target_container_id"] = reader.guid()
            data["slot_attribute_indexes"] = reader.tarray(module_slot_indexes_reader)
            data["all_slot_attribute"] = reader.tarray(lambda r: r.byte())
            data["drop_item_at_disposed"] = reader.u32()
            data["usage_type"] = reader.byte()
            data["trailing_bytes"] = reader.byte_list(4)
        case "EPalMapObjectConcreteModelModuleType::CharacterContainer":
            data["target_container_id"] = reader.guid()
            data["trailing_bytes"] = reader.byte_list(4)
        case "EPalMapObjectConcreteModelModuleType::Workee":
            data["target_work_id"] = reader.guid()
            data["trailing_bytes"] = reader.byte_list(4)
        case "EPalMapObjectConcreteModelModuleType::Energy":
            pass
        case "EPalMapObjectConcreteModelModuleType::StatusObserver":
            pass
        case "EPalMapObjectConcreteModelModuleType::ItemStack":
            pass
        case "EPalMapObjectConcreteModelModuleType::Switch":
            data["switch_state"] = reader.byte()
            data["trailing_bytes"] = reader.byte_list(4)
        case "EPalMapObjectConcreteModelModuleType::PlayerRecord":
            pass
        case "EPalMapObjectConcreteModelModuleType::BaseCampPassiveEffect":
            pass
        case "EPalMapObjectConcreteModelModuleType::PasswordLock":
            data["lock_state"] = reader.byte()
            data["password"] = reader.fstring()
            data["player_infos"] = reader.tarray(player_lock_info_reader)
            data["trailing_bytes"] = reader.byte_list(4)
        case "EPalMapObjectConcreteModelModuleType::RequireElementalAction":
            data["unlock_item"] = reader.fstring()
            data["trailing_bytes"] = reader.byte_list(12)
        case "EPalMapObjectConcreteModelModuleType::GuildSecurity":
            data["allowed_roles"] = reader.tarray(lambda r: r.byte())
            data["trailing_bytes"] = reader.byte_list(4)
        case "EPalMapObjectConcreteModelModuleType::ColorSetting":
            data["color_entries"] = reader.tarray(color_setting_entry_reader)
            data["trailing_bytes"] = reader.byte_list(4)
        case "EPalMapObjectConcreteModelModuleType::OperationalLoad":
            data["current_load"] = reader.float()
            data["trailing_bytes"] = reader.byte_list(8)
    if not reader.eof():
        raise Exception(f"Warning: EOF not reached for module type {module_type}")
    return data


def module_slot_indexes_writer(writer: FArchiveWriter, value: dict[str, Any]) -> None:
    writer.byte(value["attribute"])
    writer.tarray(lambda w, v: w.i32(v), value["indexes"])


def player_lock_info_writer(writer: FArchiveWriter, value: dict[str, Any]) -> None:
    writer.guid(value["player_uid"])
    writer.i32(value["try_failed_count"])
    writer.u32(int(value["try_success_cache"]))


def color_setting_entry_writer(writer: FArchiveWriter, value: dict[str, Any]) -> None:
    writer.fstring(value["key"])
    color = value["color"]
    writer.float(color["r"])
    writer.float(color["g"])
    writer.float(color["b"])
    writer.float(color["a"])


def encode_bytes(p: dict[str, Any], module_type: str) -> bytes:
    if p is None:
        return bytes()
    writer = FArchiveWriter()

    match module_type:
        case "EPalMapObjectConcreteModelModuleType::ItemContainer":
            writer.guid(p["target_container_id"])
            writer.tarray(module_slot_indexes_writer, p["slot_attribute_indexes"])
            writer.tarray(lambda w, v: w.byte(v), p["all_slot_attribute"])
            writer.u32(int(p["drop_item_at_disposed"]))
            writer.byte(p["usage_type"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::CharacterContainer":
            writer.guid(p["target_container_id"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::Workee":
            writer.guid(p["target_work_id"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::Switch":
            writer.byte(p["switch_state"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::PasswordLock":
            writer.byte(p["lock_state"])
            writer.fstring(p["password"])
            writer.tarray(player_lock_info_writer, p["player_infos"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::RequireElementalAction":
            writer.fstring(p["unlock_item"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::GuildSecurity":
            writer.tarray(lambda w, v: w.byte(v), p["allowed_roles"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::ColorSetting":
            writer.tarray(color_setting_entry_writer, p["color_entries"])
            writer.write(coerce_bytes(p["trailing_bytes"]))
        case "EPalMapObjectConcreteModelModuleType::OperationalLoad":
            writer.float(p["current_load"])
            writer.write(coerce_bytes(p["trailing_bytes"]))

    encoded_bytes = writer.bytes()
    return encoded_bytes
