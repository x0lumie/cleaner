# Windows Leftover Cleaner

A Windows GUI tool for scanning common application locations (Program Files, AppData, and user profile folders), estimating folder sizes, and deleting leftover folders with confirmation prompts. It can also check Start Menu shortcuts to help identify installed apps.

## Features

- Scans:
  - `C:\Program Files`
  - `C:\Program Files (x86)`
  - `%LOCALAPPDATA%` (AppData\Local)
  - `%APPDATA%` (AppData\Roaming)
  - User profile root (`C:\Users\<you>`) top-level folders
- Displays folder sizes and Start Menu shortcut matches
- Search filters:
  - Minimum size threshold (MB)
  - Search by **Path** or **App Name**
  - Optional case-sensitive search
- Sortable columns (click headers)
- Safe delete with confirmation prompt
- Live totals for filtered results

## Requirements

- Windows 10/11
- Python 3.9+ (for running from source)

## Run from source

```bash
python leftover_cleaner.py
```

## Build a standalone EXE (no Python required for users)

Install PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller --onefile --noconsole leftover_cleaner.py
```

Your EXE will be in:

```
dist/leftover_cleaner.exe
```

## Notes

- Scanning can take time depending on disk size and the number of folders.
- Deletion is permanent (does not send to Recycle Bin).

## License

Add your preferred license here.
