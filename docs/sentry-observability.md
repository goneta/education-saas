# Sentry : supervision FastAPI et Next.js

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

## Frontend Next.js

Le frontend utilise `@sentry/nextjs` 11.0.0. `instrumentation-client.ts`
initialise le navigateur ; `instrumentation.ts` charge les configurations Node et
Edge et capture les erreurs de requête ; `app/global-error.tsx` capture les
erreurs de rendu racine. `next.config.ts` compose `withNextIntl` avec
`withSentryConfig`. Sans DSN, l'envoi reste désactivé. La CSP n'autorise la
connexion externe que vers l'origine du DSN public défini au build.

Pour un déploiement, définir dans l'environnement **du build Next.js et du
processus PM2** :

- `NEXT_PUBLIC_SENTRY_DSN` : DSN public du projet frontend, inclus dans le bundle
  navigateur. Il peut être identique à celui du backend, mais deux projets
  distincts facilitent le triage. Ne pas mettre de token d'authentification ici.
- `SENTRY_DSN` : DSN du runtime Node/Edge ; si absent, le DSN public est repris.
- `SENTRY_RELEASE` et `NEXT_PUBLIC_SENTRY_RELEASE` : même identifiant de release,
  idéalement le SHA Git ; la valeur publique doit exister au build.
- `APP_ENV` et `NEXT_PUBLIC_SENTRY_ENVIRONMENT` : environnement de déploiement.
- `SENTRY_ORG`, `SENTRY_PROJECT`, `SENTRY_AUTH_TOKEN` : nécessaires **au build**
  pour envoyer les source maps privées. Sans les trois, l'upload est désactivé ;
  les erreurs remontent, mais les traces de pile minifiées peuvent être moins
  lisibles. Ne jamais exposer `SENTRY_AUTH_TOKEN` au navigateur ou à Git.

Exemple sur un hôte PM2 : placer ces valeurs dans `frontend/.env.production.local`
(ignoré par Git), exécuter `npm ci && npm run build`, puis redémarrer le
processus frontend. Conserver le même identifiant de release pendant ces étapes.
La configuration CSP est figée au build : un changement de DSN nécessite un
nouveau build, pas seulement un redémarrage. Vérifier l'upload des source maps
dans le projet Sentry et la lisibilité d'une pile en production.

Par défaut, 10 % des traces sont échantillonnées. Les corps, en-têtes, cookies,
paramètres d'URL, identités, variables locales, contexte source, messages
libres, valeurs d'exception et attributs de spans sont supprimés. Seuls le type
d'erreur, les positions de pile et les noms de route *modèle* sont conservés.
Replay, logs et profilage navigateur restent désactivés pour protéger les
données des élèves. Cette réduction limite le diagnostic métier ; elle est
volontaire.

Vérification locale : `npm ci`, `npx eslint` sur les fichiers de configuration,
`npm run build`, puis provoquer une erreur contrôlée dans l'application en cours
d'exécution et contrôler la réception dans Sentry. Une réponse HTTP 200 du site
ne prouve pas à elle seule l'ingestion. Ne laisser aucun déclencheur de test en
production. Si Sentry est indisponible, retirer les DSN du frontend et rebâtir ;
l'application continue sans télémétrie. Les vulnérabilités npm signalées par
`npm audit` doivent être qualifiées séparément avant la mise en production.

Vérification locale du 26 septembre 2026 : lint ciblé et build Next.js réussis.
Une route de test temporaire a produit une erreur HTTP 500 ; un second appel
dans le processus instrumenté a confirmé `initialized=true`, la création d'un
identifiant d'événement et `flush=true`. La route a été supprimée. La présence
de l'événement dans l'interface Sentry n'a pas pu être confirmée sans accès au
projet. Sans jeton d'upload au build, les source maps de production restent à
vérifier. `npm audit --omit=dev` signale huit vulnérabilités de production,
dont une critique dans Next.js 16.0.8 ; ce risque préexistant doit être traité
séparément avant le lancement.
