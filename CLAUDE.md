# CLAUDE.md — TeducAI working notes

AI‑first, enterprise, multi‑tenant education SaaS. **FastAPI** backend + **Next.js 16
(Turbopack)** frontend. One platform; every module shares auth, RBAC, AI services,
notifications and master data (zero data duplication).

## Conventions (read before editing)

- **DOX discipline**: every source file has a sibling `<file>.md`; each directory an
  `AGENTS.md`. Read them before editing; update the `.md` for every changed file.
- **Tenancy + RBAC**: every query is school‑scoped; writes are role‑gated.
- **Migrations**: Alembic in `alembic/versions/`; run `alembic upgrade head`. Written
  against SQLite (tests) — column‑only FKs (no `ALTER TABLE ADD CONSTRAINT`).
- **Tests**: `pytest backend`. Frontend has **no `node_modules` in the sandbox** —
  verify FE by inspection (`npm run build`/lint/Playwright can't run here).
- **Response schemas are tolerant on read** (email fields are `Optional[str]`, not
  `EmailStr`) so one bad stored value never 500s a list; input schemas stay strict. A
  global `ResponseValidationError` handler logs the exact failing field.
- **Git discipline (standing user instruction)**: every increment ends with DOX +
  CLAUDE.md updated, then `git add -A`, a descriptive commit and `git push origin main`.
  Leave the tree clean.

## Reference data + forms — the platform contract (apply to EVERY new module)

Three shared mechanisms replace per‑page code. Never re‑implement them.

1. **Hierarchical reference lists** — `backend/services/reference_data.py` +
   `routers/reference_data.py` (`/reference-data`), table `reference_items`
   (migration 0055). `school_id IS NULL` = **🌐 global TeducAI** row: created,
   edited and deleted ONLY by the Super Admin, visible to every school,
   **read‑only for schools (403 on any school write)**. `school_id` set =
   **🏫 local** row: managed by that school's admin/direction, invisible to every
   other school. `merged_items()` is the single list forms display (global +
   local, deduped by code). Categories live in the `CATEGORIES` registry —
   **adding a new referential list = one entry**, permissions/merge/management UI
   follow. `school_level` keeps the existing `SchoolLevel` referential as its
   global source (managed on `/dashboard/levels`) — zero duplication.
   Every mutation is audited (`reference.*`). UI: `/dashboard/reference-data`.
2. **Missing‑dependency form gates** — `frontend/components/ui/missing-dependency.tsx`:
   `RequireOptions` (wraps a DB‑fed select: skeleton while loading → explicit
   callout + quick‑create buttons when empty → the field otherwise),
   `MissingDependency` (standalone callout) and `missingRequired(lists)` (disables
   submit while a required list is loaded‑and‑empty). A creation form must NEVER
   render an empty DB‑fed dropdown without an explanation and a way out.
3. **Readable API errors** — `frontend/lib/api-errors.ts` (`parseApiErrorResponse`)
   turns FastAPI `detail` (string | 422 array | object) into a readable message +
   per‑field errors; forms map them with an `API_FIELD_TO_FORM` record and keep the
   values already typed. `[object Object]` must never reach the UI.

**Building a new CRUD module**: register it in `backend/routers/school_life.py`
via `_register_module(...)` (list+search+filters+pagination+detail+CRUD+CSV export,
tenant scoping, role‑gated writes, audit — all provided) and add ONE `ModuleConfig`
consumed by `frontend/components/school-life/module-page.tsx` (list, filters,
dialog, export, print, gates and merged referentials — all provided). Bespoke CRUD
code is a red flag.

## Architecture map (high‑level)

- Core: `auth`, `context` (active org/school/model/year), `system`, `site` (CMS),
  `platform` (departments, feature flags, global search).
- SIS: `students`, `student_lifecycle`, `sis` (guardians, emergency contacts, medical).
- Academic: `education` (classes/subjects/timetable engine/pedagogy), `grades`,
  `attendance`, `academics` (GPA).
- AI: `chat` + `services/ai_agents.py` (41 agents, LLM router), `ai_service`,
  `ai_automation`, `ai_credits`, `ai_learning` (lesson/quiz/exam generators).
- Finance: `finance`, `services/commerce.py`, **centralized Payment Service**
  (`services/payment_service.py` + `routers/payments.py`): Stripe/CinetPay/Djamo/cash,
  idempotent confirmation, signed webhooks.
- Smart Transport: `routers/transport.py` — fleet, drivers, vehicles, routes, bus
  stops (GPS), assignments, GPS positions, boarding attendance, incidents, fuel, AI
  route optimizer, transport→Finance billing.
- Vie scolaire: `routers/school_life.py` (`/school-life/{module}`) — Discipline,
  Examens (réutilise `exam_sessions`), Activités, Santé scolaire (lectures
  restreintes à l'administration), Internat (chambres = `rooms` de facilities);
  un moteur CRUD factorisé + une page frontend générique.
- Référentiels: `services/reference_data.py` + `routers/reference_data.py`
  (`/reference-data`) — listes globales TeducAI + extensions par établissement.
- Comms `communication` (announcements) · HR `hr` (leave approval) · Analytics
  `analytics` (CSV export + AI insights) · Extensibility `extensibility` (webhooks +
  API keys).

## Timetable constraint engine (latest)

- Backend: `services/timetable_constraints.py` (7 rule types), `timetable_config`,
  `timetable_optimizer` (scored candidates), `timetable_simulation`,
  `timetable_substitution`; endpoints under `/education/timetables/*`
  (constraint‑rules, config, holidays, subject‑requirements, optimize, explain,
  simulate, absences, substitutions).
- Frontend: `components/education/timetable-constraints-panel.tsx` renders the full
  constraint UI on the Emploi du temps page (AI optimized generation, grid config,
  weekly hours, holidays, the 7 pedagogical rule types with a dynamic param form,
  always‑enforced structural constraints). Rule types/params MUST mirror the engine.

## Remédiation de l'audit pré-production (AUDIT_2026-08_PRE-PRODUCTION.md)

Lots exécutés dans l'ordre validé : 0 → 1 → 2 → 3 → 4 → 5.

- **Lot 0 — blocage financier : FAIT.** SEC-01 `backend/webhook_auth.py`
  (fail-closed : secret non configuré en production ⇒ 503, jamais un passage
  silencieux ; 403 en comparaison temps-constant sinon) consommé par
  `payments._verify_signature` et `ai_billing._verify_webhook`. SEC-02 les 10
  variables non documentées ajoutées aux 3 `.env*.example` + `require_env` des
  secrets de webhook et contrôle PostgreSQL dans `teducai-prod-audit.sh`.
  CFG-01 `database.is_production()` (source unique) + `validate_database_url()`
  refusent le démarrage en production sans PostgreSQL. Tests
  `test_webhook_auth.py` (7) ; suite complète **317 verts**.

- **Lot 1 — confidentialité : FAIT.** PRIV-01/PRIV-02
  `backend/services/access_scope.py` = LA règle d'autorisation intra-tenant
  (`visible_student_ids` → `None` pour le personnel, son propre profil pour un
  élève, les enfants rattachés pour un parent, **ensemble vide** sinon —
  jamais « tout »). Appliquée dans `school_life` (Discipline/Internat/Santé :
  liste, détail 404, `student_id`, export CSV) et au GPA `academics`. Examens
  et Activités restent des calendriers visibles par tous (sans donnée
  personnelle), écritures administration. SEC-08 `/system/reference-data`
  authentifié et cantonné à l'établissement de l'appelant. SEC-07 recherche
  publique Emploi limitée en débit + journalisée, photo de CV réservée aux
  profils réellement publiés (`is_publicly_listed`). Tests
  `test_access_scope.py` (5) ; suite complète **322 verts**.

- **Lot 2 — authentification : FAIT.** SEC-05 réinitialisation self-service
  (`services/password_reset.py` + `POST /auth/password/forgot|reset`, migration
  0057 `password_reset_tokens`) : jeton stocké **haché**, usage unique, TTL 60
  min, throttling horaire, réponse **toujours générique** (aucune énumération),
  503 explicite si SMTP absent (jamais de faux envoi), reset ⇒ `token_version++`
  (toutes les sessions révoquées) ; pages `/forgot-password` et
  `/reset-password` + lien sur le login (i18n 4 locales). SEC-04 un échec MFA
  alimente désormais le verrouillage (5 essais/15 min) + anti-rejeu TOTP
  (`users.mfa_last_code`). SEC-03 `client_ip()` n'honore `X-Forwarded-For` que
  derrière `TRUSTED_PROXY_IPS` (défaut 127.0.0.1,::1). SEC-06 en-têtes de
  sécurité (CSP, HSTS, X-Frame-Options…) déclarés dans `next.config.ts` pour
  toutes les pages. Tests `test_auth_hardening.py` (6) ; suite **328 verts**.

- **Lot 3 — intégrité des données : FAIT.** DATA-01
  `backend/services/deletion_guard.py` : politique de suppression **explicite**
  et déclarative (`Reference` + maps `CLASS_REFERENCES` / `SUBJECT_REFERENCES` /
  `ASSESSMENT_REFERENCES`). Supprimer une donnée maîtresse encore référencée
  renvoie un **409 nommant chaque bloqueur et son nombre** au lieu d'une 500 FK
  opaque (PostgreSQL) ou d'une cascade ORM destructrice : classe (inscriptions,
  emploi du temps, devoirs, évaluations, examens, activités, frais), matière
  (auparavant **sans aucun garde-fou**), évaluation portant des notes.
  **Convention** : toute nouvelle suppression physique de donnée maîtresse
  déclare ses références ici. DATA-02 `record_usage` verrouille la ligne du
  portefeuille (`with_for_update`) avant de débiter — fin de la perte de mise à
  jour concurrente (découvert de crédits). Tests `test_deletion_guard.py` (4) ;
  suite complète **332 verts**.

## Recent change log (most recent first)

- **Documentation, Aide intégrée & référentiel piloté par valeur**: (1) site
  Docs — deux nouvelles pages EN+FR: `school-life` (les 5 modules: objectif,
  menus, modèles de données, permissions dont la confidentialité Santé,
  référentiels, workflows création/modification/suppression, API) et
  `reference-data` (🌐 global vs 🏫 local, tableau des permissions, mécanisme
  des formulaires intelligents, API, règles pour les développements futurs);
  groupes "School life"/"Vie scolaire" et entrée Admin. (2) **Aide intégrée** —
  sections `reference_data` et `school_life` en 4 locales (pourquoi une liste
  est vide, comment créer la donnée manquante, données globales vs
  établissement, permissions des référentiels, utilisation des 5 modules);
  aide contextuelle câblée (`MODULE_BY_PATH`) sur les nouvelles routes.
  (3) **Cohérence doc↔code** — la doc annonçait sanctions/récompenses/incidents
  pour Discipline alors que le formulaire n'offrait que `sanction_type`:
  ajout générique `FieldSpec.refCategoryBy {field, map}` (la catégorie de
  référence suit la valeur d'un autre champ; toutes les catégories mappées
  préchargées; filtre = union; changer le champ pilote réinitialise le champ
  dépendant) — Discipline mappe désormais sanction/récompense/incident sur
  leurs référentiels respectifs. Suite backend: 310 verts.

- **Modules Vie scolaire (Discipline, Examens, Activités, Santé scolaire,
  Internat) + Transport Externe**: cinq modules production-ready sur UN moteur
  factorisé. **Backend** — migration 0056: tables `discipline_records`,
  `school_activities`, `health_records`, `boarding_records` (school/élève-
  scoped) + `exam_sessions` EXISTANTE étendue colonne-only (subject_id Integer
  simple — SQLite n'ALTER-add pas de colonne contrainte —, durée, salle,
  barème, coefficient, notes; table partagée avec la planification operations,
  zéro duplication) + seeds globaux des 3 nouvelles catégories référentiel
  (`activity_type`, `incident_type`, `health_record_type`).
  `routers/school_life.py` (`/school-life/{slug}`): `_register_module` fournit
  à chaque module la MÊME surface — liste (recherche serveur incl. nom
  d'élève, filtres statut/type/élève, pagination skip-limit avec total exact),
  détail, create/update/delete audités (`school_life.{slug}.*`), export CSV —
  tenant-scoped; écritures SUPER_ADMIN/SCHOOL_ADMIN/DIRECTION; lectures tout
  membre de l'école SAUF `health` (données médicales: lectures restreintes
  aussi). Internat réutilise les `rooms` de facilities comme chambres.
  Tests `test_school_life.py` (3 green, in-memory + dependency overrides).
  **Frontend** — `components/school-life/module-page.tsx`: page CRUD générique
  pilotée par config (colonnes, champs typés text/textarea/date/number/
  checkbox/select/student/class/subject/room/reference) avec gates
  RequireOptions + création rapide, référentiels fusionnés 🌐+🏫, erreurs API
  lisibles, export CSV et impression; les 5 pages ne sont que des configs
  (`/dashboard/discipline`, `/dashboard/education/exams`,
  `/dashboard/activities`, `/dashboard/health`, `/dashboard/boarding-school`).
  **Menus** — Gestion: Discipline/Activités/Santé scolaire/Internat;
  Scolarité: Examens; Smart Transport (intact) + entrée **Transport Externe**
  (`/dashboard/transport/external`): section dédiée aux établissements sans
  flotte interne, point d'entrée TTransportAI (statut honnête + 11 capacités;
  architecture seulement). Un futur module de ce type = 1 appel
  `_register_module` + 1 ModuleConfig. i18n sidebar 4 locales; contenu des
  pages en français (motif classes/timetable) — sweep i18n ultérieur.

- **Gates de dépendances généralisés + section Transport prête pour
  TTransportAI**: (1) le mécanisme MissingDependency/missingRequired couvre
  maintenant AUSSI: Pédagogie (classes requises pour devoir/support),
  Stages (élèves requis + encart entreprises), Présences (classes requises
  pour l'appel), Bibliothèque (prêt: livres disponibles + élèves requis +
  erreurs API lisibles). Personnel: dépendance département OPTIONNELLE (pas
  de gate, comportement correct). Discipline/Examens/Activités/Santé/
  Internat: modules inexistants à ce jour — le mécanisme les couvrira dès
  leur création. (2) **TTransportAI (architecture seulement, RIEN d'intégré)**:
  `services/ttransport_gateway.py` = LA couture unique de la future
  intégration (11 capacités cibles listées; `integration_status()` honnête —
  `connected: False` tant que le client réel n'existe pas; env
  TTRANSPORTAI_API_URL/API_KEY documentées dans .env.example);
  `GET /transport/integration/status`; le hub Transport affiche le panneau
  « Intégration TTransportAI — À venir » avec les capacités cibles, la
  gestion locale restant pleinement fonctionnelle. Contrats pour plus tard:
  webhooks verify-first, paiements transport TOUJOURS via le Payment Service
  central. Tests `test_ttransport_gateway.py` (2 green).

- **Référentiels hiérarchiques (🌐 global + 🏫 local) + gates de dépendances
  génériques**: (1) **Backend** — table générique `ReferenceItem` (migration
  0055; school_id NULL = donnée GLOBALE TeducAI gérée par le Super Admin,
  lecture seule pour les établissements; school_id renseigné = extension LOCALE
  invisible aux autres écoles), `services/reference_data.py` (registre
  `CATEGORIES` : school_level/school_type/fee_type/room_type/building_type/
  leave_type/evaluation_type/document_type/sanction_type/reward_type — une
  nouvelle liste future = 1 entrée; `merged_items` = LA liste fusionnée des
  formulaires, dédupliquée par code; permissions: écoles jamais sur le global
  (403), 409 doublon, tout audité `reference.*`; catégorie school_level =
  référentiel `SchoolLevel` existant en global + ajouts locaux, zéro
  duplication), router `/reference-data`, seeds globaux FR dans la migration.
  Tests `test_reference_data.py` (5 green, in-memory). (2) **Page Système →
  Listes de référence** (`/dashboard/reference-data?category=`): badges
  🌐 Globale TeducAI / 🏫 Établissement, CRUD selon permissions, ajout local
  par les écoles; i18n `referenceData` 4 locales. (3) **Mécanisme générique
  « dépendance manquante »** — `components/ui/missing-dependency.tsx`
  (`MissingDependency` encart + boutons de création rapide, `RequireOptions`
  wrapper de select, `missingRequired` pour bloquer la soumission). Câblé sur :
  modal élève (niveaux fusionnés via /reference-data/school_level), Classes
  (niveau = Select référentiel, plus de texte libre), Salles (gate bâtiment +
  types de salle fusionnés), Emploi du temps (classe/matière/professeur),
  Devoirs (classe/matière), Évaluations (classe/matière/trimestre + erreurs
  API lisibles), Congés (types fusionnés). **À câbler ensuite (même motif, à
  faire au fil des incréments)** : pédagogie, stages, transport, personnel,
  bibliothèque et autres formulaires à selects DB.

- **Gestion des Élèves — liste vide, erreurs lisibles, cascade niveau/classe,
  dépendances**: (1) liste — la tolérance de lecture de `GET /students` couvre
  maintenant les profils épinglés à un modèle d'établissement DÉSACTIVÉ/remplacé
  (traités comme non épinglés via `~sma.in_(SMA actifs de l'école)`; miroir dans
  /diagnostics; `test_students_list_tolerance.py` 2 green, in-memory), et la page
  Élèves appelle `/students/diagnostics` sur liste vide pour afficher les hints
  français (contexte/établissement/modèle/année) ou « aucun élève créé » +
  bouton Ajouter. (2) **`lib/api-errors.ts`** (nouveau, réutilisable) : parse le
  `detail` FastAPI (string | array 422 | objet) → message lisible + erreurs par
  champ; les modals add/edit élève l'utilisent avec un mapping
  `API_FIELD_TO_FORM` (snake_case → état du formulaire), valeurs saisies
  conservées — **plus jamais `[object Object]`** (à généraliser aux autres
  formulaires). (3) cascade — les niveaux du formulaire élève = référentiel
  global `/levels` FUSIONNÉ avec les niveaux distincts des classes réelles du
  contexte (un référentiel vide ne bloque plus); classes filtrées par niveau,
  reset au changement. (4) dépendances manquantes — encarts explicites « aucun
  niveau » / « aucune classe pour ce niveau {level} » avec actions rapides
  (Créer une classe → education/classes, Gérer les niveaux → levels); i18n
  4 locales (`lists.students.*`, `studentForm.*`). Motif à généraliser aux
  autres formulaires de création (professeur, matière, emploi du temps…).

- **CinetPay method-first UX + receipts/refunds (gateway invisible)**: users
  now pick the ACTUAL payment method everywhere — Orange Money / MTN Mobile
  Money / Moov Money / Wave (+ Stripe/Djamo/cash) — and "CinetPay" is never
  displayed as a payment option (checkout, AI-credits purchase dialog,
  subscription settings, fees cashier select, payroll pay dialog, billing
  brands, help copy, 4-locale i18n). Backend: `CINETPAY_NETWORK_CHANNELS`
  maps the chosen method to the checkout channel (orange/mtn/moov →
  MOBILE_MONEY, wave → WALLET, none → CINETPAY_CHANNELS default; the invalid
  `payment_method` init param removed); `GET /payments/providers` returns the
  user-facing `methods` catalog; `SchoolSubscriptionChange` gains
  `mobile_money_network` (also fixed the latent TypeError on the paid-plan
  gateway path — success_url/cancel_url were omitted). School/platform money
  stays strictly separated (SchoolPayment/SCH- → school books via
  apply_school_payment; PlatformPayment/TPL-,SUB- → platform via
  apply_platform_payment; same verify-first webhook). NEW automatic receipts:
  first successful school-payment confirmation generates ONE verifiable
  receipt (`generate_school_payment_receipt`: GeneratedDocument REC- +
  DocumentRegistry QR → /verify/{uuid}, operator-brand method label,
  replay-safe; refs stored in payment.metadata_json). NEW refunds:
  `POST /payments/{reference}/refund` (admin/direction/accountant, NOT
  cashier) → `refund_school_payment` reverses the invoice, revokes the
  receipt, audits + notifies, idempotent (409 for never-successful); the
  money return itself happens at the provider (no checkout-API refund
  endpoint exists). Tests `test_cinetpay.py` now 12 green.

- **AI Multi-Agent Platform (increment 1 — OpenAI Agents SDK foundation)**:
  `services/agent_platform.py` + `routers/agent_platform.py` (`/agents`) on
  `openai-agents` 0.18 (Agent/Runner, handoffs, function tools, streaming).
  Coordinator + Academic + Student-Tutor + Finance agents; handoffs filtered
  by caller role at graph-build time AND RBAC re-checked inside every tool;
  4 tenant-scoped read tools (students/grades/attendance/invoices). Providers
  come from the EXISTING `AIProvider` registry (priority order, decrypt_secret,
  base_url → per-provider AsyncOpenAI client): `stream_conversation` retries
  down the list on any provider failure = automatic multi-provider fallback;
  env OPENAI_API_KEY works with an empty registry; no provider → clear error
  (never faked). Credit-gated via ai_credits; SSE events
  start/delta/tool/handoff/done(+history via to_input_list)/error;
  `GET /agents/capabilities`. Tests `test_agent_platform.py` (4 green).
  **Deploy note:** install `openai-agents` with `--no-deps` next to the pinned
  fastapi 0.104 stack (its transitive mcp/starlette/pydantic pins clash;
  runtime needs openai + pydantic>=2.10,<2.12 + griffe). **Increment 3 (shipped):** agents-as-tools collaboration (specialists doubled as consult_* tools; multi-domain questions answered in ONE combined reply — live-verified) + Library/HR/Transport agents with tenant-scoped tools. **Roadmap (NOT built):** admin/comms/analytics/content/knowledge-base agents, write-action tools,
  role AI dashboards, voice, file/vision inputs, session memory store,
  guardrails, per-model cost routing, provider health dashboard.

- **CinetPay payment gateway — production completion**: no SDK added (the
  PyPI/npm `cinetpay-*` packages are v0.1.x; the existing
  `services/payment_gateway.py` already speaks the checkout REST API v2
  directly — completing it in place kept zero duplication). New:
  `cinetpay_check_transaction` (server-side `/v2/payment/check` verification;
  unreachable → "unknown" = apply nothing) and `verify_cinetpay_token`
  (HMAC-SHA256 x-token per CinetPay field order, CINETPAY_SECRET_KEY);
  channels configurable via `CINETPAY_CHANNELS` (default ALL —
  Orange/MTN/Moov/Wave/cards per merchant account).
  `payment_service.apply_platform_payment` is now the single idempotent
  confirmation path for PlatformPayment (credits + subscription activation),
  shared by the legacy platform webhook (delegated) and the NEW
  CinetPay-native `POST /payments/cinetpay/notify` (public; optional HMAC 403;
  **always re-verifies with the check API before applying** → forgery/replay
  safe; 503 when gateway unreachable so CinetPay retries; SCH-→
  apply_school_payment / TPL-,SUB-→ apply_platform_payment; gateway payload
  kept in metadata_json.gateway_check). `POST /payments/{ref}/refresh`:
  authenticated gateway-backed re-verify (checkout return page polling, payer
  retry, cashier reconciliation). Frontend: `/dashboard/payments/status`
  (?transaction_id= from CinetPay return or ?ref=) with checking/pending
  (7s poll)/success/failure states; checkout success/cancel URLs point there;
  `payStatus` i18n (FR/EN, es/sw→EN). Env (examples updated): CINETPAY_API_KEY,
  CINETPAY_SITE_ID, CINETPAY_SECRET_KEY, CINETPAY_API_URL, CINETPAY_CHECK_URL,
  CINETPAY_CHANNELS, CINETPAY_NOTIFY_URL (API_PASSWORD is the transfer/payout
  API — not used by checkout). Tests `test_cinetpay.py` (8 green) +
  payment_service/gateway suites green. Live-key smoke test on production
  remains a manual step (set NOTIFY_URL + SITE_ID/SECRET_KEY in the panel).

- **Diploma & certificate template module (Scolarité)**: per-school,
  multi-tenant `DocumentTemplate` (migration 0054): kind (diploma/certificate),
  {{placeholder}} title/body, optional uploaded background, extensible
  `fields_config`, one default per (school, kind) — first created auto-defaults.
  `services/document_templates.py`: CRUD/duplicate/set-default; field engine
  resolving {{student_name}}/{{matricule}}/{{school_name}}/{{course}} (current
  class)/{{academic_year}} (current year)/{{graduation_date}}/{{certificate_
  number}}+{{diploma_number}} (auto DIP-/CERT-)/{{director_name}}/{{signature}}/
  {{school_logo}}/{{qr_code}}/{{issue_date}} from REAL data (overrides win,
  unknown override keys substitutable → extensible); reportlab A4-landscape
  renderer — PNG/JPG backgrounds full-page, PDF backgrounds merged via pypdf
  (now in requirements), DOCX stored but rendered with the standard layout
  (never faked). `generate` registers in `DocumentRegistry`
  (document_type=diploma|certificate, spec payload) and stamps the top-right
  authenticity QR → verifiable at the public `/verify/{uuid}` page. Router
  `/document-templates` (list/create/patch/delete, duplicate, default,
  background upload via file_storage, placeholders, watermarked sample preview
  — never registered, generate); RBAC admin/direction, school-scoped, audited.
  Frontend Scolarité page `/dashboard/education/document-templates` (cards,
  placeholder chips, upload, preview, generate panel using
  `/students`→student_profile.id), sidebar entry, `docTemplates` i18n (FR/EN
  full, es/sw→EN), docs page (EN+FR), DOX, tests
  (`test_document_templates.py`, 5 green).

- **Universal document QR authentication + public verification (foundation)**:
  a cross-cutting authenticity layer. New `DocumentRegistry` table (migration
  0053): public `uuid`, `document_type`, type-specific `payload`, SHA-256
  `content_hash`, `status` (valid/revoked), and `source_type`/`source_id`
  (references the origin, zero duplication; unique → idempotent registration).
  `services/document_registry.py`: `register` (idempotent per source), `qr_data`/
  `qr_text` (the JSON encoded in the QR), `render_qr_png` (qrcode+Pillow) +
  `draw_qr_on_canvas` (reportlab), `verify`, `revoke`; verification URL from
  `DOCUMENT_VERIFY_BASE_URL` env (default https://teducai.com) → `/verify/{uuid}`.
  Public **unauthenticated** `GET /verify/{uuid}` (`routers/verify.py`) + a public
  frontend page `/{locale}/verify/{uuid}` (authentic / revoked / not-found + main
  info, inline FR/EN). **Wired first for invoices:** the invoice PDF now stamps a
  top-right QR encoding the registry JSON (School/Invoice Number/Customer/Date/
  Generated By/UUID/verify URL) and prints the verify URL; `attach_registry` in
  `services/billing.py`; the detail/pdf/email endpoints register + commit. Tests
  `test_document_registry.py` (4) + billing (19) green. Docs page (EN+FR) + DOX.
  **Other generators (receipts, report cards, payslips, self-service certs) to be
  connected to the same registry incrementally.**


- **Enterprise Billing & Subscription module (foundation)**: a unified
  **Finance → Billing** page (`/dashboard/finance/billing`) — a Stripe-/OpenAI-
  style dashboard that is a *surface over the EXISTING money infra*, not a new
  money system (zero duplication). Reuses `SchoolSubscription`
  (`/system/subscription/change`), `AIWallet`/`PlatformPayment`/
  `AICreditTransaction` (`/ai_billing`) and `AuditLog`. New config tables only
  (migration 0051, new tables): `BillingPreference`, `BillingTaxProfile`,
  `WalletAutoRecharge`, `BillingPromoCode`, `BillingPromoRedemption`.
  `services/billing.py` + `routers/billing.py` (`/billing`): overview
  aggregation, plan catalog (Starter/Professional/Enterprise/Custom mirroring
  `SUBSCRIPTION_PRICES`), preferences, tax identity, auto-recharge config, promo
  validate/redeem (credits-type codes top up the school wallet + write an
  AICreditTransaction), invoices & transactions **projected** from
  `PlatformPayment`, usage (via `ai_credits.usage_summary`), billing-scoped
  audit, and Super-Admin revenue (MRR/ARR/outstanding/failed/by-country).
  RBAC: manage = admin/direction/accounting; revenue + promo authoring =
  Super-Admin only; every mutation audited (`billing.*`). Frontend page has 11
  tabs (Overview, Subscription, Payment methods, Billing history, Credits,
  Usage, Transactions, Promotions, Preferences, Tax & VAT, Audit) + CSV export;
  `billing` i18n namespace (FR/EN full, es/sw fall back to EN), sidebar Finance →
  Billing, docs page (EN+FR) + help section (4-locale) + DOX + tests
  (`test_billing.py`, 10 green). **Invoice PDF (shipped):** `GET /billing/
  invoices/{id}/pdf` renders a real reportlab PDF (issuer/bill-to/tax-inclusive
  breakdown/totals + verifiable QR); `invoice_detail` + `render_invoice_pdf` in
  `services/billing.py`; the Billing-history "Download PDF" button streams it.
  **Saved payment methods (shipped):** `BillingPaymentMethod` (migration 0052) +
  `/billing/payment-methods` CRUD (add/update/set-default/remove); PCI-safe —
  only brand/last4/expiry (+ optional gateway token) stored, never a PAN/CVV;
  first method auto-default, default-promotion on removal, expiry-state badges;
  the Payment methods tab is a real CRUD (`PaymentMethodsTab`).
  **AI billing assistant (shipped):** `POST /billing/assistant` +
  `billing_assistant`/`_assistant_context` in `services/billing.py` answer
  billing questions grounded STRICTLY in the school's real data (subscription,
  wallet, this-vs-last-month spend, outstanding/failed, recent transactions,
  plan catalog) via `ai_service.generate_response_from_config`, credit-gated;
  Overview-tab `BillingAssistant` panel with suggested-question chips.
  **Live usage charts (shipped):** `GET /billing/usage/timeseries` +
  `usage_timeseries` (per-day credits/tokens/requests/cost/spend, gap-free
  window, top-6 by-module); the Usage tab (`UsageTab`) renders a metric toggle,
  a 7/30/90-day period toggle, a dependency-free inline-SVG `LineChart` trend
  and a by-module bar chart.
  **Invoice e-mail (shipped):** `POST /billing/invoices/{id}/email` renders the
  invoice PDF and sends it as an attachment via `services/email_service.py`
  (provider-agnostic SMTP from env; Gmail/Workspace STARTTLS 587 default;
  `EmailNotConfigured`→503, never faked); recipients default to billing
  `invoice_recipients` + school e-mail; Billing-history "Email" button. SMTP
  secrets live only in the git-ignored `.env` (verified live-send OK).
  **All four former billing roadmap items are now built.**

- **Homework / exercise / correction / evaluation module (foundation)**: a
  full assignments module built on the EXISTING `Assignment` /
  `AssignmentSubmission` tables (extended column-only in migration 0050;
  `workflow_status` is a plain String so no Postgres enum-type change).
  `services/assignments.py` + `routers/assignments.py` (`/assignments`):
  11 work types, manual creation AND AI generation that also produces the
  **corrigé** (answer key: expected answers, explanations, per-question
  points, rubric — split into a student-safe `content` and the `answer_key`);
  **online** (autosave, resume, lock-after-due unless late-penalty) and
  **paper** modes; targeting a class or a student subset; submissions
  (answers + attachments, attempts, late); grading manual AND by AI (AI
  scores vs the answer key and returns comment/errors/strengths/weaknesses/
  advice — always a proposal the teacher confirms/edits); answer-key release
  control (never/after_due/immediate); a gradebook bridge
  (`push-to-gradebook` creates/reuses an Assessment + upserts Grade rows);
  per-assignment stats; notifications on publish/submit/grade to students +
  linked parents. AI calls credit-gated; nothing faked. Teacher page
  `/dashboard/assignments` (create + AI-generate + grading roster with manual/
  AI grade + push-to-gradebook) and student/parent page
  `/dashboard/my-assignments` (to-do/done/graded, online submit, corrected
  copy + corrigé when released); sidebar + 4-locale i18n + help section +
  docs page (EN+FR) + tests. **Roadmap (documented, NOT built):** rich-media
  question editor, paper-scan OCR correction wired to this module (the
  grade-scan OCR engine already exists), plagiarism / AI-answer detection,
  differentiated & variant generation, voice annotations, full analytics
  dashboards.

- **Docs site full French localization**: the public docs body was English-only
  (the language dropdown only swapped the URL locale + chrome, never the content).
  Introduced a locale-aware resolver: `lib/docs/content.ts` (English) is the
  source-of-truth/fallback, `lib/docs/content.fr.ts` holds the full French
  translation of all 26 pages + groups + tab labels + chrome strings, and
  `lib/docs/registry.ts` merges per-locale over English (per-page EN fallback,
  same graceful-fallback pattern as the Help Center). All `components/docs/*`
  now resolve via `getDocPage/getDocGroups/getTabLabel/docsUi`; group `tab`
  fields stay English (identity keys). es/sw fall back to English until their
  `content.<locale>.ts` is added.

- **Automation program (Phase 2, increment by increment)**: (A) **Relances
  impayés** — idempotent runner (`services/fee_reminders.py` + `/automations/
  fee-reminders/run|history`): scans overdue fees, 3 escalation levels (N1
  gentle notif+SMS, N2 firm, N3 urgent + admin escalation), anti-spam cooldown
  + level monotonicity via `FeeReminder` rows, SMS queued to parent phone;
  System → Automatisations UI (thresholds, run-now, summary, history). Safe to
  cron. (B) **Documents libre-service** — `/self-documents` router reusing the
  EXISTING `GeneratedDocument` table (`source_type="self_service"`, no new
  table): students/parents (via `ParentStudentLink`) generate certificat de
  scolarité, attestation and payment receipts themselves; unique verifiable
  references (CERT-/ATT-/REC-…), full payload stored for identical re-display;
  "Mes documents" page (print-ready HTML render, child selector for parents)
  in Student + Parent menus. (C) **Résumé hebdo parents + alertes de seuil** —
  `services/parent_digest.py` + `/automations/parent-digest/run|history`: one
  notification per (parent, child) in the PARENT'S language (UserPreference,
  fr/en/es/sw templates) compiling window grades (avg /20), absences/lates and
  outstanding fees; threshold alerts ride along (`parent.alert.average`,
  `parent.alert.absences`); idempotent per window (NotificationHistory
  lookback). Second card on the Automations page. (D1) **Suivi des absences +
  brief anomalies** — `services/absence_followup.py` (parent message per
  unfollowed ABSENT row, parent-language notif + SMS, once per Attendance via
  NotificationHistory source tracking) and `services/anomaly_digest.py`
  (deterministic staff brief: absence spike vs previous window, unpaid ratio,
  class-size imbalance; one brief per window). Cards 3-4 on the Automations
  page + generic `/automations/notifications/history?event_type=`. (D2)
  **Assistant de rentrée** — `services/rentree.py`: preview (dry-run plan:
  promotions per SchoolLevel sort_order, leavers, fee schedules) then run
  (new current AcademicYear, promotion to the least-filled next-level class,
  leavers archived with history kept + account active, FeeSchedule cloned);
  409 duplicate-year guard; RENTREE_ROLES = admin/direction only (no
  accountant); card 5 on the Automations page. (D3) **Planning de révision +
  rappels de devoirs** — `services/student_planner.py`: on-demand study plan
  from REAL data (class assessments, unsubmitted PUBLISHED assignments, class
  timetable) with spaced revision slots (D-5/D-2/D-1, 30/45/60 min); admin
  runner `homework-reminders/run` nudges non-submitters at D-7/D-3/D-1,
  idempotent per (assignment, student, bucket) via event type
  `homework.reminder.d7|d3|d1`. Student/Parent page `/dashboard/study-plan`
  (+ sidebar entries) and card 6 on the Automations page. (D4) **Remédiation
  IA** — `services/remediation.py`: after an assessment, one personalized
  practice set per student below the threshold (3–5 progressive exercises,
  grounded in score + teacher comment) via `ai_service.
  generate_response_from_config`, AI-credit-gated (`ensure_credits`/
  `record_usage`), delivered as `remediation.assigned` notifications,
  idempotent per (assessment, student); teacher page
  `/dashboard/remediation` (assessments stats table + threshold + expandable
  results). (D5) **Explique ma note** — `services/grade_explainer.py`:
  on-demand AI walk-through of one of the student's own grades (class
  average/best/rank + teacher-comment reading + 2–3 tips, second person, in
  the caller's UI locale), AI-credit-gated on the caller; student/parent page
  `/dashboard/explain-grade`; shared `_student_or_linked_child` resolver in
  routers/automations.py now serves study-plan + explain-grade. (D6)
  **Générateur de séquence** — `services/sequence_builder.py`: a term's full
  lesson sequence in ONE AI call, calibrated on REAL data (sessions = weekly
  Timetable slots × the term's weeks; 422 when the pair has no slots),
  credit-gated, persisted as a `sequence.generated` notification; teacher
  page `/dashboard/sequence-builder` (pair/term selectors + optional topic).
  (D7) **Automations recruteur** — `services/recruiter_agents.py` on top of
  the EXISTING `employment.match_score` engine: saved-search agents (new
  `RecruiterSavedSearch` table, migration 0047; last_run_at watermark with a
  deliberate 1-second overlap because second-resolution DB timestamps vs
  microsecond bound params would skip same-second rows; one aggregate
  EmploymentNotification per run; `run-all` endpoint cron-friendly),
  AI screening questionnaires stored on `JobOffer.screening_questions`, and
  per-candidate AI match reasons grounded strictly in match_score details;
  recruiter page gains the Questions button, "Pourquoi ?" per match and the
  saved-searches panel. (D8) **Automations chercheur d'emploi** —
  `services/jobseeker_agents.py`: `POST /me/cv/refresh` (dossier académique
  réel → CV, mécanique de year-closure exposée à l'élève), gap analysis
  (diff déterministe des compétences/langues/expérience manquantes via
  match_score + conseils IA par item) and AI cover letters grounded
  STRICTLY in the CV's real data (published offers only, credit-gated);
  student emploi page gains "Actualiser mon CV" + per-offer "Analyse
  d'écart"/"Lettre IA". (D9) **Actions parent en un clic** — `POST
  /automations/absence/{id}/justify` (linked-parent-only: ABSENT/LATE →
  EXCUSED avec remarque traçable, l'enseignant enregistreur est notifié
  `absence.justified`, 409 si déjà excusée) ; la cloche de notifications du
  header propose « Justifier l'absence » sur les `absence.followup` non lues
  et « Payer maintenant » (deep-link finance) sur fee.reminder/parent.digest
  (clés app.justifyAbsence/app.payFee, 4-locale). (D10) **Saisie de notes
  par photo (OCR)** — provider decision: OpenAI + Anthropic.
  `ai_service.generate_vision_response` (multimodal via the shared
  OpenAI-SDK clients; Anthropic spec now defaults base_url to its
  OpenAI-compatible /v1, so ANTHROPIC_API_KEY alone activates chat+vision);
  NO local fallback — 503 when no vision provider is reachable, never
  faked. `services/grade_ocr.py`: transcription-only prompt (strict JSON,
  skip unreadable), deterministic roster matching (accent/word-order-
  insensitive difflib, threshold 0.55, confidence shown), NOTHING saved by
  the scan; teacher-confirmed upsert with scale/roster 422 guards;
  credit-gated with an image surcharge. Teacher page
  `/dashboard/grade-scan` (camera capture, review table, unmatched/missing
  lists). (D11) **E-signature (in-house)** — `services/esignature.py` +
  `DocumentSignature` (migration 0048): HMAC-SHA256 keyed from a
  domain-separated derivation of SECRET_KEY over
  document|reference|content-hash|signer|timestamp; SHA-256 content hash
  freezes the document at signing (later mutation ⇒ `tampered`), forged
  signature ⇒ `authentic=False`; one signature per (document, signer), 409 on
  re-sign; student or linked parent sign self-service documents
  (`POST /self-documents/{id}/sign`), signatures ride `/mine` +
  `/verify/{reference}` and print as a verified block with a XXXX-XXXX-XXXX
  code. Integrity/authenticity signature bound to the platform account — not
  an eIDAS-qualified signature. **Phase-2 fully CLOSED (19/19).** AI provider
  order: OpenAI + Anthropic primary; OpenRouter, Manus, Genspark fallback
  (Genspark/Manus serve only once an OpenAI-compatible *_BASE_URL is
  supplied).

- **Production hardening pass (security audit)**: removed the baked-in default
  passwords (AdmissionEnrollmentCreate schema default + frontend pre-filled
  "SecurePass2026!" in sidebar/settings forms); enroll_admission and personnel
  now auto-generate policy-compliant credentials (returned once) and validate
  caller passwords; the fallback-SECRET_KEY refusal also fires when
  .env.production exists (not only APP_ENV=production); AI chat timeout 10s->60s.
  Verified good: argon2 + enforced password policy at all creation sites,
  token-gated bootstrap, CORS wildcard refusal, rate limiting + security headers,
  encrypted provider keys, per-file access control, env files git-ignored.
  Known residual: JWT in localStorage (app-wide), async webhook sender NOT READY.

- **Public partner API + outbound webhooks (live)**: `/api/v1` read-only REST API
  authenticated by tenant API keys (`X-API-Key`, hashed, school-scoped; minted in
  `/extensibility/api-keys`) — /me, /students, /teachers, /classes, /subjects,
  /announcements. `emit_event` is now actually wired: `announcement.published`,
  `leave.decided`, `payslip.paid` queue webhook deliveries; `GET /extensibility/
  deliveries` lists them. New System → API & Integrations page (keys, webhooks,
  deliveries + retry). Docs api-webhooks page documents it; docs language dropdown
  now switches locale; timetable-integration claim corrected (transport pickup
  recalculation = roadmap). Async HTTP delivery worker remains NOT READY.

- **TeducAI Platform Docs (public docs site)**: a Claude-Docs-style documentation
  experience at `/{locale}/docs` (linked from the marketing nav, next to Tarification).
  Sticky header with top tabs, left nav sidebar + search, center content with Copy-page,
  right scroll-spy TOC, and a floating "Ask TeducAI" button; responsive (sidebar drawer
  on mobile). Content is typed data in `lib/docs/content.ts` rendered by `components/docs/*`
  (no MDX build dependency). Feature pages for the AI Timetable Engine, Cash payments &
  AI credits and Smart Transport come from the supplied feature docx; the rest are written
  from the implemented modules.

- **Audit-driven program (ongoing, increment by increment)**: (a) **UI for UI-less
  backends (#1)** — surfaced HR **Congés** (`/hr/leave-requests`: self-service request
  + role-scoped list + admin approve/reject) and **Annonces** (`/communication/
  announcements`: create/list/publish). Still UI-less: analytics, extensibility,
  ai-learning. (b) **Establishment historisation (#3)** — students (`StudentEnrollment`)
  and teachers (`TeacherAssignment`) already historised; filled the **personnel** gap
  by reusing `SchoolMembership` (`/personnel/{id}/assignments` + `/assignments/{id}/end`).
  (c) **Help Center** — context-aware (route→`?section=`); documented levels/facilities/
  personnel/payroll/leave/announcements. (d) **i18n** — Teachers/Students/Subjects lists
  + TeacherListTable via the shared `lists` namespace; payroll/leave/announcements/
  facilities/personnel/transport namespaces. Done: Teacher/Student Add/Edit modals; Finance, Operations and Grades pages now
  localized via tx()/PRODUCT_COPY. Open: other scattered legacy pages may remain; Help content: chrome i18n + locale-aware section content (loc() resolver over {fr,en,es,sw}); the 6 new-module sections translated, ~16 legacy sections still French (graceful fallback).

- **Payroll / Paie system (Finance, #7) — backend foundation**: country-extensible
  calculation engine (`services/payroll.py`), per-employee `SalaryProfile`, and
  `/finance/payroll` router (salary-profiles CRUD, payslip generate with gross→net
  breakdown + itemised lines, approve/pay method-agnostic, self-service `/payslips/me`).
  Built on the existing `PayrollRecord`/`PayrollAdjustment` (extended, nullable) so the
  legacy `/operations` payroll keeps working. Frontend (Finance UI + employee/teacher
  self-service) follows. Part of a broader audit-driven program (UI-for-backend-features,
  Help Center, establishment historisation, list/table uniformity) shipped increment by
  increment.

- **Functional improvements batch (8 modules, shipped increment by increment)**:
  (#3) global Super-Admin `SchoolLevel` referential (`/levels`, delete-if-unused);
  (#5) Buildings & Rooms UI in Gestion (`Building.description`; building PATCH/
  DELETE; rooms with type/capacity); (#6) smart class/room rules — class>room
  capacity guard on timetable entries (409), room-in-use & class-with-students
  delete guards (409), `GET /facilities/rooms/{id}/classes` + `GET /education/
  classes/{id}/students`, Nb Classes / Nb Élèves columns + "Voir" modals; (#1)
  class read-only students modal (scrollable Nom/Âge/Sexe, row→profile); (#4)
  student form level→class cascade; (#7) Personnel scolaire module (`StaffProfile`
  + `/personnel`, auto-creates the User account, roles/department/function/status);
  (#8) role-based sidebars (Teacher/Student/Parent hide admin menus; establishment
  selector already scoped server-side); (#2) i18n — new modules fully localized
  (levels/facilities/personnel/classRoster namespaces, FR/EN/ES/SW parity).
  NOTE on (#2): a full app-wide sweep of all legacy pages remains an open effort;
  only this batch's surfaces are guaranteed hardcoded-text-free.

- **Timetable constraints UI**: surfaced the constraint engine on the timetable page
  (panel above; no backend change). Now also surfaces explainable-AI (/explain), scenario
  simulation (teacher-absent / extra-working-day), energy/travel metrics (derived),
  equipment & rooms, hybrid delivery-mode distribution, and multi-campus panels.
- **Production 500 fixes**: relaxed `UserResponse.email` and `SchoolResponse.email`
  (nested in user/teacher/student lists) to tolerant `Optional[str]`; cart
  `metadata_json` non‑dict normalized; global `ResponseValidationError` handler;
  `Élèves` label; student‑table self‑healing in `DashboardUxEnhancer`; robust e2e
  login locator (ids, not translated text).
- **Goal Forge slices 0–8**: Payment Service hardening; Core Platform (departments,
  feature flags, global search); SIS gaps; GPA; Communication; HR leave; Analytics;
  Extensibility; AI Learning generators. `SPEC.md`/`GOAL.md` hold scope + NOT‑READY
  items (live payments, infra/K8s, native mobile, real‑time GPS, GraphQL/marketplace).
- **Smart Transport** module (promoted out of Operations) + universal `TableFilter`
  rollout + Global Institution Context selector + 41 AI agents.

## NOT READY (need decisions/credentials/infra — never faked)

TTransportAI API integration (architecture + placeholder gateway shipped; the
real client, webhooks and data mapping await the TTransportAI API),
live payment operability (real keys/webhook secrets), WhatsApp/voice/video providers,
real‑time GPS push (MQTT/WebSocket) + facial recognition + native mobile apps,
async webhook sender/GraphQL/marketplace/SDK, Docker/K8s/HA/tracing
and the 100k‑users/300ms load targets. See `SPEC.md` §5.
**Now available:** transactional e-mail via `services/email_service.py` (SMTP from
env; Gmail/Workspace) — used for invoice delivery; other modules can reuse it.
Server-side PDF generation via reportlab is live for invoices.
