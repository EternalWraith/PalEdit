import palworld_pal_edit.PalEdit

from pathlib import Path
from loguru import logger

LOG_DIR = Path.home() / "AppData" / "Local" / "PalEdit" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()

logger.add(
    LOG_DIR / "paledit.log",
    level="DEBUG",
    rotation="5 MB",
    retention=5,
    encoding="utf-8",
    backtrace=True,
    diagnose=False,
)

palworld_pal_edit.PalEdit.main()
    
