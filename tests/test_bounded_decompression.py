import os
import random
import tempfile
import unittest

from palworld_pal_edit.SaveConverter import convert_sav_to_obj
from palworld_save_tools.palsav import (
    compress_gvas_to_sav,
    decompress_sav_to_gvas,
    oozlib,
)


class BoundedDecompressionTests(unittest.TestCase):
    def test_zlib_output_at_limit_is_accepted(self):
        payload = b"x" * 1024
        save = compress_gvas_to_sav(payload, 0x32)

        decompressed, save_type = decompress_sav_to_gvas(
            save, max_output_size=len(payload))

        self.assertEqual(decompressed, payload)
        self.assertEqual(save_type, 0x32)

    def test_incompressible_zlib_output_at_limit_is_accepted(self):
        payload = random.Random(0).randbytes(1024)
        save = compress_gvas_to_sav(payload, 0x32)

        decompressed, save_type = decompress_sav_to_gvas(
            save, max_output_size=len(payload))

        self.assertEqual(decompressed, payload)
        self.assertEqual(save_type, 0x32)

    def test_zlib_rejects_mismatched_save_types(self):
        payload = random.Random(2).randbytes(1024)
        original = compress_gvas_to_sav(payload, 0x32)

        for invalid_type in (0x31, 0x30, 0x7F):
            with self.subTest(invalid_type=invalid_type):
                save = bytearray(original)
                save[11] = invalid_type
                with self.assertRaisesRegex(ValueError, "type"):
                    decompress_sav_to_gvas(bytes(save), max_output_size=2048)

    def test_zlib_declared_output_over_limit_is_rejected(self):
        save = compress_gvas_to_sav(b"x" * 1024, 0x32)

        with self.assertRaisesRegex(ValueError, "decompressed output"):
            decompress_sav_to_gvas(save, max_output_size=512)

    def test_oodle_declared_output_over_limit_is_rejected_before_decode(self):
        compressed = b"x" * 64
        save = oozlib.build_sav(
            compressed, 1024, len(compressed), oozlib._get_magic(0x31), 0x31)

        with self.assertRaisesRegex(ValueError, "decompressed output"):
            decompress_sav_to_gvas(save, max_output_size=512)

    def test_oodle_rejects_mismatched_save_type(self):
        payload = random.Random(1).randbytes(1024)
        save = bytearray(compress_gvas_to_sav(payload, 0x31))
        save[11] = 0x32

        with self.assertRaisesRegex(ValueError, "type"):
            decompress_sav_to_gvas(bytes(save), max_output_size=2048)

    def test_oodle_decoder_rejects_non_oodle_magic(self):
        payload = random.Random(1).randbytes(1024)
        save = bytearray(compress_gvas_to_sav(payload, 0x31))
        save[8:11] = b"PlZ"

        with self.assertRaisesRegex(ValueError, "format"):
            oozlib.decompress(bytes(save), max_output_size=2048)

    def test_oodle_rejects_trailing_payload(self):
        payload = random.Random(1).randbytes(1024)
        save = compress_gvas_to_sav(payload, 0x31) + b"trailer"

        with self.assertRaisesRegex(ValueError, "payload length"):
            decompress_sav_to_gvas(save, max_output_size=2048)

    def test_oodle_rejects_truncated_payload(self):
        payload = random.Random(1).randbytes(1024)
        save = compress_gvas_to_sav(payload, 0x31)[:-1]

        with self.assertRaisesRegex(ValueError, "payload length"):
            decompress_sav_to_gvas(save, max_output_size=2048)

    def test_player_save_input_is_bounded_before_decompression(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(directory, "Player.sav")
            with open(source, "wb") as source_file:
                source_file.write(b"123456789")

            with self.assertRaisesRegex(ValueError, "too large"):
                convert_sav_to_obj(
                    source, max_input_bytes=8, max_output_size=16)


if __name__ == "__main__":
    unittest.main()
