# Feature Specification: Topic Exclusion Filter

**Feature Branch**: `005-topic-exclusion`
**Created**: 2026-02-03
**Status**: Draft
**Input**: User description: "Implement a 'Topic Exclusion' filter for the newsletter consolidation process."

## Clarifications

### Session 2026-02-03

- Q: Where should the excluded_topics array be stored? → A: Add excluded_topics array to existing config/senders.json at root level
- Q: When a user tries to add a topic that already exists in the exclusion list, what should happen? → A: Allow duplicates in the list (stored multiple times)
- Q: When ALL newsletter items match excluded topics (resulting in an empty newsletter), what should the user receive? → A: Newsletter with message explaining all items were filtered
- Q: Should there be a maximum length limit for individual excluded topic strings? → A: Limit to 100 characters per topic
- Q: Should there be a limit on the total number of topics a user can exclude? → A: Limit to 50 total excluded topics

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configure Excluded Topics via UI (Priority: P1)

As a newsletter reader, I want to configure a list of topics to exclude from my consolidated newsletter so that I don't see content about subjects I'm not interested in (like "datasette" or "low-level coding").

**Why this priority**: This is the core user-facing functionality that delivers immediate value. Without the ability to configure exclusions, the feature cannot be used.

**Independent Test**: Can be fully tested by adding topics to the exclusion list through the settings UI, saving the configuration, and verifying the topics are persisted in the configuration file.

**Acceptance Scenarios**:

1. **Given** I am viewing the settings tab, **When** I navigate to the topic exclusion section, **Then** I see an interface for managing excluded topics
2. **Given** I am in the topic exclusion settings, **When** I add a new topic (e.g., "SQL internals") and save, **Then** the topic appears in my exclusion list
3. **Given** I have topics in my exclusion list, **When** I delete a topic and save, **Then** the topic is removed from the list
4. **Given** I have configured exclusions, **When** I refresh the settings page, **Then** my previously saved exclusions are displayed

---

### User Story 2 - Filter Newsletter Content (Priority: P2)

As a newsletter reader, when the system generates my consolidated newsletter, I want items matching my excluded topics to be automatically filtered out so that my digest only contains content I care about.

**Why this priority**: This is the actual filtering functionality that makes the configuration useful. It depends on P1 being complete but delivers the core business value.

**Independent Test**: Can be tested by configuring excluded topics, triggering newsletter consolidation with test data containing both included and excluded topics, and verifying the output excludes the specified topics.

**Acceptance Scenarios**:

1. **Given** I have "datasette" in my exclusion list, **When** the system consolidates newsletters containing datasette articles, **Then** those articles do not appear in my consolidated digest
2. **Given** I have "low-level coding" in my exclusion list, **When** the system processes items with low-level coding content, **Then** the LLM is instructed to discard these items
3. **Given** I have no exclusions configured, **When** the system consolidates newsletters, **Then** all items are included as before
4. **Given** I have multiple excluded topics, **When** the system consolidates newsletters, **Then** items matching any of the excluded topics are filtered out

---

### Edge Cases

- What happens when an excluded topic is very broad or ambiguous (e.g., "coding" vs "low-level coding")?
- How does the system handle empty exclusion lists?
- What if all newsletter items match excluded topics? (Generate newsletter with informative message explaining all items were filtered by exclusion rules)
- How does the system handle case sensitivity in topic matching (e.g., "SQL" vs "sql")?
- What happens if the user enters duplicate topics in the exclusion list? (System allows duplicates; LLM handles semantic matching)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a configuration structure for storing excluded topics as a list/array
- **FR-002**: System MUST persist excluded topics in config/senders.json as a root-level "excluded_topics" array
- **FR-003**: System MUST provide a settings UI section for managing excluded topics
- **FR-004**: Users MUST be able to add new topics to the exclusion list via the settings UI (maximum 100 characters per topic, maximum 50 topics total)
- **FR-016**: System MUST prevent adding topics when the 50-topic limit is reached and display an informative message
- **FR-005**: Users MUST be able to delete topics from the exclusion list via the settings UI
- **FR-006**: System MUST save exclusion list changes when user submits the settings form
- **FR-007**: System MUST load and display existing exclusions when settings page is accessed
- **FR-008**: The consolidator module MUST accept the exclusion list as a parameter
- **FR-009**: The consolidator MUST inject exclusion instructions into the LLM prompt
- **FR-010**: The exclusion instructions in the prompt MUST be clear, direct, and high-priority for the LLM using the pattern defined in research.md Section 3: CRITICAL INSTRUCTION prefix, explicit language (MUST, Do NOT), positioned at prompt start, with bullet-formatted topic list
- **FR-011**: System MUST handle empty exclusion lists gracefully (no filtering applied)
- **FR-015**: When all items are filtered by exclusions, system MUST generate a newsletter with an informative message explaining the filtering outcome
- **FR-012**: System MUST maintain all existing consolidation functionality when no exclusions are configured
- **FR-013**: The UI MUST use HTMX for dynamic list management (add/delete without full page reload)
- **FR-014**: The exclusion list MUST be stored in a JSON-compatible format

### Key Entities

- **Excluded Topic**: A string (max 100 characters) representing a topic or subject area to filter out from newsletters (e.g., "datasette", "low-level coding", "SQL internals")
- **Configuration**: Extended structure in config/senders.json with an "excluded_topics" array at the root level alongside existing settings like "consolidation_prompt" and "retention_limit"

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add and remove excluded topics through the settings UI in under 30 seconds per topic
- **SC-002**: Consolidated newsletters exclude items matching configured excluded topics based on LLM semantic interpretation. Target: 90% exclusion rate based on manual review of sample consolidations (not automated test - LLM semantic matching is non-deterministic).
- **SC-003**: The exclusion configuration persists across application restarts and newsletter generation cycles
- **SC-004**: Users receive newsletters with only relevant content, reducing time spent scanning unwanted items by at least 50%
- **SC-005**: The feature works as a transparent filter - newsletters without excluded topics are generated identically to the previous behavior

## Assumptions

- The LLM (Gemini) is capable of understanding and following topic exclusion instructions in the prompt
- Topic matching will be semantic (handled by LLM interpretation) rather than exact string matching
- Users will configure a reasonable number of exclusions (typically 3-10 topics, with a hard limit of 50 topics)
- The settings UI follows existing Flask+HTMX patterns in the application
- Configuration changes take effect on the next newsletter consolidation cycle (not retroactive)

## Dependencies

- Existing consolidator.py module and consolidate_newsletters function
- Existing config/senders.json structure and configuration loading mechanism
- Existing Flask settings UI and HTMX integration patterns
- Access to Gemini LLM API for processing exclusion instructions

## Out of Scope

- Machine learning-based topic classification or automatic topic detection
- Fine-grained filtering rules (e.g., "exclude datasette but only from specific senders")
- Topic suggestion or auto-complete functionality
- Analytics on which topics are most commonly excluded
- Retroactive filtering of already-generated newsletters
- User-specific exclusions (multi-user support)
