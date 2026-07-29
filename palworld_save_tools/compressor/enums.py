from enum import Enum


class SaveType(Enum):
    CNK = 0x30  # CNK
    PLM = 0x31  # Oodle compressed
    PLZ = 0x32  # Zlib compressed

    @staticmethod
    def is_valid(save_type: int) -> bool:
        return save_type in (SaveType.PLZ.value, SaveType.PLM.value, SaveType.CNK.value)


class MagicBytes(Enum):
    PLZ = b"PlZ"  # Zlib magic
    PLM = b"PlM"  # Oodle magic
    CNK = b"CNK"

    @staticmethod
    def is_valid(magic: bytes) -> bool:
        return magic in (
            MagicBytes.PLZ.value,
            MagicBytes.PLM.value,
            MagicBytes.CNK.value,
        )
