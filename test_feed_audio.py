"""Test if feed items can find their audio files."""
import sys
sys.path.insert(0, 'src')

from db.repository import Repository
from db.connection import get_connection, initialize_pool
import hashlib
from pathlib import Path

from db.models import DatabaseConfig

# Initialize connection pool
config = DatabaseConfig.from_env()
initialize_pool(config.database_url)

repo = Repository()

with get_connection():
    items = repo.get_feed_items(source_type='newsletter', limit=5)

print(f"Found {len(items)} newsletter items\n")

# List available audio files
audio_files = list(Path("data/audio_cache").glob("*.wav"))
audio_hashes = {f.stem for f in audio_files}
print(f"Available audio files: {len(audio_hashes)}")
print(f"Hashes: {sorted(audio_hashes)[:5]}\n")

for item in items[:3]:
    print(f"\nItem: {item.title[:60]}...")
    print(f"  Date: {item.date.strftime('%Y-%m-%d')}")
    print(f"  Link: {item.link[:60] if item.link else 'NO LINK'}...")
    print(f"  has_audio: {item.has_audio}")
    print(f"  audio_path: {item.audio_path}")

    # Manually check what hashes we'd expect
    voices = ["bm_george", "bf_emma"]
    for voice in voices:
        # Link-based
        if item.link:
            link_hash = hashlib.sha256(f"{item.link}:{voice}".encode()).hexdigest()[:16]
            print(f"  Expected (link+{voice}): {link_hash} - {'EXISTS' if link_hash in audio_hashes else 'NOT FOUND'}")

        # Title+date based
        date_str = item.date.strftime("%Y-%m-%d")
        title_hash = hashlib.sha256(f"{item.title}:{date_str}:{voice}".encode()).hexdigest()[:16]
        print(f"  Expected (title+date+{voice}): {title_hash} - {'EXISTS' if title_hash in audio_hashes else 'NOT FOUND'}")
