# Directbot — Impilo Drilling Long-tail Directory Bot

Directbot audits and prioritises small/local business directories for **Impilo Drilling**, focusing first on the KwaZulu-Natal South Coast and then wider South Africa.

## Business profile
The canonical listing data lives in `impilo.yaml`. Keep this accurate: consistent NAP/business details are more valuable than creating inconsistent listings.

## What it does
- Audits seeded directory submission pages.
- Detects free-listing and submission signals.
- Flags CAPTCHA/login/review requirements rather than bypassing them.
- Produces a CSV audit and JSON state in `output/`.
- Runs automatically every Monday and Thursday via GitHub Actions.
- Can also be run manually with **Actions → Directbot Directory Audit → Run workflow**.

## Target strategy
Priority geography: Port Shepstone, Shelly Beach, Margate, Uvongo, Ramsgate, Hibberdene, Scottburgh, Port Edward, Ugu District, KZN South Coast, KwaZulu-Natal, South Africa.

Priority categories: borehole drilling, drilling contractors, water services, pump installation, water tanks, water purification, construction/home improvement.

## Safety / quality rules
Directbot must not bypass CAPTCHA, anti-bot protections, email verification or account security. It should not create duplicates or submit paid listings without approval. Automated submissions should respect each directory's terms and submission flow.

## Next phase
Add Playwright adapters for individual directories that explicitly allow self-service listings, plus duplicate checking, approval-email tracking, screenshot evidence, and a persistent submission ledger.
