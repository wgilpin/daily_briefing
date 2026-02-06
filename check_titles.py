"""Check if digest titles match what would be in database."""
import hashlib
from pathlib import Path
import re

# Read digest
digest_path = Path("data/output/digest_20260206_155733_459587.md")
content = digest_path.read_text()

# Extract titles from digest (### headers or **bold**)
bold_pattern = re.compile(r'^\*\*(.+?)\*\*\s*$', re.MULTILINE)
titles = bold_pattern.findall(content)

print(f"Found {len(titles)} titles in digest:\n")

# Get digest date
digest_date = "2026-02-06"
voices = ["bm_george", "bf_emma"]

# List available audio
audio_files = list(Path("data/audio_cache").glob("*.wav"))
audio_hashes = {f.stem for f in audio_files}
print(f"Available audio files: {len(audio_hashes)}\n")

for i, title in enumerate(titles[:5], 1):
    print(f"\n{i}. {title[:60]}...")

    # Check if this title would find audio
    found = False
    for voice in voices:
        title_hash = hashlib.sha256(f"{title}:{digest_date}:{voice}".encode()).hexdigest()[:16]
        if title_hash in audio_hashes:
            print(f"   ✓ Found audio: {title_hash} ({voice})")
            found = True
            break

    if not found:
        print(f"   ✗ NO AUDIO FOUND")
        # Show what hashes we tried
        for voice in voices:
            title_hash = hashlib.sha256(f"{title}:{digest_date}:{voice}".encode()).hexdigest()[:16]
            print(f"      Tried: {title_hash} ({voice})")
