from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from dissect.target.exceptions import UnsupportedPluginError
from dissect.target.helpers.record import TargetRecordDescriptor
from dissect.target.plugin import Plugin, export

if TYPE_CHECKING:
    from collections.abc import Iterator


LocalTimeRecord = TargetRecordDescriptor(
    "macos/localtime/info",
    [
        ("string", "timezone"),
        ("string", "timezone_rule"),
        ("path", "source"),
    ],
)


class MacOSLocalTimePlugin(Plugin):
    """Plugin to report the configured timezone on macOS.

    Locations:
        /etc/localtime (symlink)
        /private/var/db/timezone/localtime

    On a mounted volume localtime is a symlink and the zone name is read from
    its target. A collection (e.g. Velociraptor) follows the link and stores
    only the TZif bytes, so the name is recovered by matching those bytes
    against the collected zoneinfo tree when it is present. The POSIX rule
    from the TZif footer (e.g. EST5EDT,M3.2.0,M11.1.0) is always emitted as
    ``timezone_rule``; it is read from the file, not inferred.
    """

    __namespace__ = "localtime"

    PATHS = [
        "etc/localtime",
        "private/var/db/timezone/localtime",
    ]

    ZONEINFO_DIRS = (
        "usr/share/zoneinfo.default",
        "usr/share/zoneinfo",
        "private/var/db/timezone/zoneinfo",
    )
    # picks the canonical Area/Location name out of byte-identical aliases
    # (America/New_York, US/Eastern, EST5EDT and posixrules all match)
    IANA_AREAS = (
        "Africa", "America", "Antarctica", "Arctic", "Asia",
        "Atlantic", "Australia", "Europe", "Indian", "Pacific",
    )

    def __init__(self, target):
        super().__init__(target)
        self._tz_paths = []
        for p in self.PATHS:
            path = self.target.fs.path("/").joinpath(p)
            if path.exists():
                self._tz_paths.append(path)

    def check_compatible(self) -> None:
        if not self._tz_paths:
            raise UnsupportedPluginError("No localtime files found")

    @export(record=LocalTimeRecord)
    def info(self) -> Iterator[LocalTimeRecord]:
        """Report the configured timezone from localtime symlink."""
        for tz_path in self._tz_paths:
            try:
                timezone = ""
                try:
                    if tz_path.is_symlink():
                        link_target = str(tz_path.readlink())
                        timezone = link_target.split("zoneinfo/", 1)[1] if "zoneinfo/" in link_target else link_target
                except Exception:
                    pass

                data = b""
                try:
                    with tz_path.open("rb") as fh:
                        data = fh.read()
                except Exception:
                    pass

                if not timezone and data:
                    timezone = self._match_zone_by_content(data)

                yield LocalTimeRecord(
                    timezone=timezone,
                    timezone_rule=self._tzif_rule(data),
                    source=tz_path,
                    _target=self.target,
                )
            except Exception as e:
                self.target.log.warning("Error reading localtime %s: %s", tz_path, e)

    @staticmethod
    def _tzif_rule(data):
        """Return the POSIX TZ rule from a TZif v2+ footer, or "" for v1 / non-TZif."""
        if not data.startswith(b"TZif") or data[4:5] == b"\x00":
            return ""
        nl = data.rfind(b"\n")
        if nl <= 0:
            return ""
        start = data.rfind(b"\n", 0, nl)
        if start < 0:
            return ""
        return data[start + 1 : nl].decode("ascii", "ignore").strip()

    def _match_zone_by_content(self, data):
        """Name the zone by finding the zoneinfo file localtime is a byte copy of."""
        want = hashlib.sha256(data).hexdigest()
        matches = []
        for base in self.ZONEINFO_DIRS:
            root = self.target.fs.path("/").joinpath(base)
            try:
                if not root.exists():
                    continue
                for entry in root.rglob("*"):
                    try:
                        if entry.is_dir():
                            continue
                        with entry.open("rb") as fh:
                            if hashlib.sha256(fh.read()).hexdigest() == want:
                                matches.append(str(entry).split(base, 1)[-1].strip("/"))
                    except Exception:
                        continue
            except Exception:
                continue
            if matches:
                break
        for name in sorted(matches):
            if name.split("/", 1)[0] in self.IANA_AREAS:
                return name
        return sorted(matches)[0] if matches else ""
