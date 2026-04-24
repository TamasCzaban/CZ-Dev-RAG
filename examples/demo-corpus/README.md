# Demo corpus

> ⚠️ **These documents are synthetic.** Every company, person, date, amount, and contract clause in this folder is fabricated for demonstration purposes. Any resemblance to real agreements is coincidental.
>
> No real CZ Dev client documents are committed to this repository — the `data/input/` folder is gitignored and lives only on Tamas's host machine. See [ADR-010](../../docs/DECISIONS.md#adr-010--mit-license-public-repo-private-data-via-gitignore).

This corpus exists so a recruiter cloning the repo can run the demo end-to-end without any real client data, and so the Ragas eval harness in phase 05 has stable inputs.

## Contents

| File | Type | Purpose |
|---|---|---|
| `acmeco-msa.md` | Master Services Agreement | Tests contract-style retrieval — legal clauses, defined terms, nested sections |
| `acmeco-sow-001.md` | Statement of Work | Tests structured retrieval — milestones, acceptance criteria, tables |
| `bemer-kickoff-notes.md` | Meeting notes | Tests narrative retrieval — attendees, decisions, action items |
| `cz-dev-pricing-internal.md` | Internal pricing reference | Tests cross-document queries — pricing questions that reference the MSA + SOW |
| `bilingual-one-pager.md` | Bilingual EN + HU | Tests multilingual retrieval — BGE-M3's Hungarian capability |

## Suggested demo queries

After ingesting this corpus via the LightRAG web UI or `scripts/ingest.py`, try:

1. **Basic retrieval** — "What are the payment terms in the AcmeCo MSA?"
2. **Cross-document** — "What is the total value of SOW-001, and how does it compare to CZ Dev's build sprint pricing range?"
3. **Narrative** — "What did BEMER decide was out of scope for v2?"
4. **Multilingual** — "Mit csinál a CZ Dev?" (Hungarian — "What does CZ Dev do?")
5. **Dates and deadlines** — "When is milestone M3 of SOW-001 due, and what does it deliver?"

These queries are reused by the Ragas eval harness in phase 05.

## Adding documents

If you add another synthetic doc:
- Keep it obviously fake (fabricated names, absurd-enough amounts, implausible dates if needed)
- Add a row to the table above
- Optionally add a query to the suggested list if it exercises a new retrieval pattern
