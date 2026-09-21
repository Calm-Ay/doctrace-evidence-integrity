def sync_events(db_path: str) -> int:
    """No remote transport is configured; never mark local events transmitted."""
    raise NotImplementedError('Remote synchronization is not configured. Events remain local.')
