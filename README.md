

  # DJI Marker to Chapter Injector
Converts DJI camera highlight markers into standard MP4 chapters for video editors and players.

## The Problem

DJI cameras (like the Action 6) let you press the Quick Switch button to create markers while recording. Problem is, these markers only show up on the camera itself. Your video editor (DaVinci Resolve, Premiere, etc.) can't see them.

## The Solution

This script extracts those DJI markers and injects them as proper 'MP4 chapters'.

## Requirements

**Must be installed and in your PATH:**
- Python 3.6+
- exiftool
- ffmpeg

## Usage

1. Put your DJI videos (`.mp4`) and the script in the same folder
2. Run: `Unc_DJI.py`

The script processes all MP4 files in the folder and creates new files with `_chapters.mp4` suffix **but no worries, it doesn't delete the original file :)**.


## Example Output

```
Processing: DJI_67.mp4
  ✓ Found 3 markers
    • 0:30 (30 seconds)
    • 1:30 (90 seconds)
    • 2:30 (150 seconds)
  → Injecting chapters...
  ✓ SUCCESS: Created DJI_0123_chapters.mp4
```

## Notes

- Skips files ending in `_chapters.mp4` to avoid reprocessing
- Creates a log file with details
- Videos aren't re-encoded.
