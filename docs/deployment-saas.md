# Deploiement SaaS

Pour le VPS OVH deja deployee sur `https://teducai.com/`, utiliser aussi la
checklist operationnelle:

- `docs/teducai-production-go-live.md`
- `scripts/production/teducai-prod-audit.sh`
- `scripts/production/teducai-smoke-test.sh`
- `scripts/production/teducai-backup-now.sh`
- `scripts/production/teducai-restore-drill.sh`
- `scripts/production/teducai-cron.example`

## Variables obligatoires

- `DATABASE_URL`: base PostgreSQL de production.
- `JWT_SECRET_KEY`: secret long, aleatoire, jamais versionne.
- `FIELD_ENCRYPTION_KEY`: cle Fernet pour chiffrer les secrets fournisseurs et champs sensibles au repos.
- `CORS_ALLOWED_ORIGINS`: domaines frontend autorises.
- `APP_ENV=production`.
- `RATE_LIMIT_WINDOW_SECONDS`, `RATE_LIMIT_MAX_REQUESTS`, `AUTH_RATE_LIMIT_MAX_REQUESTS`: limites anti-abus par fenetre.
- `MAX_REQUEST_BODY_BYTES`: taille maximale acceptee pour un corps de requete.
- `FILE_STORAGE_BACKEND`, `FILE_STORAGE_LOCAL_PATH`, `MAX_UPLOAD_BYTES`, `ALLOWED_UPLOAD_MIME_TYPES`: stockage documentaire securise.
- `FILE_STORAGE_BUCKET`, `S3_ENDPOINT_URL`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_REGION`: configuration S3/MinIO.
- `SIGNED_URL_EXPIRES_SECONDS`: duree de validite des URLs signees.
- `CLAMAV_SCAN_COMMAND`: commande antivirus optionnelle pour scanner les fichiers uploades.
- `BACKUP_DIR`: dossier de sortie des sauvegardes applicatives.
- `ENCRYPT_BACKUPS=true`: chiffre les artefacts de sauvegarde avec la cle applicative.
- `REDIS_URL`: active le rate limiting distribue multi-instance.
- `SLOW_REQUEST_MS`: seuil de journalisation des requetes lentes.

## Migrations

Executer les migrations avant demarrage applicatif:

```bash
python -m alembic upgrade head
```

## Reverse proxy et frontend (chaine de requetes)

En production, une requete d'API suit cette chaine :

```
Navigateur (https://teducai.com)
  -> Apache :443  (reverse proxy TLS)
    -> Next.js frontend :3001
      -> reecriture Next  /api/backend/:path*  ->  BACKEND_INTERNAL_URL/:path*
        -> FastAPI (uvicorn/PM2)  ex. http://127.0.0.1:8001
```

Le frontend appelle le backend en **same-origin** via le prefixe
`/api/backend` (`NEXT_PUBLIC_API_URL` reste vide en production). Next reecrit
ce prefixe vers `BACKEND_INTERNAL_URL` (defaut `http://127.0.0.1:8000`).

**Variable critique du frontend (PM2/env du process Next) :**

| Variable | Role | Valeur prod |
| --- | --- | --- |
| `BACKEND_INTERNAL_URL` | cible de la reecriture `/api/backend/*` | doit correspondre au port reel du backend, ex. `http://127.0.0.1:8001` |
| `NEXT_PUBLIC_API_URL` | base API cote navigateur | **vide** en prod (utilise le proxy same-origin `/api/backend`) |

Le defaut `:8000` est pour le dev/e2e ; si le backend tourne sur `:8001`,
`BACKEND_INTERNAL_URL=http://127.0.0.1:8001` **doit** etre exporte dans l'env du
process Next, sinon Next proxifie vers un port ou rien n'ecoute.

Exemple de vhost Apache (proxy tout vers Next, qui reecrit ensuite l'API) :

```apache
ProxyPreserveHost On
ProxyPass        /  http://127.0.0.1:3001/
ProxyPassReverse /  http://127.0.0.1:3001/
```

### Backend Python sous PM2 (interpreteur)

PM2 choisit par defaut l'interpreteur **Node** pour un script sans extension
reconnue. Or `venv/bin/uvicorn` est un script **Python** : lance tel quel, PM2
l'execute avec Node et le process plante en boucle avec
`SyntaxError: Invalid or unexpected token` sur la ligne `# -*- coding: utf-8 -*-`
(la stack montre `node:internal/modules/cjs/loader`). Rien n'ecoute alors sur le
port -> Apache renvoie 503. Il faut imposer l'interpreteur Python du venv.

Ecosystem (`ecosystem.config.js`) :

```js
{
  name: "teducai-backend",
  cwd: "/var/www/html/education-saas",
  script: "./venv/bin/uvicorn",
  interpreter: "./venv/bin/python",   // sinon PM2 utilise Node
  args: "backend.main:app --host 127.0.0.1 --port 8001",
  env: { APP_ENV: "production" },
}
```

Ou en CLI (recree proprement le process) :

```bash
cd /var/www/html/education-saas && source venv/bin/activate
alembic upgrade head
pm2 delete teducai-backend
pm2 start ./venv/bin/python --name teducai-backend --interpreter none \
  --cwd /var/www/html/education-saas \
  -- -m uvicorn backend.main:app --host 127.0.0.1 --port 8001
pm2 save
```

`--interpreter none` execute le binaire directement (`python -m uvicorn`), sans
que PM2 ne tente Node. Chaque backend Python doit pointer sur SON port
(TeducAI = 8001) et le frontend correspondant doit exporter
`BACKEND_INTERNAL_URL=http://127.0.0.1:8001` pour ne pas retomber sur le backend
d'une autre app (defaut `:8000`).

### Diagnostiquer un 503 "Service Unavailable"

Un 503 avec `Server: Apache` et `Content-Type: text/html; charset=iso-8859-1`
est la page d'erreur **d'Apache** (pas de l'application) : l'upstream qu'Apache
proxifie est injoignable. Cote navigateur cela donne
`JSON.parse: unexpected character` car la reponse est du HTML, pas du JSON.

```bash
pm2 list                                   # frontend Next et backend up ?
curl -i http://127.0.0.1:8001/health       # backend joignable sur son port ?
curl -i http://127.0.0.1:3001/fr/login     # frontend Next repond ?
curl -i http://127.0.0.1:3001/api/backend/health   # la reecriture Next atteint le backend ?
sudo apachectl -S                          # vhosts + upstreams
sudo tail -n 50 /var/log/apache2/error.log # mod_proxy logue le port injoignable (AH00957)
```

Causes frequentes : process backend arrete (`pm2 restart`), `BACKEND_INTERNAL_URL`
absent ou pointant sur le mauvais port (`8000` au lieu de `8001`), ou vhost
Apache proxifiant `/api/backend` directement vers un port backend errone.

## Sauvegardes

- Sauvegarde PostgreSQL quotidienne avec retention minimale de 30 jours.
- Test mensuel de restauration sur une base isolee.
- Export separe des fichiers uploades si `FILE_STORAGE_BACKEND=s3`.
- Script de sauvegarde: `python -m backend.scripts.backup_database`.
- Script de restauration: `ALLOW_RESTORE=true BACKUP_FILE=<artifact> python -m backend.scripts.restore_database`.
- Activer `ENCRYPT_BACKUPS=true` et conserver `FIELD_ENCRYPTION_KEY` dans un coffre de secrets.

## Monitoring

- Endpoint: `/health`.
- Endpoint de readiness: `/ready`.
- Endpoint de metriques Prometheus simples: `/metrics`.
- Alertes conseillees: erreur DB, latence API, volume 5xx, disque, files de notifications.
- Logs applicatifs a router vers un collecteur centralise avec correlation par `actor_id`, `school_id`, `path`.
- Les requetes 5xx et lentes creent aussi des `security_events` exploitables par les alertes.

## Secrets

- Ne jamais stocker les secrets dans le depot.
- Utiliser le gestionnaire de secrets de l'hebergeur.
- Rotation des tokens fournisseurs SMS/email/WhatsApp apres incident ou depart operateur.
- Activer une cle `FIELD_ENCRYPTION_KEY` differente par environnement et conserver sa sauvegarde dans un coffre de secrets.

## Securite applicative

- Activer HTTPS/TLS devant l'API et le frontend.
- Bloquer l'acces direct a l'API sans proxy applicatif configure pour les en-tetes de securite.
- Surveiller les evenements `/system/security-events` et les journaux d'audit.
- Conserver les sauvegardes chiffrees et tester la restauration apres chaque changement majeur de schema.

## Stockage fichiers

- Backend recommande: S3 compatible, bucket par environnement.
- Les documents sensibles doivent etre servis via URL signee temporaire.
- Les uploads parent/eleve/prof doivent etre analyses avant publication.
- Les fichiers acceptes sont limites par type MIME, extension, taille et scan antivirus optionnel.
- Les fichiers supprimes sont d'abord marques `deleted` pour garder la tracabilite.
- En backend S3/MinIO, les telechargements passent par des URLs signees temporaires.
- Les quotas de stockage sont controles par etablissement via `storage_quota_mb`.

## CI/CD

- La CI GitHub Actions execute migrations Alembic, compilation backend, tests backend, lint frontend, build frontend et parcours E2E critique.
- Les deploiements production doivent refuser une migration non appliquee et bloquer si `CORS_ALLOWED_ORIGINS=*`.

## Conformite donnees

- Export donnees personnelles: `/system/compliance/data-export`.
- Anonymisation utilisateur: `/system/compliance/erase-user`.
- Registre consentements: `/system/compliance/consents`.
- Regles de retention: `/system/compliance/retention-rules`.
- Les operations de conformite doivent etre journalisees et limitees aux roles disposant des permissions `compliance:export` et `compliance:erase`.
