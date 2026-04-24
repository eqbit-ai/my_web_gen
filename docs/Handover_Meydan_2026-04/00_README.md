# Handover — Meydan AI Website Generator
**Package**: `Handover_Meydan_2026-04`
**Delivered**: April 2026 (last reviewed 2026-04-24)
**Audience**: A developer who has not seen the product before.

## Snapshot at handover

- **Current branch with live users**: `dev` — deployed to AWS us-east-1, served at `https://meydanfzai.com` (and `https://dev.meydanfzai.com`).
- **Prod branch**: `main` — wired to `deploy-prod.yml` targeting UAE me-central-1, but the prod cluster is **not yet provisioned**. The migration is paused (see `10_known_issues_and_support.md`).
- **Live health checks**: `GET /api/health` returns `{"status":"ok"}` on both URLs at time of writing.
- **Outstanding end-user bugs**: 1 (carousels in generated sites — `10_known_issues_and_support.md` item 1).
- **Outstanding security/config items**: apex DNS not Cloudflare-proxied (C1), SonarCloud token missing (C2), CI wait-for-stable occasionally noisy (C3). Full list in `10_known_issues_and_support.md`.

## How to read this folder

Start at the top of the list and work down. Every document is self-contained; you do not need to read files in order to understand one of them, but reading them in order is the fastest way to become operational.

| # | Document | What it answers |
|---|---|---|
| 1 | `01_system_overview.md` | What is this product, in 5 minutes? |
| 2 | `02_architecture_diagram.md` | How do the pieces fit together? |
| 3 | `03_user_workflow.md` | What does an end user actually do? |
| 4 | `04_admin_workflow.md` | How do I operate the product as an admin? |
| 5 | `05_code_structure.md` | Where does each concern live in the repo? |
| 6 | `06_api_reference.md` | What endpoints exist, and how do I call them? |
| 7 | `07_deployment_runbook.md` | How do I deploy from a clean AWS account? |
| 8 | `08_environment_and_secrets.md` | Every env var and where it comes from. |
| 9 | `09_ongoing_costs.md` | Pointer — see the Ongoing Costs sheet in the handover workbook. |
| 10 | `10_known_issues_and_support.md` | What is unfinished, and who to call. |

## Source assets

Editable architecture diagram source: `assets/architecture.drawio`
Rendered diagram: `assets/architecture.png`
Screenshots for workflows: `assets/screenshots/` (placeholders listed in each workflow doc)

## Contact at handover

- **Technical lead (vendor)**: Ashutosh — ashuken266@gmail.com
- **Meydan AI lead**: see `10_known_issues_and_support.md`

## Questions

Any questions on a specific document: raise *before* drafting changes, not after delivery. Contact the technical lead above.
