# Feature Specification: Senders Database Migration

**Feature Branch**: `013-senders-db-migration`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "the senders.json storage needs to move to the database to avoid needing the disk-based file"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sender Configuration Persists in Database (Priority: P1)

An administrator configures newsletter senders (email addresses, display names, parsing prompts, enabled/disabled state) through the web UI, and those settings are stored in and retrieved from the database rather than a file on disk.

**Why this priority**: This is the core migration - the system must read and write sender data from the database for all existing functionality to continue working. All other stories depend on this.

**Independent Test**: Can be tested by adding a new sender via the UI, restarting the application, and verifying the sender still appears with correct settings.

**Acceptance Scenarios**:

1. **Given** a sender exists in the database, **When** the application starts, **Then** all sender configurations are loaded from the database without requiring senders.json
2. **Given** an administrator adds a new sender via the UI, **When** they save, **Then** the sender is stored in the database and persists across application restarts
3. **Given** an administrator updates a sender's display name or parsing prompt, **When** they save, **Then** the updated values are retrieved on next load
4. **Given** an administrator disables a sender, **When** the newsletter processing runs, **Then** the disabled sender is not processed

---

### User Story 2 - Global Configuration Persists in Database (Priority: P2)

The global newsletter settings (consolidation prompt, retention limit, days lookback, max workers, default parsing prompt, default consolidation prompt) are stored in and retrieved from the database.

**Why this priority**: These global settings were stored alongside sender data in senders.json and must also migrate to avoid any dependency on the file.

**Independent Test**: Can be tested by changing a global setting via the UI, restarting the application, and verifying the setting is retained.

**Acceptance Scenarios**:

1. **Given** global settings exist in the database, **When** the application starts, **Then** all global settings are loaded correctly
2. **Given** an administrator updates the default parsing prompt, **When** they save, **Then** the new prompt is used for all subsequent newsletter processing
3. **Given** no senders.json file exists on disk, **When** the application starts, **Then** all functionality works normally using database-stored configuration

---

### User Story 3 - Migration from Existing File (Priority: P3)

If a senders.json file exists when the system starts, its contents are migrated to the database and the file is no longer required.

**Why this priority**: Existing deployments have data in senders.json that should not be lost during the migration.

**Independent Test**: Can be tested by starting the application with an existing senders.json and verifying all senders and settings appear in the database.

**Acceptance Scenarios**:

1. **Given** a senders.json file exists, **When** the application starts for the first time after this migration, **Then** all sender data is imported into the database
2. **Given** senders already exist in the database, **When** a senders.json file also exists, **Then** no duplicate entries are created (database takes precedence)
3. **Given** senders.json has been migrated, **When** the application runs, **Then** the system operates entirely from the database and senders.json has been renamed to `senders.json.bak`

---

### Edge Cases

- Database unavailable at startup: fail fast with a clear error message (no degraded mode)
- Malformed senders.json during migration: abort startup entirely with a clear error message; file is not renamed
- Duplicate email during migration: database record wins; file entry is skipped (no overwrite)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store all sender configurations (email, display name, parsing prompt, enabled state, created_at) in the database
- **FR-002**: System MUST store all global newsletter settings (consolidation prompt, retention limit, days lookback, max workers, default prompts) in the database
- **FR-003**: System MUST load sender and global configuration entirely from the database on startup, without requiring senders.json
- **FR-004**: System MUST support creating, reading, updating, and deleting sender configurations via the existing web UI
- **FR-005**: System MUST migrate existing data from senders.json to the database on first run if the file exists
- **FR-006**: System MUST NOT require senders.json to be present for the application to function
- **FR-007**: All existing sender management UI functionality MUST continue to work after migration
- **FR-008**: Global settings MUST be stored in a `newsletter_config` key/value table with columns `setting_name TEXT PRIMARY KEY` and `setting_value TEXT`

### Key Entities

- **Sender**: A newsletter sender identified by email address, with display name, parsing prompt, enabled flag, and creation timestamp
- **Newsletter Configuration**: Global settings including consolidation prompt, retention limit, days lookback, max workers, and default prompts; stored as a key/value table (`setting_name TEXT`, `setting_value TEXT`)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application starts and processes newsletters successfully with no senders.json file present
- **SC-002**: All sender management operations (add, update, delete, enable/disable) work correctly and persist across application restarts
- **SC-003**: Existing senders.json data is fully preserved after a successful migration - zero data loss; malformed senders.json aborts startup before any writes occur
- **SC-004**: No degradation in newsletter processing behavior compared to the file-based implementation

## Assumptions

- The existing PostgreSQL database (used for newsletter tracking) will also store sender configuration
- The web UI for managing senders already exists and only the storage backend needs to change
- senders.json will be renamed to `senders.json.bak` after successful migration and will not be actively written to after migration
- The application's existing database schema migration mechanism will handle adding new tables

## Clarifications

### Session 2026-02-11

- Q: After a successful migration from senders.json to the database, what should happen to the file? → A: Rename to `senders.json.bak`
- Q: If the database is unavailable when the application starts, what should happen? → A: Fail fast with a clear error message
- Q: If senders.json contains malformed JSON during migration, what should happen? → A: Abort startup entirely with a clear error; file is not renamed
- Q: When a sender email from senders.json already exists in the database during migration, which record wins? → A: Database record wins; file entry is skipped
- Q: How should global newsletter settings be stored in the database? → A: Key/value table (setting_name, setting_value as text)
