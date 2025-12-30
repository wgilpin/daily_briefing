<!--
Sync Impact Report:
- Version: 1.0.0 → 1.1.0
- Type: MINOR (expanded testing policy guidance)
- Modified principles: Testing Policy (expanded with unit test requirements and scope limitations)
- Added sections: N/A
- Removed sections: N/A
- Templates requiring updates:
  ✅ plan-template.md - Reviewed, compatible (testing section will reference updated policy)
  ✅ spec-template.md - Reviewed, compatible (no changes needed)
  ✅ tasks-template.md - Reviewed, compatible (test task generation aligns with new policy)
- Follow-up TODOs: None
-->

# tutor-min-py Constitution

## Core Principles

### I. Simplicity First (NON-NEGOTIABLE)

Every decision MUST prioritize simplicity over cleverness, flexibility, or premature optimization.

- Code MUST be readable by anyone familiar with Python basics
- Architecture MUST use the simplest design that works
- No abstractions until pain is felt THREE times in actual code
- If explaining the design takes more than 3 sentences, it's too complex
- Dependencies MUST be justified—prefer stdlib over third-party when feasible

**Rationale**: Complexity is the enemy of rapid development. Simple code ships faster, has fewer bugs, and is easier to iterate on.

### II. Minimal Boilerplate (NON-NEGOTIABLE)

Write only what delivers direct user value. Eliminate ceremony and boilerplate.

- No classes when functions suffice
- No configuration files until actual configuration needed
- No infrastructure code until deployment is imminent
- No "future-proofing"—YAGNI (You Aren't Gonna Need It) strictly enforced
- Use language features that reduce code volume without obscuring intent

**Rationale**: Every line of boilerplate is a line that doesn't add features. In rapid prototyping, lean code enables faster pivots.

### III. Rapid Iteration Over Perfection

Working software NOW beats perfect software later.

- Ship the minimal working version first, iterate based on actual usage
- Tests are OPTIONAL unless feature is business-critical or repeatedly breaks
- Documentation is inline comments + README only—no separate docs until GA
- Code review is self-review—peer review only for core logic or security
- Refactor only when pain is acute (slow, buggy, or blocking new work)

**Rationale**: For an LLM chat demo, learning from real interaction trumps theoretical perfection. Fast feedback loops accelerate product-market fit.

### IV. Focused Scope (NON-NEGOTIABLE)

Ruthlessly defend against scope creep. One feature at a time.

- Each feature MUST answer: "Does this make the chat demo better TODAY?"
- New ideas go into backlog, not current work
- Feature requests MUST remove a feature of equal complexity if backlog is full
- No "nice to have" work—only "must have"
- Timebox spikes: 2 hours to prove feasibility or abandon

**Rationale**: Scope creep kills demos. A working 3-feature demo beats a broken 10-feature prototype.

### V. Pleasing Simplicity (UI/UX)

UI MUST be eye-pleasing but simple—no complex frameworks or heavy dependencies.

- Use semantic HTML + minimal CSS (or lightweight utility-first frameworks)
- Favor browser defaults and native behaviors
- Interactions MUST feel responsive (perceived performance > measured performance)
- Design for keyboard + mouse, no complex gestures
- Visual polish via whitespace, typography, and color—not animations or effects

**Rationale**: Users judge quality by UI. A simple, clean interface signals a thoughtful product. Heavy frameworks slow iteration.

## Technology Constraints

**Stack Philosophy**: Minimize layers, maximize Python stdlib.

- **Language**: Python 3.13+ (leverage modern features: match, type hints)
- **Web Framework**: FastAPI or Flask—whichever ships a working endpoint fastest, with HTMX for interactivity
- **Frontend**: HTML + CSS + vanilla JavaScript OR Alpine.js/htmx for interactivity (no React/Vue unless justified by specific need)
- **LLM Integration**: Direct API calls (grok preferred, etc.)—no LangChain unless chaining is proven necessary
- **Database**: Start with JSON files or SQLite; only graduate to Postgres if scale requires it
- **Deployment**: Single-command deploy (e.g., `fly deploy`, `railway up`)—avoid multi-step orchestration

**Forbidden Until Justified**:
- ORMs (use raw SQL or lightweight query builders)
- Background task queues (use async/await first)
- Microservices (monolith until proven bottleneck)
- Docker multi-stage builds (single-stage or no Docker until deployment)
- Frontend javascript unless HTMX cannot serve

## Development Workflow

**Speed Gates**: These are CHECK-INS, not BLOCKERS—keep moving unless red flag appears.

1. **Before Coding**: Does this feature belong in the demo? (1 min gut check)
2. **During Coding**: Am I writing boilerplate? (refactor if yes)
3. **Before Commit**: Does it work? (manual smoke test)
4. **After Commit**: Did scope creep in? (review commit diff)

**Definition of Done**:
- Feature works in local demo
- README updated if user-facing behavior changed
- No obvious bugs in happy path
- Code committed with clear message

**Testing Policy**:
- Unit tests MUST be written for all functions except where that function depends on an LLM.
- Keep tests simple: if a test requires too many mocks or becomes too complex, it adds no value and should be simplified or removed.
- Test scope:
  - ✅ Unit tests for backend logic (parsing, validation, calculations, data transformations)
  - ✅ Unit tests for functions that broke twice (proven to need protection)
  - ✅ Unit tests for security/auth flows
  - ❌ Do NOT test UI components or interactions
  - ❌ Do NOT test API endpoints (test the underlying logic instead)
- Tests should not attempt to cover every edge case by default—focus on happy path and known failure modes.

**Commit Discipline**:
- Commit working code frequently (every 30-60 min)
- Messages: `<type>: <what>` (e.g., `feat: add chat history`, `fix: message overflow`)
- Push to main—no branches until team size > 1

## Governance

**Amendment Process**:
1. Identify principle violation or new constraint
2. Propose amendment with rationale (GitHub issue or inline comment)
3. Self-approve if solo, or async team approval (24h max)
4. Update this file + increment version
5. No migration plan needed—constitution guides forward work only

**Version Semantics**:
- **MAJOR**: Remove or redefine a core principle
- **MINOR**: Add new principle or section
- **PATCH**: Clarify wording or fix typos

**Compliance**:
- This constitution is a GUIDE, not law—use judgment
- When in doubt, ask: "Does this make the demo simpler and faster?"
- If constitution blocks progress, amend it (see above)—don't work around it

**Version**: 1.1.0 | **Ratified**: 2025-11-24 | **Last Amended**: 2025-01-27
