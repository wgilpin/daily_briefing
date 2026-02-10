# Feature Specification: TTS Provider Fallback

**Feature Branch**: `012-tts-fallback`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "The app currently uses Kokoro TTS, since Commit 6130d5c. Before that we used elevenlabs. I want to change it so that the system checks for Kokoro, if it finds it it uses it, if not it uses Elevenlabs again. The app also needs to be deployable to Hetzner, which means we need 2 different deployment options: for development on a PC using kokoro and espeak-ng with elevenlabs as a fallback, and the Hetzner cloud version which only uses elevenlabs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Audio Generation Works on Any Environment (Priority: P1)

A developer or the production system triggers audio generation, and it succeeds automatically regardless of which TTS engines are installed in that environment. No manual configuration changes are needed when moving between environments.

**Why this priority**: Core correctness — the app must produce audio regardless of where it is deployed. Without this, audio generation fails on environments missing Kokoro.

**Independent Test**: Deploy the app on a machine without Kokoro installed, trigger audio generation, and verify ElevenLabs produces the audio. Separately, deploy on a machine with Kokoro installed and verify Kokoro is used instead.

**Acceptance Scenarios**:

1. **Given** Kokoro is installed and available, **When** audio generation is triggered, **Then** Kokoro is used and audio is produced successfully.
2. **Given** Kokoro is NOT installed or not accessible, **When** audio generation is triggered, **Then** ElevenLabs is used as fallback and audio is produced successfully.
3. **Given** neither Kokoro nor ElevenLabs is available, **When** audio generation is triggered, **Then** the system logs a clear error and fails gracefully without crashing.

---

### User Story 2 - Development Environment Uses Kokoro with espeak-ng (Priority: P2)

A developer running the app locally gets free, offline TTS via Kokoro (backed by espeak-ng) with ElevenLabs as a fallback when Kokoro is unavailable. No manual switching is required.

**Why this priority**: Enables cost-free development iteration without consuming ElevenLabs API credits.

**Independent Test**: On a development machine with Kokoro + espeak-ng installed, generate audio and confirm Kokoro is used. Remove/disable Kokoro, regenerate, confirm ElevenLabs is used automatically.

**Acceptance Scenarios**:

1. **Given** a development environment with Kokoro and espeak-ng installed, **When** audio is generated, **Then** Kokoro handles synthesis using espeak-ng as its backend.
2. **Given** a development environment without Kokoro, **When** audio is generated, **Then** ElevenLabs is used automatically.
3. **Given** ElevenLabs credentials are not configured and Kokoro is unavailable, **When** audio is generated, **Then** a clear message indicates no TTS provider is available.

---

### User Story 3 - Hetzner Cloud Deployment Uses ElevenLabs Only (Priority: P2)

The production deployment on Hetzner cloud uses ElevenLabs as the sole TTS provider. Kokoro is never installed, detected, or attempted on the cloud server.

**Why this priority**: The Hetzner server has no GPU and no espeak-ng installed. Kokoro requires both, so it cannot run in production. ElevenLabs is the only viable provider and must work reliably without any Kokoro detection overhead.

**Independent Test**: Deploy to a Hetzner-profile environment (no Kokoro installed), trigger audio generation, verify ElevenLabs is used and no Kokoro-related errors appear in logs.

**Acceptance Scenarios**:

1. **Given** a Hetzner deployment (Kokoro not installed), **When** audio is generated, **Then** ElevenLabs is used without any Kokoro detection errors in logs.
2. **Given** the Hetzner deployment is active, **When** the app starts, **Then** logs clearly show ElevenLabs as the active provider.

---

### Edge Cases

- **Kokoro installed but broken** (e.g., espeak-ng missing, process won't start): Fall back to ElevenLabs automatically and display a "Generating with ElevenLabs" message to the user. Do not raise an error.
- What happens when the ElevenLabs API key is missing or invalid and Kokoro is also unavailable?
- What happens if Kokoro detection takes too long (hangs) at startup?
- How does the system behave when espeak-ng is missing but Kokoro is otherwise installed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST detect whether Kokoro TTS is available when audio generation is first triggered (i.e. when the user clicks the refresh/generate button), not at application startup.
- **FR-002**: If Kokoro is detected as available, the system MUST use Kokoro for audio synthesis.
- **FR-003**: If Kokoro is not detected or fails its availability check, the system MUST fall back to ElevenLabs for audio synthesis and display a "Generating with ElevenLabs" message in the existing audio status/progress area of the UI.
- **FR-004**: The development deployment profile MUST support Kokoro (with espeak-ng) as primary TTS and ElevenLabs as fallback.
- **FR-005**: The Hetzner cloud deployment profile MUST use ElevenLabs only, with no Kokoro code paths compiled or executed. The `kokoro` and `soundfile` packages MUST NOT be installed in the production build. This requires moving them out of the core dependency list and into a profile-specific dependency group (e.g., optional extras or a separate requirements file) so the production build can install without them.
- **FR-006**: The system MUST log which TTS provider was selected at the point of provider selection (when audio generation is triggered).
- **FR-007**: When no TTS provider is available, the system MUST emit a clear, actionable error message naming the missing provider(s).
- **FR-008**: Switching between deployment profiles MUST require no application code changes — only a different build/deployment configuration.

### Key Entities

- **TTS Provider**: An audio synthesis backend (Kokoro or ElevenLabs). Has an availability state and produces audio from text.
- **Deployment Profile**: A configuration context (development or Hetzner cloud) that controls which providers are attempted and in what order.
- **Availability Check**: A startup probe that determines whether a TTS provider can be used in the current environment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Audio generation succeeds on development environments whether or not Kokoro is installed (100% of cases, no manual intervention).
- **SC-002**: Audio generation succeeds on Hetzner-profile deployments using ElevenLabs (100% of cases).
- **SC-003**: The correct TTS provider is selected automatically with zero manual configuration changes between the two deployment profiles.
- **SC-004**: Logs identify the active TTS provider each time audio generation is triggered.
- **SC-005**: When no provider is available, the error message names the missing provider(s) and describes what is needed to resolve it.

## Clarifications

### Session 2026-02-10

- Q: What should happen if Kokoro is installed but fails the availability check? → A: Fall back to ElevenLabs automatically and show a "Generating with ElevenLabs" message to the user (not an error alert).
- Q: How is the deployment profile signalled? → A: Two separate deployment configs (e.g., different Dockerfiles or Compose profiles) — the Coolify/Hetzner build currently fails when Kokoro dependencies are included, so prod must have a separate build path that excludes Kokoro entirely.
- Q: Where should the "Generating with ElevenLabs" message appear? → A: In the existing audio status/progress area in the UI, where generation feedback already appears.

## Assumptions

- ElevenLabs credentials (API key, voice ID) are configured via environment variables and remain unchanged from the current implementation.
- Kokoro availability is determined locally (e.g., checking if the binary/package is present) — no network call is required.
- espeak-ng is only relevant as a Kokoro dependency on development machines; it is not used independently.
- The two deployment profiles (development PC, Hetzner cloud) are the only target environments in scope.
- Production is deployed via a GitHub webhook into Coolify on a Hetzner server; deployments are automated with no manual server access required.
- The Hetzner production server has no GPU and espeak-ng is not installed; Kokoro is therefore not viable in production under any circumstances.
- The Coolify/Hetzner build currently fails because `kokoro` and `soundfile` are in the main `pyproject.toml` dependency list and are installed on every build. These must be moved to a separate optional/dev dependency group so the production build can exclude them.
- The production build (Coolify) installs dependencies from `pyproject.toml`; the solution must work within that constraint without requiring a separate requirements file maintained in parallel.
- The only UI change required is displaying the active provider name in the existing audio status/progress area; no new UI elements are needed.
- The existing audio output format and file handling remain unchanged; only the synthesis backend changes.
- The detection mechanism has a fast timeout so it does not meaningfully delay application startup.
