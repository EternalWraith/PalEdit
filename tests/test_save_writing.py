import os
import tempfile
import unittest
from unittest.mock import patch

from palworld_pal_edit.PalEdit import (
    PalEdit,
    atomic_write_save,
    file_digest,
    load_pal_import,
    read_bounded_file,
    validate_player_save_identity,
    serialize_and_validate_save,
)


class _InvalidGvas:
    def write(self, _custom_properties):
        return b"not a gvas file"


class _SerializedGvas:
    def __init__(self, payload, trailer=b"\x00\x00\x00\x00"):
        self.payload = payload
        self.trailer = trailer

    def write(self, _custom_properties):
        return self.payload


class SaveWritingTests(unittest.TestCase):
    def test_player_save_identity_must_match_world_player_guid(self):
        class Player:
            def GetPlayerGuid(self):
                return "11111111-1111-1111-1111-111111111111"

        self.assertIs(
            validate_player_save_identity(
                Player(), "11111111-1111-1111-1111-111111111111"),
            None,
        )
        with self.assertRaisesRegex(ValueError, "identity"):
            validate_player_save_identity(
                Player(), "22222222-2222-2222-2222-222222222222")

    def test_failed_save_parse_clears_previous_session_before_save_can_run(self):
        class Value:
            def __init__(self, value):
                self.value = value

            def set(self, value):
                self.value = value

        class Widget:
            def config(self, **_kwargs):
                pass

        class Gui:
            def title(self, value):
                self.value = value

        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "Level.sav")
            with open(source, "wb") as source_file:
                source_file.write(b"candidate save")
            editor = PalEdit.__new__(PalEdit)
            editor.skilllabel = Widget()
            editor.i18n = {
                'msg_saving': 'saving',
                'msg_decompressing': 'decompressing',
                'msg_loading': 'loading',
            }
            editor.gui = Gui()
            editor.current = Value("Old player")
            editor.filename = "old.sav"
            editor.loaded_file_digest = b"old digest"
            editor.save_type = 0x31
            editor.data = {"old": True}
            editor.palguidmanager = object()
            editor.palbox = [object()]
            editor.players = {"Old player": object()}
            editor.disable_menus = lambda: None
            editor.logerror = lambda _message: None
            editor.loaddata = lambda _gvas: (_ for _ in ()).throw(
                ValueError("injected load failure"))

            with (
                    patch("palworld_pal_edit.PalEdit.askopenfilename",
                          return_value=source),
                    patch("palworld_pal_edit.PalEdit.decompress_sav_to_gvas",
                          return_value=(b"raw gvas", 0x32)),
                    patch("palworld_pal_edit.PalEdit.GvasFile.read",
                          side_effect=ValueError("injected parse failure")),
                    patch("palworld_pal_edit.PalEdit.logger", create=True),
            ):
                editor.loadfile()

            self.assertEqual(editor.filename, "")
            self.assertIsNone(editor.loaded_file_digest)
            self.assertIsNone(editor.save_type)
            self.assertIsNone(editor.data)
            self.assertIsNone(editor.palguidmanager)
            self.assertEqual(editor.palbox, [])
            self.assertEqual(editor.players, {})
            self.assertEqual(editor.current.value, "")

    def test_bounded_file_read_accepts_limit_and_rejects_one_byte_over(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "Level.sav")
            with open(source, "wb") as source_file:
                source_file.write(b"12345678")

            self.assertEqual(read_bounded_file(source, max_bytes=8), b"12345678")
            with self.assertRaisesRegex(ValueError, "too large"):
                read_bounded_file(source, max_bytes=7)

    def test_pal_import_loader_rejects_oversized_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "oversized.json")
            with open(source, "wb") as source_file:
                source_file.write(b"x" * 9)

            with self.assertRaisesRegex(ValueError, "too large"):
                load_pal_import(source, max_bytes=8)

    def test_pal_import_loader_parses_bounded_json(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "pal.json")
            with open(source, "wb") as source_file:
                source_file.write(b'{"Pals": []}')

            self.assertEqual(load_pal_import(source, max_bytes=32), {"Pals": []})

    def test_atomic_write_replaces_target_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "Level.sav")
            with open(target, "wb") as save_file:
                save_file.write(b"old save")

            atomic_write_save(target, b"new save")

            with open(target, "rb") as save_file:
                self.assertEqual(save_file.read(), b"new save")
            self.assertFalse(os.path.exists(target + ".PalEdit.tmp"))

    def test_atomic_write_does_not_follow_a_predictable_temporary_hard_link(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "Level.sav")
            victim = os.path.join(directory, "unrelated.sav")
            predictable_temporary = target + ".PalEdit.tmp"
            with open(target, "wb") as save_file:
                save_file.write(b"old save")
            with open(victim, "wb") as victim_file:
                victim_file.write(b"unrelated data")
            os.link(victim, predictable_temporary)

            atomic_write_save(target, b"new save")

            with open(target, "rb") as save_file:
                self.assertEqual(save_file.read(), b"new save")
            with open(victim, "rb") as victim_file:
                self.assertEqual(victim_file.read(), b"unrelated data")

    def test_atomic_write_refuses_target_changed_since_save_started(self):
        with tempfile.TemporaryDirectory() as directory:
            target = os.path.join(directory, "Level.sav")
            with open(target, "wb") as save_file:
                save_file.write(b"loaded save")
            expected_digest = file_digest(target)
            with open(target, "wb") as external_writer:
                external_writer.write(b"newer external save")

            with self.assertRaisesRegex(RuntimeError, "changed on disk"):
                atomic_write_save(
                    target, b"PalEdit save", expected_digest=expected_digest)

            with open(target, "rb") as save_file:
                self.assertEqual(save_file.read(), b"newer external save")


    def test_serialization_refuses_bytes_that_do_not_reparse_as_gvas(self):
        with self.assertRaises(Exception):
            serialize_and_validate_save(_InvalidGvas(), 0x31)

    def test_serialization_refuses_incomplete_reparse(self):
        with (
                patch("palworld_pal_edit.PalEdit.compress_gvas_to_sav",
                      return_value=b"compressed"),
                patch("palworld_pal_edit.PalEdit.decompress_sav_to_gvas",
                      return_value=(b"complete gvas", 0x31)),
                patch("palworld_pal_edit.PalEdit.GvasFile.read",
                      return_value=_SerializedGvas(b"partial gvas")),
                self.assertRaisesRegex(ValueError, "reparse"),
        ):
            serialize_and_validate_save(_SerializedGvas(b"complete gvas"), 0x31)

    def test_serialization_refuses_nonstandard_gvas_trailer(self):
        malformed = _SerializedGvas(b"complete gvas", trailer=b"unexpected")
        with (
                patch("palworld_pal_edit.PalEdit.compress_gvas_to_sav",
                      return_value=b"compressed"),
                patch("palworld_pal_edit.PalEdit.decompress_sav_to_gvas",
                      return_value=(b"complete gvas", 0x31)),
                patch("palworld_pal_edit.PalEdit.GvasFile.read",
                      return_value=malformed),
                self.assertRaisesRegex(ValueError, "trailer"),
        ):
            serialize_and_validate_save(_SerializedGvas(b"complete gvas"), 0x31)


if __name__ == "__main__":
    unittest.main()
