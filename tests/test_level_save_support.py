import copy
import unittest

from palworld_pal_edit.PalInfo import PalGuid
from palworld_pal_edit.PalEdit import PalEdit


ZERO_GUID = "00000000-0000-0000-0000-000000000000"
PLAYER_GUID = "11111111-1111-1111-1111-111111111111"
GROUP_GUID = "22222222-2222-2222-2222-222222222222"
CONTAINER_GUID = "33333333-3333-3333-3333-333333333333"
SOURCE_GUID = "44444444-4444-4444-4444-444444444444"
NEW_GUID = "55555555-5555-5555-5555-555555555555"
OTHER_GUID = "66666666-6666-6666-6666-666666666666"


class _Value:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class _PlayerDrop:
    def __init__(self):
        self.values = None
        self.state = None
        self.index = None

    def __setitem__(self, key, value):
        if key == "values":
            self.values = value

    def config(self, **kwargs):
        self.state = kwargs.get("state", self.state)

    def current(self, index):
        self.index = index


def pal_entry(instance_id=SOURCE_GUID, player_uid=PLAYER_GUID, slot_index=0,
              is_player=False, nickname="Pal", key_player_uid=ZERO_GUID):
    save_parameter = {
        "NickName": {"value": nickname},
        "IsPlayer": {"value": is_player},
        "OwnerPlayerUId": {"value": player_uid},
        "OldOwnerPlayerUIds": {"value": {"values": [player_uid]}},
        "SlotId": {
            "value": {
                "ContainerId": {"value": {"ID": {"value": CONTAINER_GUID}}},
                "SlotIndex": {"value": slot_index},
            }
        },
    }
    return {
        "key": {
            "PlayerUId": {"value": player_uid if is_player else key_player_uid},
            "InstanceId": {"value": instance_id},
        },
        "value": {
            "RawData": {
                "value": {
                    "group_id": GROUP_GUID,
                    "object": {"SaveParameter": {"value": save_parameter}},
                }
            }
        },
    }


def container_slot(slot_index, instance_id):
    return {
        "SlotIndex": {"type": "IntProperty", "id": None, "value": slot_index},
        "RawData": {
            "type": "ArrayProperty",
            "array_type": "ByteProperty",
            "id": None,
            "value": {
                "player_uid": ZERO_GUID,
                "instance_id": instance_id,
                "permission_tribe_id": 0,
                "unknown_bytes": b"\x00\x00\x00\x00\x00",
            },
        },
        "CustomVersionData": {
            "type": "ArrayProperty",
            "array_type": "ByteProperty",
            "id": None,
            "value": {"values": b"version"},
        },
    }


def world_data(slot_num=3, slots=None, characters=None, handles=None):
    slots = list(slots or [])
    characters = list(characters or [])
    handles = list(handles or [])
    return {
        "properties": {
            "worldSaveData": {
                "value": {
                    "CharacterSaveParameterMap": {"value": characters},
                    "CharacterContainerSaveData": {
                        "value": [
                            {
                                "key": {"ID": {"value": CONTAINER_GUID}},
                                "value": {
                                    "SlotNum": {"value": slot_num},
                                    "Slots": {"value": {"values": slots}},
                                },
                            }
                        ]
                    },
                    "GroupSaveDataMap": {
                        "value": [
                            {
                                "key": GROUP_GUID,
                                "value": {
                                    "RawData": {
                                        "value": {
                                            "admin_player_uid": PLAYER_GUID,
                                            "players": [
                                                {"player_uid": PLAYER_GUID}
                                            ],
                                            "individual_character_handle_ids": handles,
                                        }
                                    }
                                },
                            }
                        ]
                    },
                }
            }
        }
    }


class LevelSaveOperationsTests(unittest.TestCase):
    def test_empty_world_disables_player_selection_without_defaulting(self):
        editor = PalEdit.__new__(PalEdit)
        editor.players = {}
        editor.current = _Value()
        editor.playerdrop = _PlayerDrop()

        selected = editor._configure_player_selection()

        self.assertFalse(selected)
        self.assertEqual(editor.current.get(), "")
        self.assertEqual(editor.playerdrop.values, [])
        self.assertEqual(editor.playerdrop.state, "disabled")
        self.assertIsNone(editor.playerdrop.index)

    def test_player_list_requires_is_player_to_be_true(self):
        false_player = pal_entry(is_player=False, nickname="Ordinary Pal")
        malformed_player = pal_entry(
            instance_id=NEW_GUID,
            player_uid=NEW_GUID,
            is_player=1,
            nickname="Malformed Player",
        )
        true_player = pal_entry(
            instance_id=OTHER_GUID,
            player_uid=OTHER_GUID,
            is_player=True,
            nickname="Real Player",
        )
        manager = PalGuid(world_data(
            characters=[false_player, malformed_player, true_player]))

        players = manager.GetPlayerslist()

        self.assertEqual(players, {"Real Player": OTHER_GUID})

    def test_insert_pal_refuses_duplicate_target_container_ids(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        containers = data['properties']['worldSaveData']['value'][
            'CharacterContainerSaveData']['value']
        containers.append(copy.deepcopy(containers[0]))
        before = copy.deepcopy(data)

        inserted = PalGuid(data).InsertPal(
            source, PLAYER_GUID, GROUP_GUID, CONTAINER_GUID, ZERO_GUID,
            new_guid=NEW_GUID)

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_duplicate_target_group_ids(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        groups = data['properties']['worldSaveData']['value'][
            'GroupSaveDataMap']['value']
        groups.append(copy.deepcopy(groups[0]))
        before = copy.deepcopy(data)

        inserted = PalGuid(data).InsertPal(
            source, PLAYER_GUID, GROUP_GUID, CONTAINER_GUID, ZERO_GUID,
            new_guid=NEW_GUID)

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_conflicting_guild_handle_identities(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": SOURCE_GUID, "instance_id": OTHER_GUID}],
        )
        before = copy.deepcopy(data)

        deleted = PalGuid(data).DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_insert_pal_claims_first_free_slot_and_all_references(self):
        source = pal_entry()
        manager = PalGuid(
            world_data(
                slots=[container_slot(0, SOURCE_GUID), container_slot(2, OTHER_GUID)],
                characters=[source],
                handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
            )
        )

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNotNone(inserted)
        self.assertEqual(inserted["key"]["InstanceId"]["value"], NEW_GUID)
        save_parameter = inserted["value"]["RawData"]["value"]["object"]["SaveParameter"]["value"]
        self.assertEqual(save_parameter["SlotId"]["value"]["SlotIndex"]["value"], 1)
        self.assertEqual(save_parameter["SlotId"]["value"]["ContainerId"]["value"]["ID"]["value"], CONTAINER_GUID)
        self.assertEqual(manager.GetContainerSlot(CONTAINER_GUID, NEW_GUID)["SlotIndex"]["value"], 1)
        self.assertTrue(manager.GroupContainsPal(GROUP_GUID, NEW_GUID))
        self.assertEqual(len(manager._CharacterSaveParameterMap), 2)

    def test_insert_pal_is_failure_atomic_when_container_is_full(self):
        source = pal_entry()
        data = world_data(
            slot_num=1,
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_inconsistent_container_at_nominal_capacity(self):
        source = pal_entry()
        data = world_data(
            slot_num=2,
            slots=[container_slot(0, SOURCE_GUID), container_slot(0, OTHER_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_player_character_source(self):
        source = pal_entry(is_player=True)
        data = world_data(
            slots=[container_slot(0, OTHER_GUID)],
            handles=[{"guid": ZERO_GUID, "instance_id": OTHER_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_non_boolean_player_marker(self):
        source = pal_entry(is_player=1)
        source['key']['PlayerUId']['value'] = ZERO_GUID
        data = world_data(
            slots=[container_slot(0, OTHER_GUID)],
            handles=[{"guid": ZERO_GUID, "instance_id": OTHER_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_explicit_null_player_marker(self):
        source = pal_entry(is_player=False)
        source['value']['RawData']['value']['object'][
            'SaveParameter']['value']['IsPlayer'] = None
        data = world_data(
            slots=[container_slot(0, OTHER_GUID)],
            handles=[{"guid": ZERO_GUID, "instance_id": OTHER_GUID}],
        )
        before = copy.deepcopy(data)

        inserted = PalGuid(data).InsertPal(
            source, PLAYER_GUID, GROUP_GUID, CONTAINER_GUID, ZERO_GUID,
            new_guid=NEW_GUID)

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_malformed_existing_guild_handle(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"unexpected": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_nonzero_character_map_player_key(self):
        source = pal_entry(key_player_uid=OTHER_GUID)
        data = world_data(
            slots=[container_slot(0, OTHER_GUID)],
            handles=[{"guid": ZERO_GUID, "instance_id": OTHER_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_insert_pal_refuses_guid_used_by_another_container(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        containers = data['properties']['worldSaveData']['value'][
            'CharacterContainerSaveData']['value']
        other_container = copy.deepcopy(containers[0])
        other_container['key']['ID']['value'] = (
            "88888888-8888-8888-8888-888888888888")
        other_container['value']['Slots']['value']['values'] = [
            container_slot(0, NEW_GUID)
        ]
        containers.append(other_container)
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPal(
            source,
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            ZERO_GUID,
            new_guid=NEW_GUID,
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_batch_insert_is_failure_atomic_when_all_sources_do_not_fit(self):
        source = pal_entry()
        second = pal_entry(instance_id=OTHER_GUID)
        data = world_data(
            slot_num=2,
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        inserted = manager.InsertPals(
            [source, second],
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            [ZERO_GUID, ZERO_GUID],
            new_guids=[NEW_GUID, "77777777-7777-7777-7777-777777777777"],
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_batch_insert_restores_all_structures_when_later_insert_raises(self):
        class FailingSecondInsertManager(PalGuid):
            def __init__(self, data):
                super().__init__(data)
                self.calls = 0

            def InsertPal(self, *args, **kwargs):
                self.calls += 1
                if self.calls == 2:
                    raise RuntimeError("injected insertion failure")
                return super().InsertPal(*args, **kwargs)

        source = pal_entry()
        second = pal_entry(instance_id=OTHER_GUID)
        data = world_data(
            slot_num=3,
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        character_ref = data['properties']['worldSaveData']['value'][
            'CharacterSaveParameterMap']['value'][0]
        container_ref = data['properties']['worldSaveData']['value'][
            'CharacterContainerSaveData']['value'][0]
        group_ref = data['properties']['worldSaveData']['value'][
            'GroupSaveDataMap']['value'][0]
        manager = FailingSecondInsertManager(data)

        inserted = manager.InsertPals(
            [source, second],
            PLAYER_GUID,
            GROUP_GUID,
            CONTAINER_GUID,
            [ZERO_GUID, ZERO_GUID],
            new_guids=[NEW_GUID, "77777777-7777-7777-7777-777777777777"],
        )

        self.assertIsNone(inserted)
        self.assertEqual(data, before)
        self.assertIs(manager._CharacterSaveParameterMap[0], character_ref)
        self.assertIs(manager._CharacterContainerSaveData[0], container_ref)
        self.assertIs(manager._GroupSaveDataMap[0], group_ref)

    def test_single_insert_restores_all_structures_when_group_append_raises(self):
        class FailingGroupAppendManager(PalGuid):
            def AddGroupSaveData(self, *args, **kwargs):
                raise RuntimeError("injected guild append failure")

        source = pal_entry()
        data = world_data(
            slot_num=2,
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = FailingGroupAppendManager(data)

        inserted = manager.InsertPal(
            source, PLAYER_GUID, GROUP_GUID, CONTAINER_GUID, ZERO_GUID,
            new_guid=NEW_GUID)

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_delete_pal_removes_character_container_and_group_references(self):
        source = pal_entry()
        other = pal_entry(instance_id=OTHER_GUID, slot_index=1)
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID), container_slot(1, OTHER_GUID)],
            characters=[source, other],
            handles=[
                {"guid": ZERO_GUID, "instance_id": SOURCE_GUID},
                {"guid": ZERO_GUID, "instance_id": OTHER_GUID},
            ],
        )
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertTrue(deleted)
        self.assertIsNone(manager.GetContainerSlot(CONTAINER_GUID, SOURCE_GUID))
        self.assertFalse(manager.GroupContainsPal(GROUP_GUID, SOURCE_GUID))
        self.assertEqual(manager.GetContainerSlot(CONTAINER_GUID, OTHER_GUID)["SlotIndex"]["value"], 1)
        self.assertTrue(manager.GroupContainsPal(GROUP_GUID, OTHER_GUID))
        self.assertEqual(manager._CharacterSaveParameterMap, [other])

    def test_delete_pal_restores_all_structures_when_mutation_raises(self):
        class FailingRemoveManager(PalGuid):
            def RemoveGroupSaveData(self, *args, **kwargs):
                raise RuntimeError("injected removal failure")

        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        character_ref = data['properties']['worldSaveData']['value'][
            'CharacterSaveParameterMap']['value'][0]
        container_ref = data['properties']['worldSaveData']['value'][
            'CharacterContainerSaveData']['value'][0]
        group_ref = data['properties']['worldSaveData']['value'][
            'GroupSaveDataMap']['value'][0]
        manager = FailingRemoveManager(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)
        self.assertIs(manager._CharacterSaveParameterMap[0], character_ref)
        self.assertIs(manager._CharacterContainerSaveData[0], container_ref)
        self.assertIs(manager._GroupSaveDataMap[0], group_ref)

    def test_delete_pal_refuses_foreign_owner_without_changes(self):
        source = pal_entry(player_uid=OTHER_GUID)
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_nonzero_character_map_player_key(self):
        source = pal_entry(key_player_uid=OTHER_GUID)
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)

        deleted = PalGuid(data).DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_duplicate_cross_container_reference(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        containers = data['properties']['worldSaveData']['value'][
            'CharacterContainerSaveData']['value']
        other_container = copy.deepcopy(containers[0])
        other_container['key']['ID']['value'] = (
            "88888888-8888-8888-8888-888888888888")
        containers.append(other_container)
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_delete_pal_removes_guid_form_guild_reference(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": SOURCE_GUID, "instance_id": ZERO_GUID}],
        )
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertTrue(deleted)
        self.assertEqual(
            data['properties']['worldSaveData']['value']['GroupSaveDataMap']
            ['value'][0]['value']['RawData']['value']
            ['individual_character_handle_ids'],
            [],
        )

    def test_delete_pal_refuses_duplicate_character_entries_without_changes(self):
        source = pal_entry()
        duplicate = copy.deepcopy(source)
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source, duplicate],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_inconsistent_container_reference_without_changes(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, OTHER_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_duplicate_guild_references_without_changes(self):
        source = pal_entry()
        duplicate_handle = {"guid": ZERO_GUID, "instance_id": SOURCE_GUID}
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[copy.deepcopy(duplicate_handle), copy.deepcopy(duplicate_handle)],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_missing_guild_reference_without_changes(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[],
        )
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_guild_reference_in_different_group(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[],
        )
        groups = data['properties']['worldSaveData']['value']['GroupSaveDataMap']['value']
        other_group = copy.deepcopy(groups[0])
        other_group['key'] = OTHER_GUID
        other_group['value']['RawData']['value']['individual_character_handle_ids'] = [
            {"guid": ZERO_GUID, "instance_id": SOURCE_GUID}
        ]
        groups.append(other_group)
        before = copy.deepcopy(data)
        manager = PalGuid(data)

        deleted = manager.DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)

    def test_batch_insert_refuses_non_object_save_parameter(self):
        source = pal_entry()
        malformed = pal_entry(instance_id=OTHER_GUID)
        malformed['value']['RawData']['value']['object'][
            'SaveParameter']['value'] = "not an object"
        data = world_data(
            slot_num=3,
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=[{"guid": ZERO_GUID, "instance_id": SOURCE_GUID}],
        )
        before = copy.deepcopy(data)

        inserted = PalGuid(data).InsertPals(
            [source, malformed], PLAYER_GUID, GROUP_GUID, CONTAINER_GUID,
            [ZERO_GUID, ZERO_GUID], new_guids=[NEW_GUID, OTHER_GUID])

        self.assertIsNone(inserted)
        self.assertEqual(data, before)

    def test_delete_pal_refuses_non_object_guild_handle(self):
        source = pal_entry()
        data = world_data(
            slots=[container_slot(0, SOURCE_GUID)],
            characters=[source],
            handles=["not an object"],
        )
        before = copy.deepcopy(data)

        deleted = PalGuid(data).DeletePalEntry(source, PLAYER_GUID)

        self.assertFalse(deleted)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
