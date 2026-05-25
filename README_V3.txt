Daoc Bar setup and craft tool - V3

Paste an order, open an order file, or read chat.log. The tool finds the spellcraft gems, shows the quickbar order, and can set your Eden hotbars after making a backup.

What it can do:
- Paste Discord/customer text from your clipboard.
- Open Zenkcraft, Template Forge, and supported LOKI-style order files.
- Read gem names from DAoC chat.log.
- Preview where every gem will land on the quickbar.
- Set Eden hotbars for the gems, with optional item separator buttons.
- Back up the selected Eden INI before changing anything.
- Export .forge or Zenkcraft .txt files when needed.

First use:
1. Open Daoc Bar setup and craft tool.exe.
2. Pick the realm for the order.
3. Choose Pasted text, Order file, or Chat log as the input source.
4. Select the customer/order file, select chat.log, or use Paste from Clipboard.
5. Select the Eden character INI if setting hotbars, or use Find .ini for the newest character file in your Eden folder.
6. Check the quickbar preview and Bar Visual.
7. Choose Set Hotbars, or open Show Export File Options if you need a .forge/.txt file instead.

Chat log notes:
- The normal location is Documents\Electronic Arts\Dark Age of Camelot\chat.log.
- The parser uses only the newest Chat Log Opened session in the selected chat.log.
- The parser ignores normal chat noise and looks for gem names inside chat lines.
- Refresh reloads the selected chat.log without browsing for it again.
- Clear Chat Log saves a backup copy first, then empties the selected chat.log.
- If a gem name has a typo, the tool will try to correct it and show a warning.
- If a gem name is missing its tier, the tool stops and shows an error because the tier cannot be safely guessed.

Hotbar notes:
- Be logged out to the character screen before setting hotbars.
- Pick the correct realm before setting hotbars.
- The Bar Visual uses the same quickbar/page/slot math as Set Hotbars.
- Hover a filled visual slot to see its details and highlight the matching line in Quickbar Preview.
- Use the mouse wheel or the in-bar page arrows in Bar Visual to switch quickbar pages.
- The tool updates only the selected quickbar range and the item separator macros it needs.
- A backup INI is saved before the hotbar change.
- After a successful hotbar change, only the newest 3 tool backups are kept for that character INI.
- Restore Backup copies a selected backup INI back over the selected Eden INI. It does not delete the backup.
- The Eden folder defaults to the normal Eden AppData path for the current Windows user.
- Find .ini selects the newest non-backup character INI in that Eden folder, usually the last character you logged into.

Saved settings notes:
- Paths inside your Windows user folder are shown as C:\Users\%username%\... so screenshots and shared builds point users at their own profile.
- The tool remembers the last folder used for order files, but it does not reopen the last customer/order file automatically.
- The tool remembers the selected realm, chat.log path, export save folder, export type, open-folder checkbox, Eden INI, and quickbar position.
- Export file name is blank until an input is chosen, then it follows the selected export type.
- Export file creation is hidden under Show Export File Options because hotbar setup is the main workflow.

Known V3 limits:
- Template Forge and Zenkcraft currently expose a few hidden/question-mark skills without usable gem names. Those are intentionally skipped until Eden/Template Forge exposes real spellcraft gems for them.
- Chat log and pasted text parsing can correct simple typos, but it will not guess missing tiers.
- If a Midgard order gives only a bare duplicated gem name like Raw Fiery Primal Rune without the stat/skill line, the tool cannot know which duplicate skill was intended. Full order text avoids this.

Daoc Bar setup and craft tool (c) 2026 Electronic87 - A non-commercial fan project. Not affiliated with Electronic Arts, Broadsword Online Games, Mythic Entertainment, Eden-DAoC.net, DAoC Tools, Template Forge, or Zenkcraft. Dark Age of Camelot and related names, marks, and visual references belong to their respective owners.

Built by Electronic87 with AI-assisted coding support from OpenAI Codex. The author reviewed and directed the features, behavior, testing, and packaging.
