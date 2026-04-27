# Handover — Meydan AI Website Generator

**Package**: `Handover_Meydan_2026-04`
**Delivered**: April 2026 (last reviewed 2026-04-27)
**Audience**: A developer who has not seen the product before. Read top to bottom; each document is self-contained.

## Snapshot at handover

- **Live site**: `https://meydanfzai.com` — served from AWS Singapore (`ap-southeast-1`), prod account `290172088819`. via CloudFront edge (CDN + SSL + WAF).
- **Dev environment**: AWS us-east-1, account `371170753756`, served from the same `meydanfzai.com` domain prior to migration; now retained as the testing environment that receives `dev` branch pushes.
- **Health**: `GET /api/health` returns `{"status":"ok","service":"meydan-website-generator"}`.
- **Git**: branch `dev` is the latest. Push to `dev` triggers `deploy-dev.yml`; push to `main` triggers `deploy-prod.yml` (Singapore).

## How to read this folder

| # | Document | What it answers |
|---|---|---|
| 1 | `01_system_overview.md` | What is the product, in five minutes? |
| 2 | `02_architecture_diagram.md` | How do the pieces fit together? |
| 3 | `03_user_workflow.md` | What does an end user actually do? |
| 4 | `04_admin_workflow.md` | How do I operate the product as an admin? |
| 5 | `05_code_structure.md` | Where does each concern live in the repo? |
| 6 | `06_api_reference.md` | What endpoints exist, and how do I call them? |
| 7 | `07_deployment_runbook.md` | How do I deploy from a clean AWS account? |
| 8 | `08_environment_and_secrets.md` | Every env var and where it comes from. |
| 9 | `09_ongoing_costs.md` | Pointer — see the Ongoing Costs sheet in the handover workbook. |
| 10 | `10_known_issues_and_support.md` | What is unfinished, and who to call. |
| + | `disaster_recovery.md` | Backup state + recovery procedures + restore drill plan. |

## Source assets

- Editable architecture diagram source: `assets/diagrams/architecture.html` (open with any browser to edit)
- Rendered diagram: `assets/diagrams/architecture.png`
- Screenshots for workflows: `assets/screenshots/user/` and `assets/screenshots/admin/`

## Contact at handover

- **Technical lead (vendor)**: Ashutosh — ashuken266@gmail.com
- **Meydan AI lead**: see `10_known_issues_and_support.md`

Any questions on a specific document: raise *before* drafting changes, not after delivery.
