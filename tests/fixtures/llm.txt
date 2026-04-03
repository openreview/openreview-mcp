# openreview-py

> Python client for the OpenReview academic peer review platform.

## Authentication

- Username/password: `OpenReviewClient(username='...', password='...')`
- Token auth: `OpenReviewClient(token='...')` — takes precedence over username/password
- Environment variables: `OPENREVIEW_USERNAME`, `OPENREVIEW_PASSWORD`
- Expired tokens raise `TokenExpiredError`.

## Content Structure

v2 content uses `{'field_name': {'value': actual_data}}` consistently:
- Access: `note.content['title']['value']`
- Never access `note.content['title']` directly — always go through `['value']`

## Conference Workflow

Standard conference stages in order:

1. Venue Request: Post a request form to `openreview.net/Support/-/Request_Form`.
2. Deploy: Post deploy note. Creates venue group, committee groups, and submission invitation.
3. Recruit Committee: Invite SACs, then ACs, then Reviewers.
4. Submission: Authors post papers via `{VenueID}/-/Submission`.
5. Review: Reviewers submit official reviews.
6. Decision: PCs post accept/reject decisions.

## Anti-Patterns to Avoid

- Missing `await_process=True` after edits that trigger process functions.
- Using `get_notes()` when expecting more than 1000 results — use `get_all_notes()`.
- Accessing `note.content['field']` without `['value']`.
