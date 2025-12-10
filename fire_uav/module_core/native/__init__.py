try:
    import native_core as _native_core

    NATIVE_AVAILABLE = True
except Exception:  # noqa: BLE001
    _native_core = None
    NATIVE_AVAILABLE = False

__all__ = ["_native_core", "NATIVE_AVAILABLE"]

