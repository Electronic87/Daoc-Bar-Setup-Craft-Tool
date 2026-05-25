# Daoc Bar Setup And Craft Tool

Unofficial Windows tool for DAoC Eden spellcrafters.

Paste an order, open an order file, or read `chat.log`; the tool finds the spellcraft gems, shows the quickbar order, and can set your Eden hotbars after making a backup.

## Features

- Paste Discord/customer text from your clipboard.
- Open Zenkcraft, Template Forge, and supported LOKI-style order files.
- Read gem names from DAoC `chat.log`.
- Preview where every gem will land on the quickbar.
- Set Eden hotbars for the gems, with optional item separator buttons.
- Back up the selected Eden `.ini` before changing anything.
- Export `.forge` or Zenkcraft `.txt` files when needed.

## First Use

1. Open `Daoc Bar setup and craft tool V3.exe`.
2. Pick the realm for the order.
3. Choose `Pasted text`, `Order file`, or `Chat log`.
4. Paste/import the order.
5. Select the Eden character `.ini`, or use `Find .ini` to pick the newest character file in the Eden folder.
6. Check the quickbar preview and bar visual.
7. Click `Set Hotbars`, or open `Show Export File Options` if you need a `.forge` or Zenkcraft `.txt`.

## Hotbar Safety

- Log out to the character screen before setting hotbars.
- The tool updates only the selected quickbar range and the separator macros it needs.
- A timestamped `.ini` backup is created before every hotbar write.
- `Restore Backup` copies a chosen backup back over the selected Eden `.ini`.

## Chat Log Notes

- The normal chat log path is `C:\Users\%username%\Documents\Electronic Arts\Dark Age of Camelot\chat.log`.
- The parser uses only the newest `Chat Log Opened` session in the selected `chat.log`.
- `Refresh` reloads the selected chat log without browsing again.
- `Clear Chat Log` saves a backup copy first, then empties the selected chat log.
- Simple gem-name typos can be corrected, but missing tiers are not guessed.

## Build From Source

See [BUILD.md](BUILD.md).

## Project Hygiene

Do not commit personal/customer files such as `.ini`, `.log`, customer order reports, generated `.exe` files, or release zips. The `.gitignore` is set up to keep those out.

## Status

Current source is V3. Albion, Midgard, and Hibernia gems are supported. A few hidden/question-mark skills from Template Forge/Zenkcraft are skipped until those tools expose usable gem names.

## Disclaimer

Daoc Bar setup and craft tool (c) 2026 Electronic87 - A non-commercial fan project. Not affiliated with Electronic Arts, Broadsword Online Games, Mythic Entertainment, Eden-DAoC.net, DAoC Tools, or Zenkcraft. Dark Age of Camelot is a trademark of its respective owners.

Built by Electronic87 with AI-assisted coding support from OpenAI Codex. The author reviewed and directed the features, behavior, testing, and packaging.
