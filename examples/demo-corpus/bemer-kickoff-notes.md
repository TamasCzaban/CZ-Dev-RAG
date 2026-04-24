# BEMER CRM v2 — Kickoff Meeting Notes

**Date:** 2026-03-10
**Duration:** 09:00–10:45 CET
**Location:** Video call (Google Meet)
**Author:** Tamas Czaban

## Attendees

- **BEMER GmbH** — Magdalena Huber (Operations Director), Florian Weiss (Finance Controller)
- **CZ Dev** — Tamas Czaban (Engagement Lead), Zsombor Czaban (Frontend Lead)

## Agenda

1. Review of v1 outcomes
2. v2 scope alignment
3. Tech stack decisions
4. Timeline and milestone planning
5. Open questions and next steps

---

## 1. Review of v1 Outcomes

Magdalena opened with a summary of the v1 CRM (shipped 2025-11). Key points:

- Spreadsheet-based rental tracking fully replaced
- Staff time spent on contract lookups dropped from ~45 minutes/day to <10 minutes/day
- Two issues flagged for v2:
  - Document upload UX is clunky; staff avoid uploading scans until end of day
  - Multi-month contract invoicing requires manual spreadsheet export — biggest remaining pain point
- No data migration issues reported

Florian confirmed no billing discrepancies have surfaced since v1 launch.

## 2. v2 Scope Alignment

Three priorities were confirmed:

1. **Multi-month invoice automation** — generate a single invoice for rental contracts spanning 2+ months, with line items per month. Replaces the current Excel export → Word mail-merge workflow.
2. **Document intake UX revamp** — mobile-friendly upload flow; staff should be able to photograph a returned contract with their phone and upload in <30 seconds. Auto-OCR so the scanned contract is searchable.
3. **Staff performance dashboard** — per-staff rental turnover, contract error rates, average response time. Magdalena will review results monthly with the team.

Two items moved out of v2 scope:

- **Payment gateway integration** — Florian would like Stripe integration but agrees it's lower priority than invoicing. Deferred to v3.
- **Customer self-service portal** — considered but rejected; BEMER prefers staff-mediated interaction for rental agreements.

## 3. Tech Stack Decisions

Confirmed continuing with the v1 stack:
- **Frontend:** Streamlit (accepted by staff, minimal retraining)
- **Backend:** Firebase Firestore (data model stable; no migration needed)
- **Auth:** Firebase Auth (existing staff accounts carry over)
- **Hosting:** Firebase Hosting

New additions for v2:
- **OCR:** Google Document AI for scanned contract OCR (discussed as alternative to on-premise Tesseract; Magdalena preferred cloud convenience over local processing since no PII-sensitive fields are in scanned contracts)
- **PDF generation:** LaTeX via weasyprint for multi-month invoices — Florian confirmed this matches BEMER's existing invoice template style

## 4. Timeline and Milestones

Agreed schedule:

| Milestone | Description | Target |
|---|---|---|
| M1 | Invoice automation backend + one template | 2026-04-15 |
| M2 | Invoice automation UI + staff training session | 2026-05-05 |
| M3 | Document intake mobile flow in beta for 2 staff | 2026-05-26 |
| M4 | Document intake rolled out to full team | 2026-06-16 |
| M5 | Staff performance dashboard live | 2026-07-07 |

Florian requested a weekly 30-minute status call on Tuesdays at 09:30 CET. Agreed.

## 5. Open Questions and Next Steps

### Action items

- **Tamas** — draft SOW-BEMER-2026-002 by 2026-03-14. Fixed-price €34,000, milestone-based per above.
- **Tamas** — provision Document AI on CZ Dev's GCP project, share cost projection with Florian by 2026-03-17.
- **Zsombor** — mobile-flow wireframes for document intake by 2026-03-18.
- **Magdalena** — provide access to 10 scanned contracts (anonymized — personal data redacted) for OCR accuracy baseline by 2026-03-13.
- **Florian** — confirm the multi-month invoice format with their accountant and send example PDFs by 2026-03-17.

### Open questions

- How does BEMER handle VAT for rental contracts that span a tax year boundary? Needs clarification before invoice template is finalized.
- Should the staff performance dashboard be visible to all staff, or only to Magdalena? — deferred to M5 planning.

### Next meeting

SOW review call: 2026-03-14 at 10:00 CET.

---

_These notes are approximate, based on Tamas's real-time transcript. If anyone spots an error or a missing action item, please reply within 2 business days._
