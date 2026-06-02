# TeducAI production go-live checklist

Contexte: application deja deployee sur le VPS OVH et accessible via
`https://teducai.com/`. Cette checklist couvre les etapes 3 a 9 restantes:
stockage fichiers, notifications, securite, monitoring/backups, tests finaux,
conformite et donnees de demarrage.

## 0. Commandes de base

Depuis le dossier applicatif sur le VPS:

```bash
cd /var/www/teducai/education-saas
mkdir -p logs
chmod +x scripts/production/*.sh
source .env.production
python -m alembic current
python -m alembic upgrade head
```

Executer l'audit non destructif:

```bash
bash scripts/production/teducai-prod-audit.sh
```

Verifier le site public:

```bash
bash scripts/production/teducai-smoke-test.sh https://teducai.com
```

## 3. Stockage fichiers reel

Objectif: les documents d'eleves, parents, professeurs et pieces sensibles ne
doivent pas dependre uniquement du disque local du VPS.

Checklist:

- [ ] `FILE_STORAGE_BACKEND=s3` en production, ou `local` temporairement avec
  sauvegarde externe quotidienne.
- [ ] `FILE_STORAGE_BUCKET` configure.
- [ ] `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_REGION`
  configures si S3/MinIO.
- [ ] `SIGNED_URL_EXPIRES_SECONDS` court, recommande `900`.
- [ ] `MAX_UPLOAD_BYTES` adapte aux usages reels.
- [ ] `ALLOWED_UPLOAD_MIME_TYPES` limite aux types necessaires.
- [ ] `CLAMAV_SCAN_COMMAND` configure si uploads ouverts aux parents/eleves.
- [ ] Quotas par etablissement verifies via `storage_quota_mb`.
- [ ] Test upload/download/delete avec un compte admin et un compte parent.

Commandes utiles:

```bash
grep -E "^(FILE_STORAGE_BACKEND|FILE_STORAGE_BUCKET|S3_|SIGNED_URL|MAX_UPLOAD|ALLOWED_UPLOAD|CLAMAV)" .env.production
python -m alembic current
```

## 4. Notifications reelles

Objectif: les notifications doivent partir par un vrai fournisseur, avec
historique et statut.

Checklist:

- [ ] Au moins un fournisseur SMS/email actif: Twilio, Orange, SendGrid,
  Mailgun ou WhatsApp Business.
- [ ] Les secrets fournisseurs sont stockes dans `.env.production` ou un coffre
  de secrets, jamais dans Git.
- [ ] Templates FR/EN/ES/SW verifies.
- [ ] Files de retries testees via les endpoints enterprise.
- [ ] Historique visible dans le portail parent/eleve.
- [ ] Test d'un SMS retard paiement.
- [ ] Test d'un email information ecole.
- [ ] Test d'une notification absence.

Variables principales:

```bash
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM=
ORANGE_SMS_URL=
ORANGE_SMS_TOKEN=
SENDGRID_API_KEY=
SENDGRID_FROM_EMAIL=
MAILGUN_DOMAIN=
MAILGUN_API_KEY=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
```

## 5. Securite production

Objectif: proteger les donnees multi-etablissements, les sessions, les secrets
et les actions sensibles.

Checklist:

- [ ] Revoquer les tokens GitHub partages dans le chat.
- [ ] `APP_ENV=production`.
- [ ] `JWT_SECRET_KEY` long, aleatoire, non partage.
- [ ] `FIELD_ENCRYPTION_KEY` configure et sauvegarde dans un coffre.
- [ ] `CORS_ALLOWED_ORIGINS=https://teducai.com`.
- [ ] Aucun `*` dans `CORS_ALLOWED_ORIGINS`.
- [ ] HTTPS valide via Nginx/Certbot.
- [ ] MFA active pour super admin et admins ecole.
- [ ] Comptes admin nominatifs, pas de compte partage.
- [ ] RBAC teste avec admin, direction, comptable, parent, eleve.
- [ ] `REDIS_URL` configure si plusieurs processus/instances API.
- [ ] Logs sans mots de passe, tokens, secrets fournisseurs.
- [ ] Audit consultable par admin autorise.

Commandes utiles:

```bash
bash scripts/production/teducai-prod-audit.sh
curl -I https://teducai.com
curl -fsS https://teducai.com/api/health || curl -fsS https://teducai.com/health
```

## 6. Monitoring et backups

Objectif: detecter les incidents et pouvoir restaurer rapidement.

Checklist:

- [ ] `/health` supervise toutes les minutes.
- [ ] `/ready` supervise apres chaque deploy.
- [ ] `/metrics` collecte par Prometheus ou script cron.
- [ ] Alertes sur 5xx, latence, disque, RAM, CPU, jobs notifications echoues.
- [ ] Sauvegarde DB automatique quotidienne.
- [ ] Sauvegarde fichiers/documents quotidienne ou S3 versionne.
- [ ] Sauvegardes chiffrees si possible.
- [ ] Retention minimum 30 jours.
- [ ] Test de restauration mensuel.
- [ ] Journal systemd conserve et rotate.

Installer un cron exemple:

```bash
crontab scripts/production/teducai-cron.example
```

Sauvegarde immediate:

```bash
bash scripts/production/teducai-backup-now.sh
```

## 7. Tests finaux

Objectif: valider les parcours critiques reels avant ouverture large.

Checklist minimale:

- [ ] Connexion super admin.
- [ ] Creation ecole.
- [ ] Creation admin ecole.
- [ ] Creation classe/niveau/filiere.
- [ ] Creation eleve + parent.
- [ ] Affectation frais.
- [ ] Paiement partiel.
- [ ] Recu visible portail parent/eleve.
- [ ] Solde restant visible.
- [ ] Paiement total.
- [ ] Facture statut `paid`.
- [ ] Note saisie puis bulletin genere.
- [ ] Attestation scolarite generee meme si impaye.
- [ ] Autres attestations bloquees si impaye.
- [ ] Isolation tenant: l'ecole A ne lit pas les donnees de l'ecole B.
- [ ] RBAC: parent ne voit que ses enfants, eleve seulement son espace.

Commande smoke test public:

```bash
bash scripts/production/teducai-smoke-test.sh https://teducai.com
```

## 8. Conformite

Objectif: RGPD/GDPR et pratiques locales Afrique/Europe/Royaume-Uni.

Checklist:

- [ ] Politique de confidentialite publiee.
- [ ] Conditions d'utilisation publiees.
- [ ] Mentions legales CI/UK/Europe verifiees.
- [ ] Registre consentements actif.
- [ ] Endpoint export donnees personnelles teste.
- [ ] Endpoint anonymisation/suppression teste.
- [ ] Regles de retention configurees.
- [ ] Audit trail consulte par admin autorise.
- [ ] Procedure incident de donnees documentee.

Endpoints utiles:

- `/system/compliance/data-export`
- `/system/compliance/erase-user`
- `/system/compliance/consents`
- `/system/compliance/retention-rules`
- `/system/audit-logs`
- `/system/security-events`

## 9. Donnees de demarrage

Objectif: lancer avec une configuration exploitable par les premieres ecoles.

Checklist:

- [ ] Super admin production cree.
- [ ] MFA super admin active.
- [ ] Plans SaaS Free/Pro/Max configures.
- [ ] Roles standards verifies.
- [ ] Permissions roles sensibles revues.
- [ ] Templates pays/types d'etablissements verifies.
- [ ] Rubriques frais par defaut creees.
- [ ] Annee academique courante creee.
- [ ] Classes/niveaux/filieres de base creees.
- [ ] Comptes pilotes: admin ecole, direction, comptable, professeur, parent, eleve.

## Decision go-live

TeducAI peut passer en production publique lorsque:

- migrations Alembic appliquees;
- backups et restore drill valides;
- HTTPS et secrets valides;
- RBAC et isolation tenant testes;
- notifications reelles testees;
- stockage fichiers sauvegarde ou S3 actif;
- monitoring et alertes actifs;
- parcours critiques valides avec une ecole pilote.
