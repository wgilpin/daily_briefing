# Feature Specification: Newsletter Aggregator

**Feature Branch**: `002-newsletter-aggregator`  
**Created**: 2024-12-30  
**Status**: Draft  
**Input**: User description: "An app that collects emails form specified senders for processing. These sources will be newsletters. The newsletters are converted into a general foramt such as markdown, then subject to prompt-based parsing - for each newsletter there is a configurable prompt, so after the newsletter is downloaded from gmail it is then subject to processing as instructed in the prompt, to allow simple addition of more fomats. The output of all newsletters will be a list in the format of {date, title, summary, link (if provided)}. These lists are then processed by a final prompt to generate the output, which is a consolodated newsletter suitable for reading or for turning into a simple podcast style audio. This is a single user app, and all data is stored locally"

## Clarifications

### Session 2024-12-30

- Q: When collecting emails from configured senders, which emails should be processed? → A: All emails from senders (regardless of read status or location), but track locally to avoid repetition
- Q: How long should the system retain collected emails, markdown files, and parsed data locally? → A: Keep the most recent N records (configurable, with reasonable default)
- Q: How should the final consolidation prompt be configured? → A: Single configurable prompt (user can customize it)
- Q: When a single newsletter email contains multiple articles or items, how should it be processed? → A: One email can produce multiple parsed items (one per article/item found)
- Q: What format should the final consolidated newsletter output be? → A: Markdown format

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect Emails from Specified Senders (Priority: P1)

As a user, I want to collect emails from specified newsletter senders so that I can process them into a consolidated digest.

**Why this priority**: This is the foundational functionality - without collecting emails from Gmail, no processing can occur. This represents the minimum viable product.

**Independent Test**: Can be fully tested by configuring sender email addresses and verifying that emails from those senders are successfully retrieved from Gmail.

**Acceptance Scenarios**:

1. **Given** I have configured one or more sender email addresses, **When** I run the collection process, **Then** all emails from those senders are retrieved from my Gmail account (regardless of read status or location)
2. **Given** I have configured sender email addresses and there are no emails from those senders, **When** I run the collection process, **Then** I receive a message indicating no emails were found
3. **Given** I have configured sender email addresses, **When** I run the collection process, **Then** only emails not previously processed (tracked locally) are collected to avoid duplicate processing
4. **Given** I have configured sender email addresses with valid Gmail authentication, **When** I run the collection process, **Then** emails are successfully downloaded and stored locally
5. **Given** Gmail authentication fails or expires, **When** I run the collection process, **Then** I receive a clear error message with instructions to re-authenticate

---

### User Story 2 - Convert Newsletters to Standard Format (Priority: P1)

As a user, I want newsletters converted to a standard format (markdown) so that they can be consistently processed regardless of their original email format.

**Why this priority**: Standardization is essential for the prompt-based parsing to work reliably. Without conversion to a consistent format, parsing would be unreliable.

**Independent Test**: Can be fully tested by providing sample newsletter emails and verifying they are converted to properly formatted markdown files.

**Acceptance Scenarios**:

1. **Given** emails have been collected from newsletter senders, **When** the conversion process runs, **Then** each email is converted to a markdown file with preserved content structure
2. **Given** an email contains HTML content, **When** the conversion process runs, **Then** the HTML is converted to markdown with formatting preserved (headings, links, lists)
3. **Given** an email contains plain text only, **When** the conversion process runs, **Then** the text is formatted as markdown with appropriate line breaks and structure
4. **Given** an email contains images or attachments, **When** the conversion process runs, **Then** references to images are preserved in markdown format (links or embedded references)
5. **Given** conversion fails for a specific email, **When** the process runs, **Then** the error is logged and processing continues for other emails

---

### User Story 3 - Parse Newsletters Using Configurable Prompts (Priority: P1)

As a user, I want each newsletter parsed using a configurable prompt so that I can extract structured information (date, title, summary, link) in a format that works for different newsletter styles.

**Why this priority**: Prompt-based parsing enables flexibility to handle different newsletter formats without code changes. This is core to the extensibility of the system.

**Independent Test**: Can be fully tested by configuring a prompt for a newsletter type and verifying that the markdown content is parsed into the expected structured format.

**Acceptance Scenarios**:

1. **Given** I have configured a prompt for a specific sender, **When** a newsletter from that sender is processed, **Then** the prompt is applied to extract date, title, summary, and link (if available)
2. **Given** I have configured prompts for multiple senders, **When** newsletters are processed, **Then** each newsletter uses the prompt configured for its sender
3. **Given** a newsletter is processed with a prompt, **When** the parsing completes, **Then** the output is one or more structured list items with format: {date, title, summary, link (if provided)} - multiple items if the newsletter contains multiple articles
4. **Given** a newsletter lacks some information (e.g., no link), **When** the parsing completes, **Then** the structured output omits missing fields or marks them as unavailable
5. **Given** parsing fails for a newsletter, **When** the process runs, **Then** the error is logged and the newsletter is marked for manual review

---

### User Story 4 - Generate Consolidated Newsletter Digest (Priority: P1)

As a user, I want all parsed newsletter items consolidated into a single readable newsletter so that I can review all content in one place.

**Why this priority**: The consolidated output is the final deliverable that provides value to the user. Without this, the collected and parsed data has no consumable format.

**Independent Test**: Can be fully tested by providing multiple parsed newsletter lists and verifying a well-formatted consolidated newsletter is generated.

**Acceptance Scenarios**:

1. **Given** I have parsed newsletter items from multiple sources, **When** I generate the consolidated newsletter, **Then** all items are combined into a single document
2. **Given** I have parsed newsletter items, **When** I generate the consolidated newsletter, **Then** the output is formatted for easy reading (clear headings, organized sections, readable prose)
3. **Given** I have parsed newsletter items with dates, **When** I generate the consolidated newsletter, **Then** items are organized chronologically or by source as appropriate
4. **Given** I generate a consolidated newsletter, **When** the process completes, **Then** the output is suitable for reading directly or converting to audio format
5. **Given** no newsletter items are available, **When** I attempt to generate a consolidated newsletter, **Then** I receive a message indicating no content is available

---

### User Story 5 - Configure Newsletter Prompts (Priority: P2)

As a user, I want to configure prompts for different newsletter senders so that I can easily add support for new newsletter formats.

**Why this priority**: Configuration enables extensibility, but the system can function with default prompts for basic use cases.

**Independent Test**: Can be fully tested by adding a new sender configuration with a custom prompt and verifying it is used during processing.

**Acceptance Scenarios**:

1. **Given** I want to add a new newsletter sender, **When** I configure a prompt for that sender, **Then** the configuration is saved and associated with that sender's email address
2. **Given** I have configured multiple senders with prompts, **When** I view the configuration, **Then** I can see all configured senders and their associated prompts
3. **Given** I want to modify an existing prompt, **When** I update the configuration, **Then** the new prompt is used for future processing of that sender's newsletters
4. **Given** I remove a sender configuration, **When** I process newsletters, **Then** that sender's emails are no longer collected or processed

---

### Edge Cases

- What happens when Gmail authentication expires or is revoked?
  - System displays a clear error message with instructions to re-authenticate, and processing is halted until authentication is restored

- What happens when a newsletter email is malformed or corrupted?
  - System logs the error, skips the problematic email, and continues processing other emails

- What happens when a prompt fails to extract required information from a newsletter?
  - System logs the parsing failure, marks the newsletter for manual review, and includes partial data if available

- What happens when no newsletters are found from configured senders?
  - System completes successfully with a message indicating no new content, and no consolidated newsletter is generated

- What happens when the prompt-based parsing produces invalid or incomplete structured data?
  - System validates the output structure and logs warnings for incomplete items, but includes available data in the consolidated output

- What happens when local storage runs out of space?
  - System displays an error message indicating storage issues and halts processing until space is available

- What happens when the retention limit (N) is reached?
  - System automatically removes the oldest records (emails, markdown files, parsed data) to maintain only the most recent N records, based on processing date

- What happens when the final consolidation prompt fails?
  - System logs the error and provides the raw structured lists as fallback output

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST authenticate with Gmail using OAuth 2.0 to access user's email account
- **FR-002**: System MUST collect all emails from user-specified sender email addresses (regardless of read status, location, or folder)
- **FR-003**: System MUST track which emails have been processed locally to avoid duplicate processing across collection runs
- **FR-004**: System MUST convert collected email content to markdown format, preserving structure and formatting
- **FR-005**: System MUST support configurable prompts for each newsletter sender to enable format-specific parsing
- **FR-006**: System MUST apply the appropriate prompt to each newsletter based on its sender email address
- **FR-007**: System MUST extract structured information from newsletters using prompts, producing output in format: {date, title, summary, link (if provided)} - a single newsletter email may produce multiple parsed items if it contains multiple articles
- **FR-008**: System MUST store all parsed newsletter items as structured lists locally
- **FR-009**: System MUST process all parsed newsletter lists through a final consolidation prompt
- **FR-010**: System MUST generate a consolidated newsletter output in markdown format, suitable for reading or audio conversion
- **FR-011**: System MUST store all data (emails, markdown files, parsed data, configurations) locally on the user's device
- **FR-016**: System MUST retain only the most recent N records of collected emails, markdown files, and parsed data (where N is configurable by the user)
- **FR-012**: System MUST allow users to configure sender email addresses and associate prompts with each sender
- **FR-017**: System MUST allow users to configure the retention limit (N) for keeping the most recent records
- **FR-018**: System MUST allow users to configure a single consolidation prompt that is used for all newsletter consolidations
- **FR-013**: System MUST handle authentication token refresh automatically for Gmail access
- **FR-014**: System MUST provide meaningful error messages for authentication failures, parsing errors, and processing issues
- **FR-015**: System MUST gracefully handle missing or incomplete data in newsletters (missing dates, titles, links)

### Key Entities

- **Newsletter Sender**: A configured email address that sends newsletters, associated with a parsing prompt
- **Email Message**: A raw email retrieved from Gmail containing newsletter content
- **Markdown Document**: A converted email in markdown format, preserving original content structure
- **Parsed Newsletter Item**: Structured data extracted from a newsletter containing: date, title, summary, and optional link - a single newsletter email may produce multiple parsed items if it contains multiple articles
- **Newsletter List**: A collection of parsed newsletter items from a single source or time period
- **Consolidated Newsletter**: The final output document in markdown format combining all parsed newsletter items into a readable format
- **Configuration**: User settings including sender email addresses, associated parsing prompts for each sender, consolidation prompt, and data retention settings

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can successfully collect and process emails from up to 10 configured newsletter senders in under 5 minutes
- **SC-002**: System successfully converts 95% of newsletter emails to readable markdown format without data loss
- **SC-003**: Prompt-based parsing successfully extracts structured information (date, title, summary, link) from 90% of processed newsletters
- **SC-004**: Users can generate a consolidated newsletter from processed items in under 30 seconds for up to 50 newsletter items
- **SC-005**: Users can add a new newsletter sender with a custom prompt and have it processed successfully within 10 minutes of configuration
- **SC-006**: Consolidated newsletter output is readable and well-formatted, suitable for direct consumption or audio conversion
- **SC-007**: All data remains stored locally with no external data transmission beyond Gmail API authentication
- **SC-008**: System handles Gmail authentication refresh automatically without user intervention in 95% of cases

## Assumptions

- User has a Gmail account with access to newsletter emails
- User can complete Gmail OAuth 2.0 authentication flow (browser-based)
- User has local storage space available for storing emails, markdown files, and parsed data
- Newsletter emails are accessible via Gmail API (not in spam or deleted)
- User has basic understanding of how to configure prompts for their specific newsletter formats
- Prompt-based parsing will be performed using a language model or similar AI service (implementation detail, but assumed for functionality)
- The consolidation prompt will be applied using the same parsing mechanism as individual newsletters
- All processing happens on the user's local machine (no cloud processing required)
- User runs the application on-demand rather than as a continuously running service
