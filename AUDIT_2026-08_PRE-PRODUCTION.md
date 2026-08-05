# Audit pré-production TeducAI — août 2026

> **Statut : rapport d'audit uniquement. Aucune correction n'a été implémentée.**
> Cible de mise en production : **début septembre 2026**.
> Périmètre : backend FastAPI, frontend Next.js, base de données, API, sécurité,
> multi-tenant, performance, UX, métier, qualité, déploiement.

---

## 1. Résumé exécutif

### Niveau global de qualité : **bon pour un produit en construction, insuffisant en l'état pour une mise en production**

TeducAI est un produit d'une ampleur inhabituelle (≈ 47 000 lignes de backend, 49 routeurs,
46 services, 162 composants/pages frontend, 56 migrations, 81 fichiers de tests — **310 tests
verts**). La qualité de fond est réelle : hachage argon2, MFA TOTP réellement vérifiée au login,
verrouillage de compte après 5 échecs, refus du wildcard CORS en production, en-têtes de sécurité
et CSP côté API, chiffrement des secrets fournisseurs, journalisation JSON structurée, piste
d'audit, CI GitHub Actions (migrations + compilation + tests), scripts de sauvegarde, de
restauration à blanc, de smoke-test et d'audit de production, discipline documentaire (DOX)
appliquée à chaque fichier.

Cependant, l'audit identifie **4 problèmes critiques** et **11 problèmes élevés** qui exposent la
plateforme à des risques de **fraude financière**, **perte de données**, **fuite de données
d'élèves mineurs** et **indisponibilité** dès les premières semaines d'exploitation réelle.

### Niveau de préparation pour la production : **NON PRÊT — 3 à 4 semaines de remédiation nécessaires**

| Dimension | Évaluation |
|---|---|
| Sécurité applicative | ⚠️ Bonne base, **failles critiques sur les webhooks de paiement** |
| Isolation multi-tenant (inter-établissements) | ✅ Solide et testée |
| Autorisation intra-établissement | ❌ Insuffisante (élèves/parents lisent des données d'autres élèves) |
| Robustesse des données | ❌ Suppressions non maîtrisées, pas de `ondelete` |
| Performance / montée en charge | ⚠️ Index manquants, mono-processus, N+1 |
| Exploitation (ops) | ⚠️ Sauvegardes prêtes, **automatisations métier non planifiées** |
| Fonctionnel métier | ⚠️ Bulletins non imprimables, pas de réinitialisation de mot de passe |
| Qualité / tests | ✅ 310 tests verts, ⚠️ 13 routeurs sans test |

### Les 5 risques principaux

1. **Fraude financière triviale** — les webhooks de paiement historiques n'authentifient
   *rien* quand leur secret n'est pas configuré, et ce secret n'est ni documenté ni vérifié par
   le script d'audit de production. Un tiers anonyme peut créditer des portefeuilles IA,
   activer des abonnements et marquer des factures scolaires payées. *(SEC-01, SEC-02)*
2. **Démarrage silencieux sur SQLite** — si `DATABASE_URL` manque, l'application démarre sur un
   fichier local au lieu de PostgreSQL : données écrites hors sauvegarde, corruption possible,
   découverte tardive. *(CFG-01)*
3. **Confidentialité des mineurs** — dans les modules Vie scolaire, tout compte authentifié de
   l'établissement (y compris un élève ou un parent) peut lire les enregistrements
   disciplinaires de n'importe quel élève par énumération d'identifiants. *(PRIV-01)*
4. **Perte de données à la suppression** — aucune règle `ondelete` n'est définie alors que 38
   suppressions physiques existent : en PostgreSQL, supprimer une donnée référencée provoquera
   soit une erreur 500, soit une cascade silencieuse. *(DATA-01)*
5. **Automatisations jamais déclenchées** — relances d'impayés, digests parents, suivis
   d'absence et rappels de devoirs n'ont aucun ordonnanceur ; le cron d'exemple ne couvre que
   les sauvegardes et les smoke-tests. Les établissements croiront ces fonctions actives. *(OPS-01)*

### Portée et limites de cet audit

**Vérifié par lecture de code et exécution** : structure du dépôt, authentification,
autorisation, isolation multi-tenant, webhooks, référentiels, migrations, configuration,
scripts de production, CI, suite de tests backend (310 verts, exécutée).

**Non vérifiable dans cet environnement** (à faire avant le lancement) :
- audit des dépendances frontend (`npm audit`) et build Next.js — pas de `node_modules` ;
- plans d'exécution SQL réels sur PostgreSQL — pas d'instance disponible ;
- test d'intrusion actif, tests de charge, vérification des paiements en conditions réelles ;
- comportement sous concurrence réelle (les courses décrites sont déduites du code).

---

## 2. Problèmes détectés

Gravité : **C** critique · **E** élevée · **M** moyenne · **F** faible.
Probabilité : probabilité d'occurrence en exploitation réelle.

### 2.1 Sécurité

#### SEC-01 — Webhooks de paiement sans authentification quand le secret n'est pas configuré · **C**
- **Localisation** : `backend/routers/ai_billing.py:109-112` (`_verify_webhook`),
  `backend/routers/payments.py:35-43` (`_verify_signature`), endpoints
  `POST /platform/payments/webhook`, `POST /school/payments/webhook`, `POST /payments/webhook/{provider}`.
- **Description** : le contrôle s'écrit `if secret and provided != secret: 403`. Si la variable
  d'environnement est absente, la condition est fausse et **la requête est acceptée sans aucune
  vérification**. Ces endpoints sont publics (pas de dépendance d'authentification) et appellent
  directement les appliers idempotents qui créditent les portefeuilles, activent les abonnements
  et soldent les factures élèves.
- **Impact métier** : crédits IA gratuits, abonnements activés sans paiement, factures scolaires
  marquées payées → comptabilité fausse, pertes de revenus, litiges avec les familles.
- **Impact technique** : corruption de l'état financier ; réconciliation manuelle nécessaire.
- **Probabilité** : **élevée** (voir SEC-02 : le secret a toutes les chances de ne pas être défini).
- **Recommandation** : basculer en **fail-closed** — refuser (503/403) quand le secret n'est pas
  configuré et `APP_ENV=production` ; à terme, adopter partout la doctrine « verify-first » déjà
  appliquée à CinetPay (revérification côté serveur auprès du prestataire avant tout effet).

#### SEC-02 — Les secrets de webhook ne sont ni documentés ni contrôlés · **C**
- **Localisation** : `.env.example`, `.env.production.example`, `backend/.env.example` (absence de
  `SCHOOL_PAYMENT_WEBHOOK_SECRET`) ; `scripts/production/teducai-prod-audit.sh:33-56`
  (`require_env` couvre APP_ENV, DATABASE_URL, JWT_SECRET_KEY, FIELD_ENCRYPTION_KEY,
  CORS_ALLOWED_ORIGINS, BACKUP_DIR, S3… mais **aucun secret de webhook**).
- **Description** : 10 variables lues par le code ne figurent dans aucun fichier d'exemple, dont
  précisément celle qui conditionne l'authentification des webhooks de paiement.
- **Impact** : transforme SEC-01 d'un risque théorique en quasi-certitude.
- **Probabilité** : **élevée**.
- **Recommandation** : compléter les `.env*.example` (les 10 variables), ajouter les secrets de
  paiement à `require_env` dans le script d'audit, et faire échouer le démarrage en production
  si un secret de webhook manque.

#### SEC-03 — Limitation de débit contournable via `X-Forwarded-For` · **E**
- **Localisation** : `backend/security_middleware.py:38-41`.
- **Description** : la clé de limitation est l'IP lue dans l'en-tête `X-Forwarded-For`, **sans
  liste de proxys de confiance**. Un client qui fait varier cet en-tête obtient un compteur neuf
  à chaque requête : la limite (60 req/min sur `/auth/`) est annulée.
- **Impact** : force brute sur les mots de passe et les codes MFA, déni de service applicatif.
- **Probabilité** : moyenne à élevée (technique connue et automatisée).
- **Recommandation** : ne faire confiance à `X-Forwarded-For` que derrière un proxy déclaré
  (liste blanche d'IP), sinon utiliser l'IP de connexion ; envisager une limitation par compte
  en plus de l'IP.

#### SEC-04 — Les échecs MFA ne verrouillent pas le compte · **E**
- **Localisation** : `backend/routers/auth.py:132-144`.
- **Description** : un mot de passe correct suivi d'un code TOTP erroné lève une 401 **sans**
  incrémenter `failed_login_attempts` ni déclencher le verrouillage. Le second facteur (6
  chiffres, fenêtre de validité ±1) devient brute-forçable, d'autant plus avec SEC-03.
- **Impact** : contournement du second facteur pour les comptes à privilèges.
- **Probabilité** : moyenne.
- **Recommandation** : compter les échecs MFA dans le même compteur de verrouillage, ajouter une
  limitation spécifique et un anti-rejeu du code consommé.

#### SEC-05 — Aucune réinitialisation de mot de passe · **E**
- **Localisation** : `backend/routers/auth.py` (endpoints : register/school, token, me, mfa/*,
  logout — **aucun** « forgot » / « reset »).
- **Description** : un utilisateur qui oublie son mot de passe ne peut pas le réinitialiser
  lui-même ; seule une action d'administration existe.
- **Impact métier** : à la rentrée, des milliers de parents/élèves se connectent pour la première
  fois — le support de l'établissement devient le seul recours ; blocage utilisateur massif.
- **Probabilité** : **certaine**.
- **Recommandation** : flux standard par e-mail (jeton à usage unique, courte durée, invalidation
  des sessions via `token_version`) — le service e-mail SMTP existe déjà.

#### SEC-06 — Frontend sans en-têtes de sécurité ; jeton en `localStorage` · **E**
- **Localisation** : `frontend/next.config.ts` (aucun `headers()`), `frontend/contexts/auth-context.tsx:85,176`.
- **Description** : les en-têtes de sécurité (CSP, X-Frame-Options, HSTS…) ne sont posés que par
  le middleware FastAPI, donc **uniquement sur les réponses d'API** ; les pages HTML servies par
  Next n'en ont aucune. Le JWT est stocké dans `localStorage`, donc exfiltrable par tout script
  injecté.
- **Impact** : en cas de XSS (aucun `dangerouslySetInnerHTML` détecté aujourd'hui, mais le risque
  demeure), vol de session immédiat.
- **Probabilité** : moyenne.
- **Recommandation** : définir les en-têtes dans `next.config.ts` (ou au niveau du reverse proxy),
  et étudier le passage à un cookie `httpOnly`+`SameSite` pour le jeton.

#### SEC-07 — Profils et photos d'élèves accessibles sans authentification · **M**
- **Localisation** : `backend/routers/employment.py:210-229` (`/public-profiles`),
  `:263-269` (`/cv/{cv_id}/photo`).
- **Description** : le marketplace Emploi est public par conception et les CV sont filtrés par
  consentement (`share_enabled`, `looking_for_job`, `visible_in_sector_search`). Mais la
  restriction « recruteur payant » ne s'applique **que si l'appelant est authentifié**
  (`_require_paid_recruiter_if_authenticated`) : un visiteur anonyme obtient jusqu'à 60 profils
  par requête, et les photos sont servies par identifiant séquentiel.
- **Impact** : moissonnage de données de jeunes (souvent mineurs), incitation inversée (l'anonyme
  a plus de droits que le recruteur inscrit).
- **Probabilité** : moyenne.
- **Recommandation** : exiger une authentification recruteur pour la recherche et les photos,
  ou au minimum limiter le débit, paginer avec des identifiants opaques et journaliser les accès.

#### SEC-08 — Référentiels d'un établissement lisibles sans authentification · **M**
- **Localisation** : `backend/routers/system.py:429-440` (`GET /system/reference-data/{category}`,
  paramètre `school_id`, aucune dépendance d'authentification).
- **Impact** : divulgation des listes locales (types de frais, niveaux…) de n'importe quel
  établissement ; fuite d'information organisationnelle mineure mais gratuite pour l'attaquant.
- **Probabilité** : faible à moyenne.
- **Recommandation** : authentifier l'endpoint et le cantonner au contexte de l'appelant (ou le
  supprimer au profit du nouveau routeur, cf. ARCH-01).

#### SEC-09 — Énumération de comptes et rejeu TOTP · **F**
- **Localisation** : `backend/routers/auth.py:99-109` (423 « Account temporarily locked » vs 401),
  `:134` (`totp.verify(..., valid_window=1)` sans mémorisation du code consommé).
- **Impact** : un attaquant distingue les comptes existants ; un code TOTP intercepté reste
  utilisable pendant sa fenêtre.
- **Recommandation** : réponse uniforme sur l'échec d'authentification, stockage du dernier code
  accepté pour interdire le rejeu.

#### SEC-10 — Type MIME d'upload issu du client · **F**
- **Localisation** : `backend/services/file_storage.py:60-67,100-101`.
- **Description** : la liste blanche et l'extension dérivent de `upload.content_type`, fourni par
  le client ; le contenu réel n'est pas inspecté (octets magiques).
- **Impact** : stockage d'un fichier arbitraire sous une extension d'image. Atténué par le fait
  que le téléchargement se fait via des URL signées et un contrôle d'accès par fichier.
- **Recommandation** : vérifier la signature binaire du fichier et forcer
  `Content-Disposition: attachment` au téléchargement.

### 2.2 Multi-tenant et autorisation

#### PRIV-01 — Lectures Vie scolaire ouvertes à tout membre de l'établissement · **C**
- **Localisation** : `backend/routers/school_life.py` (`_read_guard` : `_require_manage`
  n'est appelé que si `restricted_read=True`, activé uniquement pour `health`).
- **Description** : pour **Discipline, Examens, Activités, Internat**, la lecture est autorisée à
  tout utilisateur authentifié rattaché à l'établissement — y compris un **élève** ou un
  **parent**. Les listes acceptent `student_id`, `search` et la pagination : un élève peut
  parcourir les sanctions, incidents et affectations d'internat de tous ses camarades.
- **Impact métier** : violation de la confidentialité de données disciplinaires concernant des
  mineurs ; risque juridique et réputationnel majeur pour l'établissement et pour TeducAI.
- **Impact technique** : aucun ; le correctif est une règle d'autorisation.
- **Probabilité** : élevée (découverte fortuite par un élève curieux, ou via les outils de
  développement du navigateur).
- **Recommandation** : restreindre la lecture au personnel (admin/direction/enseignants selon le
  module), et n'exposer à un élève/parent que ses propres enregistrements (ou ceux de son enfant),
  comme le fait déjà `self_documents.py`.
- **Note de transparence** : ce défaut a été introduit lors de l'incrément « modules Vie
  scolaire » de cette semaine, par choix explicite de « lecture ouverte sauf Santé ». Le
  raisonnement était erroné pour la Discipline et l'Internat.

#### PRIV-02 — Autorisation intra-établissement plus faible qu'inter-établissements · **E**
- **Localisation** : exemple représentatif `backend/routers/academics.py:20-34`
  (`GET /academics/students/{student_id}/gpa` : contrôle d'établissement, **aucun contrôle de
  rôle ni de lien avec l'élève**) ; motif similaire ailleurs.
- **Description** : l'isolation **entre** établissements est solide et testée
  (`test_multi_tenant_security.py`, `test_grades_tenant_isolation.py`, `test_teacher_multi_school.py`).
  À l'intérieur d'un établissement, en revanche, beaucoup d'endpoints se contentent de vérifier
  « même école » : un élève authentifié peut lire la moyenne d'un autre élève par identifiant.
- **Impact** : fuite de données scolaires entre familles.
- **Probabilité** : moyenne.
- **Recommandation** : définir une matrice d'autorisation par module (qui voit quoi : soi-même,
  son enfant, sa classe, son établissement) et l'appliquer via un utilitaire partagé, avec des
  tests dédiés « élève/parent ne voit pas les données d'autrui ».

#### MT-01 — Points positifs confirmés
- Les listes d'élèves, notes, finances, opérations et entreprises sont filtrées par
  établissement et couvertes par des tests d'isolation qui passent.
- Le référentiel hiérarchique applique correctement ses règles : un établissement ne peut ni
  modifier ni supprimer une donnée globale (403), ni voir les données locales d'un autre
  (`test_reference_data.py`, 5 tests verts).
- Le masquage en 404 des accès inter-tenants (au lieu de 403) évite la divulgation d'existence.

### 2.3 Données et intégrité

#### DATA-01 — Suppressions non maîtrisées, aucune règle `ondelete` · **E**
- **Localisation** : `backend/models.py` (**0** occurrence de `ondelete`, 16 `cascade=` ORM,
  458 colonnes de clé étrangère) ; 38 appels `db.delete(...)` dans `backend/routers/*.py`
  (ex. `education.py:333` suppression de classe, `:538` de matière).
- **Description** : le comportement de suppression n'est explicite ni au niveau base (pas de
  `ON DELETE`), ni systématiquement au niveau ORM. En PostgreSQL, supprimer une entité
  référencée lèvera une violation de contrainte (erreur 500 non explicite pour l'utilisateur) ;
  là où une cascade ORM existe, des enregistrements liés disparaîtront silencieusement.
- **Impact métier** : perte de données scolaires ou financières irréversible (seuls 2 modèles
  disposent d'un `deleted_at`), ou blocage inexpliqué de l'utilisateur.
- **Probabilité** : élevée (les administrateurs suppriment classes et matières en fin d'année).
- **Recommandation** : définir explicitement pour chaque relation la politique attendue
  (interdiction avec message métier, suppression logique, ou cascade voulue), généraliser la
  suppression logique sur les entités porteuses d'historique, et tester chaque suppression.

#### DATA-02 — Course concurrente sur la consommation de crédits IA · **M**
- **Localisation** : `backend/services/ai_credits.py:154-175` (`record_usage`,
  `wallet.balance_credits -= credits` **sans** `with_for_update()`), alors que les transferts
  d'allocation verrouillent correctement (`:276`, `:332-333`).
- **Impact** : deux requêtes simultanées lisent le même solde et le décrémentent → découvert de
  crédits, consommation d'IA non facturée.
- **Probabilité** : moyenne (un enseignant lançant plusieurs générations, un portefeuille
  d'établissement partagé).
- **Recommandation** : verrouiller la ligne du portefeuille (`with_for_update`) ou effectuer une
  mise à jour atomique conditionnelle.

#### DATA-03 — Points positifs confirmés
- Les références de paiement sont **uniques en base** (`platform_payments.reference`,
  `school_payments.reference`) : l'idempotence des confirmations dispose d'un garde-fou.
- La confirmation CinetPay revérifie systématiquement le statut auprès du prestataire avant tout
  effet (doctrine « verify-first »), et retourne 503 si le prestataire est injoignable.

### 2.4 Performance et montée en charge

#### PERF-01 — Index manquants sur les colonnes de filtrage multi-tenant · **E**
- **Localisation** : `backend/models.py` — **228** colonnes de clé étrangère sans `index=True`,
  dont **51 colonnes `school_id`** (également `student_id` ×19, `class_id` ×9,
  `academic_year_id` ×7, `created_by_id` ×26).
- **Description** : toutes les requêtes de l'application filtrent par `school_id`. Sans index, le
  coût devient linéaire avec le volume **total** de la plateforme, pas avec celui de
  l'établissement.
- **Impact** : dégradation progressive et généralisée à mesure que des établissements
  s'ajoutent — typiquement invisible en recette, douloureux en production.
- **Probabilité** : élevée.
- **Recommandation** : migration ajoutant les index manquants (en priorité `school_id`,
  `student_id`, `class_id`, `academic_year_id`), puis mesure par `EXPLAIN ANALYZE` sur un jeu de
  données réaliste.

#### PERF-02 — Requêtes en boucle (N+1) · **M**
- **Localisation** : 43 occurrences détectées, concentrées dans `system.py` (10),
  `services/school_model_templates.py` (7), `student_lifecycle.py` (4) ; exemple net
  `education.py:256` (frais chargés élève par élève).
- **Impact** : temps de réponse dégradés sur les listes de classes et les tableaux de bord.
- **Recommandation** : chargement groupé (`selectinload`, agrégations SQL), en commençant par les
  écrans réellement les plus consultés.

#### PERF-03 — Pool de connexions non configuré · **M**
- **Localisation** : `backend/database.py:28-29` (`create_engine` sans `pool_pre_ping`,
  `pool_size`, `max_overflow`, `pool_recycle`).
- **Impact** : après un redémarrage de PostgreSQL ou une coupure de connexions inactives, les
  connexions mortes du pool provoquent des erreurs 500 en rafale jusqu'au redémarrage applicatif.
- **Probabilité** : élevée sur plusieurs mois d'exploitation.
- **Recommandation** : `pool_pre_ping=True` au minimum, plus un dimensionnement explicite.

#### PERF-04 — Backend mono-processus · **M**
- **Localisation** : `ecosystem.config.js` (`uvicorn backend.main:app` sans `--workers`, un seul
  processus PM2).
- **Impact** : un seul cœur sert tous les établissements ; une requête lente (export, génération
  PDF, appel IA synchrone) bloque le traitement des autres.
- **Recommandation** : plusieurs workers (uvicorn/gunicorn) — **prérequis** : externaliser la
  limitation de débit en Redis (le compteur en mémoire devient faux avec plusieurs processus,
  `security_middleware.py:17`).

#### PERF-05 — Journalisation d'incident écrite en base · **M**
- **Localisation** : `backend/observability.py:34-42` (insertion d'un `SecurityEvent` à chaque
  réponse 5xx ou requête lente).
- **Impact** : lorsque la base est le goulot d'étranglement, chaque erreur génère une écriture
  supplémentaire — l'observabilité aggrave l'incident.
- **Recommandation** : échantillonner, écrire de façon asynchrone, ou se limiter aux journaux
  applicatifs pour ces événements.

### 2.5 Architecture et dette technique

#### ARCH-01 — Duplication du système de référentiels · **E**
- **Localisation** : ancien — `backend/models.py:1354-1365` (`ReferenceData`, table
  `reference_data`, portée globale/école identique) + `backend/routers/system.py:397-440` ;
  nouveau — `backend/models.py` (`ReferenceItem`, table `reference_items`) +
  `backend/services/reference_data.py` + `backend/routers/reference_data.py`.
- **Description** : **deux implémentations du même concept** (données globales de plateforme +
  extensions par établissement) coexistent, avec deux tables, deux API et deux modèles de
  permissions. L'ancienne est alimentée lors de l'application d'un modèle d'établissement
  (`system.py:136-142`) et n'a aucun consommateur frontend ; la nouvelle est celle utilisée par
  les formulaires.
- **Impact** : divergence des données de référence, confusion des développeurs, corrections à
  faire deux fois.
- **Probabilité** : certaine (dette déjà présente).
- **Recommandation** : décider d'une cible unique (le nouveau mécanisme), migrer les données
  utiles de `reference_data`, puis supprimer l'ancien modèle et ses endpoints.
- **Note de transparence** : cette duplication a été **introduite lors de l'incrément
  précédent** : le référentiel existant n'avait pas été détecté avant de construire le nouveau.

#### ARCH-02 — Second mécanisme de migration, mort · **F**
- **Localisation** : `backend/migrations.py` (`ensure_runtime_schema`) — défini, **jamais appelé**.
- **Impact** : code mort qui suggère un chemin de migration parallèle à Alembic ; risque qu'un
  développeur le réactive et modifie le schéma hors migration.
- **Recommandation** : supprimer le fichier.

#### ARCH-03 — Fichiers monolithiques · **M**
- **Localisation** : `backend/schemas.py` (3 884 lignes), `backend/models.py` (3 881),
  `backend/routers/system.py` (1 912), `backend/routers/education.py` (1 341).
- **Impact** : conflits de fusion, temps de compréhension, risque de régression lors des
  modifications ; `system.py` mélange configuration, abonnements, utilisateurs et référentiels.
- **Recommandation** : découpage par domaine, à planifier **après** le lancement (refactor à
  risque).

#### ARCH-04 — Dépendances déclarées mais inutilisées · **F**
- **Localisation** : `backend/requirements.txt` — `motor` (MongoDB) et `langchain` ne sont
  importés nulle part ; `docker-compose.yml` démarre un service MongoDB inutilisé.
- **Impact** : surface d'attaque et durée d'installation inutiles, confusion architecturale.
- **Recommandation** : retirer les dépendances et le service Mongo.

### 2.6 Configuration et déploiement

#### CFG-01 — Repli silencieux sur SQLite en production · **C**
- **Localisation** : `backend/database.py:26`
  (`os.getenv("DATABASE_URL", "sqlite:///./education_saas.db")`).
- **Description** : contrairement à `SECRET_KEY` (qui lève une erreur explicite en production,
  `security.py:16-21`), l'absence de `DATABASE_URL` **ne bloque pas le démarrage** : l'application
  sert normalement sur une base SQLite locale.
- **Impact métier** : les données saisies par les établissements atterrissent dans un fichier non
  sauvegardé, invisible pour la restauration ; découverte souvent après plusieurs jours.
- **Impact technique** : corruption probable dès l'usage de plusieurs processus ; migration a
  posteriori douloureuse.
- **Probabilité** : moyenne — mais impact irréversible.
- **Recommandation** : refuser le démarrage si `DATABASE_URL` n'est pas défini ou ne pointe pas
  vers PostgreSQL lorsque `APP_ENV=production`.

#### CFG-02 — Dépendances non épinglées, conflit connu · **E**
- **Localisation** : `backend/requirements.txt` (aucune version épinglée),
  `.github/workflows/ci.yml` (`pip install -r backend/requirements.txt`), note CLAUDE.md :
  `openai-agents` doit être installé `--no-deps` sous peine de conflit avec la pile FastAPI.
- **Impact** : build non reproductible ; l'intégration continue peut valider un jeu de versions
  différent de celui de production ; une publication amont peut casser la production sans aucun
  changement de code.
- **Probabilité** : élevée sur la durée.
- **Recommandation** : geler les versions (`pip freeze` / `pip-tools`), documenter la procédure
  `--no-deps`, et vérifier en CI que l'installation est déterministe.

#### CFG-03 — URL du backend par défaut divergente · **M**
- **Localisation** : `frontend/next.config.ts` (`BACKEND_INTERNAL_URL || 'http://127.0.0.1:8000'`)
  contre `ecosystem.config.js` (backend servi sur **8001**).
- **Impact** : si la variable n'est pas transmise, le frontend interroge un backend qui n'est pas
  le sien (le commentaire du fichier PM2 signale que ce scénario s'est déjà produit).
- **Recommandation** : supprimer la valeur de repli et échouer explicitement si la variable
  manque.

#### CFG-04 — Identifiants faibles et ports exposés dans `docker-compose.yml` · **M**
- **Localisation** : `docker-compose.yml` (`saas_password` en clair, ports 5432 et 27017 publiés).
- **Impact** : fichier destiné au développement, mais son usage tel quel sur un serveur exposerait
  la base à Internet avec un mot de passe trivial.
- **Recommandation** : variables d'environnement, suppression des ports publiés, mention
  explicite « développement uniquement ».

### 2.7 Exploitation

#### OPS-01 — Automatisations métier sans ordonnanceur · **E**
- **Localisation** : `scripts/production/teducai-cron.example` (sauvegarde, smoke-test, audit
  uniquement) ; endpoints `POST /automations/*` non planifiés ; aucune infrastructure de tâches
  (aucun Celery/APScheduler/BackgroundTasks détecté).
- **Impact métier** : relances d'impayés, digests hebdomadaires aux parents, suivis d'absence,
  rappels de devoirs, agents de recherche recruteurs — **rien ne s'exécutera** alors que
  l'interface et la documentation les présentent comme actifs.
- **Probabilité** : certaine si le cron n'est pas complété.
- **Recommandation** : compléter le fichier cron d'exemple, et afficher dans l'interface la date
  de dernière exécution de chaque automatisation (détection immédiate d'un ordonnanceur absent).

#### OPS-02 — Webhooks sortants jamais livrés · **E**
- **Localisation** : `backend/routers/extensibility.py:42-45` (`emit_event` met en file d'attente),
  statut `pending` (`models.py:1182`) ; **aucun processus d'envoi** dans le dépôt.
- **Impact** : les intégrations partenaires promises par la page « API & Intégrations » ne
  fonctionnent pas ; les livraisons s'accumulent en base.
- **Recommandation** : soit implémenter le worker (avec reprises), soit signaler clairement dans
  l'interface que la livraison automatique n'est pas encore active.

#### OPS-03 — Points positifs confirmés
- `scripts/production/` fournit sauvegarde, **restauration à blanc**, smoke-test et audit de
  configuration — rare à ce stade et à conserver.
- CI GitHub Actions : migrations + compilation + suite de tests à chaque `push`/PR sur `main`.

### 2.8 Fonctionnel métier

#### FONC-01 — Bulletins non imprimables · **E**
- **Localisation** : `backend/routers/grades.py:231`
  (`GET /grades/reports/student/{id}/term/{id}` → JSON) ; `reportlab` utilisé pour les factures,
  diplômes/certificats et le registre documentaire, **pas pour les bulletins**.
- **Impact métier** : le bulletin est le document central du trimestre ; sans PDF officiel
  (en-tête, moyennes, rang, appréciations, signature, QR de vérification), l'établissement
  retombe sur son ancien outil.
- **Probabilité** : certaine (première fin de trimestre).
- **Recommandation** : générer le bulletin PDF en réutilisant le moteur de gabarits documentaires
  et le registre d'authenticité déjà en place.

#### FONC-02 — Absence de réinitialisation de mot de passe
Voir **SEC-05** (classé en sécurité, impact fonctionnel majeur).

#### FONC-03 — Modules récents peu couverts fonctionnellement · **M**
- **Description** : les modules Vie scolaire livrés cette semaine offrent le socle (CRUD,
  recherche, filtres, export CSV, impression) mais pas encore : liaison Discipline → notification
  aux parents, Activités → facturation de la participation, Internat → présence/nuitées,
  Examens → génération des convocations et report des notes vers le carnet.
- **Impact** : usage partiel, ressaisie dans d'autres outils.
- **Recommandation** : à planifier après le lancement, par ordre de valeur.

#### FONC-04 — Export documentaire limité au CSV · **F**
- **Description** : l'exigence exprimée était « PDF, Excel, CSV » ; seuls le CSV et l'impression
  navigateur sont disponibles sur les nouveaux modules (`openpyxl` est déjà présent et utilisé
  ailleurs).
- **Recommandation** : ajouter l'export Excel via `openpyxl` et le PDF via `reportlab`.

### 2.9 Qualité et expérience utilisateur

#### QUAL-01 — Routeurs sans tests dédiés · **M**
- **Localisation** : aucun fichier de test correspondant pour `ai_billing` (achat de crédits,
  webhooks), `files` (contrôle d'accès aux fichiers), `library`, `internships`, `operations`,
  `enterprise`, `pedagogy`, `chat`, `dashboard`, `verify`, `automations`, `ai_automation`.
  *(Les paiements sont, eux, couverts par `test_payment_service.py` et `test_cinetpay.py`.)*
- **Impact** : les chemins financiers et de contrôle d'accès les moins testés sont précisément
  ceux dont l'échec coûte le plus cher.
- **Recommandation** : prioriser `ai_billing` et `files`.

#### UX-01 — Session de 30 minutes sans renouvellement · **M**
- **Localisation** : `backend/security.py:23` (`ACCESS_TOKEN_EXPIRE_MINUTES = 30`), aucun
  mécanisme de rafraîchissement côté frontend.
- **Impact** : déconnexion en pleine saisie (bulletin, dossier élève) avec perte du travail non
  enregistré — irritant majeur pour un usage quotidien.
- **Recommandation** : jeton de rafraîchissement, ou prolongation glissante, et sauvegarde locale
  des formulaires longs.

#### UX-02 — La déconnexion invalide toutes les sessions · **F**
- **Localisation** : `backend/routers/auth.py:259` (incrément de `token_version` au logout).
- **Impact** : se déconnecter du téléphone déconnecte l'ordinateur ; comportement inattendu.
- **Recommandation** : distinguer « déconnexion de cet appareil » et « déconnexion partout ».

#### QUAL-02 — Incohérence de durée de jeton par défaut · **F**
- **Localisation** : `backend/security.py:49-54` (repli à 15 minutes) contre
  `ACCESS_TOKEN_EXPIRE_MINUTES = 30` utilisé à l'émission.
- **Recommandation** : une seule source de vérité.

#### QUAL-03 — Internationalisation partielle · **F**
- **Description** : les libellés de menu sont traduits en 4 langues, mais le contenu de plusieurs
  pages (Vie scolaire, Classes, Emploi du temps) est en français en dur.
- **Recommandation** : campagne i18n après le lancement.

#### QUAL-04 — Variables d'environnement non documentées · **F**
- **Localisation** : 10 variables lues sans figurer dans les fichiers d'exemple
  (`ALLOW_RESTORE`, `AWS_*`, `BACKUP_FILE`, `OPENAI_DEFAULT_MODEL`, `RATE_LIMIT_ENABLED`,
  `SCHOOL_PAYMENT_WEBHOOK_SECRET`, `SUPER_ADMIN_BOOTSTRAP_TOKEN`, `TEDUCAI_SUPER_ADMIN_PASSWORD`).
- **Recommandation** : compléter (voir SEC-02 pour l'urgence sur le secret de webhook).

---

## 3. Classement des problèmes

| Gravité | Identifiants | Total |
|---|---|---|
| **Critique** | SEC-01, SEC-02, PRIV-01, CFG-01 | **4** |
| **Élevée** | SEC-03, SEC-04, SEC-05, SEC-06, PRIV-02, DATA-01, PERF-01, ARCH-01, CFG-02, OPS-01, OPS-02, FONC-01 | **12** |
| **Moyenne** | SEC-07, SEC-08, DATA-02, PERF-02, PERF-03, PERF-04, PERF-05, ARCH-03, CFG-03, CFG-04, FONC-03, QUAL-01, UX-01 | **13** |
| **Faible** | SEC-09, SEC-10, ARCH-02, ARCH-04, FONC-04, UX-02, QUAL-02, QUAL-03, QUAL-04 | **9** |
| | | **38** |

---

## 4. Plan de remédiation

Principe directeur : **corriger d'abord ce qui peut faire perdre de l'argent, des données ou la
confidentialité ; ensuite ce qui bloque l'usage quotidien ; enfin la dette**.
Les lots sont ordonnés pour limiter les régressions : la sécurité et la configuration ne touchent
presque pas au code métier, les index sont additifs, les changements d'autorisation viennent avec
leurs tests, et les refactors structurels sont volontairement repoussés **après** le lancement.

### Lot 0 — Blocage financier immédiat (avant tout déploiement) · effort **faible**
| # | Problème | Action | Effort |
|---|---|---|---|
| 0.1 | SEC-01 | Rendre les webhooks *fail-closed* (refus si secret non configuré en production) | Faible |
| 0.2 | SEC-02 | Documenter les 10 variables manquantes ; ajouter les secrets de paiement à `require_env` | Faible |
| 0.3 | CFG-01 | Refuser le démarrage en production si `DATABASE_URL` n'est pas un PostgreSQL | Faible |
> Sans dépendance. Réalisable en une journée. **Condition d'entrée pour tout le reste.**

### Lot 1 — Confidentialité et autorisation · effort **moyen**
| # | Problème | Action | Effort | Dépend de |
|---|---|---|---|---|
| 1.1 | PRIV-01 | Restreindre les lectures Vie scolaire (personnel) ; élève/parent limités à leurs propres données | Moyen | — |
| 1.2 | PRIV-02 | Matrice d'autorisation par module + utilitaire partagé + tests « ne voit pas les données d'autrui » | Moyen | 1.1 |
| 1.3 | SEC-07, SEC-08 | Authentifier les endpoints publics Emploi (ou limiter/paginer) et `/system/reference-data` | Faible | — |
> 1.2 généralise le motif introduit en 1.1 : les faire dans cet ordre évite deux conventions.

### Lot 2 — Authentification et exposition · effort **moyen**
| # | Problème | Action | Effort | Dépend de |
|---|---|---|---|---|
| 2.1 | SEC-05 | Flux de réinitialisation de mot de passe par e-mail (service SMTP déjà présent) | Moyen | — |
| 2.2 | SEC-03 | Limitation de débit fondée sur un proxy de confiance | Faible | — |
| 2.3 | SEC-04 | Échecs MFA comptabilisés dans le verrouillage + anti-rejeu TOTP | Faible | 2.2 |
| 2.4 | SEC-06 | En-têtes de sécurité côté Next.js (CSP, HSTS, X-Frame-Options) | Faible | — |
> 2.1 est le plus gros poste du lot mais conditionne l'exploitabilité dès la rentrée.

### Lot 3 — Intégrité des données · effort **élevé**
| # | Problème | Action | Effort | Dépend de |
|---|---|---|---|---|
| 3.1 | DATA-01 | Politique de suppression explicite par relation (interdiction motivée / logique / cascade voulue) + tests | Élevé | — |
| 3.2 | DATA-02 | Verrouillage de ligne sur la consommation de crédits | Faible | — |
> 3.1 est le lot le plus risqué : le traiter **avant** la mise en production mais **après** les
> lots 0–2, avec une migration dédiée et une revue relation par relation.

### Lot 4 — Exploitabilité au quotidien · effort **moyen**
| # | Problème | Action | Effort | Dépend de |
|---|---|---|---|---|
| 4.1 | OPS-01 | Compléter le cron des automatisations + indicateur « dernière exécution » dans l'UI | Faible | — |
| 4.2 | FONC-01 | Bulletin PDF (gabarits + registre d'authenticité existants) | Moyen | — |
| 4.3 | PERF-01 | Migration d'ajout des index (`school_id` en priorité) | Moyen | Lot 0.3 |
| 4.4 | PERF-03 | `pool_pre_ping` et dimensionnement du pool | Faible | — |
| 4.5 | OPS-02 | Worker de livraison des webhooks **ou** mention explicite « non actif » dans l'UI | Moyen | — |
> 4.3 doit être mesuré sur PostgreSQL (`EXPLAIN ANALYZE`), donc après la garantie 0.3.

### Lot 5 — Durcissement avant lancement · effort **faible à moyen**
| # | Problème | Action | Effort |
|---|---|---|---|
| 5.1 | CFG-02 | Épingler les versions et vérifier l'installation déterministe en CI | Faible |
| 5.2 | CFG-03, CFG-04 | Supprimer les valeurs de repli ambiguës ; assainir `docker-compose.yml` | Faible |
| 5.3 | QUAL-01 | Tests sur `ai_billing` et `files` | Moyen |
| 5.4 | UX-01 | Rafraîchissement de session (ou prolongation glissante) | Moyen |
| 5.5 | — | **Test de charge** et **répétition de restauration** sur données réalistes | Moyen |

### Après le lancement (planifiable)
| Problème | Action | Effort |
|---|---|---|
| ARCH-01 | Unifier les référentiels : migrer `reference_data` vers `reference_items`, supprimer l'ancien | Moyen |
| PERF-04 | Plusieurs workers **après** externalisation Redis de la limitation de débit | Moyen |
| PERF-02, PERF-05 | Suppression des N+1 mesurés ; échantillonnage de l'observabilité | Moyen |
| ARCH-02, ARCH-04 | Supprimer le code mort et les dépendances inutilisées | Faible |
| ARCH-03 | Découper `models.py`, `schemas.py`, `system.py` | Élevé |
| FONC-03, FONC-04 | Compléter les modules Vie scolaire ; exports Excel/PDF | Moyen |
| SEC-09, SEC-10 | Réponses uniformes, anti-rejeu, vérification des octets magiques | Faible |
| UX-02, QUAL-02/03/04 | Confort et cohérence | Faible |

### Chemin critique proposé

```
Lot 0 (1 j)  →  Lot 1 (3-4 j)  →  Lot 2 (4-5 j)  →  Lot 3 (5-6 j)  →  Lot 4 (4-5 j)  →  Lot 5 (3-4 j)
                                                                                  ↘ test de charge + restauration
```
Soit environ **3 à 4 semaines** pour une personne à temps plein, hors imprévus — compatible avec
une mise en production début septembre 2026 si le chantier démarre sans délai.

### Critères de « Go » pour la production

1. Lots 0 à 4 terminés, chacun couvert par des tests automatisés.
2. Suite complète verte en CI **avec versions épinglées**.
3. `teducai-prod-audit.sh` sans aucun `[FAIL]`, secrets de paiement inclus.
4. Restauration de sauvegarde répétée avec succès sur un environnement vierge.
5. Un paiement réel de bout en bout par opérateur mobile money (Orange, MTN, Moov, Wave).
6. Test de charge représentatif (une journée de rentrée : connexions massives, appel,
   consultation de notes) sans dégradation au-delà des objectifs.

---

## 5. Ce qui fonctionne bien (à préserver)

- **Isolation inter-établissements** solide et réellement testée.
- **Doctrine de paiement CinetPay** exemplaire : vérification côté serveur avant tout effet,
  idempotence garantie en base, 503 plutôt qu'une supposition.
- **Sécurité des comptes** : argon2, politique de mot de passe, verrouillage, MFA vérifiée,
  chiffrement des secrets fournisseurs, refus du wildcard CORS.
- **Outillage de production** : sauvegarde, restauration à blanc, smoke-test, audit de
  configuration, CI complète.
- **Mécanismes transverses récents** : référentiels globaux/locaux, gardes de dépendances des
  formulaires, erreurs API lisibles, moteur CRUD factorisé — ils réduisent réellement la
  duplication et doivent rester la convention.
- **Documentation** : DOX par fichier, CLAUDE.md, site de documentation et aide intégrée à jour.

---

*Rapport établi le 5 août 2026 par lecture exhaustive du dépôt et exécution de la suite de tests
backend (310 tests, 0 échec). Aucune modification fonctionnelle n'a été apportée au code dans le
cadre de cet audit.*
