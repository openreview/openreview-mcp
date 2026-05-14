# openreview-py — concepts and conventions

> Curated guidance for writing correct openreview-py code.
> Maintained directly in `openreview-mcp`; not synced from upstream.
> Method signatures and parameter lists are surfaced via `search_api` / `get_method_signature`. Real-world call sites come from `search_test_examples`. This file covers what those tools can't express: concepts, conventions, invariants, anti-patterns.

## Two API Versions

- v1 API: `openreview.Client(baseurl='https://api.openreview.net')` — legacy
- v2 API: `openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net')` — current/recommended
- All new venues use v2. The clients share model class names but differ in method signatures.
- Using a v1 URL with the v2 client (or vice versa) raises `OpenReviewException`.

### Method signatures differ between v1 and v2

Same method name, different parameters between clients — do NOT copy a v1 keyword onto a v2 call. The MCP `search_api` / `get_method_signature` results tag each entry with `[v1]` or `[v2]`, and the `**Module:**` field tells you which API the method came from (`openreview.api.client` = v2, `openreview.openreview` = v1). When unsure, look at the introspected signature for the exact client you're using.

## Authentication

- Auth options: username/password, token (precedence: token), or guest (no auth, public read-only).
- Env vars: `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`, `OPENREVIEW_API_BASEURL_V2` (v2), `OPENREVIEW_API_BASEURL` (v1).
- Token expiration: default 1 hour, max 1 week (`tokenExpiresIn` in seconds). Expired tokens raise `TokenExpiredError`.
- MFA: TOTP and Email OTP, resolved interactively. Non-interactive mode raises `MfaRequiredException` with `mfa_methods`, `mfa_pending_token`, `preferred_method`.
- Profile ID format: `~FirstName_LastName1`; trailing number disambiguates.

## Core Data Model

These objects are the units of work in OpenReview. Their fields are surfaced via `get_method_signature` on the class; this section covers what each object *represents* and how they relate.

- **Note** — primary content object. Papers, reviews, decisions, comments, and venue requests are all Notes. A reply Note's `forum` points at the root submission; `replyto` points at the immediate parent.
- **Group** — collection of members with permissions. Groups are hierarchical: `VenueID/Reviewers/Submission1` is both a group and a namespace. Memberships are emails, profile IDs (`~...`), or other group IDs.
- **Invitation** — defines what edits are allowed, by whom, and when. The `edit` field is a template; `process` and `preprocess` are server-side scripts.
- **Edge** — pairwise relationship: affinity score, assignment, bid, conflict. `head` is the "from" entity (usually a paper), `tail` is the "to" entity (usually a profile or group).
- **Tag** — metadata annotation on a Note or Profile.
- **Profile** — user identity. Multiple `names` and `emails` are possible; `~FirstName_LastName1` is the canonical ID.
- **Edit** — wrapper recording a change to a Note, Group, or Invitation. **All mutations in v2 go through Edits.** The Edit records who made the change (`signatures`) and under what authority (`invitation`).

## Content Structure (v2)

v2 content uses a nested `{'value': ...}` shape consistently:

```python
note.content['title']['value']      # 'My Paper Title'
note.content['authors']['value']    # ['Alice', 'Bob']
note.content['title']               # {'value': 'My Paper Title'} — almost never what you want
```

Invitation content templates define allowed parameters via a `param` block:

- `{'title': {'value': {'param': {'type': 'string', 'regex': '.*'}}}}`
- Param types: `string`, `integer`, `boolean`, `file`, `date`, `string[]`, `object[]`, `profile[]`, `group[]`, `note[]`.
- Param constraints: `regex`, `enum`, `maxLength`, `minLength`, `minimum`, `maximum`, `optional`, `deletable`, `markdown`, `input` (text/textarea/radio/checkbox/select).

## Date Handling

- **All dates are Unix epoch milliseconds (integer), not seconds.** Passing seconds produces values that look like 1970 to the server.
- `openreview.tools.datetime_millis(dt)` converts a datetime to millis.
- `openreview.tools.timestamp_GMT(year, month, day, hour, minute)` creates absolute timestamps.
- Note date fields: `cdate` (creation), `mdate` (modification), `ddate` (deletion / soft-delete), `tcdate`/`tmdate` (immutable true creation/modification), `pdate` (publication), `odate` (original).
- Invitation date fields: `cdate` (when active), `duedate` (soft deadline), `expdate` (hard cutoff).
- **Invariant:** `cdate <= duedate <= expdate`. Convention: `expdate = duedate + 30 minutes` as a grace period.

## Permission Model

Every object has:

- `readers`: group/profile IDs that can see this object
- `writers`: group/profile IDs that can modify this object
- `signatures`: group/profile IDs that created this object (provenance)
- `nonreaders`: explicitly excluded groups (overrides readers)

Special groups:

- `everyone` — all users including anonymous
- `~` — all logged-in users
- `(anonymous)` — anonymous signature
- `(guest)` — guest users

Anonymous reviewer groups: `{VenueID}/Paper{N}/Reviewer_{hash}` hide reviewer identity from authors.

Role hierarchy (highest to lowest privilege): Editors-in-Chief / Program Chairs → Senior Area Chairs → Area Chairs / Action Editors → Reviewers → Authors.

**Conflict-of-interest isolation:** authors are typically added as `nonreaders` on reviewer assignment edges so authors cannot see who's reviewing them.

## Async Processing

Many edits trigger server-side process functions (defined in the invitation's `process` script). These run asynchronously after the edit is saved.

- Pass `await_process=True` on `post_*_edit` calls to block until the server-side process completes.
- The edit response is a dict: `result['id']` is the edit ID, `result['note']['id']` is the resulting note ID.
- Process functions can cascade: one edit may trigger creation of new invitations, groups, or edges.
- **Without `await_process`, subsequent operations that depend on process results race the server and may see stale state.**

## Venue Workflow

Standard conference stages in order:

1. **Venue Request** — PC posts a note edit to `openreview.net/Support/Venue_Request/-/Conference_Review_Workflow` with venue name, dates, committee config.
2. **Deploy** — Support posts a deployment edit with the `venue_id`. Creates venue group, committee groups (Authors, Reviewers, Area_Chairs, Senior_Area_Chairs), and the submission invitation.
3. **Recruit Committee** — invite SACs, then ACs, then Reviewers.
4. **Registration** (optional) — committee members fill expertise/availability forms.
5. **Submission** — authors post papers via `{VenueID}/-/Submission`. Optional two-stage: abstract deadline then full submission.
6. **Post-Submission** — lock fields, adjust readers, hide specified fields (keywords, PDF).
7. **Bidding** — reviewers/ACs express paper preferences via bid edges.
8. **Matching** — affinity scores + conflicts computed; assignment proposed.
9. **Assignment** — assignment edges posted to `{VenueID}/Reviewers/-/Assignment`.
10. **Review** — reviewers submit `{VenueID}/Submission{N}/-/Official_Review`.
11. **Rebuttal** (optional) — authors respond to reviews.
12. **Meta-Review** — ACs synthesize reviewer feedback.
13. **Decision** — PCs post accept/reject decisions.
14. **Post-Decision** — release decisions, create camera-ready invitations, publish accepted papers.

Committee structure options:

- **Hierarchical**: SAC → AC → Reviewer (NeurIPS, ICML, AAAI)
- **Two-tier**: AC → Reviewer (EMNLP, KDD)
- **Flat**: Reviewer only (workshops)

Anonymity options: double-blind (authors and reviewers anonymous to each other) | single-blind (reviewers anonymous, authors visible) | none (workshops).

After deployment, venue groups follow the pattern: `{VenueID}`, `{VenueID}/Authors`, `{VenueID}/Reviewers`, `{VenueID}/Area_Chairs`, `{VenueID}/Senior_Area_Chairs`, `{VenueID}/Program_Chairs`. Per-paper groups follow: `{VenueID}/Submission{N}/Authors`, `{VenueID}/Submission{N}/Reviewers`, `{VenueID}/Submission{N}/Area_Chairs`.

## Journal Workflow

Standard journal stages in order:

1. **Submit** — author posts paper to `{JournalID}/-/Submission`.
2. **Author Recommends AE** — author posts AE recommendation edges.
3. **EIC Assigns AE** — EIC posts AE assignment edge.
4. **Review Approval** — AE decides "Appropriate for Review" or "Desk Reject".
5. **Under Review** — automatic state transition; `venueid` changes from `Submitted` to `Under_Review`.
6. **AE Assigns Reviewers** — reviewer assignment edges posted.
7. **Reviews** — reviewers submit reviews.
8. **Official Recommendation** (if enabled) — reviewers provide explicit recommendations.
9. **Ratings** — AE rates each review; **the decision invitation only activates after all ratings are submitted.**
10. **Decision** — AE submits decision (Accept as is / Revise / Reject) and optional certifications.
11. **Camera-Ready** — authors submit revision via `{JournalID}/Paper{N}/-/Camera_Ready_Revision`.
12. **Verification** — publication chair verifies camera-ready.

Journal-specific concepts:

- **Certifications**: Featured, Reproducibility, Survey, Outstanding (journal-specific subsets).
- **Assignment delay**: configurable wait before AE assignment (0-5 days).
- **Anonymous groups**: `{JournalID}/Paper{N}/Action_Editor_{hash}`, `{JournalID}/Paper{N}/Reviewer_{hash}`.
- **Matching edges**: Affinity_Score, Conflict, Custom_Max_Papers, Assignment_Availability.

Per-journal configuration (reviewer count, anonymity, license, etc.) varies — see each journal's request form for specifics.

## Constraints and Invariants

- Group operations (add/remove members) are idempotent — adding an existing member or removing an absent one is a no-op.
- Soft deletion via `ddate`. Items with `ddate` set are hidden by default; pass `trash=True` to include them.
- Protected fields: `venue` and `venueid` in submission content cannot be deleted via the Form_Fields invitation.
- Invitation date ordering: `cdate <= duedate <= expdate`. Convention: `expdate = duedate + 30 minutes`.
- AuthorID validation: must match profile IDs (`~...`) or valid email addresses. Accented characters in emails are rejected.
- Edge weight conventions: `1` for assignment, `-1` for conflict, `0` for completed/inactive.
- Maximum 1000 items per `get_*()` call. Use `get_all_*()` or `iterget_*()` for larger result sets.
- Content field access: always `note.content['field']['value']` in v2. Never `note.content['field']` directly.
- All dates in epoch milliseconds (not seconds).
- Form_Fields duedate is calculated as `submission_start - 30 minutes`.

## Anti-Patterns to Avoid

- **Missing `await_process=True` after edits that trigger process functions** — leads to race conditions where subsequent operations see stale state.
- **Posting edits without proper signatures** — the server validates that signatures match the authenticated user's permissions.
- **Assigning conflicted reviewers** — conflicts are checked server-side and the assignment will be rejected.
- **Deleting protected form fields** (`venue`, `venueid`) — the preprocess script blocks this with an error.
- **Using expired tokens without re-authentication** — raises `TokenExpiredError`.
- **Mixing v1 and v2 URLs** — using `api.openreview.net` with `openreview.api.OpenReviewClient` (or vice versa) raises an error.
- **Using `get_notes()` when expecting more than 1000 results** — silently truncates. Use `get_all_notes()` instead.
- **Copying v1 keyword args onto a v2 call** — e.g., `get_invitations(regex=...)` works on v1 but raises `TypeError` on v2 (use `prefix=...`). Always check the `[v1]`/`[v2]` tag.
- **Activating decision invitations before all reviewer ratings are submitted (in journals)** — the decision invitation is gated on ratings completion.
- **Directly modifying group members without `add_members_to_group()` / `remove_members_from_group()`** — use the idempotent helper methods.
- **Accessing `note.content['field']` without `['value']`** — returns the wrapper dict, not the actual data.
- **Posting notes with `content={'title': 'value'}` instead of `content={'title': {'value': 'value'}}`** — the nested structure is required in v2.
- **Bumping `cdate` without also updating `expdate`** — violates the `cdate <= duedate <= expdate` invariant and the server rejects with "cdate cannot be greater than expdate".
- **Passing epoch seconds instead of milliseconds** — `1748000000` looks like 1970 to the server; use `openreview.tools.datetime_millis(dt)`.

## Security Constraints

- **Author nonreaders on edges**: assignment and affinity edges set `nonreaders` to include the paper's authors, preventing conflict-of-interest information leakage.
- **Blind review enforcement**: `readers`/`nonreaders` on notes control what each role can see at each stage. Double-blind hides both author and reviewer identities.
- **Name validation for author claims**: DBLP author coreference validates that the claiming user's name matches the paper's author list.
- **Role-based access**: every operation is gated by the user's membership in the appropriate group. Non-members receive permission errors.
- **iThenticate integration**: plagiarism checks with EULA agreement required before submission (when enabled).
- **Profile merge is one-way**: secondary profile is merged into primary. The operation cannot be reversed.
- **Recruitment invitations use HMAC-signed URLs** to prevent unauthorized responses.
