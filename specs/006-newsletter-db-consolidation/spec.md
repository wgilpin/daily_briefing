# Feature Specification: Newsletter Database Consolidation

**Feature Branch**: `006-newsletter-db-consolidation`
**Created**: 2026-02-04
**Status**: Draft
**Input**: User description: "Remove the legacy SQLite dependency and consolidate the architecture around PostgreSQL. There is also a critical issue in the current implementation where Python's built-in hash() function (which is non-deterministic across restarts) is used for ID generation. This rationalization plan will fix that stability issue, introduce connection pooling for thread safety, and unify the storage layer.

Here is the outline:

Database Connection: Upgrade src/db/connection.py to use a ThreadedConnectionPool. This is essential because the newsletter parser runs in parallel threads, and sharing a single connection object across threads is unsafe for transactions.

Schema Migration: Create a new migration src/db/migrations/003_newsletter_consolidation.sql to port the processed_emails table from SQLite to PostgreSQL.

Repository Expansion: Update src/db/repository.py to handle email tracking and deduplication, effectively replacing the SQLite queries.

Legacy Storage Cleanup: Strip all SQLite logic from src/newsletter/storage.py, leaving only the file system operations (saving JSON/Markdown/attachments).

Logic Update: Refactor src/newsletter/email_collector.py and src/sources/newsletter.py to use the PostgreSQL repository and generate stable, deterministic IDs using SHA-256 instead of the unstable hash()."

## Clarifications

### Session 2026-02-04

- Q: What exact input format should be used for SHA-256 ID generation? → A: Hash title and date with colon separator matching current implementation: `sha256(f"{title}:{date}")`
- Q: What default values should be used for connection pool sizing (min/max connections)? → A: Balanced: minconn=2, maxconn=10
- Q: What retry strategy should be used when connection failures occur? → A: Exponential backoff: 3 retries with 1s, 2s, 4s delays
- Q: When/how should the migration script be executed in the deployment process? → A: Auto-run on startup: Application checks and runs migration automatically on first launch
- Q: Should newsletter items use existing feed_items table or create new newsletter_items table in PostgreSQL? → A: Use existing feed_items table

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Newsletter System Functions Without SQLite (Priority: P1)

After the migration, users can collect, parse, and view newsletter items without any SQLite database dependency. All email tracking, deduplication, and newsletter item storage is handled by PostgreSQL.

**Why this priority**: This is the core functionality that eliminates the dual-database architecture and ensures the system works correctly with a single database.

**Independent Test**: Can be fully tested by running the newsletter collection pipeline (email collection, conversion, parsing) and verifying that all tracking data is stored in PostgreSQL instead of SQLite. Success means no SQLite database files are created or accessed.

**Acceptance Scenarios**:

1. **Given** the system is freshly initialized with only PostgreSQL configured, **When** the newsletter collection pipeline runs, **Then** all processed emails are tracked in the PostgreSQL `processed_emails` table
2. **Given** newsletters have been collected and parsed, **When** viewing the feed, **Then** all newsletter items are retrieved from PostgreSQL without any SQLite queries
3. **Given** a newsletter email has already been processed, **When** the same email is encountered again, **Then** the system correctly identifies it as already processed using PostgreSQL deduplication records

---

### User Story 2 - ID Generation is Stable Across Restarts (Priority: P1)

Newsletter items maintain consistent IDs across application restarts. The same newsletter content always generates the same ID, enabling proper deduplication and reliable references.

**Why this priority**: This fixes a critical stability bug where Python's non-deterministic hash() function causes duplicate items and broken references after application restarts.

**Independent Test**: Can be fully tested by processing the same newsletter twice (with an application restart in between) and verifying that both runs generate identical IDs for the same items. Success means no duplicate items appear in the database.

**Acceptance Scenarios**:

1. **Given** a newsletter has been processed and stored with a specific ID, **When** the application restarts and processes the same newsletter again, **Then** the system generates the identical ID and updates the existing record instead of creating a duplicate
2. **Given** two newsletters with identical titles and dates, **When** both are processed, **Then** the system generates the same ID and only stores one item
3. **Given** a newsletter item is referenced by its ID in the web interface, **When** the application restarts, **Then** the reference continues to work with the same ID

---

### User Story 3 - Parallel Newsletter Parsing is Thread-Safe (Priority: P1)

Multiple newsletter emails can be parsed concurrently without database connection errors or transaction conflicts. The system safely handles concurrent database operations during parallel LLM parsing.

**Why this priority**: Connection pooling is essential for the existing parallel parsing architecture. Without it, thread-safety issues can cause data corruption or parsing failures.

**Independent Test**: Can be fully tested by configuring the system to parse 5+ newsletters in parallel (max_workers=5) and verifying that all newsletters are successfully parsed without database connection errors. Success means all parallel threads complete without transaction conflicts.

**Acceptance Scenarios**:

1. **Given** 10 newsletters are ready for parsing, **When** the parser runs with max_workers=5, **Then** all 10 newsletters are successfully parsed and stored in PostgreSQL without connection errors
2. **Given** multiple threads are simultaneously updating email processing status, **When** status updates occur concurrently, **Then** all updates are correctly recorded without lost updates or deadlocks
3. **Given** a parsing thread encounters an error, **When** the thread releases its database connection, **Then** other threads continue processing without interruption

---

### User Story 4 - Migration Preserves Existing Data (Priority: P2)

Existing newsletter data from the SQLite database is successfully migrated to PostgreSQL. All previously processed emails and parsed items are available after the migration.

**Why this priority**: Users with existing newsletters need their historical data preserved. This is secondary to the core functionality but important for production deployments.

**Independent Test**: Can be fully tested by running the migration with an existing SQLite database containing processed emails, then verifying that all records are present in PostgreSQL with correct data and relationships. Success means no data loss during migration.

**Acceptance Scenarios**:

1. **Given** an existing SQLite database contains 50 processed emails, **When** the application starts and automatically runs the migration, **Then** all 50 emails appear in the PostgreSQL `processed_emails` table with identical message IDs and status
2. **Given** the SQLite database contains 200 newsletter items linked to processed emails, **When** the migration completes, **Then** all 200 items are stored in PostgreSQL feed_items table with preserved data and source_type='newsletter'
3. **Given** some emails have status 'parsed' and others have status 'failed' in SQLite, **When** the migration runs, **Then** all status values are correctly preserved in PostgreSQL

---

### Edge Cases

- What happens when a PostgreSQL connection fails during parallel newsletter parsing? (System should gracefully handle connection pool exhaustion and retry failed operations using exponential backoff: 3 retries with 1s, 2s, 4s delays before final failure)
- How does the system handle migration when the SQLite database doesn't exist? (Migration should skip data import and only create the new schema)
- What happens when two identical newsletters are processed simultaneously before either completes? (SHA-256 based IDs and database constraints prevent duplicate storage)
- How does the system behave if a SHA-256 hash collision occurs (extremely unlikely but theoretically possible)? (The UNIQUE constraint on source_type+source_id will reject the duplicate, which is acceptable given collision probability ~2^-256)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST use a PostgreSQL connection pool (ThreadedConnectionPool) for all database operations to support concurrent newsletter parsing
- **FR-002**: System MUST track processed emails in a PostgreSQL `processed_emails` table with fields: message_id (PK), sender_email, subject, collected_at, processed_at, status, error_message
- **FR-003**: System MUST generate stable, deterministic IDs for newsletter items using SHA-256 hashing of title and date with format `sha256(f"{title}:{date}")` instead of Python's hash() function
- **FR-004**: Repository MUST provide methods for email deduplication: checking if a message_id has been processed and recording email processing status
- **FR-005**: System MUST remove all SQLite import statements and database connection code from the newsletter module
- **FR-006**: File system operations (saving JSON, Markdown, and attachment files) MUST continue to function after SQLite removal
- **FR-007**: Migration script MUST import existing `processed_emails` data and `newsletter_items` data from SQLite to PostgreSQL (newsletter_items migrate into feed_items table) if a legacy database exists, executed automatically on application startup (idempotent - safe to run multiple times)
- **FR-008**: System MUST maintain backward compatibility with existing file system structure (data/emails/, data/markdown/, data/parsed/ directories)
- **FR-009**: Connection pool MUST be configurable with minimum and maximum connection parameters (default: minconn=2, maxconn=10)
- **FR-010**: System MUST handle connection pool exhaustion gracefully by waiting for available connections rather than failing, with exponential backoff retry strategy (3 retries: 1s, 2s, 4s delays)

### Key Entities *(include if feature involves data)*

- **ProcessedEmail**: Represents a tracked email from a newsletter sender with fields: message_id (unique Gmail message ID), sender_email, subject, collected_at (timestamp when email was fetched), processed_at (timestamp when processing completed), status (collected/converted/parsed/failed), error_message (optional failure details)
- **NewsletterItem**: Represents a parsed article or item from a newsletter, now stored in PostgreSQL feed_items table with SHA-256 based ID instead of hash()-based ID
- **ConnectionPool**: Manages a pool of PostgreSQL connections for thread-safe concurrent access, with configurable min/max connections (default: 2 minimum, 10 maximum)
- **MigrationRecord**: Tracks which newsletter data has been migrated from SQLite to PostgreSQL (message_ids that have been transferred)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All newsletter collection, conversion, and parsing operations complete successfully without creating or accessing any SQLite database files
- **SC-002**: Processing the same newsletter content twice (with application restart between runs) produces identical IDs and does not create duplicate database records
- **SC-003**: System successfully parses 10 newsletters in parallel (max_workers=5) without database connection errors or transaction failures
- **SC-004**: Migration from an existing SQLite database with 100+ processed emails completes without data loss (all records verifiable in PostgreSQL)
- **SC-005**: Newsletter item IDs remain consistent across application restarts, enabling stable references and preventing duplicates in the feed
