# Data Model: Audio Playback UI

**Feature**: 009-audio-playback-ui
**Date**: 2026-02-06

## Overview

This feature introduces minimal data model changes - primarily client-side state for playback tracking. No new database tables required. Audio files already exist from feature 007/008.

## Client-Side State (JavaScript/Alpine.js)

### AudioPlayerState

Tracks current playback status in the browser. Managed by Alpine.js component.

**Properties:**

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `isPlaying` | boolean | Whether audio is currently playing | true/false |
| `currentItem` | object \| null | Currently loaded item metadata | See ItemMetadata |
| `currentIndex` | number | Position in feed items list | >= -1 (where -1 = no item selected) |
| `itemCount` | number | Total number of audio-enabled items in current feed view | >= 0 |

**ItemMetadata** (nested object):

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Feed item unique identifier (content hash) |
| `title` | string | Item title for display |
| `audioPath` | string | URL path to audio file (`/audio/<item_id>`) |

**Lifecycle:**

- **Initialize**: On page load, set to default state (no item playing)
- **Update**: On user interaction (play/pause/next/previous)
- **Reset**: On feed filter change, search, or navigation away from feed

**Example State:**

```javascript
{
  isPlaying: true,
  currentItem: {
    id: "1a4f6b0976cc66ba",
    title: "Quantum Computing Breakthrough",
    audioPath: "/audio/1a4f6b0976cc66ba"
  },
  currentIndex: 3,
  itemCount: 15
}
```

## Server-Side Data Extensions

### FeedItem (Existing Model - Extension)

Add audio availability indicator to existing feed item model.

**New Fields:**

| Field | Type | Required | Description | Source |
|-------|------|----------|-------------|--------|
| `has_audio` | boolean | Yes | Whether audio file exists for this item | Check file existence in `data/audio_cache/{content_hash}.mp3` |
| `audio_hash` | string \| null | No | Content hash used for audio filename | Derived from item content (existing hash) |

**Implementation:**

```python
from pathlib import Path
from pydantic import BaseModel, computed_field

class FeedItem(BaseModel):
    """Existing feed item model with audio support."""

    id: str  # Existing: content hash or DB ID
    title: str
    summary: str
    link: str | None
    date: datetime
    source_type: str
    # ... other existing fields ...

    @computed_field
    @property
    def has_audio(self) -> bool:
        """Check if audio file exists for this item."""
        audio_file = Path(f"data/audio_cache/{self.id}.mp3")
        return audio_file.exists()

    @computed_field
    @property
    def audio_path(self) -> str | None:
        """Return audio URL path if available."""
        return f"/audio/{self.id}" if self.has_audio else None
```

**Validation Rules:**

- `id` must be non-empty string (alphanumeric hash)
- Audio files must be in `data/audio_cache/` directory
- Audio files must have `.mp3` extension
- Filenames must match pattern: `{content_hash}.mp3`

## File System Structure

### Audio Storage

```
data/
└── audio_cache/
    ├── 1a4f6b0976cc66ba.mp3    # Content-addressed MP3 files
    ├── 1e54af0387a05e32.mp3
    ├── 2a98c4bba04e3d99b.mp3
    └── ...
```

**Properties:**

- **Immutable**: Once created, audio files never change (content-addressed)
- **Cache-friendly**: Long cache headers (1 year) safe due to immutability
- **No database**: File existence check determines availability

## API Data Flow

### Feed Item Rendering

```
1. User requests /feed
   ↓
2. Backend queries feed items from PostgreSQL
   ↓
3. For each item, compute has_audio property (file existence check)
   ↓
4. Render feed.html template with audio metadata
   ↓
5. Client receives HTML with data-audio-path attributes
```

**Template Data:**

```html
<article class="feed-item"
         data-item-id="{{ item.id }}"
         data-audio-path="{{ item.audio_path }}">

    {% if item.has_audio %}
    <button class="item-play-btn"
            @click="playItem('{{ item.id }}', '{{ item.audio_path }}')">
        ▶
    </button>
    {% endif %}

    <!-- ... rest of item ... -->
</article>
```

### Audio File Serving

```
1. Client requests /audio/<item_id>
   ↓
2. Flask route validates item_id format
   ↓
3. Check authentication (@login_required)
   ↓
4. Map item_id to file: data/audio_cache/{item_id}.mp3
   ↓
5. Return 404 if file not found
   ↓
6. Handle HTTP Range header (if present)
   ↓
7. Return 206 Partial Content (seek support) or 200 (full file)
```

## State Transitions

### Playback State Machine

```
                  +----------------+
                  |   No Item      |
                  |   (Initial)    |
                  +----------------+
                          |
                    [User clicks play]
                          ↓
                  +----------------+
         +------->|    Playing     |
         |        +----------------+
         |                |
    [Resume]              |
         |          [User pauses]
         |                ↓
         |        +----------------+
         +--------|    Paused      |
                  +----------------+
                          |
                    [Audio ends]
                    [Filter change]
                    [Navigate away]
                          ↓
                  +----------------+
                  |    Stopped     |
                  +----------------+
                          |
                    [Reset player]
                          ↓
                  +----------------+
                  |   No Item      |
                  +----------------+
```

**Transition Rules:**

- `No Item → Playing`: User clicks play button on any item
- `Playing → Paused`: User clicks pause or presses space bar
- `Paused → Playing`: User clicks play again (resumes from position)
- `Playing → Stopped`: Audio reaches end, filter changes, or user navigates away
- `Stopped → No Item`: Player resets, clears current item
- `Playing → Playing` (different item): User clicks next/previous

## Edge Cases & Validation

### Missing Audio File

**Scenario**: Item has `id` but audio file doesn't exist

**Handling**:
- `has_audio` property returns `false`
- Play button not rendered in template
- If somehow requested via `/audio/<item_id>`: return HTTP 404

### Invalid Item ID

**Scenario**: Client requests `/audio/../../etc/passwd` (path traversal)

**Handling**:
- Validate `item_id` matches pattern: `^[a-f0-9]{16,}$` (hexadecimal hash)
- Only serve files from `data/audio_cache/` directory
- Return HTTP 400 for invalid IDs

### Concurrent Playback Requests

**Scenario**: User rapidly clicks multiple play buttons

**Handling**:
- Client-side: Only one `<audio>` element exists (singleton)
- New play request stops current audio and starts new file
- Previous item unhighlights, new item highlights
- No server-side state to manage

### Feed Refresh During Playback

**Scenario**: HTMX updates feed content while audio is playing

**Handling**:
- Audio element preserved via `hx-preserve` attribute
- HTMX `beforeSwap` event listener pauses audio
- Player state resets (`currentItem = null`)
- User must manually select new item to play

## Performance Considerations

### File Existence Checks

**Problem**: Checking `has_audio` for 100 feed items = 100 file system calls

**Solution**: Batch check in repository layer

```python
def enrich_items_with_audio(items: list[FeedItem]) -> list[FeedItem]:
    """Add audio metadata to items in batch."""
    audio_dir = Path("data/audio_cache")

    # Single directory listing instead of 100 stat() calls
    existing_audio = {f.stem for f in audio_dir.glob("*.mp3")}

    for item in items:
        item.has_audio = item.id in existing_audio

    return items
```

**Impact**: O(n) → O(1) file system operations per page load

### Caching Headers

**Audio files** (immutable, content-addressed):
```
Cache-Control: public, max-age=31536000, immutable
```

**Feed HTML** (dynamic):
```
Cache-Control: no-cache
```

## Constraints

1. **No database storage**: Audio availability computed from file system
2. **No server-side playback state**: All state is client-side
3. **No authentication in audio files**: Auth check happens at route level
4. **No playlists or history**: Out of scope for this feature
5. **One audio element per page**: Global singleton player

## Future Extensibility (Not in Scope)

If future features require:

- **Playlist support**: Add `playlist` table with item references
- **Playback history**: Add `playback_events` table with timestamps
- **Audio transcripts**: Add `transcripts` table with text + timestamps
- **Progress tracking**: Add `user_progress` table with (user_id, item_id, position)

These would require database changes. Current implementation intentionally avoids this complexity.
