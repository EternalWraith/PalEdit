from __future__ import annotations

from typing import TYPE_CHECKING, Callable, TypeVar
from concurrent import futures


if TYPE_CHECKING:
    from palworld_pal_edit.PalEdit import PalEdit

_executor = futures.ThreadPoolExecutor()

T = TypeVar('T')
def run_task(pal_edit_instance: PalEdit, fn: Callable[..., T], *, lock_state: bool = True) -> T:
    """
    Run a long-running task in a thread to avoid blocking the UI loop, which can freeze the application.

    :param pal_edit_instance: The PalEdit instance to run the task on. When called from PalEdit, just pass `self`
    :param fn: The task you want to run. E.g. reading/parsing a large file, doing network operation, etc.
    :param lock_state: Whether to lock certain UI states (like the skill label and menus) during the task.
    :return: The result of the task.
    """

    if lock_state:
        pal_edit_instance.lock_state()

    future = _executor.submit(fn)
    while not future.done():
        # Ensure the UI continues to update while the task is running
        pal_edit_instance.gui.update()

    if lock_state:
        pal_edit_instance.unlock_state()

    return future.result()


def close_executor():
    _executor.shutdown()