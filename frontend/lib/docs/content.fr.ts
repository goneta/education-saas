// French translation of the TeducAI Platform Docs.
//
// Structure mirrors `content.ts` exactly: same slugs, same block kinds, same
// links (only the visible label of a [label](/href) link is translated — the
// href is kept identical). `tab` fields on groups stay in ENGLISH because they
// are identity keys shared with the header/sidebar state; only the group
// `title` and item `label` are translated. Pages not present here fall back to
// the English version via the registry resolver.

import type { DocBlock } from "@/components/docs/doc-blocks"
import type { DocGroup, DocPage } from "./content"

const P = (...blocks: DocBlock[]) => blocks

// Localized display labels for the top-level tabs (keys stay English).
export const TAB_LABELS_FR: Record<string, string> = {
    Guides: "Guides",
    Features: "Fonctionnalités",
    Admin: "Administration",
    Resources: "Ressources",
}

// Chrome strings rendered outside the page body.
export const DOCS_UI_FR: Record<string, string> = {
    search: "Rechercher…",
    noResults: "Aucun résultat.",
    copyPage: "Copier la page",
    copied: "Copié",
    onThisPage: "Sur cette page",
    documentation: "Documentation",
    pageNotFound: "Page introuvable",
    backHome: "Retour à l'accueil de la documentation",
    apiReference: "Référence API",
    console: "Console",
}

export const DOC_GROUPS_FR: DocGroup[] = [
    { tab: "Guides", title: "Prise en main", items: [
        { slug: "intro", label: "Introduction à TeducAI" },
        { slug: "quickstart", label: "Démarrage rapide" },
        { slug: "platform-overview", label: "Vue d'ensemble de la plateforme" },
    ]},
    { tab: "Features", title: "Gestion académique", items: [
        { slug: "students", label: "Élèves & inscriptions" },
        { slug: "classes-levels", label: "Classes, niveaux & salles" },
        { slug: "assignments", label: "Devoirs & exercices" },
        { slug: "grades", label: "Notes & bulletins" },
        { slug: "timetable-engine", label: "Moteur d'emploi du temps IA" },
    ]},
    { tab: "Features", title: "Plateforme IA", items: [
        { slug: "ai-agents", label: "Agents IA & chat" },
        { slug: "ai-learning", label: "Générateurs pédagogiques IA" },
        { slug: "ai-credits", label: "Crédits IA" },
    ]},
    { tab: "Features", title: "Finance", items: [
        { slug: "fees-payments", label: "Frais & paiements" },
        { slug: "cash-payments", label: "Paiements en espèces & crédits IA" },
        { slug: "payroll", label: "Paie" },
        { slug: "billing", label: "Facturation & abonnements" },
    ]},
    { tab: "Features", title: "Transport intelligent", items: [
        { slug: "transport-overview", label: "Vue d'ensemble" },
        { slug: "transport-fleet", label: "Flotte, chauffeurs & trajets" },
        { slug: "transport-boarding", label: "Embarquement, GPS & sécurité" },
    ]},
    { tab: "Features", title: "Automatisations", items: [
        { slug: "automations", label: "Suite d'automatisations" },
        { slug: "esignature", label: "Signature électronique & documents" },
    ]},
    { tab: "Features", title: "Communication & RH", items: [
        { slug: "announcements", label: "Annonces" },
        { slug: "leave", label: "Gestion des congés" },
    ]},
    { tab: "Admin", title: "Plateforme & administration", items: [
        { slug: "multi-tenant", label: "Établissements & contexte" },
        { slug: "roles-permissions", label: "Rôles & permissions" },
        { slug: "personnel", label: "Personnel de l'établissement" },
        { slug: "help-center", label: "Centre d'aide intégré" },
    ]},
    { tab: "Resources", title: "Développeurs", items: [
        { slug: "api-webhooks", label: "API & webhooks" },
        { slug: "extensibility", label: "Extensibilité" },
    ]},
]

export const DOC_PAGES_FR: Record<string, DocPage> = {
    "automations": {
        slug: "automations", label: "Suite d'automatisations", breadcrumb: "Fonctionnalités / Automatisations",
        title: "Suite d'automatisations",
        description: "19 automatisations pour chaque groupe d'utilisateurs — personnel de l'établissement, enseignants, élèves, parents, recruteurs et chercheurs d'emploi — bâties sur les données réelles de la plateforme, idempotentes par conception et facturées en crédits IA lorsqu'une IA intervient.",
        blocks: P(
            { k: "p", text: "TeducAI embarque un programme d'automatisation complet. Chaque automatisation suit les mêmes principes : elle s'appuie sur des **données réelles** (jamais inventées), elle est **idempotente** (relançable sans risque manuellement ou par cron — un suivi anti-spam empêche tout double envoi), les générations IA sont **facturées en crédits** sur le portefeuille de l'appelant, et tout ce qui exige une décision ou des identifiants refuse honnêtement au lieu de simuler un résultat." },
            { k: "h2", text: "Personnel & administrateurs" },
            { k: "table", headers: ["Automatisation", "Ce qu'elle fait"], rows: [
                ["Assistant de rentrée", "Un seul flux fait basculer l'année académique : prévisualisez d'abord (rien n'est écrit), puis lancez — les élèves sont promus niveau→niveau dans les classes les moins remplies, les sortants archivés avec historique conservé, les barèmes de frais clonés sur la nouvelle année. La même année ne peut jamais être basculée deux fois."],
                ["Relances des impayés", "Analyse les frais en retard et envoie des relances progressives (aimable → ferme → urgente + escalade à l'administration) avec SMS au téléphone du parent. Le délai de temporisation et le suivi de niveau rendent les relances rejouables sans risque."],
                ["Documents en libre-service", "Les élèves et les parents génèrent eux-mêmes certificats de scolarité, attestations et reçus de paiement — références uniques vérifiables, prêts à imprimer, sans intervention du personnel."],
                ["Brief anomalies", "Un brief opérationnel par période : pic d'absences vs la période précédente, ratio d'impayés au-dessus du seuil, déséquilibre des effectifs — remis à l'administrateur."],
            ]},
            { k: "h2", text: "Enseignants" },
            { k: "table", headers: ["Automatisation", "Ce qu'elle fait"], rows: [
                ["Saisie de notes par photo", "Photographiez une liste de notes ; un fournisseur de vision (OpenAI/Anthropic) transcrit les paires nom–note, rapprochées de façon déterministe de la liste de la classe avec des indices de confiance. Rien n'est enregistré tant que l'enseignant n'a pas vérifié et confirmé."],
                ["Générateur de séquence", "Le plan de cours d'un trimestre entier généré en un seul appel IA, calibré sur les créneaux hebdomadaires RÉELS de l'emploi du temps × les semaines du trimestre — refusé s'il n'existe aucun créneau."],
                ["Remédiation IA", "Après une évaluation, chaque élève sous le seuil reçoit une fiche d'exercices personnalisée (3 à 5 exercices progressifs fondés sur sa note et le commentaire de l'enseignant), livrée en notification. Les relances ne servent que les élèves nouvellement notés."],
                ["Suivi des absences", "Chaque absence non suivie déclenche le message au parent (notification dans la langue du parent + SMS si un téléphone est enregistré) — une seule fois par absence."],
            ]},
            { k: "h2", text: "Élèves" },
            { k: "table", headers: ["Automatisation", "Ce qu'elle fait"], rows: [
                ["Planning de révision", "Construit à partir de l'emploi du temps réel de l'élève, de ses prochaines évaluations et de ses devoirs non rendus : des créneaux de révision espacés à J-5 (vue d'ensemble), J-2 (exercices) et J-1 (révision finale)."],
                ["Rappels de devoirs", "Des rappels espacés à J-7 / J-3 / J-1 aux élèves qui n'ont pas rendu — un seul rappel par palier et par élève."],
                ["Explique ma note", "Un décryptage IA de n'importe laquelle des notes de l'élève : moyenne de la classe, meilleure note, rang, lecture du commentaire de l'enseignant et conseils concrets de progression, dans la langue de l'élève."],
            ]},
            { k: "h2", text: "Parents" },
            { k: "table", headers: ["Automatisation", "Ce qu'elle fait"], rows: [
                ["Résumé hebdomadaire par enfant", "Une notification par (parent, enfant) dans la langue DU PARENT, compilant les notes, absences et paiements dus de la semaine."],
                ["Alertes de seuil", "Des alertes instantanées qui accompagnent le résumé : moyenne sous le seuil, absences répétées."],
                ["Actions en un clic", "Directement depuis la cloche de notifications : justifier une absence (elle passe en excusée, l'enseignant est prévenu), payer un frais (lien direct vers la finance) et signer des documents — voir [Signature électronique](/docs/esignature)."],
            ]},
            { k: "h2", text: "Recruteurs & chercheurs d'emploi (TeducAI Emploi)" },
            { k: "table", headers: ["Automatisation", "Ce qu'elle fait"], rows: [
                ["Matching de candidats + raisons", "Les CV sont classés face à une offre par le moteur de correspondance déterministe ; une explication IA par candidat, fondée strictement sur les détails du matching."],
                ["Agents de recherche sauvegardée", "Des critères enregistrés sont re-évalués sur les CV mis à jour depuis le dernier passage — seuls les NOUVEAUX diplômés correspondants sont notifiés. Endpoint « run-all » planifiable en cron."],
                ["Questionnaires de présélection", "Un questionnaire IA par offre (connaissances, mise en situation, motivation), conservé sur l'offre pour réutilisation."],
                ["Actualisation automatique du CV", "Le dossier académique réel de l'élève alimente son CV à la demande."],
                ["Analyse d'écart", "Un diff déterministe offre-vs-profil (compétences, langues, expérience manquantes) + des conseils IA pour acquérir chaque élément manquant."],
                ["Lettres de motivation IA", "Des brouillons fondés strictement sur les données réelles du CV — le prompt interdit d'inventer diplômes ou employeurs."],
            ]},
            { k: "h2", text: "Exécution et planification" },
            { k: "p", text: "Les automatisations du personnel vivent sur la page **Système → Automatisations** (seuils, lancement immédiat, résumés de résultat, historique par exécution). Chaque runner est idempotent, donc un cron externe peut appeler les endpoints directement :" },
            { k: "code", lang: "bash", code: "POST /automations/fee-reminders/run\nPOST /automations/parent-digest/run\nPOST /automations/absence-followup/run\nPOST /automations/anomaly-digest/run\nPOST /automations/homework-reminders/run\nPOST /employment/recruiter/saved-searches/run-all" },
            { k: "h2", text: "Fournisseurs IA" },
            { k: "p", text: "Les automatisations à base d'IA passent par la couche fournisseurs de la plateforme : **OpenAI et Anthropic sont les fournisseurs principaux** ; OpenRouter, Manus et Genspark servent de repli, dans cet ordre. Les clés se placent dans `.env.production` (enregistrées automatiquement au démarrage) ou dans **Système → Fournisseurs IA** (stockées chiffrées). Les fonctions de vision (saisie de notes par photo) exigent un modèle capable de vision et refusent avec une erreur explicite lorsqu'aucun fournisseur n'est joignable — les résultats ne sont jamais fabriqués." },
            { k: "callout", tone: "note", title: "Crédits", text: "Chaque génération IA vérifie et débite le portefeuille de crédits IA de l'appelant — voir [Crédits IA](/docs/ai-credits)." },
        ),
    },

    "esignature": {
        slug: "esignature", label: "Signature électronique & documents", breadcrumb: "Fonctionnalités / Automatisations",
        title: "Signature électronique & documents en libre-service",
        description: "Les familles génèrent elles-mêmes des documents officiels et les signent électroniquement — vérifiables cryptographiquement et infalsifiables, sans fournisseur de signature externe.",
        blocks: P(
            { k: "h2", text: "Documents en libre-service" },
            { k: "p", text: "Depuis **Mes documents**, un élève (ou un parent pour un enfant rattaché) génère un certificat de scolarité, une attestation de fréquentation ou un reçu de paiement en un clic. Chaque document porte une référence unique (CERT-…, ATT-…, REC-…), s'imprime avec l'en-tête de l'établissement et peut être ré-affiché à l'identique indéfiniment — le contenu complet est enregistré au moment de la génération." },
            { k: "h2", text: "Fonctionnement de la signature électronique" },
            { k: "ol", items: [
                "Lorsqu'un signataire clique sur **Signer**, le contenu du document est canonisé puis haché (SHA-256) — ce qui fige exactement ce qui a été signé.",
                "La signature elle-même est un HMAC-SHA256, dérivé de manière isolée du secret de la plateforme, portant sur l'id du document, la référence, le hachage du contenu, le signataire et l'horodatage.",
                "La vérification recalcule les deux : une signature non concordante signifie que la ligne de signature a été forgée ; un hachage de contenu non concordant signifie que le document a été modifié après la signature (falsification).",
            ]},
            { k: "p", text: "L'élève du document et un parent rattaché peuvent signer chacun une fois. Les signatures valides s'impriment sur le document dans un bloc vérifié avec un code court (XXXX-XXXX-XXXX), et l'endpoint de vérification par référence renvoie chaque signature avec ses contrôles d'authenticité et d'intégrité en direct." },
            { k: "callout", tone: "warn", title: "Portée", text: "Il s'agit d'une signature d'intégrité/authenticité liée au compte de plateforme authentifié — une piste d'audit complète de qui a signé quoi et quand, avec preuve de non-altération. Ce n'est pas une signature électronique qualifiée au sens eIDAS." },
        ),
    },

    intro: {
        slug: "intro", label: "Introduction à TeducAI", breadcrumb: "Guides / Prise en main",
        title: "Introduction à TeducAI",
        description: "TeducAI est une plateforme éducative multi-établissements, d'entreprise et centrée sur l'IA. Une seule plateforme où chaque module partage la même authentification, le même RBAC, les mêmes services IA, notifications et données de référence — sans aucune duplication de données.",
        blocks: P(
            { k: "callout", tone: "tip", title: "Une plateforme, tous les modules", items: [
                "`Académique` — élèves, enseignants, classes, matières, le moteur d'emploi du temps IA, notes et bulletins.",
                "`IA` — 41 agents spécialisés, un assistant conversationnel, et des générateurs IA de cours / quiz / examens.",
                "`Finance` — frais, un Service de paiement centralisé (Stripe, CinetPay, Djamo, espèces), paie et crédits IA.",
                "`Transport intelligent` — flotte, chauffeurs, trajets, GPS, embarquement et optimisation IA des itinéraires.",
                "`Opérations` — communication, RH/congés, analytique et extensibilité (webhooks + clés API).",
            ]},
            { k: "h2", text: "Ce qui distingue TeducAI" },
            { k: "p", text: "Contrairement aux solutions ponctuelles (un SIS ici, un outil de paiement là, une application de transport à part), TeducAI est un système unique. Un élève créé une seule fois alimente l'inscription, la notation, la facturation, le transport et le portail parent — sans deuxième connexion, sans deuxième base de données et sans données de référence dupliquées." },
            { k: "ul", items: [
                "**Multi-établissements par conception** — de nombreux établissements coexistent avec une isolation stricte des données ; chaque requête est cloisonnée par établissement.",
                "**RBAC partout** — chaque écriture est protégée par rôle ; Super Admin, Administrateur d'établissement, enseignants, élèves et parents voient chacun une expérience adaptée.",
                "**Centré sur l'IA** — l'IA est tissée dans le produit : génération d'emploi du temps, contenu de cours, assistance pédagogique et aide à la décision.",
                "**Multilingue** — l'interface entière se localise en français et en anglais (avec les bases pour l'espagnol et le swahili).",
            ]},
            { k: "h2", text: "Qui l'utilise" },
            { k: "table", headers: ["Rôle", "Ce qu'il fait"], rows: [
                ["Super Admin", "Gère la plateforme : établissements, référentiel global des niveaux, offres de crédits IA, administration inter-établissements."],
                ["Administrateur d'établissement", "Pilote un établissement : élèves, personnel, classes, finance, emploi du temps, communication."],
                ["Enseignant", "Cours, classes, devoirs, notes, outils de génération IA, bulletins de paie et congés — menus d'administration masqués."],
                ["Élève", "Devoirs, notes, emploi du temps, documents, bulletins, paiements et notifications."],
                ["Parent", "Voit chaque enfant, bascule de l'un à l'autre et consulte le dossier scolaire complet de l'enfant."],
            ]},
            { k: "callout", tone: "note", title: "Vous cherchez l'application ?", text: "Ouvrez la [Console](/dashboard) pour utiliser TeducAI, ou lisez le [Démarrage rapide](/docs/quickstart) pour configurer votre premier établissement." },
        ),
    },

    quickstart: {
        slug: "quickstart", label: "Démarrage rapide", breadcrumb: "Guides / Prise en main",
        title: "Démarrage rapide",
        description: "Configurez votre établissement et atteignez un tableau de bord fonctionnel en quelques étapes.",
        blocks: P(
            { k: "h2", text: "1. Créez votre établissement" },
            { k: "p", text: "Un Super Admin crée l'établissement, ses **modèles d'établissement** (par ex. Général, Technique, Professionnel) et ses **années académiques**. Ces trois valeurs forment le contexte de travail actif sélectionné depuis la barre supérieure." },
            { k: "h2", text: "2. Choisissez le contexte de travail" },
            { k: "p", text: "Depuis la navigation supérieure, choisissez l'**établissement**, le **modèle** et l'**année académique**. Tout ce que vous voyez et créez est cloisonné à ce contexte. Les utilisateurs ne voient que les établissements auxquels ils sont rattachés." },
            { k: "h2", text: "3. Construisez la structure académique" },
            { k: "ol", items: [
                "Le Super Admin définit des **niveaux** réutilisables (CP1, CE1, 6ème, Terminale, BTS…) dans le référentiel global.",
                "Créez des **classes** à partir de ces niveaux (par ex. `CP1 A`, `2nde Technique A`).",
                "Ajoutez des **bâtiments** et des **salles** (avec capacité et type), ainsi que des **matières**.",
                "Inscrivez des **élèves** et ajoutez des **enseignants** et du **personnel**.",
            ]},
            { k: "h2", text: "4. Générez l'emploi du temps" },
            { k: "p", text: "Configurez les contraintes pédagogiques, puis laissez le [Moteur d'emploi du temps IA](/docs/timetable-engine) produire des emplois du temps optimisés et sans conflit." },
            { k: "callout", tone: "tip", text: "Chaque page dispose d'un bouton **Aide** contextuel qui ouvre la documentation intégrée de l'écran courant — voir [Centre d'aide intégré](/docs/help-center)." },
        ),
    },

    "platform-overview": {
        slug: "platform-overview", label: "Vue d'ensemble de la plateforme", breadcrumb: "Guides / Prise en main",
        title: "Vue d'ensemble de la plateforme",
        description: "La carte des modules et les services partagés sur lesquels chaque module s'appuie.",
        blocks: P(
            { k: "h2", text: "Socle partagé" },
            { k: "p", text: "Chaque module consomme les mêmes services fondamentaux plutôt que de les réimplémenter : identité & RBAC, le contexte actif (organisation / établissement / modèle / année), le Service de paiement centralisé, la plateforme IA, les notifications et l'analytique." },
            { k: "h2", text: "Carte des modules" },
            { k: "table", headers: ["Domaine", "Modules"], rows: [
                ["Cœur", "Authentification, contexte, système, site (CMS), plateforme (départements, feature flags, recherche globale)"],
                ["SIS", "Élèves, cycle de vie de l'élève, tuteurs, contacts d'urgence, dossiers médicaux"],
                ["Académique", "Classes, matières, moteur d'emploi du temps, pédagogie, notes, assiduité, moyenne (GPA)"],
                ["IA", "41 agents + routeur LLM, chat, automatisation, crédits, générateurs pédagogiques IA"],
                ["Finance", "Frais, Service de paiement centralisé, paie, crédits IA"],
                ["Transport intelligent", "Flotte, chauffeurs, véhicules, trajets, arrêts, GPS, embarquement, incidents, carburant, optimiseur IA"],
                ["Opérations", "Communication, RH/congés, analytique, extensibilité"],
            ]},
            { k: "callout", tone: "note", title: "Zéro duplication de données", text: "Les modules ne copient jamais les données des autres. Le transport lit les élèves depuis le SIS ; la facturation lit les frais depuis la Finance ; l'application parent lit les notes depuis le module académique — le tout via des API cloisonnées par établissement et bien définies." },
        ),
    },

    students: {
        slug: "students", label: "Élèves & inscriptions", breadcrumb: "Fonctionnalités / Gestion académique",
        title: "Élèves & inscriptions",
        description: "Le cycle de vie maître de l'élève — un dossier unique qui suit l'élève à travers les établissements et les années académiques.",
        blocks: P(
            { k: "h2", text: "Dossiers des élèves" },
            { k: "p", text: "Chaque élève dispose d'un profil unique (informations personnelles, matricule, photo, tuteurs, contacts d'urgence et données médicales). La création d'un élève provisionne automatiquement le compte de connexion." },
            { k: "h2", text: "Inscription & historique" },
            { k: "p", text: "Un élève peut appartenir à plusieurs établissements au cours de sa scolarité. Chaque inscription est historisée avec l'établissement, l'année académique, la classe, le niveau, le statut et les dates d'entrée/sortie — de sorte que l'historique scolaire complet est préservé lors des transferts." },
            { k: "h2", text: "Niveau → classe sur le formulaire" },
            { k: "p", text: "Le formulaire d'ajout d'élève comporte une section **Informations sur la Classe** : choisissez d'abord un **niveau**, puis la liste des classes se filtre pour ne montrer que celles rattachées à ce niveau. Le détail en lecture seule d'une classe affiche le nombre d'élèves inscrits et une liste défilante (nom complet, âge, sexe) — chaque ligne renvoie au profil de l'élève." },
            { k: "callout", tone: "tip", text: "Les listes de TeducAI partagent un même composant de filtre : un sélecteur de colonnes plus une recherche temporisée, insensible aux accents et à la casse." },
        ),
    },

    "classes-levels": {
        slug: "classes-levels", label: "Classes, niveaux & salles", breadcrumb: "Fonctionnalités / Gestion académique",
        title: "Classes, niveaux & salles",
        description: "Un référentiel central de niveaux, des classes bâties à partir de celui-ci, et les bâtiments & salles qui les accueillent — avec des règles d'occupation intelligentes.",
        blocks: P(
            { k: "h2", text: "Référentiel des niveaux" },
            { k: "p", text: "Le Super Admin maintient une liste globale de **niveaux** (par ex. `CP1`, `CE1`, `6ème`, `Terminale`, `BTS Informatique`). Chaque établissement construit ensuite ses classes en choisissant dans cette liste — par exemple `CP1 A`, `2nde Technique A`, `BTS COMPTA A`. Un niveau ne peut être supprimé que si aucune classe ne l'utilise." },
            { k: "h2", text: "Bâtiments & salles" },
            { k: "p", text: "Sous **Gestion**, créez des **bâtiments** (nom, description, campus, statut) et des **salles**. Pour ajouter une salle, vous sélectionnez son bâtiment, puis définissez le nom, la capacité et le type (salle de classe, laboratoire, salle informatique, atelier, gymnase, autre)." },
            { k: "h2", text: "Règles d'occupation intelligentes" },
            { k: "ul", items: [
                "Une classe de 30 ne peut pas être placée dans une salle de 25 places — l'affectation est bloquée.",
                "Une salle utilisée dans un emploi du temps ne peut pas être supprimée ; la liste des salles affiche un compteur **Classes** avec une fenêtre **Voir** listant les classes (et leur niveau) qui y sont programmées.",
                "La liste des classes affiche un compteur **Nb Élèves** avec une fenêtre **Voir** des élèves inscrits ; une classe qui a encore des élèves ne peut pas être supprimée.",
            ]},
            { k: "callout", tone: "warn", text: "Les garde-fous de capacité et d'utilisation renvoient un conflit `409` explicite plutôt qu'un échec silencieux, de sorte que les administrateurs comprennent toujours pourquoi une action a été bloquée." },
        ),
    },

    "assignments": {
        slug: "assignments", label: "Devoirs & exercices", breadcrumb: "Fonctionnalités / Gestion académique",
        title: "Devoirs, exercices, corrections & évaluation",
        description: "Un module de devoirs complet — création (manuelle ou IA, avec corrigé généré automatiquement), remise en ligne et sur papier, correction manuelle et par IA, pont vers le carnet de notes, statistiques et notifications — le tout dans TeducAI.",
        blocks: P(
            { k: "p", text: "Le module couvre tout le cycle pédagogique sur une seule plateforme, de la création d'un travail jusqu'à sa correction, sa notation et son archivage. Il réutilise les classes, matières, carnet de notes, notifications, crédits IA et services IA de la plateforme (zéro duplication de données)." },
            { k: "h2", text: "Créer des devoirs" },
            { k: "p", text: "Les enseignants créent onze types de travaux — devoir, exercice, quiz, contrôle, évaluation, examen, devoir maison, travail pratique, projet, exposé et interrogation — soit **manuellement**, soit avec le **générateur IA**." },
            { k: "ul", items: [
                "La **génération IA** produit les questions ET le corrigé à partir de la matière, du chapitre, du niveau, de la difficulté et du nombre de questions — réponses attendues, explications, points par question et barème.",
                "Types de questions variés : QCM, vrai/faux, réponses courtes/longues, texte à trous, association, classement, calcul, problème, étude de cas, programmation, rédaction et compréhension de texte.",
                "La génération consomme les crédits IA de l'enseignant ; il vérifie et ajuste avant de publier.",
            ]},
            { k: "h2", text: "Deux modes de réalisation" },
            { k: "table", headers: ["Mode", "Fonctionnement"], rows: [
                ["En ligne", "Les élèves répondent dans TeducAI — sauvegarde automatique, reprise après interruption, et la copie se verrouille après la date limite (sauf pénalité de retard configurée)."],
                ["Papier", "Le devoir est téléchargeable/imprimable ; les élèves le réalisent et le remettent physiquement pour correction."],
            ]},
            { k: "h2", text: "Attribuer & remettre" },
            { k: "p", text: "Un devoir cible une classe entière ou un sous-ensemble d'élèves, avec date d'ouverture, date limite, nombre de tentatives et pénalité de retard facultative. À la publication, les élèves ciblés (et, lors de la correction, leurs parents) sont notifiés. Les élèves remettent des réponses en ligne et/ou des fichiers joints." },
            { k: "h2", text: "Correction" },
            { k: "ul", items: [
                "La liste **« Donner des notes »** montre chaque élève et qui a remis, qui est en retard ou absent.",
                "L'enseignant ouvre une copie, la note à la main (note + commentaire + annotations) ou lance la **correction IA** — l'IA note la copie contre le corrigé et renvoie un commentaire, les erreurs détectées, points forts, points faibles et conseils.",
                "La correction IA reste toujours une **proposition** : l'enseignant valide, modifie ou refuse la note. Les pénalités de retard sont appliquées automatiquement.",
            ]},
            { k: "h2", text: "Carnet de notes, statistiques & accès" },
            { k: "p", text: "« Envoyer au carnet de notes » crée l'évaluation correspondante et y verse les notes, alimentant bulletins, moyennes et statistiques. Les stats par devoir montrent les remis/corrigés, la moyenne de classe, le taux de réussite et les retards. Le corrigé est diffusé aux élèves selon la règle — jamais, après la date limite, ou immédiat — l'enseignant le voyant toujours. Élèves et parents consultent la copie corrigée, le commentaire et (si diffusé) le corrigé." },
            { k: "callout", tone: "note", title: "Fondation + feuille de route", text: "Voici le cœur du module (création dont IA + corrigé, modes en ligne/papier, remises, correction manuelle + IA, pont carnet de notes, stats, notifications, contrôle d'accès). Feuille de route : éditeur de questions multimédia, correction OCR des copies papier reliée à ce module (le moteur OCR [grade-scan](/docs/automations) existe déjà), détection de plagiat / de réponses IA, génération différenciée et de variantes, annotations vocales, et les tableaux de bord analytiques complets." },
        ),
    },

    "billing": {
        slug: "billing", label: "Facturation & abonnements", breadcrumb: "Fonctionnalités / Finance",
        title: "Facturation & gestion des abonnements",
        description: "Une page Facturation d'entreprise unique pour le forfait TeducAI, les crédits IA, les factures, la consommation, les promotions, la fiscalité et l'audit — une surface unifiée au-dessus de l'infrastructure d'abonnements, de crédits et de paiements de la plateforme.",
        blocks: P(
            { k: "p", text: "Le module Facturation (Finance → Billing) réunit les abonnements des établissements, les crédits IA et les paiements de la plateforme dans un tableau de bord de type Stripe/OpenAI. Il ne réimplémente pas la gestion de l'argent : c'est une surface unifiée au-dessus du moteur d'abonnements existant, des portefeuilles de crédits IA et du Service de paiement centralisé (zéro duplication de données)." },
            { k: "h2", text: "Onglets" },
            { k: "table", headers: ["Onglet", "Rôle"], rows: [
                ["Aperçu", "Forfait actuel (nom, prix, cycle, statut, renouvellement), solde de crédits, statut de recharge automatique, accès rapide et activité récente. Le Super-Admin voit aussi les indicateurs de revenu (MRR/ARR, impayés, paiements échoués)."],
                ["Abonnement", "Catalogue de forfaits (Starter / Professional / Enterprise / Custom) avec crédits inclus, stockage, utilisateurs, établissements et niveau de support ; le changement passe par le flux d'abonnement existant (avec paiement lorsqu'un fournisseur est défini)."],
                ["Moyens de paiement", "Enregistrer, surnommer, définir par défaut et supprimer des moyens de paiement (carte / mobile-money / banque / portefeuille) chez tous les fournisseurs pris en charge (CinetPay — Orange/Wave/MTN/Moov, Djamo, Stripe, Visa, Mastercard, Amex, PayPal, Apple/Google Pay, virement), avec alertes d'expiration. Sûr (PCI) : seuls la marque, les 4 derniers chiffres et l'expiration sont enregistrés — jamais le numéro complet."],
                ["Historique / Transactions", "Factures et transactions projetées depuis les paiements de la plateforme, avec badges de statut, filtres, export CSV et téléchargement de la facture en PDF en un clic (un vrai PDF généré par reportlab avec émetteur, destinataire, détail de la taxe, totaux et une référence QR vérifiable)."],
                ["Crédits / Consommation", "Solde de crédits et consommation (crédits utilisés, jetons IA, coût estimé, crédits achetés) ; la boutique de crédits ouvre la page des crédits IA."],
                ["Promotions", "Saisir un code coupon, promo, cadeau ou parrainage — vérifié puis appliqué ; les codes de type crédits rechargent immédiatement le portefeuille de l'établissement."],
                ["Préférences / TVA & Fiscalité", "Devise, fuseau horaire, langue des factures, envoi par e-mail, rappels de paiement/renouvellement, renouvellement automatique et destinataires ; identité TVA/GST/taxe, taux, exonération et adresse de facturation."],
                ["Journaux d'audit", "Chaque action de facturation (préférences, fiscalité, recharge automatique, promo, changement d'abonnement, paiement) avec l'auteur et l'horodatage."],
                ["Assistant de facturation IA", "Posez des questions sur votre facture, votre consommation, vos factures ou votre forfait (« pourquoi ma facture est-elle plus élevée ? », « recommander un forfait moins cher », « pourquoi mon paiement a-t-il échoué ? ») — la réponse s'appuie strictement sur vos données réelles, décomptée sur vos crédits IA."],
            ]},
            { k: "h2", text: "Sécurité" },
            { k: "p", text: "La gestion de la facturation est réservée aux rôles administration, direction et comptabilité ; les analyses de revenu et la création de codes promo sont réservées au Super-Admin. Chaque modification est auditée et cloisonnée par établissement." },
            { k: "callout", tone: "note", title: "Socle + feuille de route", text: "Livré : la page et l'API unifiées (aperçu, changement d'abonnement, préférences, fiscalité, configuration de recharge automatique, vérification/application de promo, factures/transactions projetées, consommation, audit, revenu super-admin) ainsi que le téléchargement de la facture en PDF en un clic, la gestion complète des moyens de paiement enregistrés et un assistant de facturation IA ancré dans vos données réelles. Feuille de route : envoi des factures par e-mail et graphiques de consommation en direct — les données sous-jacentes existent déjà dans TeducAI." },
        ),
    },

    grades: {
        slug: "grades", label: "Notes & bulletins", breadcrumb: "Fonctionnalités / Gestion académique",
        title: "Notes & bulletins",
        description: "Évaluations, saisie des notes et bulletins par trimestre avec moyennes automatiques.",
        blocks: P(
            { k: "h2", text: "Évaluations" },
            { k: "p", text: "Créez des évaluations (examens, devoirs, quiz) pour une classe, une matière et un trimestre, chacune avec une note maximale et un coefficient. Un écran de saisie dédié liste les élèves de la classe pour une saisie rapide des notes et des commentaires." },
            { k: "h2", text: "Bulletins" },
            { k: "p", text: "Générez le bulletin d'un élève pour un trimestre : moyennes par matière sur 20, coefficient de la matière, évaluations contributives et moyenne générale — le tout calculé automatiquement." },
            { k: "callout", tone: "note", text: "Les notes alimentent le calcul de la moyenne (GPA) et les portails élève/parent ; les enseignants peuvent aussi rédiger le contenu des évaluations avec les [générateurs pédagogiques IA](/docs/ai-learning)." },
        ),
    },

    "timetable-engine": {
        slug: "timetable-engine", label: "Moteur d'emploi du temps IA", breadcrumb: "Fonctionnalités / Gestion académique",
        title: "Moteur d'emploi du temps IA",
        description: "Un moteur de planification intelligent et entièrement configurable — comparable à Untis ou aSc Timetables, mais natif à l'IA et intégré au reste de TeducAI.",
        blocks: P(
            { k: "p", text: "Le moteur génère des emplois du temps optimisés et sans conflit à partir d'un ensemble de contraintes configurables. Aucune règle n'est codée en dur : chaque contrainte vit en base de données et s'administre depuis l'interface, de sorte que chaque établissement définit sa propre politique pédagogique." },
            { k: "h2", text: "Ce qu'il résout" },
            { k: "ul", items: [
                "Enseignants internes vs externes, y compris ceux qui enseignent dans plusieurs établissements et les transferts entre écoles.",
                "Disponibilité des enseignants et heures hebdomadaires par matière.",
                "Aucun enseignant dans deux classes à la fois ; aucune classe avec deux cours simultanés.",
                "Salles et laboratoires disponibles, avec prise en compte des équipements.",
                "Contraintes de matière — par ex. ne pas enseigner une matière deux jours de suite.",
                "Règles de précédence — certaines matières ne doivent jamais suivre d'autres (par ex. la physique juste après l'EPS).",
                "Répartition équilibrée des matières lourdes vs légères, et plafond d'heures consécutives d'une même matière.",
                "Pauses, récréation et déjeuner ; jours fériés et jours non travaillés ; créneaux verrouillés.",
            ]},
            { k: "h2", text: "Règles de contraintes configurables" },
            { k: "p", text: "Les établissements expriment leur politique sous forme de données. Par exemple :" },
            { k: "ul", items: [
                "« Les mathématiques ne peuvent pas être programmées deux jours de suite. »",
                "« La physique ne peut jamais suivre immédiatement l'EPS. »",
                "« Le français doit toujours être enseigné avant 11h00. »",
                "« Un cours de laboratoire doit toujours être précédé d'un cours théorique. »",
                "« Un enseignant externe n'enseigne que le mardi et le jeudi. »",
                "« Les élèves du primaire n'ont jamais plus de deux matières lourdes le même jour. »",
                "« Les salles informatiques restent libres le vendredi après-midi. »",
            ]},
            { k: "h2", text: "Au-delà des planificateurs classiques" },
            { k: "table", headers: ["Capacité", "Ce qu'elle fait"], rows: [
                ["Génération optimisée par IA", "Produit plusieurs emplois du temps notés, classés par qualité, puis résout les conflits automatiquement."],
                ["IA explicable", "Explique les décisions derrière un emploi du temps généré afin que les administrateurs comprennent les arbitrages."],
                ["Simulation de scénarios", "Répond à « et si un enseignant est absent ? » ou « et si l'école ouvre le samedi ? »."],
                ["Remplacements", "Génère automatiquement des remplacements lorsqu'un enseignant est absent."],
                ["Énergie & déplacements", "Regroupe les cours pour réduire les coûts de fonctionnement et minimise les déplacements des enseignants entre bâtiments ou campus."],
                ["Hybride & multi-campus", "Gère la présence en présentiel/à distance et plusieurs campus, en s'adaptant aux calendriers scolaires par pays."],
            ]},
            { k: "callout", tone: "tip", title: "Intégré, pas isolé", text: "L'emploi du temps est le cœur de la plateforme : l'assiduité est enregistrée face aux créneaux de l'emploi du temps, les changements et remplacements notifient les utilisateurs concernés, et il consomme les enseignants, salles et matières des données de référence partagées. Le recalcul des heures de ramassage du transport à partir des changements d'emploi du temps est prévu à la feuille de route." },
        ),
    },

    "ai-agents": {
        slug: "ai-agents", label: "Agents IA & chat", breadcrumb: "Fonctionnalités / Plateforme IA",
        title: "Agents IA & chat",
        description: "41 agents IA spécialisés derrière un assistant conversationnel unifié, orientés vers le modèle le plus adapté à chaque tâche.",
        blocks: P(
            { k: "p", text: "TeducAI embarque une flotte d'agents spécifiques à un rôle et à un domaine (assistant enseignant, tuteur élève, RH, finance, décision, recherche et plus) derrière une seule surface de chat. Un routeur LLM choisit le bon modèle par tâche et la conversation est journalisée à des fins d'audit." },
            { k: "h2", text: "Points forts" },
            { k: "ul", items: [
                "Assistance pédagogique pour les enseignants ; tutorat et planification des études pour les élèves.",
                "Réponses multilingues ; explications ancrées dans le contexte éducatif.",
                "Alimenté par les crédits IA (voir [Crédits IA](/docs/ai-credits)).",
            ]},
            { k: "callout", tone: "note", text: "Les modèles Claude les plus récents et les plus performants alimentent les fonctions IA ; le routeur peut se rabattre entre niveaux pour le coût et la latence." },
        ),
    },

    "ai-learning": {
        slug: "ai-learning", label: "Générateurs pédagogiques IA", breadcrumb: "Fonctionnalités / Plateforme IA",
        title: "Générateurs pédagogiques IA",
        description: "Générez des cours, quiz, examens et devoirs adaptés au niveau de l'élève et à la matière.",
        blocks: P(
            { k: "ul", items: [
                "**Générateur de cours IA** — contenu de cours structuré pour une matière et un niveau.",
                "**Générateur de quiz / examens IA** — évaluations avec corrigés.",
                "**Générateur de devoirs IA** — exercices d'entraînement alignés sur le programme.",
                "**Retours & recommandations IA** — s'adaptent à l'apprenant.",
            ]},
            { k: "callout", tone: "tip", text: "Les enseignants accèdent à ces outils depuis leur propre tableau de bord ; le matériel généré s'intègre au flux [notes](/docs/grades). L'usage de l'IA consomme des crédits." },
        ),
    },

    "ai-credits": {
        slug: "ai-credits", label: "Crédits IA", breadcrumb: "Fonctionnalités / Plateforme IA",
        title: "Crédits IA",
        description: "Les crédits mesurent l'usage de l'IA. Ils peuvent être achetés en ligne ou en espèces, octroyés gratuitement, et distribués par un établissement à ses utilisateurs.",
        blocks: P(
            { k: "h2", text: "Offres de crédits" },
            { k: "p", text: "Le Super Admin crée des offres de crédits IA — chacune avec un nom, un prix, une devise, un montant de crédits, une description, un statut actif et une cible (utilisateur individuel, établissement, ou les deux). Par exemple :" },
            { k: "table", headers: ["Pack", "Prix", "Crédits"], rows: [
                ["Pack Starter", "3 000 F", "1 000 crédits IA"],
                ["Pack Standard", "5 000 F", "2 500 crédits IA"],
                ["Pack École", "50 000 F", "50 000 crédits IA"],
            ]},
            { k: "h2", text: "Distribution au niveau de l'établissement" },
            { k: "p", text: "Lorsqu'un établissement achète un pack, les crédits alimentent le solde global de l'établissement. Depuis **Gestion des crédits IA**, l'Administrateur d'établissement voit le solde, choisit quels utilisateurs peuvent utiliser l'IA, attribue un nombre précis de crédits à chacun et suit la consommation par utilisateur. La distribution ne peut jamais dépasser les crédits achetés par l'établissement." },
            { k: "callout", tone: "note", text: "Les recharges en espèces et gratuites sont enregistrées avec un historique complet ; voir [Paiements en espèces & crédits IA](/docs/cash-payments)." },
        ),
    },

    "fees-payments": {
        slug: "fees-payments", label: "Frais & paiements", breadcrumb: "Fonctionnalités / Finance",
        title: "Frais & paiements",
        description: "Un Service de paiement centralisé qu'utilise chaque module facturable — aucun module n'implémente sa propre logique de paiement.",
        blocks: P(
            { k: "p", text: "Scolarité, transport, examens, cantine et toute autre activité facturable passent par un seul Service de paiement. Il prend en charge plusieurs fournisseurs derrière un flux métier unique, avec confirmation idempotente, webhooks signés, reçus et une piste d'audit complète." },
            { k: "h2", text: "Moyens de paiement" },
            { k: "table", headers: ["Moyen", "Prend en charge"], rows: [
                ["Stripe", "Cartes, Apple Pay, Google Pay, page de paiement hébergée, abonnements, remboursements, webhooks"],
                ["CinetPay", "Mobile Money (Orange, MTN), Wave, paiements bancaires & carte, QR, remboursements"],
                ["Djamo", "Cartes virtuelles & physiques, paiements par portefeuille, synchronisation des statuts"],
                ["Espèces", "Enregistrement manuel par un caissier ou un administrateur, avec génération de reçu"],
            ]},
            { k: "callout", tone: "tip", text: "Les établissements activent ou désactivent des passerelles spécifiques. Chaque paiement confirmé met à jour le module correspondant automatiquement et garde les rapports financiers synchronisés." },
        ),
    },

    "cash-payments": {
        slug: "cash-payments", label: "Paiements en espèces & crédits IA", breadcrumb: "Fonctionnalités / Finance",
        title: "Paiements en espèces & crédits IA",
        description: "Enregistrez les paiements en espèces des frais scolaires et des crédits IA avec une traçabilité complète — pour les élèves, le personnel et des établissements entiers.",
        blocks: P(
            { k: "h2", text: "Paiement en espèces des frais scolaires" },
            { k: "p", text: "Les élèves peuvent régler tout type de frais en espèces : inscription, scolarité, examens, activités, transport, cantine et plus. Lorsqu'un élève paie en espèces, l'Administrateur d'établissement :" },
            { k: "ol", items: [
                "sélectionne l'élève,",
                "choisit le type de frais,",
                "saisit le montant payé,",
                "règle le moyen sur **Espèces** et valide,",
                "le compte de l'élève se met à jour automatiquement et le paiement apparaît dans sa liste de paiements.",
            ]},
            { k: "p", text: "Chaque paiement enregistre le nom de l'élève, le type de frais, le montant, la date, le moyen, le statut, l'administrateur qui a validé, et une note ou référence interne facultative." },
            { k: "h2", text: "Paiement en espèces des crédits IA" },
            { k: "p", text: "Les élèves, enseignants, personnels et administrateurs peuvent acheter des crédits IA pour utiliser l'agent IA. Pour un achat en espèces, le Super Admin ouvre **Gestion des crédits IA**, trouve l'utilisateur (organisé par rôle), choisit une offre de crédits, règle le moyen sur Espèces, valide, et les crédits sont ajoutés au compte de l'utilisateur et journalisés dans l'historique d'achats/octrois." },
            { k: "h2", text: "Crédits pour un établissement entier" },
            { k: "p", text: "Un Administrateur d'établissement peut payer en espèces un pack destiné à tout l'établissement. Le Super Admin sélectionne l'établissement, l'offre et Espèces, valide — et les crédits arrivent dans le solde global de l'établissement, que l'Administrateur d'établissement distribue ensuite aux utilisateurs autorisés." },
            { k: "h2", text: "Moyens pris en charge" },
            { k: "ul", items: [
                "**Espèces** — validé manuellement par le Super Admin ou un administrateur autorisé.",
                "**Gratuit** — le Super Admin peut octroyer des crédits gratuitement, avec une note expliquant la raison (promotion, geste, test, bonus).",
                "**En ligne** — Stripe, Djamo et CinetPay ajoutent les crédits automatiquement une fois le paiement confirmé.",
            ]},
            { k: "h2", text: "Historique & traçabilité" },
            { k: "p", text: "Le système conserve un historique complet des paiements de frais, achats de crédits, recharges manuelles, octrois gratuits, consommation et distributions établissement→utilisateur. Chaque opération enregistre l'utilisateur, l'établissement (le cas échéant), le montant, les crédits, le moyen, le statut, la date, le validateur, la référence de transaction et un commentaire facultatif." },
            { k: "callout", tone: "note", title: "Permissions", items: [
                "**Super Admin** — voit tous les utilisateurs et établissements, crée les offres de crédits, valide les paiements en espèces, octroie des crédits gratuits, recharge n'importe quel compte, lit tout l'historique.",
                "**Administrateur d'établissement** — gère les paiements en espèces de frais pour ses élèves, voit le solde IA de son établissement et distribue les crédits aux utilisateurs autorisés.",
                "**Utilisateur** — voit son propre solde, son historique d'achats et de consommation, et achète des crédits si c'est activé.",
            ]},
        ),
    },

    payroll: {
        slug: "payroll", label: "Paie", breadcrumb: "Fonctionnalités / Finance",
        title: "Paie",
        description: "Un véritable système de paie sous Finance : profils de salaire, un moteur de calcul extensible par pays, bulletins de paie et libre-service.",
        blocks: P(
            { k: "h2", text: "Profils de salaire" },
            { k: "p", text: "Chaque employé (personnel ou enseignant) a un profil de salaire : type d'employé (permanent, contractuel, temporaire, consultant), type de rémunération (horaire, journalier, hebdomadaire, mensuel), taux de base, devise, et taux de cotisations & d'imposition." },
            { k: "h2", text: "Générer des bulletins de paie" },
            { k: "p", text: "Générez un bulletin de paie pour une période avec des lignes détaillées (indemnités, primes, heures supplémentaires, retenues, avances). Le moteur calcule le détail complet — base, brut, cotisations sociales, base imposable, impôt sur le revenu, retenues et net — et est extensible par pays." },
            { k: "h2", text: "Approuver, payer & libre-service" },
            { k: "ul", items: [
                "Les administrateurs/comptables approuvent et paient les bulletins (virement bancaire, espèces, Stripe, CinetPay, Djamo).",
                "Les employés et les enseignants ne voient que leurs propres bulletins sous **Finance → Mes bulletins**, avec une vue prête à imprimer.",
            ]},
        ),
    },

    "transport-overview": {
        slug: "transport-overview", label: "Vue d'ensemble", breadcrumb: "Fonctionnalités / Transport intelligent",
        title: "Transport intelligent — vue d'ensemble",
        description: "Le transport scolaire intégré à TeducAI comme un module pleinement intégré — une connexion, une base de données, une source de vérité.",
        blocks: P(
            { k: "p", text: "Plutôt qu'une autre application avec sa propre connexion et sa propre base, le Transport intelligent consomme les données partagées de la plateforme : élèves depuis le SIS, calendrier académique, emploi du temps, parents, finance et assiduité. Cela supprime les données dupliquées et crée une source de vérité unique." },
            { k: "h2", text: "Données de référence partagées" },
            { k: "table", headers: ["Lit depuis", "Pour produire"], rows: [
                ["Élèves", "Affectations de transport"],
                ["Classes & emploi du temps", "Horaires de ramassage & calcul de l'heure d'arrivée"],
                ["Calendrier académique", "Calendrier des bus"],
                ["Parents", "Notifications"],
                ["Finance", "Frais de transport sur la facture mensuelle"],
                ["Assiduité", "Assiduité d'embarquement réconciliée avec l'assiduité scolaire"],
            ]},
            { k: "h2", text: "Multi-établissements" },
            { k: "p", text: "Une même société de transport peut servir plusieurs établissements : chaque établissement ne voit que ses propres élèves, tandis que la société gère tous les contrats, flottes, chauffeurs et trajets depuis un tableau de bord centralisé." },
            { k: "callout", tone: "tip", text: "Voir [Flotte, chauffeurs & trajets](/docs/transport-fleet) et [Embarquement, GPS & sécurité](/docs/transport-boarding) pour le détail opérationnel." },
        ),
    },

    "transport-fleet": {
        slug: "transport-fleet", label: "Flotte, chauffeurs & trajets", breadcrumb: "Fonctionnalités / Transport intelligent",
        title: "Flotte, chauffeurs & trajets",
        description: "Véhicules, chauffeurs, trajets, arrêts et optimisation IA des itinéraires.",
        blocks: P(
            { k: "h2", text: "Gestion de la flotte" },
            { k: "p", text: "Gérez bus, minibus, fourgons, motos, bateaux et bus électriques, chacun avec immatriculation, assurance, entretien, kilométrage, carburant et documents." },
            { k: "h2", text: "Chauffeurs & personnel" },
            { k: "p", text: "Les profils des chauffeurs contiennent le permis & son expiration, les certificats, les vérifications d'antécédents, les dossiers médicaux et la disponibilité. Le personnel de transport comprend contrôleurs, assistants, superviseurs et inspecteurs." },
            { k: "h2", text: "Trajets & arrêts" },
            { k: "ul", items: [
                "Trajets illimités, chacun avec distance, durée estimée, tracé GPS, un bus et un chauffeur assignés.",
                "Chaque arrêt de bus enregistre des coordonnées GPS, une adresse, un rayon, les élèves assignés et l'heure d'arrivée.",
                "Les élèves se voient assigner un trajet, un bus, une place, des arrêts de montée et de descente et un horaire.",
            ]},
            { k: "h2", text: "Optimiseur IA d'itinéraires" },
            { k: "p", text: "L'IA optimise les itinéraires en fonction du carburant, de la distance, du trafic, de la météo et des routes fermées, et peut régénérer les itinéraires chaque matin. Les frais de transport alimentent la Finance comme une catégorie de frais supplémentaire." },
        ),
    },

    "transport-boarding": {
        slug: "transport-boarding", label: "Embarquement, GPS & sécurité", breadcrumb: "Fonctionnalités / Transport intelligent",
        title: "Embarquement, GPS & sécurité",
        description: "Assiduité d'embarquement, suivi GPS en direct, surveillance de sécurité par IA et notifications.",
        blocks: P(
            { k: "h2", text: "Assiduité d'embarquement" },
            { k: "p", text: "Les élèves montent via QR code, RFID ou reconnaissance faciale ; l'assiduité est enregistrée et les parents sont notifiés. L'assiduité d'embarquement se réconcilie avec l'assiduité scolaire." },
            { k: "h2", text: "Surveillance de sécurité par IA" },
            { k: "p", text: "L'IA détecte un élève manquant, dans le mauvais bus, qui n'est jamais monté, qui est parti tôt, ou un passager non autorisé — et alerte les parents immédiatement. Elle peut aussi signaler « monté dans le bus mais jamais entré à l'école »." },
            { k: "h2", text: "GPS & notifications" },
            { k: "ul", items: [
                "Chaque véhicule diffuse sa position GPS vers le tableau de bord et l'application parent pour un suivi en direct et une ETA.",
                "Notifications automatiques : bus qui arrive, en retard, élève monté/déposé, chauffeur ou trajet modifié, urgence.",
                "Canaux : push, SMS, e-mail et WhatsApp.",
            ]},
            { k: "h2", text: "Analytique" },
            { k: "p", text: "Les indicateurs incluent véhicules, élèves transportés, taux d'occupation moyen, coût de carburant et d'entretien, efficacité des itinéraires, performance des chauffeurs, arrivées tardives, incidents de sécurité, revenus et dépenses." },
            { k: "callout", tone: "warn", text: "Le push GPS en temps réel (MQTT/WebSocket), la reconnaissance faciale et les applications mobiles natives sont des éléments de la feuille de route qui nécessitent une infrastructure supplémentaire." },
        ),
    },

    announcements: {
        slug: "announcements", label: "Annonces", breadcrumb: "Fonctionnalités / Communication & RH",
        title: "Annonces",
        description: "Publiez des annonces à la communauté scolaire avec ciblage de l'audience, marquage d'urgence et planification.",
        blocks: P(
            { k: "ol", items: [
                "Rédigez un titre et un message et choisissez l'audience (tout le monde, enseignants, élèves ou parents).",
                "Marquez-la éventuellement comme une urgence et planifiez une date de publication.",
                "Créez-la comme brouillon ou élément planifié, puis Publiez pour diffuser via la couche de notifications.",
            ]},
            { k: "p", text: "Suivez le statut de chaque annonce (brouillon, planifiée, publiée) dans la liste." },
        ),
    },

    leave: {
        slug: "leave", label: "Gestion des congés", breadcrumb: "Fonctionnalités / Communication & RH",
        title: "Gestion des congés",
        description: "Demandes de congé en libre-service avec approbation par l'administrateur.",
        blocks: P(
            { k: "ol", items: [
                "Tout employé ou enseignant soumet une demande : type (annuel, maladie, sans solde, maternité/paternité, autre), dates de début et de fin, et un motif facultatif.",
                "Les administrateurs voient toutes les demandes de l'établissement et les approuvent ou refusent ; les autres membres ne voient que les leurs.",
                "Le demandeur est notifié ; le statut devient Approuvé ou Refusé et la décision est historisée.",
            ]},
            { k: "callout", tone: "note", text: "La date de fin ne peut pas précéder la date de début, et seuls les administrateurs peuvent décider d'une demande." },
        ),
    },

    "multi-tenant": {
        slug: "multi-tenant", label: "Établissements & contexte", breadcrumb: "Administration / Plateforme & administration",
        title: "Établissements & contexte",
        description: "Architecture multi-établissements et contexte de travail actif qui cloisonne tout ce que vous faites.",
        blocks: P(
            { k: "h2", text: "Le contexte de travail" },
            { k: "p", text: "Chaque session a un contexte actif : organisation → établissement → modèle d'établissement → année académique. Toutes les lectures et écritures y sont cloisonnées. Le sélecteur de la barre supérieure permet de changer de contexte, et les utilisateurs ne voient que les établissements auxquels ils sont rattachés (adhésions + leur établissement d'origine)." },
            { k: "h2", text: "Isolation" },
            { k: "ul", items: [
                "Isolation stricte des données entre établissements — chaque requête est cloisonnée par établissement.",
                "Les enseignants, élèves et parents sélectionnent l'établissement, le modèle et l'année, et ne voient que les établissements où ils ont enseigné / qu'ils ont fréquentés.",
            ]},
        ),
    },

    "roles-permissions": {
        slug: "roles-permissions", label: "Rôles & permissions", breadcrumb: "Administration / Plateforme & administration",
        title: "Rôles & permissions",
        description: "Contrôle d'accès basé sur les rôles avec des tableaux de bord adaptés à chaque rôle.",
        blocks: P(
            { k: "p", text: "Les enseignants, élèves et parents ne voient jamais les menus d'administration (Gestion, Administration académique, Finance, Opérations, Système) — ceux-ci sont réservés au Super Admin et à l'Administrateur d'établissement. Chaque rôle restreint dispose de sa propre barre latérale :" },
            { k: "ul", items: [
                "**Enseignant** — cours, classes, matières, notes, documents, bibliothèque, portail et outils de génération IA.",
                "**Élève** — emploi du temps, notes, documents, bibliothèque, stages, paiements, portail.",
                "**Parent** — liste chaque enfant, bascule de l'un à l'autre et consulte le dossier complet de l'enfant (notes, documents, paiements, bulletins, certificats).",
            ]},
            { k: "callout", tone: "tip", text: "Les écritures sont protégées par rôle côté serveur, de sorte que masquer un menu relève de la défense en profondeur et non du seul contrôle." },
        ),
    },

    personnel: {
        slug: "personnel", label: "Personnel de l'établissement", breadcrumb: "Administration / Plateforme & administration",
        title: "Personnel de l'établissement",
        description: "Créez et gérez les comptes du personnel ; les affectations sont historisées à travers les établissements.",
        blocks: P(
            { k: "p", text: "Sous **Gestion → Personnel de l'établissement**, créez un compte de personnel avec informations personnelles, rôle principal, rôles supplémentaires, département, fonction et statut. La création provisionne automatiquement le compte utilisateur et affiche un mot de passe temporaire à usage unique." },
            { k: "h2", text: "Historique multi-établissements" },
            { k: "p", text: "Un membre du personnel peut travailler dans plusieurs établissements. Chaque affectation est historisée (rôle, dates, statut) ; un Administrateur d'établissement affecte au sein de son propre établissement et le Super Admin partout. La suppression d'un membre du personnel désactive le compte sans le détruire." },
        ),
    },

    "help-center": {
        slug: "help-center", label: "Centre d'aide intégré", breadcrumb: "Administration / Plateforme & administration",
        title: "Centre d'aide intégré",
        description: "Aide contextuelle : le bouton Aide ouvre la documentation de la page courante.",
        blocks: P(
            { k: "p", text: "Chaque page du tableau de bord a un bouton Aide qui ouvre le Centre d'aide intégré déroulé jusqu'à la section correspondante — aucune recherche requise. Chaque fonctionnalité documentée présente son objectif, un guide pas à pas, les champs clés (avec valeur attendue et validation) et le résultat attendu." },
            { k: "callout", tone: "note", text: "Les nouveaux modules sont ajoutés au Centre d'aide au fil de leur mise en service, et le cadre est adapté à la langue." },
        ),
    },

    "api-webhooks": {
        slug: "api-webhooks", label: "API & webhooks", breadcrumb: "Ressources / Développeurs",
        title: "API & webhooks",
        description: "Une API REST documentée et des webhooks sortants pour que des applications tierces lisent les données de TeducAI et réagissent aux événements de la plateforme.",
        blocks: P(
            { k: "p", text: "TeducAI expose une API REST (FastAPI, décrite dans le schéma OpenAPI à `/docs` sur le serveur d'API). En interne, les modules partagent les données de référence via des endpoints cloisonnés par établissement et bien définis ; en externe, les partenaires utilisent l'**API publique v1** ci-dessous. Le Service de paiement traite aussi des webhooks signés et idempotents provenant de fournisseurs de paiement externes." },
            { k: "h2", text: "Authentification" },
            { k: "p", text: "L'accès tiers utilise des **clés API d'établissement**, gérées par un Administrateur d'établissement sous **Système → API & Intégrations**. Une clé n'est affichée qu'une fois à la création (seul son hachage est stocké) et peut être révoquée à tout moment. Envoyez-la à chaque requête :" },
            { k: "code", code: "GET /api/v1/students?limit=50&offset=0\nHost: api.teducai.example\nX-API-Key: tk_xxxxxxxxxxxxxxxxxxxx" },
            { k: "callout", tone: "note", text: "Chaque clé est cloisonnée à un seul établissement. Un partenaire ne pourra jamais lire que les données de cet établissement — l'isolation est imposée côté serveur, et `last_used_at` est suivi par clé." },
            { k: "h2", text: "Endpoints de l'API publique v1" },
            { k: "p", text: "En lecture seule, paginés avec `limit` (max 200) et `offset` :" },
            { k: "table", headers: ["Endpoint", "Renvoie"], rows: [
                ["`GET /api/v1/me`", "Le nom, le préfixe et le périmètre (établissement) de la clé appelante"],
                ["`GET /api/v1/students`", "Les élèves avec matricule, sexe, classe et statut"],
                ["`GET /api/v1/teachers`", "Enseignants, formateurs et instructeurs"],
                ["`GET /api/v1/classes`", "Les classes avec leur niveau"],
                ["`GET /api/v1/subjects`", "Les matières avec leur coefficient"],
                ["`GET /api/v1/announcements`", "Les annonces publiées (le flux de communication externe)"],
            ]},
            { k: "h2", text: "Webhooks sortants" },
            { k: "p", text: "Enregistrez des URL d'endpoint sous **Système → API & Intégrations** pour recevoir les événements de la plateforme. Chaque endpoint peut s'abonner à des types d'événements spécifiques, ou à tout en laissant la liste vide ; un secret facultatif est stocké pour la signature HMAC par l'émetteur de livraison. Chaque événement est mis en file comme une livraison avec un suivi de reprise (tentatives, tentatives max, prochaine reprise), visible et rejouable manuellement depuis la même page." },
            { k: "h3", text: "Types d'événements" },
            { k: "table", headers: ["Événement", "Se déclenche quand", "Points clés du payload"], rows: [
                ["`announcement.published`", "Une annonce est publiée à la communauté", "`announcement_id`, `title`, `audience`, `is_emergency`"],
                ["`leave.decided`", "Une demande de congé est approuvée ou refusée", "`leave_request_id`, `staff_user_id`, `leave_type`, `status`"],
                ["`payslip.paid`", "Un bulletin de paie est marqué payé", "`payroll_record_id`, `staff_user_id`, `period`, `net_amount`, `method`"],
            ]},
            { k: "callout", tone: "tip", text: "Tout module peut publier des événements supplémentaires via le service partagé `emit_event` — d'autres types d'événements seront ajoutés à mesure que les modules l'adoptent." },
            { k: "callout", tone: "warn", text: "Le worker de livraison HTTP asynchrone (qui poste les livraisons en file vers votre URL et applique le calendrier de reprise) est un composant d'exécution de la feuille de route, aux côtés de GraphQL, d'une marketplace et d'un SDK. Les livraisons sont aujourd'hui mises en file, listables et rejouables." },
        ),
    },

    extensibility: {
        slug: "extensibility", label: "Extensibilité", breadcrumb: "Ressources / Développeurs",
        title: "Extensibilité",
        description: "Comment TeducAI est conçu pour s'étendre — fournisseurs IA enfichables, feature flags et services modulaires.",
        blocks: P(
            { k: "ul", items: [
                "**IA enfichable** — le routeur LLM permet de remplacer ou d'ajouter des fournisseurs de modèles sans toucher aux appelants.",
                "**Feature flags** — activez modules et capacités par établissement.",
                "**Services modulaires** — des services déployables indépendamment (par ex. transport, paiements) réutilisent l'identité et les données partagées.",
                "**Moteurs extensibles par pays** — les règles de paie et d'emploi du temps sont configurables, pas codées en dur.",
            ]},
        ),
    },
}
