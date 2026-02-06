# Feature Specification: Audio Playback UI Controls

**Feature Branch**: `009-audio-playback-ui`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "Let's add UI playback of the audio. Based on the current UI. Add buttons Play/Pause, Next, Previous. Play the audio segment for the current item. Next will skip to next item. Scroll the UI so the current playing item is at the top of the screen"

## Clarifications

### Session 2026-02-06

- Q: Where should the playback controls be located? → A: Single global player bar at top right with all controls (Play/Pause/Next/Previous)
- Q: How do users select which feed item to play? → A: Click a small play icon/button on each feed item card
- Q: What happens when clicking Next on last item or Previous on first item? → A: Stop playback and disable the respective button
- Q: What happens to playback when user changes filters or searches? → A: Stop playback completely and reset player to initial state
- Q: How should the system link feed items to audio files? → A: Use feed item unique ID or stable hash

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Basic Audio Playback (Priority: P1)

Users can play and pause audio narration for feed items directly from the unified feed interface.

**Why this priority**: Core functionality - without play/pause, users cannot consume the audio content at all. This is the minimum viable feature.

**Independent Test**: Can be fully tested by clicking play button on any feed item and verifying audio plays, then clicking pause and verifying audio stops. Delivers immediate value of audio consumption.

**Acceptance Scenarios**:

1. **Given** a user is viewing the unified feed with items that have audio, **When** they click the play icon on a feed item card, **Then** the audio for that item begins playing, the global player bar activates showing "Pause", and the item is visually highlighted
2. **Given** audio is currently playing for a feed item, **When** the user clicks the Pause button in the global player bar, **Then** the audio pauses and the button changes to show "Play"
3. **Given** audio is paused mid-playback, **When** the user clicks Play again, **Then** the audio resumes from where it was paused
4. **Given** audio is playing, **When** the audio reaches the end of the item, **Then** playback stops and the button returns to "Play" state

---

### User Story 2 - Sequential Navigation (Priority: P2)

Users can navigate between feed items using Next and Previous buttons while audio is playing.

**Why this priority**: Enables continuous listening experience without manual clicking. Users can consume multiple items in sequence, which significantly improves the audio experience beyond single-item playback.

**Independent Test**: Can be tested by starting audio playback on one item, clicking Next, and verifying that the next item's audio begins playing. Works independently of P1 functionality.

**Acceptance Scenarios**:

1. **Given** audio is playing for a feed item, **When** the user clicks the Next button, **Then** the current audio stops and the next feed item's audio begins playing automatically
2. **Given** audio is playing for a feed item that is not the first item, **When** the user clicks the Previous button, **Then** the current audio stops and the previous feed item's audio begins playing automatically
3. **Given** audio is playing for the last feed item in the visible list, **When** the user clicks Next, **Then** playback stops, the Next button becomes disabled, and the Play/Pause button returns to "Play" state
4. **Given** audio is playing for the first feed item, **When** the user clicks Previous, **Then** playback stops, the Previous button becomes disabled, and the Play/Pause button returns to "Play" state
5. **Given** the Previous button is disabled because playback was on the first item, **When** the user starts playing a different item that is not the first, **Then** the Previous button becomes enabled again
6. **Given** a user navigates to a new item using Next/Previous, **When** the new item begins playing, **Then** the playing item is visually highlighted or indicated in the feed

---

### User Story 3 - Auto-Scroll to Playing Item (Priority: P3)

The feed automatically scrolls to keep the currently playing item visible at the top of the viewport.

**Why this priority**: Quality-of-life improvement - helps users follow along with the visual content while listening, but the audio playback is functional without it. Particularly useful for long feeds where items scroll off-screen.

**Independent Test**: Can be tested by scrolling down in the feed, starting playback on an off-screen item, and verifying the page scrolls to bring that item to the top. Delivers value of synchronized visual/audio experience.

**Acceptance Scenarios**:

1. **Given** a user starts playing audio for a feed item that is not currently visible, **When** playback begins, **Then** the page smoothly scrolls to position that item at or near the top of the viewport
2. **Given** audio is playing and the user navigates to the next item, **When** the new item begins playing, **Then** the page scrolls to position the new playing item at the top
3. **Given** the currently playing item is already visible at the top of the viewport, **When** the user clicks Next, **Then** the scroll behavior still brings the next item to the top (consistent behavior)
4. **Given** a user manually scrolls away from the currently playing item, **When** they navigate to the next item, **Then** the page scrolls back to show the new playing item at the top

---

### Edge Cases

- What happens when a user clicks Play on an item that doesn't have audio available? (Should show error message or disable button)
- How does the system handle network errors when loading audio files? (Should display error and allow retry)
- What happens if the user changes filters/search while audio is playing? Stop playback completely, reset player to initial state, and clear any item highlighting
- How does playback behave when reaching the end of filtered results? Stop playback and disable Next button at last filtered item
- What happens when the user navigates away from the feed page while audio is playing? (Should pause or stop audio)
- How does the system handle very short audio segments (< 2 seconds)? (Should play normally, Next/Previous should still work)
- What happens when the user rapidly clicks Next/Previous multiple times? (Should handle gracefully, debounce or queue commands)
- How does the player behave when the feed is refreshed while audio is playing? (Should pause/stop to avoid playback of stale content)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a global player bar positioned at top right of the feed interface containing Play/Pause, Previous, and Next controls
- **FR-001a**: System MUST provide a small play icon/button on each feed item card that has associated audio to initiate playback
- **FR-002**: System MUST toggle between "Play" and "Pause" states in the global player bar based on current playback status
- **FR-003**: System MUST provide Previous and Next navigation buttons within the global player bar to move between feed items during playback
- **FR-004**: System MUST automatically begin playing the next/previous item's audio when Next/Previous is clicked
- **FR-005**: System MUST visually indicate which feed item is currently playing (e.g., highlight, different background color, play icon)
- **FR-006**: System MUST automatically scroll the page to position the currently playing item at or near the top of the viewport when playback starts or when navigating between items
- **FR-007**: System MUST use smooth scrolling animation when auto-scrolling to the playing item (not instant jump)
- **FR-008**: System MUST load and play the correct audio file that corresponds to each feed item
- **FR-009**: System MUST handle the end of an audio segment by stopping playback and resetting the Play/Pause button to "Play" state
- **FR-010**: System MUST hide the play icon on feed item cards that do not have associated audio content
- **FR-011**: System MUST preserve playback position when paused, allowing resume from the same point
- **FR-012**: System MUST stop or pause audio playback when the user navigates away from the feed page
- **FR-013**: System MUST display user-friendly error messages when audio fails to load or play
- **FR-014**: System MUST stop playback and disable the Next button when Next is clicked on the last feed item with audio
- **FR-014a**: System MUST stop playback and disable the Previous button when Previous is clicked on the first feed item with audio
- **FR-014b**: System MUST re-enable navigation buttons when playback moves to a non-boundary item
- **FR-015**: System MUST stop playback completely and reset the player to initial state when the user changes source filters, search query, or days filter

### Key Entities

- **Audio Segment**: References an MP3 file in data/audio_cache/ directory, associated with a specific feed item via stable content hash filename (e.g., `1a4f6b0976cc66ba.mp3`)
- **Playback State**: Tracks current playing status (playing/paused/stopped), currently playing item identifier, playback position, and playback queue position
- **Feed Item**: Existing entity that now includes a unique identifier (ID or stable hash) used to locate its corresponding audio file, plus a boolean flag indicating audio availability

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully play audio for any feed item with available audio in under 2 seconds from clicking Play
- **SC-002**: Page scrolls to position the playing item within the viewport in under 500ms when playback starts or navigation occurs
- **SC-003**: 100% of navigation actions (Next/Previous) complete within 1 second, including loading and starting playback of the new item
- **SC-004**: Users can pause and resume playback without loss of playback position (within 1 second accuracy)
- **SC-005**: Visual indication of currently playing item is clearly visible to users (validated through user testing or accessibility standards)
- **SC-006**: System handles all edge cases (no audio, network errors, end of list) without crashes or broken UI states
- **SC-007**: Audio controls are accessible via keyboard navigation for users who cannot use a mouse
- **SC-008**: 95% of users can successfully play, pause, and navigate between audio items on first attempt without instructions

## Assumptions & Dependencies

### Assumptions

- Audio files for feed items already exist in the data/audio_cache/ directory (from feature 007/008)
- Each feed item that has audio can be uniquely identified and linked to its corresponding audio file using content-based hash filenames (e.g., `1a4f6b0976cc66ba.mp3`)
- Audio files are in MP3 format compatible with HTML5 audio playback in modern browsers
- Users are accessing the feed via a modern web browser with HTML5 audio support
- The feed UI (feed.html) can be modified to add controls without breaking existing functionality
- HTMX is available for dynamic updates and interactions
- Smooth scrolling behavior is supported by the browser (with fallback to instant scroll)
- Network connection is sufficient to stream audio files (no requirement for offline playback)

### Dependencies

- **Internal**: Existing feed rendering system (src/web/templates/feed.html, partials/feed_item.html)
- **Internal**: Audio generation system from features 007/008 that creates MP3 files
- **Internal**: Feed item data structure must include audio file path or ID
- **External**: Modern web browser with HTML5 audio API support
- **External**: JavaScript for playback control logic (may use vanilla JS or minimal library)

### Out of Scope

- Playlist creation or saving favorite items
- Volume controls (browser default controls are sufficient)
- Playback speed controls (1x, 1.5x, 2x)
- Audio waveform visualization
- Downloading audio files for offline listening
- Sharing or exporting audio segments
- Audio transcripts or closed captions display
- Background playback when browser tab is not active
- Integration with system media controls (OS-level play/pause)
- Audio analytics (tracking which items are played most)
- Continuous playback across page navigation or refreshes
