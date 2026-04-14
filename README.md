# Dissect Plugin Reference — macOS Triage

## How to Run

Point `target-query` at the extracted Velociraptor output's `uploads/auto` directory:

```bash
target-query --plugin-path <Plugin Path> -f <function> "<path-to-velo-output>/uploads/auto" -j
```

**Flags:**
- `-j` — JSON output
- `-s` — CSV/structured output
- Drop both for human-readable output
- `| head -20` — preview first 20 lines

**Note:** Some artifacts require `sudo` if files are root-owned.

---

## Plugin List

### Shell & User Activity

| Function | Description |
|----------|-------------|
| `shellhistory.entries` | Parse zsh/bash history files — commands with timestamps (zsh extended format), duration, and shell type |
| `knowledgec.app_usage` | Parse application usage events from knowledgeC.db — which apps were used and when |
| `knowledgec.web_usage` | Parse web browsing events from knowledgeC.db |
| `knowledgec.display` | Parse display backlight on/off state from knowledgeC.db |
| `knowledgec.bluetooth` | Parse bluetooth connection events from knowledgeC.db |
| `knowledgec.media_usage` | Parse media playback events from knowledgeC.db |
| `knowledgec.notifications` | Parse notification events from knowledgeC.db |
| `knowledgec.intents` | Parse app intent events from knowledgeC.db |
| `knowledgec.discoverability` | Parse discoverability signal events from knowledgeC.db |
| `knowledgec.histograms` | Parse activity level histograms from knowledgeC.db |
| `knowledgec.sync_peers` | Parse synced device peers from knowledgeC.db |
| `knowledgec.sources` | Parse registered event sources from knowledgeC.db |
| `knowledgec.custom_metadata` | Parse custom metadata entries from knowledgeC.db |

### Biome (iOS/macOS Telemetry)

| Function | Description |
|----------|-------------|
| `biome.all` | Parse all Biome streams into timestamped records with extracted strings |
| `biome.streams` | List all available Biome streams with segment counts and sizes |
| `biome.app_in_focus` | Which app had focus and when |
| `biome.app_activity` | Application activity events |
| `biome.app_intents` | App intents (messages, media, calls) |
| `biome.now_playing` | Media playback events (Spotify, Apple Music, etc.) |
| `biome.media_usage` | Media usage events |
| `biome.wifi` | WiFi state events |
| `biome.wifi_connections` | WiFi connection/disconnection events |
| `biome.bluetooth` | Bluetooth connection events |
| `biome.display` | Display on/off state |
| `biome.location` | Semantic location data |
| `biome.notifications` | Notification events |
| `biome.screentime` | Screen Time app usage data |
| `biome.safari_history` | Safari history events from DuetKnowledge |
| `biome.safari_navigations` | Safari URL navigations |
| `biome.safari_page_load` | Safari page load events |
| `biome.safari_pageview` | Safari page views |
| `biome.messages_read` | Message read events |
| `biome.web_usage` | Web browsing events tracked by the OS |
| `biome.user_focus` | Inferred Focus/Do Not Disturb mode |
| `biome.user_focus_computed` | Computed Focus mode |
| `biome.screen_sharing` | Screen sharing sessions |
| `biome.siri_execution` | Siri command executions |
| `biome.carplay` | CarPlay connection events |
| `biome.low_power_mode` | Low power mode state changes |
| `biome.dk_low_power` | DuetKnowledge low power events |
| `biome.activity_level` | Device activity level |
| `biome.harvested_mail` | Harvested mail metadata |
| `biome.harvested_messages` | Harvested message metadata |
| `biome.harvested_notes` | Harvested notes metadata |
| `biome.harvested_notifications` | Harvested notification data |
| `biome.intelligence_donations` | Siri intelligence donations |
| `biome.third_party_apps` | Third-party app usage |

### Communication

| Function | Description |
|----------|-------------|
| `imessage.messages` | Parse iMessage/SMS messages with sender handle information |
| `imessage.chats` | Parse iMessage/SMS chat entries |
| `imessage.attachments` | Parse iMessage/SMS attachments |
| `callhistory.calls` | Parse call records from CallHistory.storedata |
| `interactions.entries` | Parse communication interactions from interactionC.db |
| `interactions.contacts` | Parse contact entries from interactionC.db |
| `addressbook.contacts` | Parse contacts from AddressBook ZABCDRECORD table |
| `addressbook.emails` | Parse email addresses joined with contact names |
| `addressbook.phones` | Parse phone numbers joined with contact names |

### Browsers

| Function | Description |
|----------|-------------|
| `safari.history` | Parse Safari browsing history from History.db |
| `safari.bookmarks` | Parse Safari bookmarks from Bookmarks.plist |
| `safari.downloads` | Parse Safari download history from Downloads.plist |
| `safari.topsites` | Parse Safari frequently visited sites |
| `firefox.history` | Parse browsing history from Firefox places.sqlite |
| `firefox.cookies` | Parse cookies from Firefox cookies.sqlite |
| `firefox.downloads` | Parse download history from Firefox places.sqlite |
| `firefox.bookmarks` | Parse bookmarks from Firefox places.sqlite |
| `firefox.logins` | Parse saved login entries (no passwords extracted) |
| `firefox.formhistory` | Parse form autofill history |
| `firefox.permissions` | Parse site permissions |
| `firefox.searches` | Parse search terms |
| `chromium.history` | Parse browsing history from Chromium-based browsers |
| `chromium.cookies` | Parse cookies from Chromium-based browsers |
| `chromium.downloads` | Parse download history from Chromium-based browsers |
| `chromium.bookmarks` | Parse bookmarks from Chromium-based browsers |
| `chromium.logins` | Parse saved login entries (no passwords extracted) |
| `chromium.searches` | Parse keyword search terms |
| `chromium.topsites` | Parse top sites |

### System Info

| Function | Description |
|----------|-------------|
| `osinfo.version` | Parse SystemVersion.plist for macOS version, build number |
| `osinfo.install_date` | Get install date from .AppleSetupDone timestamp |
| `localusers.entries` | Parse local user account plists from dslocal (uid, gid, shell, home, realname) |
| `localtime.info` | Report the configured timezone from localtime symlink |
| `hostfile.entries` | Parse /etc/hosts entries |
| `dhcp.leases` | Parse DHCP lease files |

### Persistence & Autostart

| Function | Description |
|----------|-------------|
| `autostart.launch_items` | Parse all Launch Agents and Daemons combined |
| `autostart.launch_agents` | Parse Launch Agents (user, system, Apple) |
| `autostart.launch_daemons` | Parse Launch Daemons (system and Apple) |
| `autostart.kernel_extensions` | Parse installed kexts |
| `autostart.system_extensions` | Parse system extensions from db.plist |
| `autostart.cronjobs` | Parse cron jobs |
| `autostart.periodic` | Parse periodic scripts (daily/weekly/monthly) |
| `autostart.startup_items` | Parse legacy StartupItems |
| `autostart.startup_files` | Parse launchd.conf and rc.common |
| `kext.installed` | Parse installed kernel extensions from Info.plist files |
| `kext.load_history` | Parse kext load history from KextPolicy database |
| `kext.policy` | Parse kext approval policies from KextPolicy database |
| `kext.system_extensions` | Parse system extensions |
| `kext.classification` | Parse kext vendor classifications |

### Security

| Function | Description |
|----------|-------------|
| `firewall.pf_rules` | Parse PF packet filter rules from /etc/pf.conf |
| `firewall.alf_config` | Parse Application Level Firewall global configuration |
| `firewall.alf_apps` | Parse ALF per-application firewall rules |
| `firewall.alf_exceptions` | Parse ALF firewall exceptions |
| `firewall.alf_services` | Parse ALF firewall service rules |
| `keychain.generic` | Parse generic password entries from keychains (no secrets) |
| `keychain.internet` | Parse internet password entries from keychains (no secrets) |
| `keychain.certificates` | Parse certificate entries from keychains |
| `keychain.systemkey` | Parse SystemKey (master key for System.keychain) |
| `sudoers.entries` | Parse sudoers configuration entries |
| `sudolog.entries` | Parse sudo timestamp files — last sudo usage per user |
| `execpolicy.entries` | Parse executed binary measurements from ExecPolicy database |
| `profiles.installed` | Parse installed configuration profiles |
| `profiles.payloads` | Parse individual payloads from configuration profiles |
| `profiles.settings` | Parse configuration profile settings plists |

### Filesystem & Forensics

| Function | Description |
|----------|-------------|
| `dsstore.entries` | Parse .DS_Store entries — files/folders that existed in each directory |
| `dsstore.files` | List all .DS_Store files with entry counts |
| `fsevents.events` | Parse FSEvents records — file system activity |
| `docrevisions.files` | Parse tracked files from DocumentRevisions database |
| `docrevisions.generations` | Parse document revision generations (file versions) |
| `trash.files` | List files in user Trash and volume-level .Trashes |
| `trash.icloud` | List files in iCloud Drive trash |
| `quicklook.thumbnails` | Parse QuickLook thumbnail cache entries |
| `savedstate.entries` | Report apps with saved application state |
| `terminalstate.files` | List files in Terminal saved state directory |
| `spotlight.applist` | Parse Spotlight applist.dat for known applications |
| `spotlightshortcuts.entries` | Parse Spotlight shortcuts and search preferences |

### Applications & Productivity

| Function | Description |
|----------|-------------|
| `applications.installed` | Parse installed applications from Info.plist files |
| `installhistory.entries` | Parse software installation history from InstallHistory.plist |
| `officemru.entries` | Parse Microsoft Office recently opened documents (JSON + securebookmarks.plist) |
| `notes.entries` | Parse Apple Notes — title, snippet, body text, folder, timestamps |
| `notes.accounts` | Parse note accounts (iCloud, local, etc.) |
| `notes.attachments` | Parse note attachments |
| `notes.folders` | Parse note folders |
| `wallet.passes` | Parse Apple Wallet passes (boarding passes, tickets, reservations) |
| `wallet.transactions` | Parse Apple Pay payment transactions |
| `wallet.payment_cards` | Parse registered Apple Pay payment cards |
| `wallet.pass_types` | Parse registered pass type identifiers |
| `wallet.pass_details` | Parse detailed pass fields from .pkpass directories |
| `crashreporter.events` | Parse CrashReporter plists for crash and force-quit timestamps |
| `crashreporter.entries` | Parse per-app usage and crash statistics |
| `printjobs.entries` | Parse CUPS print job cache entries |
| `launchpad.apps` | Parse Launchpad apps with bundle ID, category, folder position |

### Network & Remote Access

| Function | Description |
|----------|-------------|
| `ssh.known_hosts` | Parse SSH known_hosts for previously connected hosts |
| `ssh.config` | Parse SSH config files and extract Host blocks |
| `ard.access` | Parse Apple Remote Desktop access entries |
| `ard.config` | Parse ARD configuration from plist files |
| `msrdc.connections` | Parse Microsoft Remote Desktop connection bookmarks |
| `netusage.processes` | Parse per-process network usage statistics |
| `notifications.entries` | Parse notification entries from usernoted db |
| `notifications.apps` | Parse registered notification apps |

### Logs

| Function | Description |
|----------|-------------|
| `logs.list` | List all discovered log files with sizes |
| `logs.all_raw` | Parse all log files as raw lines |
| `logs.system` | Parse system.log entries in syslog format |
| `logs.user` | Parse user application logs from ~/Library/Logs/ |
| `logs.install` | Parse install.log entries |
| `logs.asl` | Parse all ASL binary database files |
| `logs.asl_system` | Parse system-wide ASL logs from /var/log/asl/ |
| `logs.asl_diagnostics` | Parse ASL files from DiagnosticMessages |
| `logs.asl_powermanagement` | Parse ASL power management logs (sleep/wake) |
| `logs.audit_classes` | Parse audit class definitions |
| `logs.audit_events` | Parse audit event definitions |
| `powerlogs.app_usage` | Parse application usage from powerlog database |
| `powerlogs.network` | Parse cumulative network usage from powerlog |
| `powerlogs.sleep_wake` | Parse sleep/wake power state events |

### Cloud & Sync

| Function | Description |
|----------|-------------|
| `icloudfiles.files` | List files in iCloud Drive local storage |
| `sharedfilelist.favorites` | Parse Finder sidebar favorite items |
| `sharedfilelist.volumes` | Parse favorite volumes (mounted drives, network shares) |
| `sharedfilelist.recent_apps` | Parse recently launched applications |
| `sharedfilelist.recent_docs` | Parse recently opened documents |
| `sharedfilelist.projects` | Parse Finder project/tag items |
| `sharedfilelist.all` | Parse all SharedFileList .sfl3 files |
| `sharepoints.entries` | Parse sharepoint definitions from dslocal |

### Device & Config

| Function | Description |
|----------|-------------|
| `preferences.entries` | Parse all preference plists into flattened key-value records |
| `preferences.list` | List all preference plist files with top-level keys |
| `etcfiles.entries` | Read common /etc configuration files as raw lines |
| `utmpx.entries` | Parse binary utmpx login records |
| `lockdown.entries` | Parse iOS device pairing plists from /private/var/db/lockdown/ |

---

