# Quickstart: Audio Playback UI

**Feature**: 009-audio-playback-ui
**Last Updated**: 2026-02-06

## Overview

Add audio playback controls to the unified feed interface, allowing users to listen to narrated versions of feed items with Play/Pause/Next/Previous controls.

**What you'll build:**
- Global audio player bar (top right of feed page)
- Per-item play buttons (only shown for items with audio)
- Keyboard shortcuts for hands-free navigation
- Smooth auto-scroll to keep playing item visible

**Tech Stack:**
- Backend: Flask route for serving MP3 files with HTTP 206 range support
- Frontend: Alpine.js (12KB) for reactive UI state
- Audio: HTML5 `<audio>` element (browser native)
- Styling: CSS added to existing feed.html template

## Prerequisites

- Audio files already exist in `data/audio_cache/` (from feature 007/008)
- Flask web app running with existing feed interface
- User authentication system in place (`@login_required` decorator)

##Quick Start

### 1. Add Alpine.js to Base Template

**File:** `src/web/templates/base.html`

Add CDN script before closing `</body>` tag:

```html
<!-- Alpine.js for reactive UI components -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
</body>
```

### 2. Create Global Audio Player Bar

**File:** `src/web/templates/feed.html`

Add player bar at top of content block (after header):

```html
{% block content %}
<div class="feed-header">
    <h2>Unified Feed</h2>
    <!-- existing header content -->
</div>

<!-- NEW: Global Audio Player Bar -->
<div id="audio-player-bar"
     hx-preserve
     x-data="audioPlayerState()"
     class="audio-player-bar">

  <audio id="global-audio-player"
         @play="isPlaying = true"
         @pause="isPlaying = false"
         @ended="resetPlayer()">
  </audio>

  <div class="player-controls">
    <button @click="playPause()"
            :disabled="!currentItem"
            :aria-label="isPlaying ? 'Pause' : 'Play'"
            class="btn-play-pause">
      <span x-show="!isPlaying">▶ Play</span>
      <span x-show="isPlaying">⏸ Pause</span>
    </button>

    <button @click="previous()"
            :disabled="currentIndex <= 0"
            aria-label="Previous"
            class="btn-nav">
      ⏮ Previous
    </button>

    <button @click="next()"
            :disabled="currentIndex >= itemCount - 1"
            aria-label="Next"
            class="btn-nav">
      Next ⏭
    </button>

    <span class="now-playing" x-text="currentItem?.title || 'No audio playing'"></span>
  </div>
</div>

<!-- existing feed content -->
{% endblock %}
```

### 3. Update Feed Item Template

**File:** `src/web/templates/partials/feed_item.html`

Add play button and data attributes:

```html
<article class="feed-item"
         data-item-id="{{ item.id }}"
         {% if item.has_audio %}data-audio-path="/audio/{{ item.id }}"{% endif %}
         :class="{ 'playing': currentItem?.id === '{{ item.id }}' }">

  <div class="feed-item-header">
    <!-- existing header content -->

    <!-- NEW: Play button (only if audio exists) -->
    {% if item.has_audio %}
    <button @click="playItem('{{ item.id }}', '/audio/{{ item.id }}')"
            class="item-play-btn"
            aria-label="Play {{ item.title }}">
      ▶
    </button>
    {% endif %}
  </div>

  <!-- rest of feed item template unchanged -->
</article>
```

### 4. Add Alpine.js Audio State Component

**File:** `src/web/templates/feed.html` (in `{% block extra_head %}` or before `</body>`)

```javascript
<script>
function audioPlayerState() {
  return {
    isPlaying: false,
    currentItem: null,
    currentIndex: -1,
    itemCount: 0,

    playPause() {
      const audio = document.getElementById('global-audio-player');
      if (this.isPlaying) {
        audio.pause();
      } else {
        audio.play();
      }
    },

    next() {
      const items = document.querySelectorAll('[data-audio-path]');
      if (this.currentIndex < items.length - 1) {
        const nextItem = items[this.currentIndex + 1];
        this.playItem(nextItem.dataset.itemId, nextItem.dataset.audioPath);
      } else {
        // At end of list - stop and disable Next button
        const audio = document.getElementById('global-audio-player');
        audio.pause();
        this.resetPlayer();
      }
    },

    previous() {
      const items = document.querySelectorAll('[data-audio-path]');
      if (this.currentIndex > 0) {
        const prevItem = items[this.currentIndex - 1];
        this.playItem(prevItem.dataset.itemId, prevItem.dataset.audioPath);
      } else {
        // At start of list - stop and disable Previous button
        const audio = document.getElementById('global-audio-player');
        audio.pause();
        this.resetPlayer();
      }
    },

    playItem(itemId, audioPath) {
      const audio = document.getElementById('global-audio-player');
      const items = document.querySelectorAll('[data-audio-path]');

      this.currentIndex = Array.from(items).findIndex(
        el => el.dataset.itemId === itemId
      );
      this.itemCount = items.length;

      const itemElement = items[this.currentIndex];
      this.currentItem = {
        id: itemId,
        title: itemElement.querySelector('.feed-item-title').textContent.trim()
      };

      audio.src = audioPath;
      audio.play();

      // Scroll to playing item
      itemElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },

    resetPlayer() {
      this.isPlaying = false;
      this.currentItem = null;
      this.currentIndex = -1;
    }
  };
}

// Stop playback when feed content changes (filter/search)
document.body.addEventListener('htmx:beforeSwap', (event) => {
  if (event.detail.target.id === 'feed-items') {
    const audio = document.getElementById('global-audio-player');
    audio.pause();
    audio.src = '';
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.target.matches('input, textarea, select')) return;

  const audio = document.getElementById('global-audio-player');

  switch(e.key) {
    case ' ':
      e.preventDefault();
      audio.paused ? audio.play() : audio.pause();
      break;
    case 'n':
    case 'N':
      e.preventDefault();
      document.querySelector('[aria-label="Next"]')?.click();
      break;
    case 'p':
    case 'P':
      e.preventDefault();
      document.querySelector('[aria-label="Previous"]')?.click();
      break;
  }
});
</script>
```

### 5. Add Flask Route for Audio Serving

**File:** `src/web/feed_routes.py` (or new `audio_routes.py`)

```python
from flask import Blueprint, send_file, request, abort, make_response
from flask_login import login_required
from pathlib import Path
import os

audio_bp = Blueprint('audio', __name__)

@audio_bp.route('/audio/<item_id>')
@login_required
def serve_audio(item_id: str):
    """Serve MP3 file with HTTP 206 partial content support."""

    # Validate item_id format (hexadecimal hash)
    if not item_id.isalnum() or len(item_id) < 16:
        abort(400, "Invalid item ID format")

    # Map item_id to audio file
    audio_path = Path('data/audio_cache') / f"{item_id}.mp3"
    if not audio_path.exists():
        abort(404, "Audio not found")

    file_size = audio_path.stat().st_size
    range_header = request.headers.get('Range')

    if not range_header:
        # Full file request
        response = send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=False,
            conditional=True
        )
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        return response

    # Parse range: "bytes=start-end"
    byte_range = range_header.replace('bytes=', '').split('-')
    start = int(byte_range[0]) if byte_range[0] else 0
    end = int(byte_range[1]) if byte_range[1] else file_size - 1
    length = end - start + 1

    # Validate range
    if start >= file_size or end >= file_size:
        response = make_response('', 416)
        response.headers['Content-Range'] = f'bytes */{file_size}'
        return response

    # Read partial content
    with open(audio_path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    # Build 206 response
    response = make_response(data, 206)
    response.headers['Content-Type'] = 'audio/mpeg'
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    response.headers['Content-Length'] = str(length)
    response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'

    return response
```

**Register blueprint in `app.py`:**

```python
from src.web.audio_routes import audio_bp

app.register_blueprint(audio_bp)
```

### 6. Update FeedItem Model

**File:** `src/models/feed_models.py` (or wherever FeedItem is defined)

Add computed property for audio availability:

```python
from pathlib import Path
from pydantic import BaseModel, computed_field

class FeedItem(BaseModel):
    id: str
    title: str
    # ... existing fields ...

    @computed_field
    @property
    def has_audio(self) -> bool:
        """Check if audio file exists for this item."""
        audio_file = Path(f"data/audio_cache/{self.id}.mp3")
        return audio_file.exists()
```

### 7. Add CSS Styling

**File:** `src/web/templates/feed.html` (in `{% block extra_head %}`)

```css
<style>
/* Audio player bar */
.audio-player-bar {
  position: sticky;
  top: 0;
  right: 0;
  background: #f9f9f9;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 10px 15px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 100;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.btn-play-pause, .btn-nav {
  padding: 8px 15px;
  border: 1px solid #3498db;
  background: #3498db;
  color: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.btn-play-pause:disabled, .btn-nav:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.now-playing {
  flex: 1;
  font-size: 0.9em;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Item play button */
.item-play-btn {
  background: none;
  border: none;
  font-size: 1.2em;
  cursor: pointer;
  color: #3498db;
  padding: 4px 8px;
}

.item-play-btn:hover {
  color: #2980b9;
}

/* Playing item highlight */
.feed-item.playing {
  background-color: #e8f4f8;
  border-left: 4px solid #3498db;
}

/* Smooth scroll */
html {
  scroll-behavior: smooth;
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;
  }
}

/* Focus indicators for accessibility */
button:focus-visible {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}
</style>
```

## Testing

### Manual Testing Checklist

- [ ] Click play button on any feed item - audio plays
- [ ] Click pause in global player - audio stops
- [ ] Click play again - audio resumes from same position
- [ ] Click next - plays next item's audio
- [ ] Click previous - plays previous item's audio
- [ ] Click next on last item - playback stops, button disabled
- [ ] Click previous on first item - playback stops, button disabled
- [ ] Press spacebar - toggles play/pause
- [ ] Press N key - plays next item
- [ ] Press P key - plays previous item
- [ ] Change filter while playing - audio stops
- [ ] Search while playing - audio stops
- [ ] Playing item is highlighted
- [ ] Page auto-scrolls to playing item
- [ ] Items without audio don't show play button

### Browser DevTools Checks

1. **Network tab**: Verify `/audio/<id>` returns:
   - `Accept-Ranges: bytes` header
   - `206 Partial Content` when seeking
   - `Cache-Control: public, max-age=31536000`

2. **Console**: No JavaScript errors

3. **Lighthouse**: Accessibility score should remain high

## Troubleshooting

### Audio doesn't play

- Check `data/audio_cache/` contains .mp3 files
- Verify file names match item IDs (content hashes)
- Check browser console for 404 errors on `/audio/<id>`

### Seeking doesn't work

- Verify Flask route returns `Accept-Ranges: bytes` header
- Check DevTools Network tab shows 206 responses
- Ensure `send_file()` uses `conditional=True`

### Player state lost on filter change

- Verify `hx-preserve` attribute on audio player bar
- Check HTMX `beforeSwap` listener is firing

### Keyboard shortcuts don't work

- Check if focus is in an input field (shortcuts disabled there)
- Verify event listener is attached to document
- Look for JavaScript errors in console

## Next Steps

After quickstart implementation:

1. Run full test suite: `pytest tests/`
2. Test with screen reader (NVDA/JAWS)
3. Verify keyboard-only navigation
4. Check accessibility with Lighthouse
5. Test on mobile browsers (iOS Safari, Chrome Android)

## Files Modified Summary

| File | Changes |
|------|---------|
| `src/web/templates/base.html` | Added Alpine.js CDN script |
| `src/web/templates/feed.html` | Added player bar, Alpine component, CSS |
| `src/web/templates/partials/feed_item.html` | Added play button, data attributes |
| `src/web/feed_routes.py` (or new `audio_routes.py`) | Added `/audio/<id>` route with HTTP 206 support |
| `src/models/feed_models.py` | Added `has_audio` computed property |
| `src/web/app.py` | Registered audio blueprint |

## Performance Notes

- Audio files are immutable (content-addressed) - safe to cache aggressively
- HTTP 206 range support allows instant seeking (no full file download)
- Alpine.js is 12KB minified - negligible impact on page load
- File existence checks batched in repository layer (one `glob()` vs many `exists()`)

## Security Notes

- `@login_required` enforces authentication
- Item ID validation prevents path traversal
- Audio files only served from `data/audio_cache/` directory
- No directory listing exposed
