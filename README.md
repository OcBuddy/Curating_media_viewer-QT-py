# Media Viewer

A desktop image and video browser built with **PyQt6**. Designed for curating media — quickly navigate, view, and delete files with **unlimited undo**.

## Features

- **Browse images** (jpg, png, gif, bmp, webp, tiff, …) and **videos** (mp4, mov, avi, mkv, webm, …) from any folder
- **Navigatation**: next/previous, skip ±10, jump to first
- **Delete with undo**: deleted files are copied to a hidden `.media_viewer_undo/` folder before removal, so you can always restore them
- **Unlimited undo**: undo buffer persists as long as you stay in the same folder (cleared when opening a new folder)
- **Trash integration**: uses `send2trash` if installed, otherwise permanently deletes files
- **Keyboard-driven** or click toolbar buttons

## Keyboard Shortcuts

| Action       | Keys                                              |
|--------------|---------------------------------------------------|
| Next         | Right Arrow, N, Enter, Space                      |
| Previous     | Left Arrow, P, Backspace                          |
| Skip +10     | Down Arrow, Page Down                             |
| Skip -10     | Up Arrow, Page Up                                 |
| First Item   | Home                                              |
| Delete       | D, Delete                                         |
| Undo         | U, Ctrl+Z                                         |
| Open Folder  | O                                                 |
| Help         | F1                                                |

## Requirements

- **Python 3.6+** (3.8+ recommended)
- **PyQt6** — GUI framework
- `send2trash` (optional) — sends deleted files to the OS trash instead of permanent deletion

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python3 mm-curating_media_viewer.py
```

On launch, select a folder containing images and/or videos. The first media file is displayed immediately.
