# Changelog

## 1.0.1

- Live terminal hosted on Modal (`modal_app.py`: one container, scaled to zero between visitors, run
  registry on a persistent volume) with `.github/workflows/deploy-modal.yml` redeploying on push. The
  Hugging Face Space route is kept as a Docker host option only: Docker Spaces now require a PRO
  subscription. `sync-to-hf.yml` removed; README front matter removed.

## 1.0.0

First release of the Policy Scenario Lab terminal.

- Agent based synthetic AI economy (eight firm archetypes, regulator, public trust, four media
  agents, market) stepped monthly on common random numbers with per path streams, so smaller
  re simulations pair with the main run.
- Library of fifteen regulatory instruments as bounded JSON documents; custom instruments, firm
  templates and assumption overrides from the terminal.
- Welfare accounting (harm avoided, consumer surplus, output, resident producer surplus, compliance,
  enforcement, leakage, relocation, labour) with transfers excluded; industry value change per firm
  and sector; safety forecast; numeric news forecast and a composed wire; decision metrics with a
  bootstrap (P(best), winner stability, decision gap, P(inversion)); constraints read from the question.
- Assurance: tornado over every declared value judgement (reweighted or re simulated and paired),
  structural variants, red team gaming strategies whose honest values equal the headline figures,
  analogue event study on uploaded series.
- Governance carried from the Herding Scenario Lab: hash chained HMAC signed ledger, register of
  regulated persons with mandatory functions and four eyes, dev mode (Developer1, Developer2), two
  gates with refusal and reasons, emergency stop, an independent critic that recomputes every figure
  and vets every number in the briefing (unit suffixes included), evidence pack, ATRS record,
  security posture, quarantine for uploads that refuses personal data.
- Terminal: fifteen function codes, keyboard and footer navigation from any page, resizable and
  scrollable panels, live news wire and equity panel, charts drawn client side from specifications,
  grounded oracle, run registry, New run.
