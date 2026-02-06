# Research: HTML5 Audio Playback UI Implementation

**Date**: 2026-02-06
**Feature**: 009-audio-playback-ui
**Focus**: Simple, maintainable audio playback for Flask + HTMX prototype

## 1. Client-Side Audio State Management

### Decision: Vanilla JavaScript with DOM-based State

Use a single global `<audio>` element with vanilla JavaScript event listeners to track playback state. Store current item ID and position in JavaScript variables, synchronized with DOM data attributes for visual feedback.

### Rationale

- **Zero dependencies**: No libraries needed for basic audio control
- **HTMX compatibility**: DOM attributes integrate naturally with HTMX's attribute-based architecture
- **Browser native**: HTMLMediaElement API is stable and universally supported
- **Simple state model**: ~50 lines of JavaScript can handle all playback logic

### Implementation Pattern

```javascript
// Global state object - simple and explicit
const audioPlayer = {
  audio: null,  // HTMLAudioElement
  currentItemId: null,
  currentIndex: -1,
  isPlaying: false
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  audioPlayer.audio = document.getElementById('global-audio-player');

  // Core event listeners
  audioPlayer.audio.addEventListener('play', () => {
    audioPlayer.isPlaying = true;
    updatePlayButton('pause');
  });

  audioPlayer.audio.addEventListener('pause', () => {
    audioPlayer.isPlaying = false;
    updatePlayButton('play');
  });

  audioPlayer.audio.addEventListener('ended', () => {
    audioPlayer.isPlaying = false;
    audioPlayer.currentItemId = null;
    updatePlayButton('play');
    clearHighlight();
  });

  // Track position for resume capability
  audioPlayer.audio.addEventListener('timeupdate', () => {
    // Position automatically preserved in audio.currentTime
  });
});

// Play specific item
function playItem(itemId, audioPath) {
  const items = document.querySelectorAll('.feed-item');
  audioPlayer.currentIndex = Array.from(items).findIndex(
    item => item.dataset.itemId === itemId
  );

  audioPlayer.currentItemId = itemId;
  audioPlayer.audio.src = audioPath;
  audioPlayer.audio.play();

  highlightItem(itemId);
  scrollToItem(itemId);
}
```

### Alternatives Considered

**Option 1: Web Audio API**
- **Rejected**: Overkill for simple playback. Designed for audio synthesis, effects, visualization. Adds complexity with no benefit for basic play/pause/seek.

**Option 2: Lightweight library (Howler.js, Plyr)**
- **Rejected**: Violates "simplicity over generalization" principle. HTMLMediaElement provides all needed functionality. Adding a library is maintenance overhead for features we don't need (playlists, effects, custom UI themes).

**Option 3: React/Vue state management**
- **Rejected**: Would require rewriting entire UI. HTMX is already the chosen architecture. Adding a JS framework contradicts the hypermedia approach.

### Browser Support

All modern browsers fully support HTMLMediaElement with consistent event APIs:
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support (including iOS)
- No polyfills needed for 2026 target browsers

**Sources:**
- [MDN: HTMLAudioElement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLAudioElement/Audio)
- [MDN: Cross-browser audio basics](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Audio_and_video_delivery/Cross-browser_audio_basics)
- [HTML5 Doctor: HTML5 Audio State of Play](http://html5doctor.com/html5-audio-the-state-of-play/)

---

## 2. Audio File Serving from Flask

### Decision: HTTP 206 Partial Content with Flask send_file + Range Headers

Serve MP3 files using Flask's `send_file()` with manual HTTP 206 Range request support for proper seeking and browser compatibility.

### Rationale

- **Browser requirement**: Chrome and Firefox expect 206 responses for media seeking. Without it, seeking breaks and `ended` events don't fire reliably.
- **Streaming efficiency**: Partial content allows browsers to request only needed byte ranges, reducing bandwidth and enabling instant seeking.
- **Flask native**: `send_file()` handles MIME types, caching, and file handles correctly. We just add Range header logic on top.
- **Security**: Serve from dedicated `/audio/<item_id>` route with authentication check before file access.

### Implementation Pattern

```python
from flask import send_file, request, abort
import os

@app.route('/audio/<item_id>')
@login_required  # Authentication gate
def serve_audio(item_id):
    """Serve MP3 file with HTTP 206 partial content support."""

    # Map item_id to audio file (using content hash)
    audio_path = get_audio_path_for_item(item_id)
    if not audio_path or not os.path.exists(audio_path):
        abort(404, "Audio not found")

    # Get file size for Content-Length
    file_size = os.path.getsize(audio_path)

    # Check for Range header (byte-range request)
    range_header = request.headers.get('Range')

    if not range_header:
        # Full file request (first load)
        response = send_file(
            audio_path,
            mimetype='audio/mpeg',
            as_attachment=False,
            conditional=True  # Enable ETag/Last-Modified
        )
        response.headers['Accept-Ranges'] = 'bytes'
        return response

    # Parse range: "bytes=start-end"
    byte_range = range_header.replace('bytes=', '').split('-')
    start = int(byte_range[0]) if byte_range[0] else 0
    end = int(byte_range[1]) if byte_range[1] else file_size - 1
    length = end - start + 1

    # Read partial file content
    with open(audio_path, 'rb') as f:
        f.seek(start)
        data = f.read(length)

    # Build 206 response
    response = make_response(data, 206)
    response.headers['Content-Type'] = 'audio/mpeg'
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    response.headers['Content-Length'] = str(length)

    # Caching headers (audio files are immutable once generated)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year

    return response

def get_audio_path_for_item(item_id):
    """Map item ID to audio file path."""
    # Audio files named by content hash (e.g., 1a4f6b0976cc66ba.mp3)
    audio_dir = Path('data/audio_cache')
    audio_file = audio_dir / f"{item_id}.mp3"
    return str(audio_file) if audio_file.exists() else None
```

### Security Considerations

1. **Authentication required**: Route uses `@login_required` decorator (existing auth system)
2. **Path traversal prevention**: Only serve files from `data/audio_cache/` directory
3. **Input validation**: Sanitize `item_id` parameter (alphanumeric hash only)
4. **File existence check**: Return 404 for missing files (don't leak file system structure)
5. **No directory listing**: Serve individual files only, never expose directory contents

### Caching Strategy

```python
# For immutable audio files (content-addressed by hash)
Cache-Control: public, max-age=31536000, immutable

# Conditional requests enabled via send_file(conditional=True)
# Browser sends: If-None-Match: "etag-value"
# Server responds: 304 Not Modified (if unchanged)
```

### Alternatives Considered

**Option 1: Direct static file serving (Flask static folder)**
- **Rejected**: No authentication, no range request handling by default, exposes file paths. Insecure and doesn't meet browser media requirements.

**Option 2: Streaming with `stream_with_context()`**
- **Rejected**: Designed for long-lived connections (SSE, large uploads). Adds complexity with generators. `send_file()` with range support is simpler and handles all media needs.

**Option 3: Nginx X-Accel-Redirect**
- **Rejected**: Requires Nginx configuration, adds deployment complexity. This is a prototype running locally or on simple hosting. The Python implementation is sufficient for expected load.

**Sources:**
- [HTTP 206 Partial Content for Flask](https://blog.asgaard.co.uk/2012/08/03/http-206-partial-content-for-flask-python)
- [Flask streaming audio file (GitHub Gist)](https://gist.github.com/hosackm/289814198f43976aff9b)
- [DEV Community: Media Streaming with Flask](https://dev.to/singhpratyush/the-taste-of-media-streaming-with-flask-58a4)

---

## 3. UI Synchronization with HTMX

### Decision: Alpine.js for Local Interactivity + HTMX for Server Sync

Use Alpine.js (12KB) for audio player UI state (play/pause button, highlights) and preserve the audio element across HTMX content swaps with `hx-preserve`.

### Rationale

- **HTMX preservation**: The `hx-preserve` attribute keeps the audio player and its state intact during HTMX partial updates
- **Alpine.js fit**: Designed for exactly this use case - small reactive UI components in hypermedia architectures. Widely adopted with HTMX (2026 best practice).
- **No framework overhead**: Alpine works with existing HTML, doesn't require build tools or virtual DOM
- **Event-driven sync**: Custom events bridge audio playback state to UI updates

### Implementation Pattern

```html
<!-- Global audio player (preserved across HTMX swaps) -->
<div id="audio-player-bar"
     hx-preserve
     x-data="audioPlayerState()"
     class="audio-player-bar">

  <audio id="global-audio-player"
         @play="isPlaying = true"
         @pause="isPlaying = false"
         @ended="resetPlayer()"></audio>

  <div class="player-controls">
    <button @click="playPause()"
            :disabled="!currentItem"
            :aria-label="isPlaying ? 'Pause' : 'Play'">
      <span x-show="!isPlaying">▶ Play</span>
      <span x-show="isPlaying">⏸ Pause</span>
    </button>

    <button @click="previous()"
            :disabled="currentIndex <= 0"
            aria-label="Previous">
      ⏮ Previous
    </button>

    <button @click="next()"
            :disabled="currentIndex >= itemCount - 1"
            aria-label="Next">
      ⏭ Next
    </button>

    <span class="now-playing" x-text="currentItem?.title || 'No audio playing'"></span>
  </div>
</div>

<!-- Feed items with play buttons -->
<article class="feed-item"
         data-item-id="{{ item.id }}"
         data-audio-path="/audio/{{ item.id }}"
         :class="{ 'playing': $store.audio.currentId === '{{ item.id }}' }">

  {% if item.has_audio %}
  <button @click="$store.audio.playItem('{{ item.id }}', '/audio/{{ item.id }}')"
          class="item-play-btn"
          aria-label="Play {{ item.title }}">
    ▶
  </button>
  {% endif %}

  <!-- rest of feed item template -->
</article>

<script>
// Alpine.js component for player state
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
        this.playItem(
          nextItem.dataset.itemId,
          nextItem.dataset.audioPath
        );
      }
    },

    previous() {
      const items = document.querySelectorAll('[data-audio-path]');
      if (this.currentIndex > 0) {
        const prevItem = items[this.currentIndex - 1];
        this.playItem(
          prevItem.dataset.itemId,
          prevItem.dataset.audioPath
        );
      }
    },

    playItem(itemId, audioPath) {
      const audio = document.getElementById('global-audio-player');
      const items = document.querySelectorAll('[data-audio-path]');

      this.currentIndex = Array.from(items).findIndex(
        el => el.dataset.itemId === itemId
      );
      this.itemCount = items.length;

      this.currentItem = {
        id: itemId,
        title: items[this.currentIndex].querySelector('.feed-item-title').textContent
      };

      audio.src = audioPath;
      audio.play();

      // Scroll to item
      items[this.currentIndex].scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    },

    resetPlayer() {
      this.isPlaying = false;
      this.currentItem = null;
    }
  };
}

// Handle HTMX feed updates (filter changes, search)
document.body.addEventListener('htmx:beforeSwap', (event) => {
  // Stop playback when feed content changes
  if (event.detail.target.id === 'feed-items') {
    const audio = document.getElementById('global-audio-player');
    audio.pause();
    audio.src = '';

    // Reset Alpine state
    Alpine.store('audio', {
      currentId: null,
      currentIndex: -1
    });
  }
});
</script>
```

### HTMX Preservation Strategy

The `hx-preserve` attribute tells HTMX to keep the element across swaps:
- Audio element and playback state remain intact
- No interruption when feed content updates
- Player bar persists at top during scrolling and filtering

### Alternatives Considered

**Option 1: Pure vanilla JS without Alpine**
- **Rejected**: Would require ~150 lines of manual DOM manipulation for reactive UI updates. Alpine reduces this to ~50 lines with declarative syntax. The 12KB library cost is justified by maintainability improvement.

**Option 2: Full HTMX state management (server-driven)**
- **Rejected**: Audio playback is inherently client-side. Making every play/pause/seek call a server round-trip would add 50-200ms latency and unnecessary server load. Local state is correct here.

**Option 3: Global JavaScript state with custom events**
- **Rejected**: Reimplements Alpine's reactivity system. More code, more bugs, harder to maintain. Alpine is the "point solution library" that fits the constitution.

### Alpine.js Justification (Constitution Check)

Alpine.js qualifies as acceptable because:
1. **Small footprint**: 12KB minified - comparable to hand-written vanilla JS for this functionality
2. **Purpose-built**: Designed specifically for HTMX/hypermedia architectures (2026 recommended pairing)
3. **No build step**: Works with CDN, no webpack/bundler needed
4. **Reduces complexity**: Declarative bindings prevent 100+ lines of querySelector/addEventListener boilerplate

**Sources:**
- [HTMX Preservation with Audio Players](https://htmx.org/docs/)
- [HTMX in 2026: Hypermedia Dominance](https://vibe.forem.com/del_rosario/htmx-in-2026-why-hypermedia-is-dominating-the-modern-web-41id)
- [Hypermedia Sync Experiments](https://hypermedia.utilitygods.com/)

---

## 4. Keyboard Accessibility (WCAG Compliance)

### Decision: Native Button Elements + ARIA Labels + Standard Media Key Bindings

Use semantic HTML buttons with proper ARIA attributes and implement standard keyboard shortcuts for audio control.

### Rationale

- **WCAG 2.1 Level AA requirement**: Media players must be keyboard accessible
- **Screen reader support**: ARIA labels provide context for non-visual users
- **Standard conventions**: Space bar for play/pause, arrow keys for seek - users expect these
- **Zero extra code**: Native `<button>` elements are keyboard-focusable by default

### Implementation Pattern

```html
<!-- Player controls with full accessibility -->
<div class="audio-player-bar" role="region" aria-label="Audio player controls">

  <audio id="global-audio-player"
         aria-label="Feed item audio player">
  </audio>

  <div class="player-controls">
    <!-- Play/Pause button -->
    <button id="play-pause-btn"
            type="button"
            tabindex="0"
            @click="playPause()"
            @keydown.space.prevent="playPause()"
            :aria-label="isPlaying ? 'Pause audio' : 'Play audio'"
            :aria-pressed="isPlaying">
      <span aria-hidden="true" x-show="!isPlaying">▶</span>
      <span aria-hidden="true" x-show="isPlaying">⏸</span>
      <span class="sr-only" x-text="isPlaying ? 'Pause' : 'Play'"></span>
    </button>

    <!-- Previous button -->
    <button type="button"
            tabindex="0"
            @click="previous()"
            :disabled="currentIndex <= 0"
            aria-label="Play previous item">
      <span aria-hidden="true">⏮</span>
      <span class="sr-only">Previous</span>
    </button>

    <!-- Next button -->
    <button type="button"
            tabindex="0"
            @click="next()"
            :disabled="currentIndex >= itemCount - 1"
            aria-label="Play next item">
      <span aria-hidden="true">⏭</span>
      <span class="sr-only">Next</span>
    </button>

    <!-- Now playing indicator -->
    <div role="status"
         aria-live="polite"
         aria-atomic="true"
         class="now-playing">
      <span x-text="currentItem ? `Now playing: ${currentItem.title}` : 'No audio playing'"></span>
    </div>
  </div>
</div>

<!-- Feed item play buttons -->
<button type="button"
        tabindex="0"
        @click="$store.audio.playItem('{{ item.id }}', '/audio/{{ item.id }}')"
        aria-label="Play audio for {{ item.title }}"
        class="item-play-btn">
  <span aria-hidden="true">▶</span>
  <span class="sr-only">Play</span>
</button>

<style>
/* Screen-reader only text */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Visible focus indicator (WCAG 2.1 requirement) */
button:focus {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}

button:focus:not(:focus-visible) {
  outline: none;
}

button:focus-visible {
  outline: 2px solid #3498db;
  outline-offset: 2px;
}
</style>

<script>
// Global keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Only activate if no input is focused
  if (e.target.matches('input, textarea, select')) return;

  const audio = document.getElementById('global-audio-player');

  switch(e.key) {
    case ' ':  // Spacebar - play/pause
      e.preventDefault();
      if (audio.paused) {
        audio.play();
      } else {
        audio.pause();
      }
      break;

    case 'ArrowLeft':  // Seek backward 5 seconds
      e.preventDefault();
      audio.currentTime = Math.max(0, audio.currentTime - 5);
      break;

    case 'ArrowRight':  // Seek forward 5 seconds
      e.preventDefault();
      audio.currentTime = Math.min(audio.duration, audio.currentTime + 5);
      break;

    case 'n':  // Next item (lowercase)
    case 'N':  // Next item (uppercase)
      e.preventDefault();
      document.querySelector('[aria-label="Play next item"]')?.click();
      break;

    case 'p':  // Previous item
    case 'P':
      e.preventDefault();
      document.querySelector('[aria-label="Play previous item"]')?.click();
      break;
  }
});
</script>
```

### WCAG 2.1 Level AA Checklist

- ✅ **1.4.2 Audio Control**: User can pause/stop audio that plays automatically
- ✅ **2.1.1 Keyboard**: All functionality available via keyboard
- ✅ **2.1.2 No Keyboard Trap**: Focus can move away from audio controls
- ✅ **2.4.7 Focus Visible**: Focus indicator visible on all controls
- ✅ **4.1.2 Name, Role, Value**: ARIA labels provide accessible names
- ✅ **4.1.3 Status Messages**: `aria-live` announces playback state changes

### Standard Keyboard Shortcuts (Industry Convention)

| Key | Action | Standard |
|-----|--------|----------|
| Space | Play/Pause | YouTube, Spotify, VLC |
| Left Arrow | Seek -5 seconds | YouTube, HTML5 video |
| Right Arrow | Seek +5 seconds | YouTube, HTML5 video |
| N | Next item | Spotify, media players |
| P | Previous item | Spotify, media players |

### Alternatives Considered

**Option 1: Custom focus management system**
- **Rejected**: Browser handles tab order correctly with native buttons. Custom system would break expected behavior and require more code.

**Option 2: Click-only interface (no keyboard)**
- **Rejected**: Violates WCAG 2.1 Level A requirement 2.1.1. Would exclude keyboard-only users (motor disabilities, screen reader users).

**Option 3: Full media player library (Able Player, Plyr)**
- **Rejected**: Overkill for simple play/pause/next/prev. These libraries include video support, captions, transcripts - features we don't need. The ~50 lines above provide full accessibility.

**Sources:**
- [W3C: Media Players Accessibility](https://www.w3.org/WAI/media/av/player/)
- [WCAG 2.1: Audio Control Success Criterion](https://www.w3.org/WAI/WCAG21/Understanding/audio-control.html)
- [Radiant Media Player: Accessibility Features](https://www.radiantmediaplayer.com/docs/latest/accessibility-features.html)
- [DigitalA11Y: Accessible HTML5 Media Players](https://www.digitala11y.com/accessible-jquery-html5-media-players/)

---

## 5. Smooth Scrolling Implementation

### Decision: Native `scrollIntoView()` with `behavior: 'smooth'`

Use the browser-native `scrollIntoView()` API with smooth behavior option. No polyfills or libraries needed for 2026 browser targets.

### Rationale

- **Universal support**: All modern browsers support smooth scrolling as of 2020+ (Chrome, Firefox, Safari, Edge)
- **Zero dependencies**: Built into the DOM API
- **Performant**: Hardware-accelerated by browser rendering engine
- **Configurable**: Control alignment (top, center, nearest) and behavior (smooth, auto, instant)

### Implementation Pattern

```javascript
// Scroll to currently playing item
function scrollToPlayingItem(itemId) {
  const item = document.querySelector(`[data-item-id="${itemId}"]`);

  if (item) {
    item.scrollIntoView({
      behavior: 'smooth',    // Animated scroll (vs 'auto' for instant)
      block: 'start',        // Align to top of viewport
      inline: 'nearest'      // Don't scroll horizontally
    });

    // Announce to screen readers
    announceToScreenReader(`Now playing: ${item.querySelector('.feed-item-title').textContent}`);
  }
}

// Optional: Add offset for fixed header
function scrollToPlayingItemWithOffset(itemId, offsetPx = 80) {
  const item = document.querySelector(`[data-item-id="${itemId}"]`);

  if (item) {
    const itemTop = item.getBoundingClientRect().top;
    const offsetPosition = itemTop + window.pageYOffset - offsetPx;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }
}

// Helper for accessibility
function announceToScreenReader(message) {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', 'polite');
  announcement.className = 'sr-only';
  announcement.textContent = message;

  document.body.appendChild(announcement);
  setTimeout(() => announcement.remove(), 1000);
}
```

### CSS Alternative (Global Smooth Scrolling)

```css
/* Apply smooth scroll globally - simplest option */
html {
  scroll-behavior: smooth;
}

/* Or scope to specific container */
.feed-items {
  scroll-behavior: smooth;
}
```

With CSS `scroll-behavior: smooth`, any JavaScript call to `scrollIntoView()`, `scrollTo()`, or clicking anchor links will animate smoothly. Even simpler than the JavaScript option.

### Browser Support (2026)

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 61+ | ✅ Full | Since 2017 |
| Firefox 36+ | ✅ Full | Since 2015 |
| Safari 15.4+ | ✅ Full | Since March 2022 |
| Edge 79+ | ✅ Full | Chromium-based |

**No polyfills needed** for 2026 deployment. 99%+ of users have supporting browsers.

### Recommended Approach: CSS + JavaScript Hybrid

```css
/* Global smooth scroll for all navigation */
html {
  scroll-behavior: smooth;
}

/* Disable during page load for performance */
html.no-smooth-scroll {
  scroll-behavior: auto;
}
```

```javascript
// Disable smooth scroll during initial page load
document.documentElement.classList.add('no-smooth-scroll');

window.addEventListener('load', () => {
  // Enable after page fully loaded
  document.documentElement.classList.remove('no-smooth-scroll');
});

// Scroll to playing item (CSS handles animation automatically)
function scrollToPlayingItem(itemId) {
  const item = document.querySelector(`[data-item-id="${itemId}"]`);
  item?.scrollIntoView({ block: 'start' });
}
```

### Alternatives Considered

**Option 1: JavaScript animation library (GSAP, Anime.js)**
- **Rejected**: Overkill. Browser-native smooth scroll is sufficient. These libraries are for complex animations (parallax, physics), not simple scrolling.

**Option 2: jQuery animate()**
- **Rejected**: jQuery is deprecated in modern development. Native API is simpler and more performant.

**Option 3: Custom scroll animation loop**
```javascript
// Manual animation with requestAnimationFrame
function smoothScrollTo(element) {
  const start = window.pageYOffset;
  const target = element.getBoundingClientRect().top + start;
  const duration = 500;
  // ... 30+ lines of easing function, RAF loop, etc.
}
```
- **Rejected**: Reimplements browser functionality. More code, more bugs, worse performance (not GPU-accelerated). The native API does exactly this.

**Option 4: CSS `scroll-snap-*` properties**
- **Rejected**: Designed for swipeable carousels, not for programmatic scrolling. Would interfere with normal feed scrolling behavior.

### Performance Considerations

- **Smooth scroll is GPU-accelerated** in modern browsers (no jank)
- **User preference**: Respect `prefers-reduced-motion` for accessibility:

```css
@media (prefers-reduced-motion: reduce) {
  html {
    scroll-behavior: auto;  /* Instant scroll for users who need it */
  }
}
```

**Sources:**
- [MDN: Element.scrollIntoView()](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView)
- [Native Smooth Scrolling](https://hospodarets.com/native_smooth_scrolling)
- [Lucas Paganini: Native Smooth Scroll with CSS and JS](https://www.lucaspaganini.com/academy/native-smooth-scroll-with-pure-css-and-js/)
- [CSS-Tricks: Smooth Scrolling](https://css-tricks.com/snippets/jquery/smooth-scrolling/)

---

## Summary: Technology Decisions

| Component | Decision | Library/API | Size | Justification |
|-----------|----------|-------------|------|---------------|
| **Audio State** | Vanilla JS + HTMLMediaElement | Browser native | 0KB | ~50 lines handles all state |
| **Audio Serving** | Flask HTTP 206 + send_file | Flask built-in | 0KB | Required for seeking |
| **UI Sync** | Alpine.js + hx-preserve | Alpine.js | 12KB | HTMX best practice, prevents boilerplate |
| **Accessibility** | Semantic HTML + ARIA | Browser native | 0KB | WCAG compliance |
| **Smooth Scroll** | scrollIntoView + CSS | Browser native | 0KB | Universal support |

**Total JavaScript overhead**: 12KB (Alpine.js only)

All other functionality uses browser-native APIs with zero dependencies. This aligns with the project's "simplicity over generalization" principle while meeting all functional requirements.

---

## Implementation Checklist

- [ ] Add Alpine.js to base template (CDN link)
- [ ] Create global audio player bar with `hx-preserve`
- [ ] Add Flask route `/audio/<item_id>` with HTTP 206 support
- [ ] Update feed item template with play buttons and data attributes
- [ ] Implement Alpine.js audio state component
- [ ] Add keyboard event listeners for shortcuts
- [ ] Style focus indicators for accessibility
- [ ] Add CSS `scroll-behavior: smooth` with reduced-motion support
- [ ] Test with screen reader (NVDA/JAWS)
- [ ] Test keyboard navigation (Tab, Space, arrows)
- [ ] Test HTMX filter changes with audio playing
- [ ] Verify HTTP 206 range requests in browser DevTools

---

## References

### Client-Side State Management
- [JavaScript Check If Audio Is Playing](https://copyprogramming.com/howto/jquery-check-if-audio-is-playing)
- [HTML5 Audio Player Tutorial (IMAJINE)](https://imajineweb.com/javascriptaudioplayer/)
- [MDN: HTMLAudioElement](https://developer.mozilla.org/en-US/docs/Web/API/HTMLAudioElement/Audio)
- [MDN: Cross-browser Audio Basics](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Audio_and_video_delivery/Cross-browser_audio_basics)

### Flask Audio Serving
- [HTTP 206 Partial Content for Flask/Python](https://blog.asgaard.co.uk/2012/08/03/http-206-partial-content-for-flask-python)
- [Flask Streaming Audio File (GitHub Gist)](https://gist.github.com/hosackm/289814198f43976aff9b)
- [DEV Community: Media Streaming with Flask](https://dev.to/singhpratyush/the-taste-of-media-streaming-with-flask-58a4)

### HTMX UI Synchronization
- [HTMX in 2026: Why Hypermedia is Dominating](https://vibe.forem.com/del_rosario/htmx-in-2026-why-hypermedia-is-dominating-the-modern-web-41id)
- [HTMX Documentation](https://htmx.org/docs/)
- [Hypermedia Sync Experiments](https://hypermedia.utilitygods.com/)

### Accessibility
- [W3C: Media Players Accessibility](https://www.w3.org/WAI/media/av/player/)
- [WCAG 2.1: Audio Control](https://www.w3.org/WAI/WCAG21/Understanding/audio-control.html)
- [Radiant Media Player: Accessibility Features](https://www.radiantmediaplayer.com/docs/latest/accessibility-features.html)
- [DigitalA11Y: Accessible HTML5 Media Players](https://www.digitala11y.com/accessible-jquery-html5-media-players/)

### Smooth Scrolling
- [MDN: Element.scrollIntoView()](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView)
- [Native Smooth Scrolling](https://hospodarets.com/native_smooth_scrolling)
- [Lucas Paganini: Native Smooth Scroll](https://www.lucaspaganini.com/academy/native-smooth-scroll-with-pure-css-and-js/)
