"""Apple Shortcuts (App Intents) library plugin.

``~/Library/Shortcuts/ToolKit/Tools-prod.v*-*.sqlite`` is the system-wide
catalog of every Shortcut / App Intent the device knows how to run —
both Apple's built-ins and third-party app contributions. Includes the
``Tools`` table (the actual shortcuts) and ``Categories``, ``Search
Keywords``, and per-tool localisations.
"""

from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from dissect.target.exceptions import UnsupportedPluginError
from dissect.target.helpers.record import TargetRecordDescriptor
from dissect.target.plugin import Plugin, export

if TYPE_CHECKING:
    from collections.abc import Iterator


COCOA_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def _cocoa_ts(v):
    if v is None:
        return None
    try:
        return COCOA_EPOCH + timedelta(seconds=float(v))
    except (OSError, OverflowError, ValueError, TypeError):
        return None


ShortcutToolRecord = TargetRecordDescriptor(
    "macos/shortcuts/tool",
    [
        ("string", "identifier"),
        ("string", "name"),
        ("string", "subtitle"),
        ("string", "bundle_id"),
        ("string", "category"),
        ("string", "language"),
        ("path", "source"),
    ],
)


class AppleShortcutsPlugin(Plugin):
    """Parse the Apple Shortcuts toolkit catalog."""

    __namespace__ = "shortcuts"

    GLOB = "Users/*/Library/Shortcuts/ToolKit/Tools-prod.v*-*.sqlite"

    def __init__(self, target):
        super().__init__(target)
        self._db_paths = list(self.target.fs.path("/").glob(self.GLOB))

    def check_compatible(self) -> None:
        if not self._db_paths:
            raise UnsupportedPluginError("No Shortcuts toolkit found")

    def _open(self, db_path):
        with db_path.open("rb") as fh:
            data = fh.read()
        tmp = tempfile.NamedTemporaryFile(suffix=".db")  # noqa: SIM115
        tmp.write(data)
        tmp.flush()
        for suffix in ("-wal", "-shm"):
            src = db_path.parent.joinpath(db_path.name + suffix)
            if src.exists():
                with src.open("rb") as sf, open(tmp.name + suffix, "wb") as df:  # noqa: PTH123
                    df.write(sf.read())
        conn = sqlite3.connect(tmp.name)
        conn.row_factory = sqlite3.Row
        return conn, tmp

    @export(record=ShortcutToolRecord)
    def tools(self) -> Iterator[ShortcutToolRecord]:
        """One record per shortcut / App Intent in the catalog."""
        for db_path in self._db_paths:
            try:
                yield from self._parse(db_path)
            except Exception as e:
                self.target.log.warning("Error parsing Shortcuts %s: %s", db_path, e)

    def _parse(self, db_path):
        conn, tmp = self._open(db_path)
        try:
            cur = conn.cursor()
            tables = {r[0] for r in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "Tools" not in tables:
                return
            cols = {r[1] for r in cur.execute("PRAGMA table_info(Tools)").fetchall()}

            def col(*names, default="NULL"):
                for n in names:
                    if n in cols:
                        return n
                return default

            ident = col("identifier", "id")
            name_col = col("name", "displayName", "title")
            sub_col = col("subtitle", "summary", "description")
            bundle_col = col("bundleIdentifier", "bundleID")
            cat_col = col("categoryID", "category")
            lang_col = col("language", "locale")
            cur.execute(
                f"SELECT {ident} AS ident, {name_col} AS name, "  # noqa: S608
                f"{sub_col} AS sub, {bundle_col} AS bundle, "
                f"{cat_col} AS cat, {lang_col} AS lang FROM Tools"
            )
            for row in cur:
                yield ShortcutToolRecord(
                    identifier=str(row["ident"] or ""),
                    name=row["name"] or "",
                    subtitle=row["sub"] or "",
                    bundle_id=row["bundle"] or "",
                    category=str(row["cat"] or ""),
                    language=row["lang"] or "",
                    source=db_path,
                    _target=self.target,
                )
        finally:
            conn.close()
            tmp.close()
