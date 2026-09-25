# Sentry setup

- Source : `backend/sentry_setup.py`, appelée avant la création de FastAPI.
- Sans `SENTRY_DSN`, aucune initialisation ni transmission. Le DSN provient de l'environnement racine/du processus ; aucune valeur réelle n'est versionnée.
- `sentry-sdk==2.70.0` : intégrations explicites FastAPI et logging. Auto-intégrations désactivées pour éviter l'envoi de prompts IA ou d'autres contenus métiers.
- Erreurs : requêtes, identités, tags, contexte, paramètres locaux, messages libres et données des breadcrumbs sont supprimés. Les traces retirent descriptions et paramètres des spans ; seuls les noms de routes FastAPI résolues sont conservés, jamais une URL utilisateur brute. Les logs WARNING+ gardent uniquement sévérité et emplacement du code.
- Valeurs par défaut : 10 % de traces et 1 % de sessions profilées ; ajuster par variables d'environnement entre 0 et 1. Aucun profilage manuel au chargement des modules.
- Vérification : `python -m pytest backend/test_sentry_setup.py`, puis un message/métrique synthétiques contrôlés sur l'hôte choisi.
