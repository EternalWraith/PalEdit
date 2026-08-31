import zlib

from loguru import logger
from palworld_save_tools.compressor import Compressor, SaveType


class Zlib(Compressor):
    def __init__(self):
        """
        OozLib is an open source library for compression and decompression using Oodle.
        """
        self.SAFE_SPACE_PADDING = 128

    def compress(self, data: bytes, save_type: int) -> bytes:
        logger.info("Starting compression process with zlib...")

        uncompressed_len = len(data)
        compressed_data = zlib.compress(data)
        compressed_len = len(compressed_data)
        if save_type != 0x32:
            raise Exception(
                f"Unhandled compression type: 0x{save_type:02X}, only 0x32 (double zlib) is supported"
            )
        compressed_data = zlib.compress(compressed_data)
        magic_bytes = self._get_magic(save_type)

        logger.debug("File information (Compress):")
        logger.debug(f"  Magic bytes: {magic_bytes.decode('ascii', errors='ignore')}")
        logger.debug(f"  Save type: 0x{save_type:02X}")
        logger.debug(f"  Compressed size: {compressed_len:,} bytes")
        logger.debug(f"  Uncompressed size: {uncompressed_len:,} bytes")
        logger.debug(f"  Hex dump: {compressed_data.hex()[:64]}")

        sav_data = self.build_sav(
            compressed_data,
            uncompressed_len,
            compressed_len,
            magic_bytes,
            save_type,
        )

        return sav_data

    @staticmethod
    def _decompress_bounded(data: bytes, maximum: int) -> bytes:
        decoder = zlib.decompressobj()
        output = decoder.decompress(data, maximum + 1)
        if len(output) > maximum or decoder.unconsumed_tail:
            raise ValueError("SAV decompressed output exceeds the configured limit")
        output += decoder.flush()
        if len(output) > maximum:
            raise ValueError("SAV decompressed output exceeds the configured limit")
        if not decoder.eof or decoder.unused_data:
            raise ValueError("Invalid or trailing zlib payload")
        return output

    def decompress(self, data: bytes, max_output_size=None) -> bytes:
        logger.info("Starting decompression process with zlib...")

        format_result = self.check_sav_format(data)

        if format_result is None:
            raise ValueError("Unknown save format")

        if format_result == SaveType.PLM:
            raise ValueError(
                "Detected PLM format (Oodle), this tool only supports PLZ format (Zlib)"
            )

        uncompressed_len, compressed_len, magic, save_type, data_offset = (
            self._parse_sav_header(data)
        )
        if save_type != SaveType.PLZ.value:
            raise ValueError("Zlib save header has an invalid save type")
        if max_output_size is not None and uncompressed_len > max_output_size:
            raise ValueError("SAV decompressed output exceeds the configured limit")
        if (max_output_size is not None
                and compressed_len > max(max_output_size, len(data))):
            raise ValueError("SAV intermediate output exceeds the configured limit")

        logger.debug("File information (Decompress):")
        logger.debug(f"  Magic bytes: {magic.decode('ascii', errors='ignore')}")
        logger.debug(f"  Save type: 0x{save_type:02X}")
        logger.debug(f"  Compressed size: {compressed_len:,} bytes")
        logger.debug(f"  Uncompressed size: {uncompressed_len:,} bytes")
        logger.debug("Detected PLZ format (Zlib), starting decompression...")

        outer_limit = compressed_len
        uncompressed_data = self._decompress_bounded(
            data[data_offset:], outer_limit)

        if save_type == SaveType.PLZ.value:
            if compressed_len != len(uncompressed_data):
                raise Exception(f"incorrect compressed length: {compressed_len}")

            inner_limit = max_output_size if max_output_size is not None else uncompressed_len
            uncompressed_data = self._decompress_bounded(
                uncompressed_data, inner_limit)

        if uncompressed_len != len(uncompressed_data):
            raise Exception(
                f"incorrect uncompressed length: {uncompressed_len} != {len(uncompressed_data)}"
            )

        logger.info(
            f"Decompression successful, decompressed size: {len(uncompressed_data):,} bytes"
        )

        return uncompressed_data, save_type
