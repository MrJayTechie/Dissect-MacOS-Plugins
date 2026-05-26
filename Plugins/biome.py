from __future__ import annotations

import struct
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from dissect.target.exceptions import UnsupportedPluginError
from dissect.target.helpers.record import TargetRecordDescriptor
from dissect.target.plugin import Plugin, export

if TYPE_CHECKING:
    from collections.abc import Iterator


COCOA_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


def _cocoa_ts(value):
    if value:
        try:
            return COCOA_EPOCH + timedelta(seconds=value)
        except (OSError, OverflowError, ValueError):
            return COCOA_EPOCH
    return COCOA_EPOCH


def _extract_protobuf_strings(data, start, end):
    """Extract length-delimited strings and typed numerics from a protobuf
    fragment. Streams that carry only numeric payloads (display brightness,
    WiFi RSSI, bluetooth link quality) produce no strings under a text-only
    extractor, which is why biome.display / biome.wifi used to emit rows
    with nothing but a timestamp. Surfacing varints and floats alongside
    strings keeps those streams useful without per-stream protobuf schemas.
    """
    strings = []
    numerics = []
    pos = start
    while pos < end - 2:
        tag = data[pos]
        wire = tag & 0x07
        field_num = tag >> 3
        # wire type 2 — length-delimited (strings, sub-messages)
        if wire == 2 and tag > 0x08:
            slen = data[pos + 1]
            if 2 < slen < 200 and pos + 2 + slen <= end:
                try:
                    s = data[pos + 2 : pos + 2 + slen].decode("utf-8")
                    if s.isprintable():
                        strings.append((field_num, s))
                except UnicodeDecodeError:
                    pass
        # wire type 0 — varint (booleans, ints, enum codes)
        elif wire == 0 and tag > 0x08:
            v, new_pos = _read_varint(data, pos + 1, end)
            if v is not None and new_pos - pos <= 10:
                # Skip very large values — usually bad alignment
                if 0 <= v < 1 << 32:
                    numerics.append((field_num, f"i{v}"))
                pos = new_pos - 1  # -1 because outer loop does pos += 1
        # wire type 5 — fixed32 (floats, int32)
        elif wire == 5 and tag > 0x08 and pos + 5 <= end:
            try:
                f = struct.unpack("<f", data[pos + 1 : pos + 5])[0]
                if -1e9 < f < 1e9:
                    numerics.append((field_num, f"f{f:.4g}"))
            except struct.error:
                pass
        pos += 1
    return strings + numerics


def _read_varint(data, pos, end):
    """Decode a protobuf varint starting at pos. Return (value, new_pos)
    or (None, pos) if malformed."""
    shift = 0
    result = 0
    while pos < end and shift < 64:
        b = data[pos]
        result |= (b & 0x7F) << shift
        pos += 1
        if not (b & 0x80):
            return result, pos
        shift += 7
    return None, pos


# Streams whose protobuf payloads are dominated by sensor numerics
# (brightness deltas, RSSI, link quality). The numeric fallback in
# _extract_protobuf_strings turns these into unreadable junk like
# "f1.401e-45 | f-1.01e+05 | i1 …" — those bytes are alignment artifacts,
# not real values. For these streams, drop numerics and emit only real
# strings (UUIDs, bundle ids) plus the timestamp.
_NUMERIC_NOISE_STREAMS = frozenset({
    "Device.Display.Backlight",
    "Device.Wireless.WiFi",
    "Device.Wireless.Bluetooth",
    "Device.Wireless.BluetoothNearbyDevice",
    "Notification.Usage",
    "UserFocus.InferredMode",
    "UserFocus.ComputedMode",
    # Tahoe streams whose protobuf payloads carry sensor numerics next to
    # the useful strings — drop the alignment-artifact floats so analysts
    # see UUIDs + bundle ids + task identifiers cleanly.
    "Lighthouse.Ledger.TaskCustomEvent",
    "Lighthouse.Ledger.TaskStatus",
    "Lighthouse.Ledger.TaskTelemetry",
    "Lighthouse.Ledger.TaskError",
    "Lighthouse.Ledger.TrialdEvent",
    "Lighthouse.Ledger.LighthousePluginEvent",
    "Lighthouse.Ledger.DeviceTelemetry",
    "Lighthouse.Ledger.DediscoPrivacyEvent",
    "Lighthouse.Ledger.MlruntimedEvent",
    "GenerativeModels.GenerativeFunctions.Instrumentation",
    "SystemSettings.SearchTerms",
})


def _is_numeric_token(s):
    """A token from _extract_protobuf_strings's numeric fallback starts
    with 'f' or 'i' followed by a digit, '-' or '+'."""
    return len(s) >= 2 and s[0] in ("f", "i") and (s[1].isdigit() or s[1] in "-+")


def _join_strings(strings, stream_name):
    """Join extracted tokens, dropping numeric-junk for streams known to
    carry only sensor numerics in their payload."""
    if stream_name in _NUMERIC_NOISE_STREAMS:
        tokens = [s for _, s in strings if not _is_numeric_token(s)]
    else:
        tokens = [s for _, s in strings]
    return " | ".join(tokens)


def _parse_segb_records(data):
    """Parse SEGB (Segmented Binary) file and yield (timestamp, strings) tuples.

    Older Biome streams encoded timestamps as float64 Cocoa seconds in a
    protobuf fixed64 field. macOS 26 (Tahoe) streams (Lighthouse.Ledger.*,
    Siri.Remembers.*, AppleIntelligence.Reporting.*, SystemSettings.*) often
    use int64 Cocoa-nanosecond timestamps and place them under
    field_num=1 (tag byte 0x09) which the legacy scan rejected.

    Strategy: scan every position; at each candidate, try both decodings
    (float64-seconds, int64-nanoseconds) and only accept values within the
    plausible Cocoa window. Dedupe nearby hits so we don't emit a record
    per byte of the same timestamp.

    Fallback: very sparse SEGB segments (e.g. ``SystemSettings.SearchTerms``)
    contain a single header timestamp at bytes 0x08..0x10 and no per-record
    timestamps. When the body scan finds nothing, we emit one synthesized
    record per segment using the header timestamp + every printable string.
    """
    if len(data) < 0x30 or data[:4] != b"SEGB":
        return

    # Plausible Cocoa-epoch window: 2023..2028 in seconds and ns.
    LO_S, HI_S = 700_000_000, 900_000_000
    LO_NS, HI_NS = LO_S * 1_000_000_000, HI_S * 1_000_000_000

    pos = 0x20
    last_ts_pos = -100  # deduplicate nearby timestamps
    body_hits = 0

    while pos < len(data) - 9:
        tag = data[pos]
        wire = tag & 0x07
        # Accept any fixed64-tagged value (wire type 1). Don't require
        # tag > 0x08 — Tahoe streams put the timestamp in field_num=1
        # (tag byte 0x09) where the legacy scan rejected.
        if wire != 1 or tag == 0:
            pos += 1
            continue
        if pos - last_ts_pos <= 8:
            pos += 1
            continue

        try:
            d_val = struct.unpack("<d", data[pos + 1 : pos + 9])[0]
            i_val = struct.unpack("<q", data[pos + 1 : pos + 9])[0]
        except struct.error:
            pos += 1
            continue

        ts = None
        if LO_S < d_val < HI_S:
            ts = _cocoa_ts(d_val)
        elif LO_NS < i_val < HI_NS:
            ts = _cocoa_ts(i_val / 1_000_000_000)

        if ts is not None:
            search_start = max(0x20, pos - 50)
            search_end = min(len(data), pos + 250)
            strings = _extract_protobuf_strings(data, search_start, search_end)
            last_ts_pos = pos
            body_hits += 1
            yield ts, strings

        pos += 1

    # Header-timestamp fallback for sparse streams. The SEGB header carries
    # a float64 Cocoa-seconds value at bytes 0x08..0x10 representing the
    # segment's creation time.
    if body_hits == 0:
        try:
            h_val = struct.unpack("<d", data[0x08:0x10])[0]
        except struct.error:
            return
        if LO_S < h_val < HI_S:
            ts = _cocoa_ts(h_val)
            strings = _extract_protobuf_strings(data, 0x20, len(data))
            if strings:
                yield ts, strings


# ── Record Descriptors ───────────────────────────────────────────────────

BiomeStreamRecord = TargetRecordDescriptor(
    "macos/biome/stream",
    [
        ("datetime", "ts"),
        ("string", "stream_name"),
        ("string", "strings"),
        ("string", "segment"),
        ("string", "data_source"),
        ("path", "source"),
    ],
)

BiomeStreamListRecord = TargetRecordDescriptor(
    "macos/biome/stream_list",
    [
        ("string", "stream_name"),
        ("varint", "segment_count"),
        ("varint", "total_size_bytes"),
        ("string", "data_source"),
        ("path", "source"),
    ],
)

BiomeAppInFocusRecord = TargetRecordDescriptor(
    "macos/biome/app_in_focus",
    [
        ("datetime", "ts"),
        ("string", "bundle_id"),
        ("string", "app_version"),
        ("string", "segment"),
        ("path", "source"),
    ],
)

BiomeAppIntentRecord = TargetRecordDescriptor(
    "macos/biome/app_intent",
    [
        ("datetime", "ts"),
        ("string", "bundle_id"),
        ("string", "intent_class"),
        ("string", "intent_verb"),
        ("string", "segment"),
        ("path", "source"),
    ],
)

BiomeGenericRecord = TargetRecordDescriptor(
    "macos/biome/generic",
    [
        ("datetime", "ts"),
        ("string", "stream_name"),
        ("string", "strings"),
        ("string", "segment"),
        ("path", "source"),
    ],
)

# Mapping of stream names to their namespace function names
DEDICATED_STREAMS = [
    "App.InFocus",
    "App.Intent",
    "App.WebUsage",
    "App.Activity",
    "App.MediaUsage",
    "Media.NowPlaying",
    "Notification.Usage",
    "_DKEvent.Wifi.Connection",
    "Device.Wireless.Bluetooth",
    "Device.Wireless.WiFi",
    "Device.Display.Backlight",
    "Device.Power.LowPowerMode",
    "Location.Semantic",
    "Safari.Navigations",
    "Safari.PageLoad",
    "ScreenTime.AppUsage",
    "UserFocus.InferredMode",
    "UserFocus.ComputedMode",
    "ProactiveHarvesting.ThirdPartyApp",
    "ProactiveHarvesting.Safari.PageView",
    "ProactiveHarvesting.Messages",
    "ProactiveHarvesting.Notes",
    "ProactiveHarvesting.Notifications",
    "ProactiveHarvesting.Mail",
    "IntelligenceEngine.Interaction.Donation",
    "_DKEvent.Safari.History",
    "_DKEvent.Activity.Level",
    "_DKEvent.Device.LowPowerMode",
    "Siri.Execution",
    "Messages.Read",
    "CarPlay.Connected",
    "Screen.Sharing",
]


class MacOSBiomePlugin(Plugin):
    """Plugin to parse macOS Biome data stores.

    Biome is Apple's successor to KnowledgeC, storing pattern-of-life
    data in SEGB (Segmented Binary) protobuf files.

    Locations:
    - ~/Library/Biome/ (user biome data)
    - /private/var/db/biome/ (system biome data)
    """

    __namespace__ = "biome"

    BIOME_GLOBS = [
        "Users/*/Library/Biome/streams/restricted/*/local/*",
        "private/var/db/biome/streams/restricted/*/local/*",
    ]

    def __init__(self, target):
        super().__init__(target)
        self._stream_files = {}
        for pattern in self.BIOME_GLOBS:
            for path in self.target.fs.path("/").glob(pattern):
                if not path.is_file() or path.name == "tombstone" or "/tombstone/" in str(path):
                    continue
                parts = str(path).split("/")
                try:
                    restricted_idx = parts.index("restricted")
                    stream_name = parts[restricted_idx + 1]
                except (ValueError, IndexError):
                    continue
                data_source = "user" if "/Users/" in str(path) else "system"
                self._stream_files.setdefault(stream_name, []).append((path, data_source))

    def check_compatible(self) -> None:
        if not self._stream_files:
            raise UnsupportedPluginError("No Biome data found")

    def _read_segb(self, path):
        with path.open("rb") as fh:
            return fh.read()

    def _iter_stream(self, stream_name):
        for path, data_source in self._stream_files.get(stream_name, []):
            try:
                data = self._read_segb(path)
                yield path, data_source, data
            except Exception as e:
                self.target.log.warning("Error reading biome stream %s: %s", path, e)

    def _parse_stream_generic(self, stream_name):
        """Generic parser that yields BiomeGenericRecord for any stream."""
        for path, _data_source, data in self._iter_stream(stream_name):
            try:
                for ts, strings in _parse_segb_records(data):
                    str_vals = _join_strings(strings, stream_name)
                    yield BiomeGenericRecord(
                        ts=ts,
                        stream_name=stream_name,
                        strings=str_vals,
                        segment=path.name,
                        source=path,
                        _target=self.target,
                    )
            except Exception as e:
                self.target.log.warning("Error parsing biome stream %s: %s", path, e)

    # ── List all streams ─────────────────────────────────────────────────

    @export(record=BiomeStreamListRecord)
    def streams(self) -> Iterator[BiomeStreamListRecord]:
        """List all available Biome streams with segment counts and sizes."""
        for stream_name, files in sorted(self._stream_files.items()):
            total_size = 0
            for path, _data_source in files:
                try:
                    stat = path.stat()
                    total_size += stat.st_size if hasattr(stat, "st_size") else 0
                except Exception:
                    pass
            yield BiomeStreamListRecord(
                stream_name=stream_name,
                segment_count=len(files),
                total_size_bytes=total_size,
                data_source=files[0][1],
                source=files[0][0],
                _target=self.target,
            )

    # ── All streams combined ─────────────────────────────────────────────

    @export(record=BiomeStreamRecord)
    def all(self) -> Iterator[BiomeStreamRecord]:
        """Parse all Biome streams into timestamped records with extracted strings."""
        for stream_name in sorted(self._stream_files):
            for path, data_source, data in self._iter_stream(stream_name):
                try:
                    for ts, strings in _parse_segb_records(data):
                        str_vals = _join_strings(strings, stream_name)
                        yield BiomeStreamRecord(
                            ts=ts,
                            stream_name=stream_name,
                            strings=str_vals,
                            segment=path.name,
                            data_source=data_source,
                            source=path,
                            _target=self.target,
                        )
                except Exception as e:
                    self.target.log.warning("Error parsing biome stream %s: %s", path, e)

    # ── App In Focus ─────────────────────────────────────────────────────

    @export(record=BiomeAppInFocusRecord)
    def app_in_focus(self) -> Iterator[BiomeAppInFocusRecord]:
        """Parse App.InFocus — which app had focus and when."""
        for path, _data_source, data in self._iter_stream("App.InFocus"):
            try:
                for ts, strings in _parse_segb_records(data):
                    str_dict = dict(strings)
                    bundle_id = str_dict.get(6, "")
                    version = str_dict.get(9, "")
                    if bundle_id:
                        yield BiomeAppInFocusRecord(
                            ts=ts,
                            bundle_id=bundle_id,
                            app_version=version,
                            segment=path.name,
                            source=path,
                            _target=self.target,
                        )
            except Exception as e:
                self.target.log.warning("Error parsing App.InFocus: %s", e)

    # ── App Intents ──────────────────────────────────────────────────────

    @export(record=BiomeAppIntentRecord)
    def app_intents(self) -> Iterator[BiomeAppIntentRecord]:
        """Parse App.Intent — app intents (messages, media, calls, etc.)."""
        for path, _data_source, data in self._iter_stream("App.Intent"):
            try:
                for ts, strings in _parse_segb_records(data):
                    str_vals = [val for _, val in strings]
                    bundle_id = intent_class = intent_verb = ""
                    for val in str_vals:
                        if "." in val and not val.startswith("IN") and not val.startswith("Send"):
                            bundle_id = val
                        elif val.startswith("IN") or val.endswith("Intent"):
                            intent_class = val
                        elif val[0].isupper() and len(val) < 30 and "." not in val:
                            intent_verb = val
                    yield BiomeAppIntentRecord(
                        ts=ts,
                        bundle_id=bundle_id,
                        intent_class=intent_class,
                        intent_verb=intent_verb,
                        segment=path.name,
                        source=path,
                        _target=self.target,
                    )
            except Exception as e:
                self.target.log.warning("Error parsing App.Intent: %s", e)

    # ── Dedicated stream functions (generic record) ──────────────────────

    @export(record=BiomeGenericRecord)
    def now_playing(self) -> Iterator[BiomeGenericRecord]:
        """Parse Media.NowPlaying — media playback events."""
        yield from self._parse_stream_generic("Media.NowPlaying")

    @export(record=BiomeGenericRecord)
    def web_usage(self) -> Iterator[BiomeGenericRecord]:
        """Parse App.WebUsage — web browsing events tracked by the OS."""
        yield from self._parse_stream_generic("App.WebUsage")

    @export(record=BiomeGenericRecord)
    def app_activity(self) -> Iterator[BiomeGenericRecord]:
        """Parse App.Activity — application activity events."""
        yield from self._parse_stream_generic("App.Activity")

    @export(record=BiomeGenericRecord)
    def media_usage(self) -> Iterator[BiomeGenericRecord]:
        """Parse App.MediaUsage — media usage events."""
        yield from self._parse_stream_generic("App.MediaUsage")

    @export(record=BiomeGenericRecord)
    def wifi_connections(self) -> Iterator[BiomeGenericRecord]:
        """Parse _DKEvent.Wifi.Connection — WiFi connection/disconnection events."""
        yield from self._parse_stream_generic("_DKEvent.Wifi.Connection")

    @export(record=BiomeGenericRecord)
    def bluetooth(self) -> Iterator[BiomeGenericRecord]:
        """Parse Bluetooth events. Reads both ``Device.Wireless.Bluetooth``
        (pre-Tahoe) and ``Device.Wireless.BluetoothNearbyDevice`` (Tahoe+) —
        Apple renamed the stream in macOS 26."""
        for stream in (
            "Device.Wireless.Bluetooth",
            "Device.Wireless.BluetoothNearbyDevice",
        ):
            yield from self._parse_stream_generic(stream)

    @export(record=BiomeGenericRecord)
    def wifi(self) -> Iterator[BiomeGenericRecord]:
        """Parse Device.Wireless.WiFi — WiFi state events."""
        yield from self._parse_stream_generic("Device.Wireless.WiFi")

    @export(record=BiomeGenericRecord)
    def display(self) -> Iterator[BiomeGenericRecord]:
        """Parse Device.Display.Backlight — display on/off state."""
        yield from self._parse_stream_generic("Device.Display.Backlight")

    @export(record=BiomeGenericRecord)
    def low_power_mode(self) -> Iterator[BiomeGenericRecord]:
        """Parse Device.Power.LowPowerMode — low power mode state changes."""
        yield from self._parse_stream_generic("Device.Power.LowPowerMode")

    @export(record=BiomeGenericRecord)
    def location(self) -> Iterator[BiomeGenericRecord]:
        """Parse Location.Semantic — semantic location data."""
        yield from self._parse_stream_generic("Location.Semantic")

    @export(record=BiomeGenericRecord)
    def notifications(self) -> Iterator[BiomeGenericRecord]:
        """Parse Notification.Usage — notification events."""
        yield from self._parse_stream_generic("Notification.Usage")

    @export(record=BiomeGenericRecord)
    def safari_navigations(self) -> Iterator[BiomeGenericRecord]:
        """Parse Safari.Navigations — Safari URL navigations."""
        yield from self._parse_stream_generic("Safari.Navigations")

    @export(record=BiomeGenericRecord)
    def safari_page_load(self) -> Iterator[BiomeGenericRecord]:
        """Parse Safari.PageLoad — Safari page load events."""
        yield from self._parse_stream_generic("Safari.PageLoad")

    @export(record=BiomeGenericRecord)
    def safari_history(self) -> Iterator[BiomeGenericRecord]:
        """Parse _DKEvent.Safari.History — Safari history events (DuetKnowledge)."""
        yield from self._parse_stream_generic("_DKEvent.Safari.History")

    @export(record=BiomeGenericRecord)
    def screentime(self) -> Iterator[BiomeGenericRecord]:
        """Parse ScreenTime.AppUsage — Screen Time app usage data."""
        yield from self._parse_stream_generic("ScreenTime.AppUsage")

    @export(record=BiomeGenericRecord)
    def user_focus(self) -> Iterator[BiomeGenericRecord]:
        """Parse UserFocus.InferredMode — inferred Focus/Do Not Disturb mode."""
        yield from self._parse_stream_generic("UserFocus.InferredMode")

    @export(record=BiomeGenericRecord)
    def user_focus_computed(self) -> Iterator[BiomeGenericRecord]:
        """Parse UserFocus.ComputedMode — computed Focus mode."""
        yield from self._parse_stream_generic("UserFocus.ComputedMode")

    @export(record=BiomeGenericRecord)
    def activity_level(self) -> Iterator[BiomeGenericRecord]:
        """Parse _DKEvent.Activity.Level — device activity level."""
        yield from self._parse_stream_generic("_DKEvent.Activity.Level")

    @export(record=BiomeGenericRecord)
    def dk_low_power(self) -> Iterator[BiomeGenericRecord]:
        """Parse _DKEvent.Device.LowPowerMode — DuetKnowledge low power events."""
        yield from self._parse_stream_generic("_DKEvent.Device.LowPowerMode")

    @export(record=BiomeGenericRecord)
    def third_party_apps(self) -> Iterator[BiomeGenericRecord]:
        """Parse ProactiveHarvesting.ThirdPartyApp — third-party app usage."""
        yield from self._parse_stream_generic("ProactiveHarvesting.ThirdPartyApp")

    @export(record=BiomeGenericRecord)
    def safari_pageview(self) -> Iterator[BiomeGenericRecord]:
        """Parse ProactiveHarvesting.Safari.PageView — Safari page views."""
        yield from self._parse_stream_generic("ProactiveHarvesting.Safari.PageView")

    @export(record=BiomeGenericRecord)
    def harvested_messages(self) -> Iterator[BiomeGenericRecord]:
        """Parse ProactiveHarvesting.Messages — harvested message metadata."""
        yield from self._parse_stream_generic("ProactiveHarvesting.Messages")

    @export(record=BiomeGenericRecord)
    def harvested_notes(self) -> Iterator[BiomeGenericRecord]:
        """Parse ProactiveHarvesting.Notes — harvested notes metadata."""
        yield from self._parse_stream_generic("ProactiveHarvesting.Notes")

    @export(record=BiomeGenericRecord)
    def harvested_notifications(self) -> Iterator[BiomeGenericRecord]:
        """Parse ProactiveHarvesting.Notifications — harvested notification data."""
        yield from self._parse_stream_generic("ProactiveHarvesting.Notifications")

    @export(record=BiomeGenericRecord)
    def harvested_mail(self) -> Iterator[BiomeGenericRecord]:
        """Parse ProactiveHarvesting.Mail — harvested mail metadata."""
        yield from self._parse_stream_generic("ProactiveHarvesting.Mail")

    @export(record=BiomeGenericRecord)
    def intelligence_donations(self) -> Iterator[BiomeGenericRecord]:
        """Parse IntelligenceEngine.Interaction.Donation — Siri intelligence donations."""
        yield from self._parse_stream_generic("IntelligenceEngine.Interaction.Donation")

    @export(record=BiomeGenericRecord)
    def siri_execution(self) -> Iterator[BiomeGenericRecord]:
        """Parse Siri.Execution — Siri command executions."""
        yield from self._parse_stream_generic("Siri.Execution")

    @export(record=BiomeGenericRecord)
    def messages_read(self) -> Iterator[BiomeGenericRecord]:
        """Parse Messages.Read — message read events."""
        yield from self._parse_stream_generic("Messages.Read")

    @export(record=BiomeGenericRecord)
    def carplay(self) -> Iterator[BiomeGenericRecord]:
        """Parse CarPlay.Connected — CarPlay connection events."""
        yield from self._parse_stream_generic("CarPlay.Connected")

    @export(record=BiomeGenericRecord)
    def screen_sharing(self) -> Iterator[BiomeGenericRecord]:
        """Parse Screen.Sharing — screen sharing sessions."""
        yield from self._parse_stream_generic("Screen.Sharing")

    # ── Tahoe / Apple Intelligence streams (macOS 26+) ───────────────────

    @export(record=BiomeGenericRecord)
    def apple_intelligence_tasks(self) -> Iterator[BiomeGenericRecord]:
        """Parse the ``Lighthouse.Ledger.*`` stream family — Apple
        Intelligence's task execution ledger introduced in Tahoe.

        Captures, per record: which background AI / Siri task ran, its
        lifecycle phase (start / load / process / upload / finished),
        status transitions (Running / Completed / Not Started), and any
        emitted telemetry or errors. The ``strings`` field carries the
        task identifier (e.g. ``com.apple.aiml.mlpt.FedStats.MLHostPlugin.
        Message-Spam-Detection``) plus the phase/status token.
        """
        for stream in (
            "Lighthouse.Ledger.TaskCustomEvent",
            "Lighthouse.Ledger.TaskStatus",
            "Lighthouse.Ledger.TaskTelemetry",
            "Lighthouse.Ledger.TaskError",
            "Lighthouse.Ledger.TrialdEvent",
            "Lighthouse.Ledger.LighthousePluginEvent",
            "Lighthouse.Ledger.DeviceTelemetry",
            "Lighthouse.Ledger.DediscoPrivacyEvent",
            "Lighthouse.Ledger.MlruntimedEvent",
        ):
            yield from self._parse_stream_generic(stream)

    @export(record=BiomeGenericRecord)
    def system_settings_search(self) -> Iterator[BiomeGenericRecord]:
        """Parse ``SystemSettings.SearchTerms`` — Tahoe+ stream recording
        every query typed into the System Settings search box (e.g. the
        user typing ``shar`` to find Bluetooth Sharing). Forensically
        useful: directly attributes intent to the user."""
        yield from self._parse_stream_generic("SystemSettings.SearchTerms")

    @export(record=BiomeGenericRecord)
    def ai_model_catalog(self) -> Iterator[BiomeGenericRecord]:
        """Parse AI model asset delivery and catalog subscription streams.

        - ``AppleIntelligence.Reporting.AssetDeliveryLog.ModelCatalog`` —
          which Apple foundation models the device fetched, when, for
          which Apple Intelligence use case
          (e.g. ``memoryCreation.AssetCurationOutlier``).
        - ``ModelCatalog.Subscriptions.Decisions`` — model subscription
          decisions (whether each use case opted into a model).
        """
        for stream in (
            "AppleIntelligence.Reporting.AssetDeliveryLog.ModelCatalog",
            "ModelCatalog.Subscriptions.Decisions",
        ):
            yield from self._parse_stream_generic(stream)

    @export(record=BiomeGenericRecord)
    def generative_functions(self) -> Iterator[BiomeGenericRecord]:
        """Parse ``GenerativeModels.GenerativeFunctions.Instrumentation`` —
        Apple Intelligence per-request instrumentation. Records each
        generative-AI invocation: which function (e.g.
        ``summarization.summarizeMailMessage``), source app
        (``com.apple.mail``), source record id, model used, and lifecycle
        events (``executeRequest.begin`` / ``transitionAsset``). High
        forensic value: per-prompt trace of every AI feature the user
        triggered."""
        yield from self._parse_stream_generic(
            "GenerativeModels.GenerativeFunctions.Instrumentation"
        )

    @export(record=BiomeGenericRecord)
    def siri_remembers(self) -> Iterator[BiomeGenericRecord]:
        """Parse the ``Siri.Remembers.*`` stream family — Siri's persistent
        memory of past user interactions. Includes message history,
        interaction history, call history, audio history, and assistant
        suggestions where present."""
        for stream in (
            "Siri.Remembers.MessageHistory",
            "Siri.Remembers.InteractionHistory",
            "Siri.Remembers.CallHistory",
            "Siri.Remembers.AudioHistory",
            "Siri.Remembers.AssistantSuggestions",
        ):
            yield from self._parse_stream_generic(stream)
