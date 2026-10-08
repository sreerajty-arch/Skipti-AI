# Skipti AI Living Specification

Skipti AI is an MCP-first context intelligence MVP. The preview uses a demo owner session and the local Mongo persistence adapter; the included Supabase migration is the production target but is not active without credentials.

## Core flows
- Demo owner enters at `/login`, reviews Base/Living Persona context, and can run the adaptive interview at `/setup`.
- Project Holders keep structured canonical state. Progress is first stored as a proposal, then an owner approval creates an immutable revision checkpoint with optimistic concurrency protection.
- The Context Router selects minimum approved context by query and optional project scope. The Playground sends that exact selection to Gemini and displays the retrieval trace.
- The official Python MCP SDK exposes authenticated Streamable HTTP at `/mcp/`. A bearer token protects discovery and tools; MCP and REST call the same service layer.
- Persona Pass uses one-time QR credentials, read-only scoped guest sessions, expiration, and immediate server-side revocation. Redeemed guests enter a real Gemini chat where every message runs permission-aware context retrieval against the latest approved Persona and Project Holder state.
- Every newly created Persona Pass is also written to Supabase with normalized category permissions. Cookie-less AI fetch tools can read `GET /api/connect/{token}/context?q=...` as `text/plain`; every request rechecks expiry/revocation, filters active entries by Supabase session permissions, and logs an `external_fetch` access event.
- Temporary guest chat keeps a bounded per-session history for follow-up questions. At QR creation the owner chooses whether chat is deleted on end/revoke (default) or retained only until the pass expires.

## Visual system
- Two-family editorial type system: Cormorant Garamond for confident display typography and IBM Plex Sans for interface/body text.
- Dark charcoal surfaces, one burgundy accent, consistent rounded panels, restrained shadows, visible focus states, reduced-motion support, skeleton loading states, and full mobile navigation.
- Public surfaces use custom Skipti context artwork, real system proof, social preview metadata, a custom Skipti favicon, and a dedicated 404 experience.

## Seed facts
- Demo owner: Alex Morgan (`demo@skipti.ai`)
- Seed Project Holders: Skipti AI (`11111111-1111-4111-8111-111111111111`, revision 3) and Focus Room (`22222222-2222-4222-8222-222222222222`, revision 2)
- Six approved Persona entries cover goals, skills, AI preferences, hardware, and tools.

## Data model
`users`, `auth_sessions`, `personas`, `persona_entries`, `interview_sessions`, `projects`, `project_context_entries`, `project_update_proposals`, `project_checkpoints`, `temporary_grants`, `guest_sessions`, `guest_chat_messages`, and `context_access_logs`.

## Auth roles
- Owner: demo httpOnly cookie, full REST access and approval controls.
- MCP owner client: bearer token with read/write scopes.
- Guest: one-time redeemed Persona Pass cookie, read-only authorized context until expiry or revocation. The high-entropy QR token can separately authorize the no-cache plain-text AI link; it never grants write access.