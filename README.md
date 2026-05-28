# Dissect macOS Forensics Plugins

Custom plugins for the [Dissect](https://github.com/fox-it/dissect) forensics framework targeting macOS artefacts. Paired with the [Velociraptor macOS collector](https://github.com/MrJayTechie/MacOS-Velociraptor-Collectors).

**Tested on:** macOS 15 (Sequoia) and macOS 16 (Tahoe) — Apple Silicon and Intel.
**Coverage:** 83 plugin modules, 232 exported functions.

## Quick Start

```bash
pip install dissect.target

# Optional: alias target-query
alias target-query='python3 -m dissect.target.tools.query'

# Live system
target-query --plugin-path Plugins -f <namespace.function> local -j

# Velociraptor collection (extract first)
bsdtar -xf Collection-*.zip -C ~/dissect-collections/
target-query --plugin-path Plugins \
             -f <namespace.function> \
             ~/dissect-collections/uploads/auto -j
```

**Flags:** `-j` JSON · `-s` structured (CSV-ish) · drop both for human-readable.
Root-owned artefacts may need `sudo`.

---

## Plugin List

### Shell & User Activity

| Function | Description |
|----------|-------------|
| `shellhistory.entries` | Parse shell history files (zsh extended format and plain commands) |
| `knowledgec.app_usage` | Parse application usage events from knowledgeC.db |
| `knowledgec.web_usage` | Parse web browsing events from knowledgeC.db |
| `knowledgec.media_usage` | Parse media playback events from knowledgeC.db |
| `knowledgec.notifications` | Parse notification events from knowledgeC.db |
| `knowledgec.intents` | Parse app intent events from knowledgeC.db |
| `knowledgec.display` | Parse display backlight state from knowledgeC.db |
| `knowledgec.bluetooth` | Parse bluetooth connection events from knowledgeC.db |
| `knowledgec.discoverability` | Parse discoverability signal events from knowledgeC.db |
| `knowledgec.sync_peers` | Parse synced device peers from knowledgeC.db |
| `knowledgec.sources` | Parse registered event sources from knowledgeC.db |
| `knowledgec.histograms` | Parse activity level histograms from knowledgeC.db |
| `knowledgec.custom_metadata` | Parse custom metadata entries from knowledgeC.db |
| `screentime.usage` | Parse ScreenTime app usage data |
| `screentime.blocks` | Parse ScreenTime usage blocks |

### Biome (iOS/macOS Telemetry)

| Function | Description |
|----------|-------------|
| `biome.streams` | List all available Biome streams with segment counts and sizes |
| `biome.all` | Parse all Biome streams into timestamped records with extracted strings |
| `biome.app_in_focus` | App.InFocus — which app had focus and when |
| `biome.app_intents` | App.Intent — app intents (messages, media, calls, etc.) |
| `biome.now_playing` | Media.NowPlaying — media playback events |
| `biome.web_usage` | App.WebUsage — web browsing events tracked by the OS |
| `biome.app_activity` | App.Activity — application activity events |
| `biome.media_usage` | App.MediaUsage — media usage events |
| `biome.wifi_connections` | _DKEvent.Wifi.Connection — WiFi connection/disconnection events |
| `biome.bluetooth` | Bluetooth events |
| `biome.wifi` | Device.Wireless.WiFi — WiFi state events |
| `biome.display` | Device.Display.Backlight — display on/off state |
| `biome.low_power_mode` | Device.Power.LowPowerMode — low power mode state changes |
| `biome.location` | Location.Semantic — semantic location data |
| `biome.notifications` | Notification.Usage — notification events |
| `biome.safari_navigations` | Safari.Navigations — Safari URL navigations |
| `biome.safari_page_load` | Safari.PageLoad — Safari page load events |
| `biome.safari_history` | _DKEvent.Safari.History — Safari history events (DuetKnowledge) |
| `biome.screentime` | ScreenTime.AppUsage — Screen Time app usage data |
| `biome.user_focus` | UserFocus.InferredMode — inferred Focus/Do Not Disturb mode |
| `biome.user_focus_computed` | UserFocus.ComputedMode — computed Focus mode |
| `biome.activity_level` | _DKEvent.Activity.Level — device activity level |
| `biome.dk_low_power` | _DKEvent.Device.LowPowerMode — DuetKnowledge low-power events |
| `biome.third_party_apps` | ProactiveHarvesting.ThirdPartyApp — third-party app usage |
| `biome.safari_pageview` | ProactiveHarvesting.Safari.PageView — Safari page views |
| `biome.harvested_messages` | ProactiveHarvesting.Messages — harvested message metadata |
| `biome.harvested_notes` | ProactiveHarvesting.Notes — harvested notes metadata |
| `biome.harvested_notifications` | ProactiveHarvesting.Notifications — harvested notification data |
| `biome.harvested_mail` | ProactiveHarvesting.Mail — harvested mail metadata |
| `biome.intelligence_donations` | IntelligenceEngine.Interaction.Donation — Siri intelligence donations |
| `biome.siri_execution` | Siri.Execution — Siri command executions |
| `biome.messages_read` | Messages.Read — message read events |
| `biome.carplay` | CarPlay.Connected — CarPlay connection events |
| `biome.screen_sharing` | Screen.Sharing — screen sharing sessions |
| `biome.apple_intelligence_tasks` | Lighthouse.Ledger.* — Apple Intelligence task ledger (Tahoe+) |
| `biome.system_settings_search` | SystemSettings.SearchTerms — settings search history (Tahoe+) |
| `biome.ai_model_catalog` | AI model asset delivery and catalog subscription streams |
| `biome.generative_functions` | GenerativeModels.GenerativeFunctions.Instrumentation |
| `biome.siri_remembers` | Siri.Remembers.* — Siri's persistent memory |
| `biome.siri_self_events` | Siri.SELFProcessedEvent — Siri Self-Experience events |
| `biome.siri_metrics` | Siri.Metrics.* / Siri.ODDI.* — Siri performance metrics |
| `biome.llm_cache` | LLMCache.CacheManagerTelemetry — LLM cache telemetry (Tahoe+) |
| `biome.media_analysis` | MediaAnalysis.* — Photos/Camera on-device analysis |
| `biome.safari_extra` | Tahoe-era Safari signals not covered by other Safari streams |
| `biome.messages_shared` | Messages.SharedWithYou.Feedback — Shared with You interactions |
| `biome.intelligence_views_updated` | IntelligencePlatform.Views.Updated emissions |
| `biome.entities` | IntelligencePlatform.Entity databases |
| `biome.entity_changes` | *Changes audit tables in IntelligencePlatform |
| `biome.recent_apps` | Games.RecentlyPlayed database |
| `biome.cloud_sync` | Biome sync.db SyncSessionLog table |

### Communication

| Function | Description |
|----------|-------------|
| `imessage.messages` | iMessage/SMS messages with sender handle information |
| `imessage.chats` | iMessage/SMS chat entries |
| `imessage.attachments` | iMessage/SMS attachments |
| `facetime.links` | FaceTime conversation links |
| `facetime.handles` | FaceTime handles (phone numbers/identifiers) |
| `callhistory.calls` | Call records from CallHistory.storedata |
| `interactions.entries` | Communication interactions from interactionC.db |
| `interactions.contacts` | Contact entries from interactionC.db |
| `addressbook.contacts` | Contacts from AddressBook ZABCDRECORD table |
| `addressbook.emails` | Email addresses joined with contact names |
| `addressbook.phones` | Phone numbers joined with contact names |
| `mail.messages` | One record per indexed message with sender/subject/recipients |
| `mail.attachments` | One record per indexed attachment (name + MIME + size) |
| `ids.handles` | One record per IDS short-handle (per-service Apple-ID identity) |

### Browsers

| Function | Description |
|----------|-------------|
| `safari.history` | Safari browsing history from History.db |
| `safari.bookmarks` | Safari bookmarks from Bookmarks.plist |
| `safari.downloads` | Safari download history from Downloads.plist |
| `safari.topsites` | Safari frequently visited sites from TopSites.plist |
| `firefox.history` | Browsing history from Firefox places.sqlite |
| `firefox.cookies` | Cookies from Firefox cookies.sqlite |
| `firefox.downloads` | Download history from Firefox places.sqlite |
| `firefox.bookmarks` | Bookmarks from Firefox places.sqlite |
| `firefox.logins` | Saved login entries from Firefox logins.json (no passwords) |
| `firefox.formhistory` | Form autofill history from Firefox formhistory.sqlite |
| `firefox.permissions` | Site permissions from Firefox permissions.sqlite |
| `firefox.searches` | Search terms from Firefox places.sqlite |
| `chromium.history` | Browsing history from Chromium-based browsers |
| `chromium.cookies` | Cookies from Chromium-based browsers |
| `chromium.downloads` | Download history from Chromium-based browsers |
| `chromium.bookmarks` | Bookmarks from Chromium-based browsers |
| `chromium.logins` | Saved login entries from Chromium-based browsers (no passwords) |
| `chromium.searches` | Keyword search terms from Chromium-based browsers |
| `chromium.topsites` | Top sites from Chromium-based browsers |
| `cookies.entries` | Parse cookies from .binarycookies files |
| `cookies.hsts` | Parse HSTS (HTTP Strict Transport Security) entries |

### System Info

| Function | Description |
|----------|-------------|
| `osinfo.version` | Parse SystemVersion.plist for OS version information |
| `osinfo.install_date` | Install date from .AppleSetupDone file modification time |
| `users.entries` | Local user account plists from dslocal |
| `accounts.entries` | Configured Internet Accounts |
| `accounts.types` | Registered account types |
| `accounts.properties` | Account properties (key-value pairs per account) |
| `accounts.credentials` | Credential items (service names, expiration — no secrets) |
| `localtime.info` | Configured timezone from localtime symlink |
| `hosts.entries` | /etc/hosts entries |
| `dhcp.leases` | DHCP lease files from /private/var/db/dhcpclient/leases/ |
| `softwareupdate.appstore_installs` | App Store install history from storeSystem.db |
| `softwareupdate.appstore_updates` | App Store update history from storeSystem.db |
| `softwareupdate.receipts` | Software installation receipts from /var/db/receipts/ |
| `softwareupdate.config` | macOS Software Update configuration |

### Persistence & Autostart

| Function | Description |
|----------|-------------|
| `autostart.launch_items` | All Launch Agents and Daemons combined |
| `autostart.launch_agents` | Launch Agents (user, system, and Apple) |
| `autostart.launch_daemons` | Launch Daemons (system and Apple) |
| `autostart.kernel_extensions` | Installed Kernel Extensions (kexts) |
| `autostart.system_extensions` | Installed System Extensions from db.plist |
| `autostart.cronjobs` | Cron jobs from /var/at/tabs/ and /etc/crontab |
| `autostart.periodic` | Periodic scripts (daily/weekly/monthly) |
| `autostart.startup_items` | Legacy StartupItems |
| `autostart.startup_files` | /private/etc/launchd.conf and /private/etc/rc.common |
| `kext.installed` | Installed kernel extensions from Info.plist across all kext locations |
| `kext.load_history` | Kext load history from the legacy KextPolicy database |
| `kext.policy` | Kext approval policies from the legacy KextPolicy database |
| `kext.system_extensions` | System extensions from /Library/SystemExtensions/db.plist |
| `kext.classification` | Kext vendor classifications from KextClassification.plist |

### Security

| Function | Description |
|----------|-------------|
| `firewall.pf_rules` | PF packet filter rules from /etc/pf.conf and anchors |
| `firewall.alf_config` | ALF (Application Level Firewall) global configuration |
| `firewall.alf_apps` | ALF per-application firewall rules |
| `firewall.alf_exceptions` | ALF firewall exceptions and explicit authorizations |
| `firewall.alf_services` | ALF firewall service rules (SSH, file sharing, screen sharing, etc.) |
| `keychain.generic` | Generic password entries from keychains (no secrets extracted) |
| `keychain.internet` | Internet password entries from keychains (no secrets extracted) |
| `keychain.certificates` | Certificate entries from keychains |
| `keychain.systemkey` | SystemKey (System.keychain master key, SIP-protected on live) |
| `sudoers.entries` | Sudoers configuration entries |
| `sudolastrun.entries` | Sudo timestamp files — last sudo usage per user |
| `execpolicy.entries` | Executed binary measurements from the ExecPolicy database |
| `profiles.installed` | Installed configuration profiles |
| `profiles.payloads` | Individual payloads from installed configuration profiles |
| `profiles.settings` | Configuration profile settings plists (key-value pairs) |
| `auth.rules` | One record per authorization right defined in auth.db |
| `tcc.access` | TCC access permissions (grants/denials) from TCC.db |
| `tcc.expired` | Expired TCC permissions from TCC.db |
| `tcc.location_clients` | Location services client authorizations from clients.plist |
| `quarantine.events` | One record per quarantine event (downloads + AirDrop + browser) |

### Filesystem & Forensics

| Function | Description |
|----------|-------------|
| `dsstore.entries` | All .DS_Store entries — files/folders that existed in each directory |
| `dsstore.files` | All .DS_Store files with entry counts and referenced filenames |
| `fsevents.events` | All FSEvents records showing file system activity |
| `docrevisions.files` | Tracked files from the DocumentRevisions database |
| `docrevisions.generations` | Document revision generations (file versions) |
| `trash.files` | Files in the user Trash and volume-level .Trashes |
| `trash.icloud` | Files in the iCloud Drive trash |
| `quicklook.thumbnails` | QuickLook thumbnail cache entries |
| `savedstate.entries` | Apps with saved application state (windows.plist) |
| `terminalstate.files` | Files in Terminal saved state directory |
| `spotlight.applist` | Spotlight applist.dat known applications |
| `spotlightshortcuts.entries` | One record per learned Spotlight shortcut |
| `timemachine.destinations` | One record per configured backup destination |
| `timemachine.config` | Top-level TimeMachine config keys (auto-backup, interval, etc.) |

### Applications & Productivity

| Function | Description |
|----------|-------------|
| `applications.installed` | Installed applications from Info.plist files |
| `installhistory.entries` | Software installation history from InstallHistory.plist |
| `ams.content` | One record per AMS engagement cache entry (App Store / Music / Books / News) |
| `officemru.entries` | Microsoft Office recently opened documents |
| `notes.entries` | All notes with title, snippet, body text, folder, and timestamps |
| `notes.accounts` | Note accounts (iCloud, local, etc.) |
| `notes.attachments` | Note attachments (images, files, etc.) |
| `notes.folders` | Note folders |
| `calendar.events` | One record per CalendarItem (events, tasks, birthdays) |
| `calendar.calendars` | One record per configured calendar (account / source identifier) |
| `calendar.alarms` | One record per scheduled alarm with the linked event summary |
| `reminders.entries` | One record per saved reminder |
| `shortcuts.tools` | One record per shortcut / App Intent in the catalog |
| `wallet.passes` | Wallet passes (boarding passes, tickets, reservations, etc.) |
| `wallet.transactions` | Apple Pay payment transactions |
| `wallet.payment_cards` | Registered Apple Pay payment cards |
| `wallet.pass_types` | Registered pass type identifiers |
| `wallet.pass_details` | Detailed pass fields from .pkpass directories |
| `crashreporter.events` | CrashReporter plists — crash and force-quit timestamps |
| `crashreporter.entries` | CrashReporter Intervals plist — per-app usage and crash statistics |
| `printjobs.entries` | CUPS print job cache entries |
| `launchpad.apps` | Launchpad apps with bundle ID, category, folder, and grid position |
| `launchpad.groups` | Launchpad folders/groups |
| `dockprefs.items` | One record per Dock tile (persistent + recent apps and docs) |
| `photos.assets` | One record per photo / video / screenshot with EXIF + GPS |
| `photos.albums` | One record per user album / smart album / cloud-shared album |
| `photos.persons` | One record per recognised person across the library |
| `linkd.links` | One record per rich-preview-generated URL (timestamp + source bundles) |
| `statuskit.channels` | One record per published Focus channel |
| `statuskit.statuses` | One record per published local status |

### Network & Remote Access

| Function | Description |
|----------|-------------|
| `ssh.known_hosts` | SSH known_hosts files — previously connected hosts |
| `ssh.config` | SSH config files and Host blocks with their settings |
| `ard.access` | Apple Remote Desktop access entries from cliauth and rmdb |
| `ard.config` | Apple Remote Desktop configuration from plist files |
| `msrdc.connections` | Microsoft Remote Desktop connection bookmarks |
| `screensharing.connections` | Screen Sharing connection history |
| `vpnconfig.configs` | One record per configured VPN / NetworkExtension instance |
| `notifications.entries` | Notification entries from usernoted db |
| `notifications.apps` | Registered notification apps from usernoted db |
| `powerlogs.network` | Cumulative network usage per interface from the powerlog database |

### Logs

| Function | Description |
|----------|-------------|
| `logs.list` | List all discovered log files with their sizes |
| `logs.all_raw` | Parse all log files as raw lines |
| `logs.system` | system.log entries in syslog format |
| `logs.user` | User application log files from ~/Library/Logs/ |
| `logs.install` | install.log entries (software installation history) |
| `logs.asl` | All ASL (Apple System Log) binary database files |
| `logs.asl_system` | ASL files from /var/log/asl/ (system-wide ASL logs) |
| `logs.asl_diagnostics` | ASL files from /private/var/log/DiagnosticMessages/ |
| `logs.asl_powermanagement` | ASL files from /var/log/powermanagement/ (sleep/wake events) |
| `logs.audit_classes` | Audit class definitions from /etc/security/audit_class |
| `logs.audit_events` | Audit event definitions from /etc/security/audit_event |
| `powerlogs.app_usage` | Frontmost-application history from the powerlog database |
| `powerlogs.sleep_wake` | Sleep/wake power state events from the powerlog database |

### Cloud & Sync

| Function | Description |
|----------|-------------|
| `icloud.files` | Files in iCloud Drive local storage |
| `icloudacct.accounts` | One record per iCloud account configured (Apple ID + enabled services) |
| `sharedfilelist.favorites` | Finder sidebar favorite items |
| `sharedfilelist.volumes` | Favorite volumes (mounted drives, network shares) |
| `sharedfilelist.recent_apps` | Recently launched applications |
| `sharedfilelist.recent_docs` | Recently opened documents |
| `sharedfilelist.projects` | Finder project/tag items |
| `sharedfilelist.all` | All SharedFileList .sfl3 files |
| `sharepoints.entries` | Sharepoint definitions from dslocal plist files |
| `idevicebackup.info` | iOS backup device information from Info.plist |
| `idevicebackup.files` | Backed-up file list from Manifest.db |

### Device & Config

| Function | Description |
|----------|-------------|
| `preferences.entries` | All preference plists flattened to key-value records |
| `preferences.list` | All preference plist files with their top-level keys |
| `etcfiles.entries` | Common /etc configuration files as raw lines |
| `utmpx.entries` | Binary utmpx login records |
| `lockdown.paired` | One record per paired iOS device — UDID, model, serial, MACs, ECID |
| `sysconfig.wifi_known` | One record per known WiFi network (SSID + BSSID + last-joined) |
| `sysconfig.network_interfaces` | One record per network interface — MAC + type + IOKit path |
| `sysconfig.network_locations` | One record per saved network location (Home/Work/etc) + current pointer |
| `sysconfig.firewall` | One record per top-level Application Firewall setting in alf.plist |
| `ble.devices_seen` | One record per BLE peripheral the Mac has observed (paired or not) |
| `bluetoothpaired.devices` | One record per paired Bluetooth device (timestamps + vendor/product IDs) |
| `homekit.accessories` | One record per paired HomeKit accessory (lights, locks, sensors) |
| `homekit.homes` | One record per HomeKit home (residence the user configured) |
| `homekit.triggers` | One record per automation trigger (time-of-day, location, event) |
| `locationd.clients` | One record per app that has requested Core Location access |
| `wifiintelligence.wifi_events` | WiFi connect/disconnect events from views.db |
| `wifiintelligence.person_interactions` | Person interaction mechanisms from views.db |
| `wifiintelligence.entity_aliases` | Entity aliases from views.db |
| `trial.experiments` | One record per Trial namespace (experiment) the device is enrolled in |

---

## Repository Layout

```
Plugins/   # 83 plugin modules — point --plugin-path here
README.md  # This file
```

For the companion Velociraptor collectors and analyst tooling, see [MacOS-Velociraptor-Collectors](https://github.com/MrJayTechie/MacOS-Velociraptor-Collectors) and [Dissectify](https://github.com/MrJayTechie/Dissectify).
