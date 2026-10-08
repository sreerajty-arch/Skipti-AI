# Skipti AI Living Specification

Skipti AI is a multi-tenant, MCP-first context intelligence application. Supabase Auth provides email/password identities and sessions, Supabase Storage keeps private project files, and every application record in the Mongo service layer is isolated by the verified Supabase user UUID.

## Core flows
- Users create an account or sign in at `/signup` and `/login`. Every owner view is guarded, and profile details come from the active Supabase account.
- Project Holders keep structured canonical state. Progress is first stored as a proposal, then an owner approval creates an immutable revision checkpoint with optimistic concurrency protection.
- The Context Router selects minimum approved context by query and optional project scope. The Playground sends that exact selection to Gemini and displays the retrieval trace.
- The official Python MCP SDK exposes authenticated Streamable HTTP at `/mcp/`. A bearer token protects discovery and tools; MCP and REST call the same service layer.
- Persona Pass uses one-time QR credentials, read-only scoped guest sessions, expiration, and immediate server-side revocation. Redeemed guests enter a real Gemini chat where every message runs permission-aware context retrieval against the latest approved Persona and Project Holder state.
- Every newly created Persona Pass is also written to Supabase with normalized category permissions. Cookie-less AI fetch tools can read `GET /api/connect/{token}/context?q=...` as `text/plain`; every request rechecks expiry/revocation, filters active entries by Supabase session permissions, and logs an `external_fetch` access event.
- Temporary guest chat keeps a bounded per-session history for follow-up questions. At QR creation the owner chooses whether chat is deleted on end/revoke (default) or retained only until the pass expires.

## Visual system
- Two-family editorial type system: Cormorant Garamond for confident display typography and IBM Plex Sans for interface/body text.
- Dark charcoal surfaces, one burgundy accent, consistent rounded panels, restrained shadows, visible focus states, reduced-motion support, skeleton loading states, and full mobile navigation. Shared `.panel` surfaces use restrained glassmorphism with a 24px backdrop blur.
- Public surfaces use custom Skipti context artwork, real system proof, social preview metadata, a custom Skipti favicon, and a dedicated 404 experience.

## Seed facts
- Legacy seeded records remain archived under their old owner identifier and are inaccessible to registered accounts.
- Each account starts empty and creates its own Persona, Project Holders, temporary passes, project files, and account-scoped MCP token.

## Data model
Supabase: `auth.users`, `public.users`, private `storage.objects`, `personas`, `persona_entries`, `projects`, `temporary_sessions`, `session_permissions`, and `context_access_logs`. Mongo service collections: `personas`, `persona_entries`, `interview_sessions`, `projects`, `project_context_entries`, `project_files`, `project_update_proposals`, `project_checkpoints`, `temporary_grants`, `guest_sessions`, `guest_chat_messages`, `mcp_tokens`, and `context_access_logs`.

## Auth roles
- Owner: verified Supabase access/refresh tokens held only in secure httpOnly cookies, with full access only to records matching the token subject.
- MCP owner client: per-account revocable bearer token with read/write scopes.
- Guest: one-time redeemed Persona Pass cookie, read-only authorized context until expiry or revocation. The high-entropy QR token can separately authorize the no-cache plain-text AI link; it never grants write access.

## Project folders
- A Project Holder accepts a local folder up to 50 MB. Owners choose private original storage or context-only import.
- Private originals use owner/project-prefixed Supabase Storage paths and short-lived download URLs.
- Context-only imports accept text/code formats, create project-scoped context entries, and never persist the original file bytes.