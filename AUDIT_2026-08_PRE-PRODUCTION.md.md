# AUDIT_2026-08_PRE-PRODUCTION.md
## Source File
- `AUDIT_2026-08_PRE-PRODUCTION.md`
## Purpose
- Rapport d'audit pré-production (août 2026) : 38 problèmes identifiés par lecture exhaustive du
  dépôt et exécution de la suite backend — 4 critiques (webhooks de paiement fail-open + secrets
  non documentés/non vérifiés, lectures Vie scolaire ouvertes aux élèves/parents, repli silencieux
  sur SQLite), 12 élevés, 13 moyens, 9 faibles — avec pour chacun localisation, gravité, impacts
  métier/technique, probabilité et recommandation ; plus un plan de remédiation en 6 lots ordonnés
  (dépendances, effort, avant/après lancement) et des critères de Go production.
## Local Contracts
- Document d'audit : AUCUNE correction n'a été appliquée. Toute remédiation doit être validée puis
  menée lot par lot ; mettre à jour le statut des problèmes ici au fur et à mesure.
## Verification
- Constats vérifiés par inspection du code (références fichier:ligne) et `pytest backend`
  (310 verts). Non vérifiés dans le bac à sable : `npm audit`/build frontend, EXPLAIN PostgreSQL,
  test d'intrusion, tests de charge.
