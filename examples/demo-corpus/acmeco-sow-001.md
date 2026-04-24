# Statement of Work #001

**SOW Number:** SOW-ACMECO-2026-001
**Under MSA:** MSA-ACMECO-2026-001 (Effective 2026-02-01)
**Effective date:** 2026-02-15
**Client:** AcmeCo Industries Inc.
**Provider:** CZ Dev Kft.

---

## 1. Engagement Summary

Provider will design and implement a redesigned customer dashboard for AcmeCo's SaaS product, replacing the existing Angular 12 dashboard with a modern React + TypeScript stack. The engagement covers discovery, design, implementation, QA, and handover.

## 2. Deliverables

1. **Discovery report** — stakeholder interviews (5), user journey maps, metric-impact analysis. Delivered as a single PDF.
2. **Design system baseline** — Figma file with design tokens, 12 core components, and 6 dashboard page layouts.
3. **Implementation** — React 18 + TypeScript codebase with:
   - Authentication integration (Client's existing Auth0 tenant)
   - 6 dashboard pages (Overview, Billing, Team, Usage, Settings, Support)
   - End-to-end tests (Playwright) covering critical user flows
   - CI/CD integration with Client's existing GitHub Actions workflows
4. **QA report** — test coverage summary, accessibility audit (WCAG 2.1 AA), Lighthouse scores for all 6 pages
5. **Handover package** — runbook, onboarding guide for Client's internal engineers, 2 knowledge-transfer sessions

## 3. Milestones and Schedule

| Milestone | Description | Target Date | Payment |
|---|---|---|---|
| M1 | Discovery report accepted | 2026-03-06 | €8,000 |
| M2 | Design system baseline accepted | 2026-03-27 | €12,000 |
| M3 | Implementation — 3 pages live in staging | 2026-04-24 | €14,000 |
| M4 | Implementation — 6 pages live in staging | 2026-05-15 | €10,000 |
| M5 | QA report + production launch | 2026-06-05 | €4,000 |
| | **Total** | | **€48,000** |

## 4. Acceptance Criteria

### 4.1 Discovery report

- Report submitted to Client's designated stakeholder within 3 weeks of SOW effective date
- Includes at least 5 stakeholder interview summaries
- Includes at least 3 user journey maps
- Client accepts by email or provides written revision requests within 5 business days

### 4.2 Design system baseline

- All 12 core components match the reference wireframes from discovery
- Figma file accessible to at least 3 Client designers
- Components pass contrast checks at the AA level
- Client accepts by email or provides written revision requests within 5 business days

### 4.3 Implementation

- All 6 pages render correctly in evergreen browsers (Chrome, Firefox, Safari, Edge — latest 2 versions)
- Page-level Lighthouse performance score ≥ 85 on desktop and ≥ 70 on mobile
- Accessibility score ≥ 95 on all pages
- E2E test coverage: at least one happy-path test per page
- No P0 or P1 bugs open at milestone review

### 4.4 QA report and launch

- QA report submitted at least 5 business days before target launch date
- WCAG 2.1 AA compliance verified
- Production deployment completed with no P0 issues outstanding
- Handover sessions attended by at least 2 Client engineers

## 5. Fees

Fixed price: **€48,000** payable against milestones as listed in Section 3. Invoices are issued upon milestone acceptance and are due net thirty (30) days per MSA Section 4.1.

Expenses (if any, pre-approved) are invoiced separately at cost plus 10%.

## 6. Change Management

Scope changes must be documented in a written Change Order signed by both parties. Change Orders may modify fees, timelines, or deliverables. Provider will not perform work outside of this SOW without an executed Change Order.

## 7. Assumptions and Dependencies

- Client provides timely access to their staging environment, Auth0 tenant credentials, and a technical point of contact with at least 10 hours per week of availability
- Client provides design assets (logo, brand colors, fonts) by 2026-02-22
- Provider may use its internal AI-assisted tooling (see MSA §6) in performing the Services
- Assumptions regarding Client response times are baked into the schedule; delays exceeding 5 business days may shift target dates on a day-for-day basis

## 8. Team

**Provider team:**
- Tamas Czaban — Engagement lead, backend + data
- Zsombor Czaban — Frontend + UX lead

**Client point of contact:** Priya Mehta, VP Product (priya.mehta@acmeco.example)

---

**FOR CLIENT:** AcmeCo Industries Inc.
_Priya Mehta, VP Product · 2026-02-15_

**FOR PROVIDER:** CZ Dev Kft.
_Tamas Czaban, Managing Director · 2026-02-15_
