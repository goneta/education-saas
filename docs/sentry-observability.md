# Sentry : supervision du backend

Le backend FastAPI charge Sentry au démarrage si `SENTRY_DSN` est défini. Sans
DSN, le fonctionnement reste local. Le SDK est épinglé dans
`backend/requirements.txt`. Installer avec `python -m pip install -r
backend/requirements.txt` sur le serveur, puis configurer le DSN dans
`.env.production` ou dans les variables du gestionnaire de processus. Ne jamais
versionner ce fichier ni placer le DSN dans le code source.

Variables prises en charge :

- `SENTRY_DSN` : DSN du projet Sentry (obligatoire pour activer l'envoi).
- `SENTRY_RELEASE` : identifiant de déploiement, par exemple le SHA Git.
- `SENTRY_TRACES_SAMPLE_RATE` : proportion de requêtes tracées, défaut `0.1`.
- `SENTRY_PROFILES_SAMPLE_RATE` : proportion de sessions profilées, défaut `0.01`.

Les taux doivent être compris entre 0 et 1. Les requêtes, adresses IP,
identités, corps, en-têtes, messages de log libres, paramètres SQL et variables
locales ne sont pas exportés. Les traces conservent les noms de routes résolues
par FastAPI, sans URL brute. Les logs structurés WARNING+ ne conservent que
leur sévérité et leur emplacement. L'intégration automatique avec des services
IA reste désactivée. Cette politique privilégie les données d'élèves et les
données financières ; les événements Sentry restent utiles pour repérer la
fonction et la ligne en échec, mais contiennent moins de contexte métier.

Vérification : exécuter `python -m pytest backend/test_sentry_setup.py` puis,
sur un hôte de test où le DSN est configuré, envoyer uniquement le message
contrôlé `teducai.sentry.smoke` et une métrique synthétique. Vérifier leur
présence dans le projet Sentry et l'absence de données personnelles. Ne pas
provoquer de division par zéro dans le service en production. Redémarrer le
processus FastAPI après modification des variables ; en cas de problème,
retirer `SENTRY_DSN` et redémarrer pour désactiver l'envoi.

Vérification locale du 25 septembre 2026 : 716 tests backend réussis. Un
message contrôlé a obtenu un identifiant d'événement Sentry et une métrique
synthétique a été émise ; leur apparition dans l'interface Sentry reste à
confirmer par un opérateur du projet. `pip check` signale trois conflits
préexistants dans l'environnement local (OpenAI Agents/Pydantic,
SSE Starlette/Starlette et FastAPI/AnyIO), indépendants du SDK Sentry.
