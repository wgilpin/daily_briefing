# Feature Specification: Newsletter Audio Generation

**Feature Branch**: `007-newsletter-audio`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "The system should take the daily newsletter it generates and process it using eleven labs. Have two voices, one male one female on alternating items. The output is an mp3 file saved to disk alongside the markdown"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Audio Newsletter Generation (Priority: P1)

A user wants to consume their daily newsletter in audio format, listening while commuting, exercising, or doing other activities where reading is impractical. The system automatically generates an audio version of each newsletter using text-to-speech technology with alternating voices to make content more engaging and easier to follow.

**Why this priority**: This is the core value proposition - enabling audio consumption of newsletter content. Without this, the feature provides no value.

**Independent Test**: Can be fully tested by generating a newsletter, verifying an MP3 file is created alongside the markdown, and confirming the audio contains the newsletter content with alternating voices. Delivers immediate value as a standalone audio output feature.

**Acceptance Scenarios**:

1. **Given** a daily newsletter has been generated and saved as markdown, **When** the audio generation process runs, **Then** an MP3 file is created in the same directory with the same base filename
2. **Given** the newsletter contains multiple items (articles), **When** the audio is generated, **Then** odd-numbered items use a male voice and even-numbered items use a female voice
3. **Given** a newsletter with 5 items has been converted to audio, **When** listening to the MP3, **Then** the voices alternate: male, female, male, female, male
4. **Given** the audio generation process completes successfully, **When** checking the output directory, **Then** both the markdown and MP3 files exist with matching timestamps in their filenames

---

### User Story 2 - Automatic Processing of New Newsletters (Priority: P2)

The system automatically detects when a new newsletter is generated and triggers audio generation without manual intervention, ensuring users always have an audio version available.

**Why this priority**: Automation removes manual steps and ensures consistency. Users shouldn't need to remember to generate audio - it should just be there.

**Independent Test**: Generate a new newsletter through the existing workflow and verify that an audio file is automatically created without any additional commands. Demonstrates the integration works seamlessly.

**Acceptance Scenarios**:

1. **Given** the newsletter generation process completes, **When** the markdown file is saved, **Then** the audio generation is automatically triggered
2. **Given** audio generation fails for any reason, **When** the error occurs, **Then** the system logs the error and the markdown newsletter remains available for reading
3. **Given** multiple newsletters are generated in sequence, **When** each completes, **Then** each has its own corresponding audio file

---

### User Story 3 - Ultra-Clean Audio Content (Priority: P3)

The audio contains only article content with no metadata whatsoever - no section headers, no article titles, no dates, no source URLs. This creates a radio-style listening experience where content flows naturally from one item to the next, distinguished only by alternating voices.

**Why this priority**: Spoken metadata breaks the listening flow. Article titles are often redundant with the first sentence, and headers/dates/URLs add no value when listened to. Voice alternation provides sufficient topic separation.

**Independent Test**: Generate audio from a newsletter with multiple sections, titles, dates, and source links, then listen to verify that ONLY article content body text is spoken - no other elements from the markdown.

**Acceptance Scenarios**:

1. **Given** a newsletter with category headers (like "## Artificial Intelligence"), **When** the audio is generated, **Then** the category name is NOT spoken - audio flows directly from one article content to the next
2. **Given** a newsletter item with "#### Article Title", **When** the audio is generated, **Then** the title is NOT spoken - audio starts directly with the content paragraph
3. **Given** a newsletter item with date ("*Date: February 5, 2026*") and source ("*Source: example.com*"), **When** that item is converted to audio, **Then** only the body content is spoken (dates and source URLs are excluded)

---

### Edge Cases

- What happens when the newsletter markdown file is empty or contains no items?
- How does the system handle ElevenLabs API failures (rate limits, authentication errors, service outages)?
- What happens if the output directory is not writable or disk space is insufficient?
- How does the system handle special characters, URLs, and markdown formatting in the newsletter text?
- What happens if ElevenLabs API is slow and audio generation takes longer than expected?
- How are very long newsletters handled (potential API payload limits or file size considerations)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate an MP3 audio file for each newsletter markdown file created
- **FR-002**: System MUST save the audio file in the same directory as the source markdown file with the same base filename (e.g., `digest_20260205_135306_678384.md` → `digest_20260205_135306_678384.mp3`)
- **FR-003**: System MUST use ElevenLabs text-to-speech API to convert newsletter text to audio
- **FR-004**: System MUST use two distinct voices - one male and one female
- **FR-005**: System MUST alternate voices between newsletter items, with odd-numbered items using male voice and even-numbered items using female voice
- **FR-006**: System MUST parse the markdown newsletter to extract article content while preserving logical structure (titles, sections, body text)
- **FR-007**: System MUST exclude metadata not suitable for audio (source URLs, raw dates) from the spoken content
- **FR-008**: System MUST handle API failures gracefully and log errors without crashing the newsletter generation process
- **FR-009**: System MUST store ElevenLabs API credentials securely in environment variables (via `.env` file)
- **FR-010**: System SHOULD NOT include section headers, article titles, dates, or source links in spoken audio (article content only for clean listening)
- **FR-011**: System MUST process the complete newsletter text including all categories and items in sequence

### Key Entities *(include if feature involves data)*

- **Newsletter Markdown**: The source document containing formatted newsletter content with categories, subsections, article titles, dates, summaries, and source links
- **Audio Segment**: A portion of the generated audio corresponding to a single newsletter item, associated with a specific voice (male or female)
- **Voice Configuration**: The ElevenLabs voice identifiers for the male and female voices used in alternating pattern
- **Audio File**: The final MP3 output containing all segments concatenated in sequence with matching filename to the source markdown

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every newsletter generation produces both a markdown file and a corresponding MP3 file in the same directory
- **SC-002**: Audio files contain all newsletter content in the correct sequence with alternating voices
- **SC-003**: Users can listen to the complete newsletter content without needing to refer to the markdown file
- **SC-004**: Audio generation completes within 5 minutes for newsletters up to 50 items
- **SC-005**: The audio clearly distinguishes between items through voice alternation, making it easy to follow topic changes

## Assumptions

- ElevenLabs API is accessible and users have valid API credentials
- The existing newsletter generation system produces markdown files in a consistent format
- Newsletter items are clearly delimited in the markdown (either by headers or consistent markdown structure)
- Standard speech synthesis of technical content is acceptable (no custom pronunciation required)
- MP3 is an acceptable audio format for users
- Audio quality provided by ElevenLabs default settings is sufficient
- Sequential processing is acceptable (no need for parallel audio generation)
- The newsletter generation process can be extended to call audio generation after markdown creation
