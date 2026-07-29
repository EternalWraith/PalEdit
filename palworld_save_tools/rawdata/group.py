from typing import Sequence

from palworld_save_tools.archive import *


def player_info_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "player_uid": reader.guid(),
        "player_info": {
            "last_online_real_time": reader.i64(),
            "player_name": reader.fstring(),
        },
    }


def player_info_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    writer.guid(p["player_uid"])
    writer.i64(p["player_info"]["last_online_real_time"])
    writer.fstring(p["player_info"]["player_name"])


def guild_player_info_reader(reader: FArchiveReader) -> dict[str, Any]:
    p = player_info_reader(reader)
    p["role"] = reader.byte()  # EPalGuildRole
    return p


def guild_player_info_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    player_info_writer(writer, p)
    writer.byte(p["role"])


def guild_marker_reader(reader: FArchiveReader) -> dict[str, Any]:
    """FPalGuildMarkerData: 60 bytes."""
    return {
        "marker_id": reader.guid(),
        "icon_location": reader.vector_dict(),
        "icon_type": reader.i32(),
        "owner_player_uid": reader.guid(),
    }


def guild_marker_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    writer.guid(p["marker_id"])
    writer.vector_dict(p["icon_location"])
    writer.i32(p["icon_type"])
    writer.guid(p["owner_player_uid"])


def role_permission_reader(reader: FArchiveReader) -> dict[str, Any]:
    return {
        "role": reader.byte(),  # EPalGuildRole
        "permissions": reader.tarray(lambda r: r.byte()),  # EPalGuildPermission
    }


def role_permission_writer(writer: FArchiveWriter, p: dict[str, Any]) -> None:
    writer.byte(p["role"])
    writer.tarray(lambda w, v: w.byte(v), p["permissions"])


def _read_guild_tail_v2(reader: FArchiveReader) -> dict[str, Any]:
    """Guild tail as of the 2026-07 update: chest roles, per-player role, permissions."""
    return {
        "guild_chest_allowed_roles": reader.tarray(lambda r: r.byte()),
        "unknown_i32": reader.i32(),
        "admin_player_uid": reader.guid(),
        "players": reader.tarray(guild_player_info_reader),
        "role_permissions": reader.tarray(role_permission_reader),
        "trailing_bytes": reader.byte_list(4),
    }


def _read_guild_tail_v1(reader: FArchiveReader) -> dict[str, Any]:
    """Guild tail before the 2026-07 update."""
    return {
        "admin_player_uid": reader.guid(),
        "players": reader.tarray(player_info_reader),
        "trailing_bytes": reader.byte_list(4),
    }


def _read_guild_tail(reader: FArchiveReader) -> dict[str, Any]:
    """Pick the guild tail layout by which one consumes the blob exactly.

    There is no version flag in the blob, so the two layouts are told apart by
    trial. Landing precisely on EOF is the discriminator; a v2 attempt that
    over- or under-reads is rejected and v1 is tried instead. If v1 also fails
    to reach EOF, decode_bytes' own check raises.
    """
    start = reader.data.tell()
    try:
        tail = _read_guild_tail_v2(reader)
        if reader.eof():
            return tail
    except Exception:
        pass  # not v2; fall through and try the pre-update layout
    reader.data.seek(start)
    return _read_guild_tail_v1(reader)


def decode(
    reader: FArchiveReader, type_name: str, size: int, path: str
) -> dict[str, Any]:
    if type_name != "MapProperty":
        raise Exception(f"Expected MapProperty, got {type_name}")
    value = reader.property(type_name, size, path, nested_caller_path=path)
    # Decode the raw bytes and replace the raw data
    group_map = value["value"]
    for group in group_map:
        group_type = group["value"]["GroupType"]["value"]["value"]
        group_bytes = group["value"]["RawData"]["value"]["values"]
        group["value"]["RawData"]["value"] = decode_bytes(
            reader, group_bytes, group_type
        )
    return value


def decode_bytes(
    parent_reader: FArchiveReader, group_bytes: Sequence[int], group_type: str
) -> dict[str, Any]:
    reader = parent_reader.internal_copy(coerce_bytes(group_bytes), debug=False)
    group_data = {
        "group_type": group_type,
        "group_id": reader.guid(),
        "group_name": reader.fstring(),
        "individual_character_handle_ids": reader.tarray(instance_id_reader),
    }
    if group_type in [
        "EPalGroupType::Guild",
        "EPalGroupType::IndependentGuild",
        "EPalGroupType::Organization",
    ]:
        group_data |= {"org_type": reader.byte()}
    if group_type == "EPalGroupType::Organization":
        group_data |= {"trailing_bytes": reader.byte_list(12)}

    if group_type == "EPalGroupType::Guild":
        guild: dict[str, Any] = {
            "leading_bytes": reader.byte_list(4),
            "base_ids": reader.tarray(uuid_reader),
            "unknown_1": reader.i32(),
            "base_camp_level": reader.i32(),
            "map_object_instance_ids_base_camp_points": reader.tarray(uuid_reader),
            "guild_name": reader.fstring(),
            "last_guild_name_modifier_player_uid": reader.guid(),
            # Formerly read as 4 opaque "unknown_2" bytes: it is the count of
            # this array, which was always 0 before guild map markers existed.
            "guild_markers": reader.tarray(guild_marker_reader),
        }
        group_data |= guild
        group_data |= _read_guild_tail(reader)
    if group_type == "EPalGroupType::IndependentGuild":
        guild: dict[str, Any] = {
            "base_camp_level": reader.i32(),
            "map_object_instance_ids_base_camp_points": reader.tarray(uuid_reader),
            "guild_name": reader.fstring(),
        }
        group_data |= guild
        indie = {
            "player_uid": reader.guid(),
            "guild_name_2": reader.fstring(),
            "player_info": {
                "last_online_real_time": reader.i64(),
                "player_name": reader.fstring(),
            },
        }
        group_data |= indie
    if not reader.eof():
        raise Exception("Warning: EOF not reached")
    return group_data


def encode(
    writer: FArchiveWriter, property_type: str, properties: dict[str, Any]
) -> int:
    if property_type != "MapProperty":
        raise Exception(f"Expected MapProperty, got {property_type}")
    group_map = []
    for group in properties["value"]:
        raw_data = encoded_raw_data(group["value"]["RawData"], encode_bytes)
        if raw_data is group["value"]["RawData"]:
            group_map.append(group)
        else:
            group_map.append(
                {**group, "value": {**group["value"], "RawData": raw_data}}
            )
    properties = without_custom_type(properties)
    properties["value"] = group_map
    return writer.property_inner(property_type, properties)


def encode_bytes(p: dict[str, Any]) -> bytes:
    writer = FArchiveWriter()
    writer.guid(p["group_id"])
    writer.fstring(p["group_name"])
    writer.tarray(instance_id_writer, p["individual_character_handle_ids"])
    if p["group_type"] in [
        "EPalGroupType::Guild",
        "EPalGroupType::IndependentGuild",
        "EPalGroupType::Organization",
    ]:
        writer.byte(p["org_type"])
    if p["group_type"] == "EPalGroupType::Organization":
        writer.write(coerce_bytes(p["trailing_bytes"]))
    if p["group_type"] == "EPalGroupType::IndependentGuild":
        writer.guid(p["player_uid"])
        writer.fstring(p["guild_name_2"])
        writer.i64(p["player_info"]["last_online_real_time"])
        writer.fstring(p["player_info"]["player_name"])
    if p["group_type"] == "EPalGroupType::Guild":
        writer.write(coerce_bytes(p["leading_bytes"]))
        writer.tarray(uuid_writer, p["base_ids"])
        writer.i32(p["unknown_1"])
        writer.i32(p["base_camp_level"])
        writer.tarray(uuid_writer, p["map_object_instance_ids_base_camp_points"])
        writer.fstring(p["guild_name"])
        writer.guid(p["last_guild_name_modifier_player_uid"])
        if "guild_markers" in p:
            writer.tarray(guild_marker_writer, p["guild_markers"])
        else:
            # JSON produced before guild_markers was named: 4 bytes, always zero.
            writer.write(coerce_bytes(p["unknown_2"]))
        if "role_permissions" in p:
            writer.tarray(lambda w, v: w.byte(v), p["guild_chest_allowed_roles"])
            writer.i32(p["unknown_i32"])
            writer.guid(p["admin_player_uid"])
            writer.tarray(guild_player_info_writer, p["players"])
            writer.tarray(role_permission_writer, p["role_permissions"])
        else:
            writer.guid(p["admin_player_uid"])
            writer.tarray(player_info_writer, p["players"])
        writer.write(coerce_bytes(p["trailing_bytes"]))
    encoded_bytes = writer.bytes()
    return encoded_bytes
