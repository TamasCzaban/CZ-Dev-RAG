# Phase 12 — File Tailscale SSH follow-up issue + update ADR-008 rollout status

**Issue:** [#28](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/28)
**Branch:** `phase/12-tailscale-ssh-issue-adr008`
**Type:** docs-only + GH issue creation — no code, no tests

## Objective

Close the deferred Tailscale SSH item from the Decision Summary by:
1. Creating a GitHub issue for "Enable Tailscale SSH for Tamas-only convenience access"
2. Appending a "Rollout status" note to ADR-008 in `docs/DECISIONS.md` with the completion date and a forward reference to the new issue

## Steps

1. Create GitHub issue: "Enable Tailscale SSH for Tamas-only convenience access"
   - Body: use case (access host from own laptop when box is on), note that it is deferred from the Tailscale v1 rollout
   - Label: `slice` or `enhancement`

2. Append to ADR-008 in `docs/DECISIONS.md`:
   - A "Rollout status" subsection with today's date (2026-04-30)
   - Forward reference to the new GitHub issue number

## Acceptance criteria (from issue #28)

- [ ] New GH issue "Enable Tailscale SSH for Tamas-only convenience access" exists with use-case description and deferred-from-v1 note
- [ ] `docs/DECISIONS.md` ADR-008 has appended "Rollout status" note with date + issue reference
- [ ] No Tailscale SSH config added
