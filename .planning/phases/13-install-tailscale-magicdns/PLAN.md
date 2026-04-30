# Phase 13 — Install Tailscale on host + enable MagicDNS [HITL]

**Issue:** [#29](https://github.com/TamasCzaban/CZ-Dev-RAG/issues/29)
**Branch:** `phase/13-install-tailscale-magicdns`
**Type:** HITL — OS-level installer + browser-based SSO auth; no automated test possible
**Date planned:** 2026-04-30

---

## Objective

Install Tailscale on Tamas's Windows 11 host, authenticate to the personal tailnet, enable MagicDNS, and record the stable MagicDNS hostname for use in downstream phases (14–17).

---

## HITL Gate — Human Action Required

This phase **cannot be executed by Claude Code**. It requires:
1. A Windows installer that modifies kernel-level networking (WireGuard TAP driver)
2. Browser-based OAuth/SSO authentication to tailscale.com
3. Manual configuration in the Tailscale admin web console

**Resume signal:** Once all acceptance criteria below are checked, re-run `/gsd-run-phase 14` (or update `ROADMAP.md` Phase 13 status to `DONE` manually and push to complete the phase gate).

---

## Pre-flight checklist (verify before starting)

- [ ] Windows 11 host is running and has internet access
- [ ] You have admin rights (UAC elevation will be required)
- [ ] You have a Tailscale account at https://login.tailscale.com (use your Google SSO at `tomi13824@gmail.com`)
- [ ] Docker Desktop is paused or not running its WireGuard-adjacent networking — Tailscale's WireGuard driver can conflict on first install

---

## Step-by-step manual instructions

### Step 1 — Install Tailscale

**Option A (winget — preferred):**
```powershell
winget install tailscale.tailscale
```
- UAC prompt will appear — approve it.
- Installer downloads the WireGuard TAP driver and installs the Tailscale service.
- The system tray icon appears when complete.

**Option B (GUI installer — fallback if winget fails):**
1. Go to https://tailscale.com/download/windows
2. Download the `.exe` installer
3. Run it as Administrator
4. Follow the installer wizard

**Verify install:**
```powershell
tailscale version
```
Should print a version number (e.g. `1.x.x`). If `tailscale` is not in PATH, restart PowerShell or add `C:\Program Files\Tailscale` to PATH.

---

### Step 2 — Authenticate to the tailnet

```powershell
tailscale up
```
- A browser window opens automatically pointing to `https://login.tailscale.com/a/<token>`
- Log in with `tomi13824@gmail.com` (Google SSO)
- Authorize the device when prompted ("Authorize device — tamas-pc")
- The terminal should print: `Success.`

**Verify:**
```powershell
tailscale status
```
Expected output: at least one line showing this machine with a `100.x.x.x` IP and state `active`.

```powershell
tailscale ip -4
```
Should return a single line: `100.x.x.x`

---

### Step 3 — Enable MagicDNS in the admin console

1. Go to https://login.tailscale.com/admin/dns
2. Under **DNS**, scroll to **MagicDNS**
3. Toggle **Enable MagicDNS** → On
4. Click **Save** (or the console auto-saves)

MagicDNS assigns stable `<hostname>.<tailnet-name>.ts.net` names to all devices.

---

### Step 4 — Verify MagicDNS hostname

```powershell
tailscale status
```
The host entry for this machine should now show a `.ts.net` hostname in the format:
`tamas-pc.tail-XXXX.ts.net` (the exact suffix depends on your tailnet name).

Note the full MagicDNS hostname — you will need it in:
- Phase 14 (ACL policy — `src` device tag)
- Phase 16 (RUNBOOK.md — `<TAILSCALE_HOST>` placeholder)

---

### Step 5 — Record the MagicDNS hostname

Edit `docs/RUNBOOK.md` (if the `<TAILSCALE_HOST>` placeholder exists) and replace it with the actual hostname from `tailscale status`.

Also note the `100.x.x.x` IP — record both values in your notes for Phase 16.

---

### Step 6 — Run a connectivity smoke test

Once MagicDNS is enabled, verify that the Tailscale IP reaches the host:

```powershell
# From this same machine (loopback via Tailscale)
curl http://$(tailscale ip -4):9621/health
```

If the RAG stack is not running yet, a connection refused is expected — what matters is that the Tailscale IP resolves. The MagicDNS name will be fully testable once Zsombor joins the tailnet (Phase 15).

---

## Acceptance criteria (from issue #29)

- [ ] `winget install tailscale.tailscale` (or GUI installer) completes without error
- [ ] `tailscale up` authenticates and the device appears in the tailnet admin console
- [ ] MagicDNS is enabled in the tailnet admin console (Settings → DNS → Enable MagicDNS)
- [ ] `tailscale ip -4` returns a `100.x.x.x` IP
- [ ] `tailscale status` shows the host with a MagicDNS hostname (e.g. `tamas-pc.tail-XXXX.ts.net`)
- [ ] The MagicDNS hostname is recorded for use in Phases 14, 15, 16 (RUNBOOK.md updates)

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `winget install` times out or 404s | Use GUI installer from tailscale.com/download/windows |
| Browser does not open automatically | Copy the URL from terminal output and paste into browser manually |
| `tailscale up` errors with "route conflict" | Run `tailscale up --accept-routes=false` to skip subnet routing for now |
| WireGuard driver install fails | Disable Hyper-V temporarily: `Disable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V` (reboot required); re-enable after Tailscale installs |
| Docker Desktop stops working after Tailscale install | In Docker Desktop → Settings → Network → uncheck "Use Tailscale for Docker Desktop networking" if visible; or reset Docker network via Docker Desktop UI |
| MagicDNS toggle missing in console | Ensure you are the owner of the tailnet (not a guest user on someone else's tailnet) |

---

## What this phase does NOT do (out of scope)

- No code changes to this repository
- No ACL configuration (Phase 14)
- No Zsombor invite (Phase 15)
- No RUNBOOK.md update (Phase 16 — will use the hostname captured here)
- No Tailscale SSH setup (deferred — see issue #35 if it exists)

---

## After completion

1. Update `ROADMAP.md` Phase 13 status to `DONE`
2. Update `STATE.md` current phase to Phase 14
3. Commit + push to `phase/13-install-tailscale-magicdns`
4. Open PR against `main` referencing issue #29
5. Proceed to Phase 14: `phase/14-tailscale-acl-device-tags`
