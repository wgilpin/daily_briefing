"""Debug script to check audio file matching."""
import sys
sys.path.insert(0, 'src')

from db.repository import Repository
from db.connection import get_connection, initialize_pool
import hashlib
from pathlib import Path

print("Checking feed items and audio files...\n")

initialize_pool()
repo = Repository()

with get_connection():
    items = repo.get_feed_items(source_type='newsletter', limit=10)

print(f"Found {len(items)} newsletter items\n")

for item in items[:3]:
    print(f"Item: {item.title[:60]}...")
    print(f"  ID: {item.id}")
    print(f"  Source ID: {item.source_id}")
    print(f"  Link: {item.link[:80] if item.link else 'NO LINK'}...")

    if item.link:
        # Check both voices
        for voice in ["bm_george", "bf_emma"]:
            content_hash = hashlib.sha256(f"{item.link}:{voice}".encode()).hexdigest()[:16]
            audio_file = Path(f"data/audio_cache/{content_hash}.mp3")
            exists = audio_file.exists()
            print(f"  Audio hash ({voice}): {content_hash} - {'EXISTS' if exists else 'NOT FOUND'}")

    print(f"  has_audio: {item.has_audio}")
    print(f"  audio_path: {item.audio_path}")
    print()

print("\nAudio cache files:")
cache_files = list(Path("data/audio_cache").glob("*.mp3"))
print(f"Total: {len(cache_files)}")
for f in cache_files[:5]:
    print(f"  {f.name}")
