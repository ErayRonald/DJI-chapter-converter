#!/usr/bin/env python3
"""
DJI Marker to MP4 Chapter Injector
Extracts DJI highlight markers and injects them as standard MP4 chapters
"""

import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime

# ANSI color codes so its pretty 
class Color:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def check_tools():
    """Check if tools are present"""
    tools = {'exiftool': False, 'ffmpeg': False}
    
    for tool in tools.keys():
        try:
            subprocess.run([tool, '-version'], 
                         capture_output=True, 
                         check=False)
            tools[tool] = True
        except FileNotFoundError:
            pass
    
    missing = [t for t, available in tools.items() if not available]
    
    if missing:
        print(f"{Color.RED}ERROR: Missing required tools: {', '.join(missing)}{Color.RESET}")
        print(f"{Color.YELLOW}Please install them and ensure they're in your PATH{Color.RESET}")
        return False
    
    return True

def extract_dji_markers(video_file):
    """extract DJI  markers from video using exiftool"""
    try:
        result = subprocess.run(
            ['exiftool', '-G1', '-s', '-HighlightMarkers', '-ee', str(video_file)],
            capture_output=True,
            text=True,
            check=False
        )
        
        # look for HighlightMarkers line
        for line in result.stdout.splitlines():
            if 'HighlightMarkers' in line:
                match = re.search(r':\s*(.+)$', line)
                if match:
                    markers_str = match.group(1).strip()
                    markers = [int(m.strip()) for m in markers_str.split(',')]
                    return sorted(markers)
        
        return []
    
    except Exception as e:
        print(f"{Color.RED}Error extracting markers: {e}{Color.RESET}")
        return []

def create_metadata_file(markers, output_file):
    """FFMPEG metadata file with chapters"""
    metadata = ";FFMETADATA1\n"
    
    for i, marker_sec in enumerate(markers):
        start_ms = marker_sec * 1000
        
        if i + 1 < len(markers):
            end_ms = markers[i + 1] * 1000
        else:
            end_ms = start_ms + 1000
        
        mm = marker_sec // 60
        ss = marker_sec % 60
        chapter_title = f"Highlight {mm:02d}:{ss:02d}"
        
        metadata += f"[CHAPTER]\n"
        metadata += f"TIMEBASE=1/1000\n"
        metadata += f"START={start_ms}\n"
        metadata += f"END={end_ms}\n"
        metadata += f"title={chapter_title}\n\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(metadata)

def inject_chapters(input_file, markers):
    """inject chapters into video file"""
    input_path = Path(input_file)
    output_file = input_path.stem + "_chapters" + input_path.suffix
    metadata_file = f"temp_chapters_{input_path.stem}.txt"
    
    try:
        create_metadata_file(markers, metadata_file)
        
        print(f"  {Color.CYAN}→ Injecting chapters...{Color.RESET}")
        
        result = subprocess.run([
            'ffmpeg',
            '-i', str(input_file),
            '-i', metadata_file,
            '-map_metadata', '1',
            '-codec', 'copy',
            '-y',
            output_file
        ], capture_output=True, text=True, check=False)
        
        Path(metadata_file).unlink(missing_ok=True)
        
        if result.returncode == 0 and Path(output_file).exists():
            print(f"  {Color.GREEN}✓ SUCCESS: Created {output_file}{Color.RESET}")
            return True
        else:
            print(f"  {Color.RED}✗ FAILED: ffmpeg error{Color.RESET}")
            if result.stderr:
                print(f"  {Color.GRAY}{result.stderr[:200]}{Color.RESET}")
            return False
    
    except Exception as e:
        print(f"  {Color.RED}✗ Error: {e}{Color.RESET}")
        Path(metadata_file).unlink(missing_ok=True)
        return False

def process_directory():
    """Process all MP4 files in current directory"""
    log_file = "chapter_injection_log.txt"
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"DJI Marker to Chapter Injection - {datetime.now()}\n")
        f.write("=" * 50 + "\n\n")
    
    print(f"{Color.CYAN}{Color.BOLD}Starting DJI marker extraction and chapter injection...{Color.RESET}")
    print()
    
    # Statistics
    total_files = 0
    success_files = 0
    skipped_files = 0
    
    # get all MP4 files
    mp4_files = list(Path('.').glob('*.mp4'))
    
    if not mp4_files:
        print(f"{Color.YELLOW}No MP4 files found in current directory{Color.RESET}")
        return
    
    for video_file in mp4_files:
        # Sskip already processed files
        if video_file.stem.endswith('_chapters'):
            print(f"{Color.YELLOW}⊘ Skipping: {video_file.name} (already processed){Color.RESET}")
            skipped_files += 1
            continue
        
        total_files += 1
        
        print(f"{Color.CYAN}{'━' * 50}{Color.RESET}")
        print(f"{Color.WHITE}Processing: {video_file.name}{Color.RESET}")
        
        # log to file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"File: {video_file.name}\n")
        
        # extract markers
        markers = extract_dji_markers(video_file)
        
        if not markers:
            print(f"  {Color.YELLOW}⚠ No DJI highlights found - skipping{Color.RESET}")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write("  No highlights found - skipped\n\n")
            skipped_files += 1
            print()
            continue
        
        print(f"  {Color.GREEN}✓ Found {len(markers)} markers{Color.RESET}")
        
        # display markers
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"  Found {len(markers)} markers\n")
            for sec in markers:
                mm = sec // 60
                ss = sec % 60
                formatted = f"{mm}:{ss:02d}"
                print(f"    {Color.GRAY}• {formatted} ({sec} seconds){Color.RESET}")
                f.write(f"    {formatted}\n")
        
        # inject chapters
        if inject_chapters(video_file, markers):
            success_files += 1
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"  Success: {video_file.stem}_chapters.mp4 created\n\n")
        else:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"  Failed: ffmpeg error\n\n")
        
        print()
    
    # summary
    print(f"{Color.CYAN}{'━' * 50}{Color.RESET}")
    print(f"{Color.WHITE}{Color.BOLD}SUMMARY{Color.RESET}")
    print(f"  Total files found:      {total_files}")
    print(f"  {Color.GREEN}Successfully processed: {success_files}{Color.RESET}")
    print(f"  {Color.YELLOW}Skipped:                {skipped_files}{Color.RESET}")
    print()
    print(f"{Color.CYAN}Log saved to: {log_file}{Color.RESET}")
    
    # Write summary to log
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\nSUMMARY\n")
        f.write(f"Total files: {total_files}\n")
        f.write(f"Success: {success_files}\n")
        f.write(f"Skipped: {skipped_files}\n")
    
    print(f"{Color.GREEN}Done!{Color.RESET}")

def main():
    """Main entry point"""
    # check for required tools
    if not check_tools():
        sys.exit(1)
    
    # process all videos in current directory
    process_directory()

if __name__ == "__main__":
    main()