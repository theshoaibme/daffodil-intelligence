"""CopyCat input lock helpers — optional daffodil-kit overlay on local machine."""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

COPYCAT_MESSAGE = "CopyCat is running — mouse and keyboard are disabled"


def acquire(mode: str = "replay", recording_name: Optional[str] = None) -> None:
    try:
        from daffodil_kit.input_lock import acquire as _acquire
        from daffodil_kit.audit import log_event

        _acquire(mode=mode, recording_name=recording_name)
        log_event("copycat.lock_start", detail={"mode": mode, "recording": recording_name, "source": "api"})
    except ImportError:
        logger.debug("daffodil-kit not installed — CopyCat overlay skipped")
    except Exception as e:
        logger.warning("CopyCat lock acquire failed: %s", e)


def release() -> None:
    try:
        from daffodil_kit.input_lock import release as _release
        from daffodil_kit.audit import log_event

        _release()
        log_event("copycat.lock_end", detail={"source": "api"})
    except ImportError:
        pass
    except Exception as e:
        logger.warning("CopyCat lock release failed: %s", e)


def is_locked() -> bool:
    try:
        from daffodil_kit.input_lock import is_locked as _is_locked

        return _is_locked()
    except ImportError:
        return False
