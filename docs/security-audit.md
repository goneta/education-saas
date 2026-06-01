# Audit de securite applicatif

Date: 2026-06-01

## Synthese

L'audit a couvert le backend FastAPI, le frontend Next.js, les API, l'authentification, le RBAC existant, les integrations de notification, les journaux, les tests et la configuration de deploiement. Les corrections implementees renforcent les controles OWASP Top 10 les plus critiques: authentification, abus d'API, exposition de secrets, journalisation, controle des sessions et durcissement HTTP.

## Vulnerabilites corrigees

| Criticite | Zone | Risque identifie | Correction apportee |
| --- | --- | --- | --- |
| Elevee | Authentification | Absence de MFA, verrouillage faible contre brute force et jetons non revocables | MFA TOTP, verrouillage apres echecs, evenements de securite, version de jeton et endpoint logout revocatoire |
| Elevee | Secrets fournisseurs | Secrets SMS/email/WhatsApp stockes et reutilises en clair | Chiffrement applicatif au repos via `FIELD_ENCRYPTION_KEY`, dechiffrement uniquement au moment de l'appel fournisseur, masquage dans les reponses |
| Elevee | API | Pas de limitation globale des requetes ni de taille de corps | Middleware de rate limiting par IP/route et limite `MAX_REQUEST_BODY_BYTES` |
| Moyenne | Frontend | Session persistante sans expiration d'inactivite cote client | Deconnexion automatique apres 30 minutes d'inactivite et appel logout serveur |
| Moyenne | En-tetes HTTP | Protections navigateur incompletes | CSP, HSTS HTTPS, anti-clickjacking, no-sniff, referrer policy et permissions policy |
| Moyenne | Journaux | Risque de fuite de secrets dans les details d'audit | Sanitisation recursive des cles sensibles avant persistance |
| Moyenne | Chat IA | Endpoint utilisable sans utilisateur authentifie et message non borne | Authentification obligatoire et validation stricte de longueur |
| Moyenne | Documents publics | Verification PDF enumerable par identifiant seul | Code de verification requis dans l'URL/QR pour reduire l'enumeration |
| Moyenne | Configuration serveur | CORS wildcard possible avec configuration production | Blocage du demarrage si `CORS_ALLOWED_ORIGINS=*` en production |
| Moyenne | Mots de passe | Politique de mot de passe insuffisante pour nouveaux comptes | Regles minimales: 12 caracteres, majuscule, minuscule, chiffre et caractere special |
| Faible | Tests | Absence de tests dedies aux controles securite ajoutes | Tests backend pour mot de passe faible, verrouillage et en-tetes securite |

## Mesures implementees

- Authentification: MFA TOTP, politique de mots de passe, verrouillage temporaire, invalidation par `token_version`.
- Autorisation: conservation des gardes RBAC existants et compatibilite avec les roles multi-tenant deja en place.
- Donnees sensibles: chiffrement des secrets fournisseur, masquage API, nettoyage des journaux.
- API: rate limiting, taille maximale de corps, erreurs d'authentification moins verbeuses, validation Pydantic renforcee.
- Observabilite: table `security_events`, endpoint admin systeme, audit trail global avec donnees sensibles masquees.
- Frontend: champ MFA au login et expiration d'inactivite.
- Deploiement: variables d'environnement documentees pour secrets, chiffrement, rate limiting et taille de requetes.
- Documents: verification publique conditionnee par un code inclus dans le document genere.

## Recommandations restantes

- Utiliser Redis ou un service partage pour le rate limiting en production multi-instance.
- Activer un scanner antivirus reel pour les fichiers uploades avant publication.
- Servir les documents sensibles via stockage prive avec URLs signees temporaires.
- Ajouter WAF/CDN anti-DDoS devant l'API et le frontend.
- Mettre en place SAST/Dependency scanning dans CI et rotation planifiee des secrets.
- Ajouter une politique CSP adaptee domaine par domaine lorsque les fournisseurs reels sont figes.
- Formaliser un plan de reprise d'activite avec tests de restauration trimestriels.
