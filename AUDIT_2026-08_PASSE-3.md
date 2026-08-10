# Passe 3 — audit indépendant avant lancement (septembre 2026)

> Passe de vérification **indépendante**, menée après les lots 0→6 et la seconde
> passe. Objectif : trouver ce que les passes précédentes ont manqué, en
> s'appuyant sur des **preuves d'exécution** et non sur de la relecture.
> Méthode : sondes réelles (HTTP de bout en bout), scan statique des routeurs,
> exécution complète de la suite, mesure du frontend.

---

## 0. Résultat en une ligne

Trois constats nouveaux, dont **deux bloquants** — tous deux introduits ou
révélés par la remédiation elle-même, et tous deux **corrigés et vérifiés ici**.
La suite passe de **3 échecs / 607 tests** à **0 échec / 617 tests**, et de
11 min 32 s à 8 min 15 s.

| ID | Constat | Gravité | État |
|---|---|---|---|
| **P3-A** | Identifiant ambigu sur le bulletin : `profile.id == x OR profile.user_id == x` pouvait renvoyer **le bulletin d'un autre enfant** ; combiné au contrôle de tenancy, il transformait aussi des accès légitimes en 404 | **P0** | ✅ Corrigé |
| **P3-B** | Aucune isolation des tests : 26 modules écrivaient dans la base de développement (7,3 Mo accumulés) → suite **non déterministe** (3 échecs fantômes), lente, et rien n'empêchait un run de viser une vraie base | **P1** | ✅ Corrigé |
| **P3-C** | Le garde-fou « dépendance manquante » des Salles s'armait sur une **erreur serveur** : un 500 affichait « aucun bâtiment — créez-en un » et désactivait le formulaire | **P2** | ✅ Corrigé |

---

## 1. P3-A — Bulletin : identifiant ambigu (P0)

**Le problème.** La route accepte indifféremment un id de `StudentProfile` ou
l'id du compte `User` de l'élève, et les résolvait par un OU :

```python
(StudentProfile.id == student_id) | (StudentProfile.user_id == student_id)
```

L'id `5` correspond alors **à la fois** au profil n°5 et au profil dont le
`user_id` vaut 5 — **deux enfants différents** — et `.first()` tranchait
arbitrairement.

**Deux conséquences, l'une pire que l'autre :**

1. **Mauvais bulletin servi.** Nom, notes, moyennes et rang d'un élève pouvaient
   être renvoyés pour un autre. En établissement multi-écoles, la ligne
   sélectionnée pouvait même appartenir à un autre établissement.
2. **Refus d'accès légitimes.** Le contrôle de tenancy ajouté par la
   remédiation s'exécutait *après* la sélection : il rejetait correctement la
   ligne étrangère… mais renvoyait alors **404 sur une demande parfaitement
   légitime**. Le bulletin — document le plus important du trimestre —
   devenait inaccessible.

> Détail méthodologique important : la sonde inter-établissement seule ne
> pouvait pas voir le second effet, puisqu'elle **attend** un 403/404. Elle
> passait « au vert » pendant que la fonctionnalité était cassée pour tout le
> monde. Il a fallu un test **positif** (le bulletin d'un élève de sa propre
> école doit répondre 200) pour révéler la panne. Toute règle d'autorisation
> doit être couverte par les deux sens.

**Correction** (`backend/routers/grades.py`) : la tenancy est appliquée **dans
la requête** et non après, et la résolution devient déterministe — id de profil
d'abord, repli sur l'id de compte seulement si rien ne correspond. Aucune ligne
étrangère ne peut donc être sélectionnée, puis rejetée.

**Vérification** : `test_deep_grades.py` (positif) + `test_cross_tenant_probe.py`
(négatif) + `test_report_cards.py` → **26 tests verts**. Migration : aucune.

---

## 2. P3-B — Aucune isolation des tests (P1)

**Le problème.** Il n'existait **aucun `conftest.py`**. Les 26 modules qui
pilotent l'application réelle via `TestClient(app)` écrivaient dans la base de
développement `./education_saas.db`, déjà à **7,3 Mo** de données de test
accumulées.

**Trois risques de production :**

* **Suite non fiable.** L'accumulation d'écoles, de comptes et de matricules
  uniques provoquait des collisions selon l'ordre d'exécution :
  `test_ai_agent_rbac` (×2) et `test_timetable_constraint_api` échouaient en
  suite complète et passaient isolément. *Une barrière de lancement à laquelle
  on ne peut pas se fier n'est pas une barrière.*
* **Lenteur croissante.** Une seule inscription d'école atteignait ~14 s contre
  le fichier gonflé ; la suite complète prenait 11 min 32 s.
* **Rien n'empêchait un run d'écrire dans une vraie base.** Si `DATABASE_URL`
  avait pointé vers la préproduction, le trafic `TestClient` y serait allé.

**Correction** (`backend/conftest.py`) : base SQLite privée par session (une par
PID, donc compatible exécution parallèle), créée avant l'import de
`backend.database`, schéma monté au démarrage, fichier supprimé à la fin — et
**refus de démarrer** si `DATABASE_URL` ne pointe pas vers SQLite.

**Vérification** : **617 tests verts, 0 échec, 8 min 15 s** (contre 3 échecs /
607 / 11 min 32 s). Les trois échecs fantômes ont disparu ; les suites
« profondes » passent de 28 erreurs à 39 verts.

---

## 3. P3-C — Erreur serveur présentée comme « donnée absente » (P2)

Sur `/dashboard/rooms`, un échec de `/facilities/buildings` laissait
`buildingsLoaded = true` avec une liste vide : le mécanisme
`RequireOptions` / `missingRequired` annonçait alors **« aucun bâtiment — créez-en
un »** et désactivait la soumission. L'utilisateur est invité à recréer des
données qui existent déjà — exactement le scénario de duplication décrit dans
la campagne « erreurs avalées ». Idem pour la liste des salles
(`r.ok ? await r.json() : []`).

**Correction** : seule une réponse réussie arme le garde-fou ; un échec affiche
le bandeau d'erreur (`facilities.loadFailed`, 4 locales, parité vérifiée).

---

## 4. Ce qui a été vérifié et jugé SAIN (preuves)

| Domaine | Preuve |
|---|---|
| **Isolation inter-établissements** | Sonde réelle A→B sur 7 surfaces (élève, enseignant, bulletin JSON, bulletin PDF, élèves d'une classe, présences, reçu PDF) : **toutes refusées**. `test_cross_tenant_probe.py` |
| **Secrets** | Aucun `.env` réel suivi par git ; **aucun secret dans l'historique** (`git log -S` sur les préfixes de clés) ; seuls les `.env*.example` sont versionnés, sans valeur |
| **Présences — écriture** | `/attendance/batch` valide l'appartenance au contexte d'inscription (403 sur id inexistant), résout correctement id de compte → profil (pas de report sur le mauvais élève), et l'appel répété **met à jour** au lieu de dupliquer |
| **Présences — lecture** | Pagination et plafond effectifs, portée `access_scope` appliquée, filtre par classe d'un autre établissement → liste vide |
| **Bulletin PDF** | Hérite du contrôle du JSON (il appelle `get_report_card`) — pas de contournement par la route PDF |

---

## 5. Restant à faire (inchangé, non réalisable en bac à sable)

Test de charge, répétition de restauration de sauvegarde, `npm audit` + build
frontend, paiement réel par opérateur mobile money. Voir
`AUDIT_2026-08_PRE-PRODUCTION.md` §0.

**Dette identifiée, non corrigée ici (P2/P3, chiffrée) :**

* Campagne « erreurs avalées » : **176** `if (res.ok)` sans `else` et **67**
  `.catch(() => undefined)` subsistent (le motif le plus toxique — 500 → liste
  vide — est passé de 28 à **2** : `documents/page.tsx:238`,
  `emploi-recruteur/page.tsx:123`). Ces deux pages n'ont ni état d'erreur ni
  traducteur : le correctif demande un bandeau + i18n, non fait ici faute de
  pouvoir vérifier le rendu (pas de `node_modules`).
* Les suites `test_deep_*.py` restent **dépendantes de l'ordre** (état partagé
  via une fixture de module) ; elles passent désormais, mais cette fragilité
  devrait être retirée avant d'en faire une barrière CI.

---

## 6. Recommandation

**CONDITIONAL GO** pour septembre. Les deux bloquants trouvés dans cette passe
sont corrigés et couverts par des tests dans les deux sens (autorisé / interdit).
La condition qui reste porte sur les tâches d'exploitation réelles — charge,
restauration de sauvegarde, build frontend, paiement live — qui exigent
l'environnement de production et ne peuvent pas être validées ici.

**Leçon transverse de cette passe** : les deux bloquants ont été *créés ou
révélés par la remédiation*. Le code écrit pour corriger un audit mérite la même
défiance que le code d'origine — et toute règle d'autorisation doit être testée
dans les deux sens, faute de quoi une fonctionnalité entièrement cassée peut
passer pour « sécurisée ».
