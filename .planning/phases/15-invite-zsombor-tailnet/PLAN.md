# Phase 15 — Invite Zsombor to tailnet via Google SSO + assign tag:rag-user

**Issue:** [#31](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/31)
**Branch:** `phase/15-invite-zsombor-tailnet`
**Type:** HITL (Human-In-The-Loop) — no code changes; all steps require manual action in the Tailscale admin console and on Zsombor's machine.
**Depends on:** Phase 13 (Tailscale installed, MagicDNS enabled), Phase 14 (ACL defined, tag:rag-host/tag:rag-user exist)

---

## Tailnet context

| Item | Value |
|------|-------|
| Tailnet domain | `tailabdd49.ts.net` |
| Tamas's host | `desktop-rh9a2o7` |
| Tamas's Tailscale IP | `100.105.249.5` |
| Tamas's device tag | `tag:rag-host` |
| Zsombor's target tag | `tag:rag-user` |
| Zsombor's email | **[ZSOMBOR_EMAIL]** — fill in before Step 1 |

> **ACTION REQUIRED:** Replace `[ZSOMBOR_EMAIL]` with Zsombor's actual Google-account email before sending the invite.

---

## Step 1 — Tamas: send the invite from Tailscale admin console

1. Go to [https://login.tailscale.com/admin/users](https://login.tailscale.com/admin/users)
2. Click **Invite users**.
3. Enter `[ZSOMBOR_EMAIL]` (Zsombor's Google account email).
4. Leave the role as **Member** (not Admin).
5. Click **Send invite**.
6. Confirm the invite appears in the **Pending invites** list.

---

## Step 2 — Zsombor: accept the invite and install Tailscale

Zsombor performs these steps on his machine (macOS / Linux / Windows — whichever he uses):

1. Check email for the Tailscale invite from `[ZSOMBOR_EMAIL]` and click **Accept invite**.
2. If Tailscale is not yet installed:
   - **macOS:** `brew install tailscale` or download from [https://tailscale.com/download/mac](https://tailscale.com/download/mac)
   - **Linux:** `curl -fsSL https://tailscale.com/install.sh | sh`
   - **Windows:** download from [https://tailscale.com/download/windows](https://tailscale.com/download/windows)
3. Sign in to Tailscale using the same Google account (`[ZSOMBOR_EMAIL]`).
4. After sign-in, confirm device is connected:
   ```
   tailscale status
   ```
   The output should show Zsombor's device as **connected** and Tamas's host `desktop-rh9a2o7` as a peer.

---

## Step 3 — Tamas: assign tag:rag-user to Zsombor's device

Once Zsombor's device appears in the tailnet:

1. Go to [https://login.tailscale.com/admin/machines](https://login.tailscale.com/admin/machines)
2. Find Zsombor's machine in the list.
3. Click the machine name → **Machine settings** (three-dot menu or machine detail page).
4. Under **Tags**, click **Edit tags**.
5. Add `tag:rag-user`.
6. Click **Save**.

> Note: only a tag owner (Tamas, as per ADR-008 ACL) can assign `tag:rag-user`. The tag was defined in Phase 14.

---

## Step 4 — Verify access from Zsombor's machine

Zsombor runs the following from his machine to confirm the ACL permits access to the RAG host:

```bash
# Confirm Tamas's host is reachable via MagicDNS
ping desktop-rh9a2o7.tailabdd49.ts.net

# Confirm the LightRAG health endpoint returns 200
curl -v http://desktop-rh9a2o7.tailabdd49.ts.net:9621/health

# Confirm MCP server is reachable
curl -v http://desktop-rh9a2o7.tailabdd49.ts.net:3000/health
```

All three commands should succeed. If `curl` returns connection refused or times out, check:
- LightRAG and MCP containers are running on Tamas's host: `docker compose ps`
- ACL permits `tag:rag-user → tag:rag-host` on ports 9621 and 3000 (verified in Phase 14)
- Zsombor's device has `tag:rag-user` assigned (Step 3 above)

---

## Step 5 — Tamas: verify from host side

On Tamas's host, confirm Zsombor's device appears as a peer:

```bash
tailscale status
```

Expected: Zsombor's device listed with a `100.x.x.x` IP and status `connected`.

---

## Acceptance criteria (from issue #31)

- [ ] Tailscale admin console shows Zsombor as a **Member** of the tailnet
- [ ] `tailscale status` on Tamas's host lists Zsombor's device as a peer
- [ ] `curl http://desktop-rh9a2o7.tailabdd49.ts.net:9621/health` from Zsombor's machine returns **HTTP 200**
- [ ] Zsombor's device has `tag:rag-user` assigned in the admin console

---

## Done condition

Mark this phase DONE in `ROADMAP.md` (update the Status line) once all four acceptance criteria are checked off.

Update `STATE.md` to reflect Phase 15 complete and Phase 16 as the next phase.
