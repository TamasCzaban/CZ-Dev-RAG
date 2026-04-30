# Phase 14 — Tailscale admin — device tagging + tag-based ACL [HITL]

**Issue:** [#30](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/30)
**Branch:** `phase/14-tailscale-acl-device-tags`
**Type:** HITL — Tailscale admin console UI work; no automated test possible
**Date planned:** 2026-04-30

---

## Objective

In the Tailscale admin console, define `tag:rag-host` and `tag:rag-user` tags, assign Tamas's 3090 box the `tag:rag-host` tag, and deploy a tag-based ACL that restricts tailnet access to ports 9621 (LightRAG query), 9622 (LightRAG ingest), and 3000 (Langfuse) to `tag:rag-user → tag:rag-host` only.

**Tailnet info (from Phase 13):**
- Tailnet domain: `tailabdd49.ts.net`
- Host machine name: `desktop-rh9a2o7`
- Tailscale IP: `100.105.249.5`
- MagicDNS hostname: `desktop-rh9a2o7.tailabdd49.ts.net`

---

## HITL Gate — Human Action Required

This phase **cannot be executed by Claude Code**. It requires:
1. Login to the Tailscale admin console at https://login.tailscale.com/admin
2. UI-based tag definition (tagOwners block in ACL JSON)
3. Manual device tag assignment in the Machines view
4. ACL JSON editor in the console

**Resume signal:** Once all acceptance criteria below are checked, mark `ROADMAP.md` Phase 14 status to `DONE` and run `git commit && git push` to complete the phase gate.

---

## Pre-flight checklist (verify before starting)

- [ ] Phase 13 is DONE — Tailscale installed, `tailscale ip -4` returns `100.105.249.5`, MagicDNS enabled
- [ ] You are logged into https://login.tailscale.com/admin as `tomi13824@gmail.com`
- [ ] You are the **owner** of the tailnet (only owners can edit ACLs and define tags)

---

## Step-by-step manual instructions

### Step 1 — Open the ACL editor

1. Go to https://login.tailscale.com/admin/acls
2. You will see the current HuJSON ACL policy in an editor pane.
3. Click **Edit** (or the pencil icon) to enter edit mode.

---

### Step 2 — Paste the ACL JSON

Replace the **entire contents** of the ACL editor with the following HuJSON. This is the complete policy — it defines tags, their owners, and the access rules.

```jsonc
// Tailscale ACL for tailabdd49.ts.net
// Phase 14 — tag-based access control for CZ-Dev-RAG
{
  // Define tags and their owners.
  // The tag owner (autogroup:admin) can assign these tags to devices.
  "tagOwners": {
    "tag:rag-host": ["autogroup:admin"],
    "tag:rag-user": ["autogroup:admin"]
  },

  // ACL rules.
  // Tailscale evaluates rules top-to-bottom; first match wins.
  "acls": [
    // Rule 1: tag:rag-user devices can reach tag:rag-host on RAG service ports.
    {
      "action": "accept",
      "src":    ["tag:rag-user"],
      "dst":    ["tag:rag-host:9621",  // LightRAG query API
                 "tag:rag-host:9622",  // LightRAG ingest API
                 "tag:rag-host:3000"]  // Langfuse dashboard
    },
    // Rule 2: tag:rag-host devices can initiate outbound connections (e.g. Ollama pull).
    {
      "action": "accept",
      "src":    ["tag:rag-host"],
      "dst":    ["*:*"]
    },
    // Rule 3: admin (autogroup:admin) retains full access for management.
    {
      "action": "accept",
      "src":    ["autogroup:admin"],
      "dst":    ["*:*"]
    }
  ]
}
```

> **Important:** Tailscale's ACL editor uses **HuJSON** (JSON with `//` comments). The comments above are valid — do not strip them before pasting.

---

### Step 3 — Validate the ACL

1. After pasting, click **Validate** (or the shield/check icon in the editor toolbar).
2. The console should show **"Policy is valid"** or a green checkmark with no errors.
3. If you see errors, see the Troubleshooting section below.

---

### Step 4 — Save the ACL

1. Click **Save** to deploy the ACL to the tailnet.
2. The console confirms the save. All connected devices now operate under the new policy.

---

### Step 5 — Assign `tag:rag-host` to the 3090 box

1. Go to https://login.tailscale.com/admin/machines
2. Find the machine named `desktop-rh9a2o7` (IP `100.105.249.5`).
3. Click the **⋮** (kebab menu) or the machine name → **Edit route settings** or **Machine settings**.
4. Look for **Tags** or **Edit tags**.
5. Add the tag `tag:rag-host`.
6. Click **Save**.

> **Note:** After tagging, the device loses its user-owned identity and becomes owned by the tag. This means `tailscale status` will show it as `tagged-devices` rather than a user device. This is expected — the ACL rules apply based on the tag.

---

### Step 6 — Verify the tag assignment

1. Still on the Machines page, confirm `desktop-rh9a2o7` shows **rag-host** in its tags column.
2. Run on the host (PowerShell):
   ```powershell
   tailscale status
   ```
   The local device entry should now show `tag:rag-host` rather than the user email.

---

### Step 7 — Smoke test (optional but recommended)

If you have a second device on the tailnet (or after Phase 15 when Zsombor joins), verify connectivity:

```bash
# From a tag:rag-user device (or from the host itself as a quick loopback test)
curl http://100.105.249.5:9621/health
```

Expected: HTTP 200 with `{"status":"ok"}` (if the RAG stack is running) or `Connection refused` (if stack is down — that's fine; what matters is that Tailscale routes the packet).

A device **without** `tag:rag-user` should get no response (timeout/blocked by ACL).

---

## Acceptance criteria (from issue #30)

- [ ] Tag `tag:rag-host` is defined in the tailnet's ACL `tagOwners` section.
- [ ] Tag `tag:rag-user` is defined in the tailnet's ACL `tagOwners` section.
- [ ] Tamas's 3090 box (`desktop-rh9a2o7`) has the `tag:rag-host` tag applied in the Machines view.
- [ ] The ACL JSON includes a rule allowing `tag:rag-user` → `tag:rag-host` on ports 9621, 9622, 3000 (TCP).
- [ ] ACL is saved and validated without errors in the admin console.
- [ ] A device tagged `tag:rag-user` can reach `http://100.105.249.5:9621/health` (200 response when stack is up).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| ACL editor shows "invalid JSON" | Check for stray commas or missing braces; Tailscale uses HuJSON so `//` comments are fine |
| `tagOwners` key not accepted | Ensure you are the tailnet **owner** (not just an admin member of someone else's tailnet) |
| Machine tags option not visible | Machine must already be on the tailnet; check `tailscale status` on the host |
| After tagging, `tailscale ssh` stops working | Expected — tagged devices use ACL rules, not user SSH grants. Phase 12 already filed the SSH follow-up issue (#35). |
| Port 9621 still unreachable after ACL save | Verify Docker Compose is running: `docker compose ps`. ACL allows traffic; app still needs to be up. |
| ACL validator warns "no rules match tag:rag-user" | This is a warning, not an error, when no devices are yet tagged `tag:rag-user`. It clears after Phase 15. |

---

## What this phase does NOT do (out of scope)

- No code changes to this repository (HITL-only)
- No Zsombor invite (Phase 15)
- No RUNBOOK.md update (Phase 16)
- No SSH ACL rules (deferred — issue #35)

---

## After completion

1. Update `ROADMAP.md` Phase 14 status to `DONE`
2. Update `STATE.md` current phase to Phase 15
3. Commit changes:
   ```bash
   git add ROADMAP.md STATE.md
   git commit -m "chore(state): mark phase 14 DONE in ROADMAP + STATE"
   git push
   ```
4. Proceed to Phase 15: `phase/15-invite-zsombor-tailnet`
