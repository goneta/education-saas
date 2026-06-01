# Deploiement SaaS

## Variables obligatoires

- `DATABASE_URL`: base PostgreSQL de production.
- `JWT_SECRET_KEY`: secret long, aleatoire, jamais versionne.
- `FIELD_ENCRYPTION_KEY`: cle Fernet pour chiffrer les secrets fournisseurs et champs sensibles au repos.
- `CORS_ALLOWED_ORIGINS`: domaines frontend autorises.
- `APP_ENV=production`.
- `RATE_LIMIT_WINDOW_SECONDS`, `RATE_LIMIT_MAX_REQUESTS`, `AUTH_RATE_LIMIT_MAX_REQUESTS`: limites anti-abus par fenetre.
- `MAX_REQUEST_BODY_BYTES`: taille maximale acceptee pour un corps de requete.

## Migrations

Executer les migrations avant demarrage applicatif:

```bash
python -m alembic upgrade head
```

## Sauvegardes

- Sauvegarde PostgreSQL quotidienne avec retention minimale de 30 jours.
- Test mensuel de restauration sur une base isolee.
- Export separe des fichiers uploades si `FILE_STORAGE_BACKEND=s3`.

## Monitoring

- Endpoint: `/health`.
- Alertes conseillees: erreur DB, latence API, volume 5xx, disque, files de notifications.
- Logs applicatifs a router vers un collecteur centralise avec correlation par `actor_id`, `school_id`, `path`.

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
