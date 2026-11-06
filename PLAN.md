# Halisi: Status & Next Steps (replaces the 2026-09 audit)

The previous version of this file said the merchant dashboard, onboarding and simulator did not exist.
They do. The authoritative status is the task board in [AGENTS.md](AGENTS.md) section 3; deployment steps are in
[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md); the pitch is [docs/PITCH.md](docs/PITCH.md).

## Ready now (verified 2026-11-05)

* Backend: `cd backend && ruff check . && pytest -q` (511 passed, 3 skipped, 3 xfailed).
* Frontend: `cd frontend && npm run typecheck && npm run lint` (0 errors).
* Offline demo: `DEMO_MODE=true` backend, or no backend at all (frontend fixtures).

## Before the finals, in order

1. **Run the schema v2.3 upgrade block on Supabase** (`database/schema.sql`). Trust tiers, verification codes and the watchlist need it. Until then run the demo in `DEMO_MODE`.
2. **Run `npm run build`** in `frontend/` and open the site on a real phone.
3. **Source one statistic or use none** (docs/PITCH.md section 6). Never restore the v1 figures.
4. **Rehearse failover three times** and write the measured times into docs/PITCH.md section 4.
5. **Re-verify the curated real-brand handles** before showing them publicly.
6. Merchant side (TSK-050 Strike Console, TSK-051 onboarding/verification UI) is still only re-themed. Build these only after 1 to 5.

## Not yet proven against real services

Supabase (tested against a fake client), live NVIDIA NIM output (mocked in tests), live Instagram/OpenGraph fetching from Brev, CLIP on the GPU.
