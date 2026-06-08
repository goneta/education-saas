"use client"

import { useEffect, useMemo, useState } from "react"
import { useSearchParams } from "next/navigation"
import type { ComponentType } from "react"
import { BookOpen, BriefcaseBusiness, CheckCircle2, CircleHelp, CreditCard, FileText, GraduationCap, MessageSquareText, Search, Settings, Users, Wand2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type HelpField = {
    name: string
    type: string
    expected: string
    validation: string
}

type HelpSection = {
    id: string
    title: string
    icon: ComponentType<{ className?: string }>
    purpose: string
    steps: string[]
    fields: HelpField[]
    result: string
}

const HELP_SECTIONS: HelpSection[] = [
    {
        id: "dashboard",
        title: "Tableau de bord",
        icon: BookOpen,
        purpose: "Donner une vue rapide sur l'activité de l'établissement: élèves, classes, activités récentes, alertes et indicateurs clés.",
        steps: [
            "Vérifiez le nom de l'établissement en haut de page pour confirmer le bon contexte.",
            "Utilisez la recherche globale pour retrouver rapidement un élève, une classe, un module ou une opération.",
            "Ouvrez les cartes de synthèse pour contrôler les volumes et repérer les actions urgentes.",
        ],
        fields: [
            { name: "Recherche", type: "Texte", expected: "Nom, matricule, module ou mot-clé.", validation: "Saisir au moins deux caractères pour une recherche utile." },
            { name: "Langue", type: "Liste", expected: "Français, anglais, espagnol ou swahili.", validation: "La sélection change les libellés de l'interface." },
        ],
        result: "L'administrateur visualise immédiatement l'état général de l'établissement et accède aux modules adaptés à son rôle.",
    },
    {
        id: "students",
        title: "Élèves, parents et fiches scolaires",
        icon: Users,
        purpose: "Créer et suivre les fiches élèves avec identité, classe, parent/tuteur, statut et documents.",
        steps: [
            "Ouvrez Scolarité ou Élèves, puis cliquez sur Ajouter un élève.",
            "Renseignez l'identité de l'élève, son matricule, sa classe et les informations du parent/tuteur.",
            "Ajoutez les documents d'inscription et vérifiez les champs obligatoires.",
            "Cliquez sur Enregistrer pour créer la fiche et la rendre visible dans les listes, rapports et portails.",
        ],
        fields: [
            { name: "Nom complet", type: "Texte", expected: "Nom et prénoms officiels de l'élève.", validation: "Champ obligatoire, éviter les abréviations." },
            { name: "Matricule", type: "Texte unique", expected: "Identifiant scolaire, par exemple MAT-2026-001.", validation: "Doit être unique dans l'établissement." },
            { name: "Classe", type: "Liste ou ID", expected: "Classe actuelle de l'élève.", validation: "La classe doit exister dans l'établissement actif." },
            { name: "Parent/tuteur", type: "Texte + téléphone", expected: "Nom, relation et contact international.", validation: "Le téléphone doit respecter le pays configuré." },
            { name: "Statut", type: "Liste", expected: "Affecté ou non affecté.", validation: "Le statut pilote les listes de classe et les rapports." },
        ],
        result: "La fiche élève est créée, consultable, imprimable et utilisable par la scolarité, la finance, les parents et l'Agent IA selon permissions.",
    },
    {
        id: "teachers",
        title: "Gestion des enseignants",
        icon: GraduationCap,
        purpose: "Créer et maintenir les dossiers enseignants, formateurs et intervenants avec leurs informations de contact, affectations, matières, documents et rôles.",
        steps: [
            "Ouvrez Gestion puis Professeurs dans la barre latérale.",
            "Cliquez sur Ajouter un enseignant ou sélectionnez une ligne existante.",
            "Renseignez l'identité, l'adresse email, le téléphone, les matières enseignées et les affectations de classe.",
            "Ajoutez les documents utiles si le module le demande: contrat, diplôme, pièce d'identité ou autorisation.",
            "Cliquez sur Enregistrer pour rendre l'enseignant disponible dans les emplois du temps, notes, devoirs et communications.",
        ],
        fields: [
            { name: "Nom complet", type: "Texte obligatoire", expected: "Nom et prénoms officiels de l'enseignant.", validation: "Utilisé dans les emplois du temps, bulletins et rapports." },
            { name: "Email", type: "Adresse email", expected: "Adresse professionnelle ou personnelle valide.", validation: "Sert à la connexion et aux notifications." },
            { name: "Téléphone", type: "Numéro international", expected: "Numéro avec indicatif pays.", validation: "Doit respecter le format téléphonique configuré." },
            { name: "Matières / spécialités", type: "Liste", expected: "Matières, UE ou domaines d'enseignement.", validation: "Utilisé pour les affectations et la génération d'emplois du temps." },
            { name: "Statut", type: "Liste", expected: "Actif, suspendu, vacataire, permanent ou autre statut configuré.", validation: "Contrôle l'accès au portail enseignant." },
        ],
        result: "Le dossier enseignant est disponible pour la scolarité, les emplois du temps, les notes, les devoirs, les documents et les notifications selon permissions.",
    },
    {
        id: "timetable",
        title: "Création et génération des emplois du temps",
        icon: Wand2,
        purpose: "Créer, générer, modifier, verrouiller, publier et exporter les emplois du temps de classes, professeurs, salles et élèves.",
        steps: [
            "Configurez d'abord les classes, matières, professeurs et salles disponibles.",
            "Dans Emplois du temps, choisissez une génération complète ou partielle.",
            "Définissez le périmètre: classe, niveau, professeur ou matières sélectionnées.",
            "Renseignez les salles, horaires autorisés et durée maximale d'un cours.",
            "Cliquez sur Générer les emplois du temps.",
            "Contrôlez les conflits affichés: salle, professeur, classe, horaire ou règle pédagogique.",
            "Modifiez manuellement un cours si nécessaire: horaire, classe, salle, professeur, matière ou verrouillage.",
            "Cliquez sur Publier pour rendre l'emploi du temps visible aux professeurs, élèves et parents.",
        ],
        fields: [
            { name: "Mode", type: "Liste", expected: "Régénération complète ou partielle.", validation: "La complète supprime les cours non verrouillés du périmètre." },
            { name: "Périmètre", type: "Liste", expected: "Classe, niveau, professeur ou matière.", validation: "Utilisé pour limiter la génération." },
            { name: "Salles disponibles", type: "Texte séparé par virgules", expected: "Salle 1, Salle 2, Laboratoire 1.", validation: "Chaque valeur devient une salle utilisable." },
            { name: "Horaires autorisés", type: "Heure", expected: "Début et fin, par exemple 07:00 à 19:00.", validation: "Les cours hors plage déclenchent un avertissement." },
            { name: "Durée maximale", type: "Nombre", expected: "Durée en minutes, par exemple 180.", validation: "Les dépassements sont signalés avant publication." },
            { name: "Verrouillage", type: "Case à cocher", expected: "Cours à préserver lors d'une régénération.", validation: "Un cours verrouillé n'est pas modifié par le moteur automatique." },
        ],
        result: "Les emplois du temps validés sont publiés dans les dashboards professeurs, élèves et parents, avec notifications et exports PDF/CSV/Excel.",
    },
    {
        id: "finance",
        title: "Finance, frais, paiements et caisse",
        icon: CreditCard,
        purpose: "Paramétrer les frais, enregistrer les paiements, produire les reçus, suivre les impayés et clôturer la caisse.",
        steps: [
            "Dans Paramètres financiers, créez les rubriques de frais: inscription, scolarité, assurance, transport, cantine, annexes.",
            "Indiquez le montant, l'année académique, le niveau ou la classe concernée.",
            "Dans Frais/Paiements, sélectionnez l'élève ou le frais à payer.",
            "Renseignez le montant encaissé et validez.",
            "Contrôlez le solde restant, le reçu généré et le journal de caisse.",
            "En fin de journée, ouvrez Journal de caisse, saisissez la caisse comptée et soumettez la clôture.",
        ],
        fields: [
            { name: "Nom de rubrique", type: "Texte", expected: "Libellé officiel du frais.", validation: "Obligatoire pour factures et reçus." },
            { name: "Montant", type: "Nombre", expected: "Montant positif dans la devise de l'établissement.", validation: "Ne pas utiliser de lettres ou symboles." },
            { name: "Date d'échéance", type: "Date", expected: "Date limite de paiement.", validation: "Utilisée pour retards et impayés." },
            { name: "Montant payé", type: "Nombre", expected: "Somme réellement encaissée.", validation: "Paiement partiel autorisé selon le solde." },
            { name: "Caisse comptée", type: "Nombre", expected: "Montant physique compté en fin de journée.", validation: "Comparé au total système." },
        ],
        result: "La facture, le paiement, le reçu, le solde, le journal de caisse, les rapports et les notifications sont mis à jour automatiquement.",
    },
    {
        id: "ai",
        title: "Agent IA",
        icon: MessageSquareText,
        purpose: "Aider chaque utilisateur selon son rôle: assistance pédagogique, recherche, rapports, explications et actions autorisées.",
        steps: [
            "Ouvrez le panneau Agent IA à gauche du dashboard.",
            "Posez une question claire: élève, paiement, absence, rapport, cours, devoir ou procédure.",
            "L'Agent IA vérifie votre rôle et vos permissions avant de répondre ou d'agir.",
            "Si une action est interdite, l'Agent IA explique le refus et invite à contacter l'administrateur.",
        ],
        fields: [
            { name: "Message", type: "Texte libre", expected: "Question ou instruction précise.", validation: "Ne demandez que les données que votre rôle peut consulter." },
            { name: "Pièce jointe", type: "Fichier", expected: "Document utile au contexte si autorisé.", validation: "Type et taille contrôlés par la sécurité fichier." },
            { name: "Micro", type: "Audio", expected: "Dictée ou question vocale si disponible.", validation: "Le texte reconnu suit les mêmes permissions." },
        ],
        result: "L'Agent IA fournit une réponse contextualisée et journalise les actions ou refus sensibles dans l'audit.",
    },
    {
        id: "documents",
        title: "Partage de documents",
        icon: FileText,
        purpose: "Centraliser les documents de l'etablissement et permettre le partage securise entre etablissements, utilisateurs internes, parents, eleves, etudiants et personnels autorises.",
        steps: [
            "Ouvrez Scolarite puis Documents depuis la barre laterale du Dashboard.",
            "Dans Ajouter un document, saisissez un nom clair et obligatoire pour le document.",
            "Choisissez une categorie afin de faciliter les recherches: scolarite, finance, RH, administratif, pedagogie ou autre.",
            "Choisissez la visibilite: prive, public interne ou public externe selon le niveau d'acces souhaite.",
            "Ajoutez le fichier autorise puis cliquez sur Enregistrer.",
            "Pour partager, cliquez sur l'action Partager du document concerne.",
            "Choisissez le type de partage: B2B entre etablissements, B2P de l'etablissement vers ses utilisateurs, ou P2P entre utilisateurs autorises.",
            "Recherchez les destinataires par nom, email, NumRef, role, niveau ou classe selon le cas.",
            "Selectionnez les destinataires, definissez une expiration ou une limite de telechargement si necessaire, puis envoyez le partage.",
            "Les destinataires autorises retrouvent ensuite le document dans leur espace, avec les droits de consultation ou de telechargement prevus.",
        ],
        fields: [
            { name: "Nom du document", type: "Texte obligatoire", expected: "Nom lisible du document, par exemple Certificat de scolarite 2026.", validation: "Utilise pour nommer le fichier selon la convention NomDocument_userID.ext." },
            { name: "Categorie", type: "Texte ou liste", expected: "Scolarite, finance, RH, administratif, pedagogie, inspection, etc.", validation: "Aide a classer, filtrer et retrouver rapidement les documents." },
            { name: "Visibilite", type: "Liste", expected: "Prive, public interne ou public externe.", validation: "Un document public depose par un eleve ou etudiant peut necessiter une approbation administrative." },
            { name: "Fichier", type: "Upload", expected: "PDF, Word, Excel, CSV, XML ou image.", validation: "Les extensions dangereuses sont bloquees, la taille est limitee et le scan antivirus est applique." },
            { name: "Type de partage", type: "Liste", expected: "B2B, B2P ou P2P.", validation: "Le type disponible depend du role et des permissions de l'utilisateur connecte." },
            { name: "NumRef", type: "Texte unique", expected: "Reference utilisateur, par exemple USR-2026-000123.", validation: "Permet de cibler precisement un destinataire meme si plusieurs utilisateurs portent un nom similaire." },
            { name: "Role", type: "Texte", expected: "teacher, parent, student, cashier, accountant, etc.", validation: "Filtre les destinataires dans le partage B2P ou P2P." },
            { name: "Classe ID / Niveau", type: "Nombre ou texte", expected: "Identifiant de classe ou niveau scolaire.", validation: "Permet de cibler les eleves d'une classe ou d'un niveau precis." },
            { name: "Expiration", type: "Date et heure", expected: "Date limite d'acces au document.", validation: "Apres cette date, le partage n'est plus accessible." },
            { name: "Limite de telechargement", type: "Nombre", expected: "Nombre maximal de telechargements autorises.", validation: "Lorsque la limite est atteinte, le lien de partage devient inutilisable." },
            { name: "Autoriser le repartage", type: "Case a cocher", expected: "Active uniquement si le destinataire peut transmettre le document.", validation: "Le repartage reste soumis aux permissions du role du destinataire." },
        ],
        result: "Le document est stocke dans l'espace de l'etablissement, les partages sont traces, les destinataires recoivent l'acces autorise et chaque consultation ou telechargement sensible est journalise.",
    },
    {
        id: "internships",
        title: "Gestion des stages en entreprise",
        icon: BriefcaseBusiness,
        purpose: "Gerer les entreprises partenaires, affecter les eleves ou etudiants en stage, suivre les presences, valider le carnet, evaluer les competences et produire les documents officiels.",
        steps: [
            "Ouvrez Scolarite puis Stages dans la barre laterale.",
            "Ajoutez d'abord les entreprises partenaires avec leurs coordonnees, responsable RH, capacite d'accueil et informations administratives.",
            "Creez un stage en selectionnant l'entreprise, les stagiaires, le niveau, la filiere, le service, les dates, le superviseur entreprise et le referent ecole.",
            "Pendant le stage, renseignez le suivi quotidien: presence, activites, competences, outils, difficultes et observations.",
            "Demandez aux eleves ou etudiants de tenir leur carnet de stage avec les taches, heures, competences et solutions proposees.",
            "Validez ou corrigez les entrees de carnet, puis saisissez les evaluations entreprise, rapport, soutenance, pratique et note finale.",
            "Ajoutez les documents: convention, assurance, feuille de presence, rapport, presentation, evaluation ou annexes.",
            "En fin de stage, utilisez Generer les documents pour creer les attestations, certificats, fiches d'evaluation et releves lies au stage.",
            "Utilisez l'analyse IA pour obtenir une synthese des carnets et evaluations, puis verifier les recommandations avant validation finale.",
        ],
        fields: [
            { name: "Nom de l'entreprise", type: "Texte obligatoire", expected: "Nom legal de l'entreprise partenaire.", validation: "Utilise dans les conventions, attestations, statistiques et exports." },
            { name: "RCCM / numero fiscal", type: "Texte facultatif", expected: "References administratives de l'entreprise.", validation: "Permet d'identifier officiellement le partenaire." },
            { name: "Adresse / ville / pays / GPS", type: "Texte et nombres", expected: "Localisation complete et coordonnees si disponibles.", validation: "Utilise pour visites, cartes, rapports et exports ministeriels." },
            { name: "Responsable RH", type: "Texte + contact", expected: "Nom, fonction, telephone et email du contact RH.", validation: "Sert aux notifications, conventions et validations." },
            { name: "IDs eleves", type: "Liste numerique", expected: "Un ou plusieurs IDs de profils eleves separes par virgule.", validation: "Chaque ID doit appartenir a l'etablissement actif." },
            { name: "Titre et objectifs", type: "Texte long", expected: "Mission de stage, objectifs pedagogiques et competences attendues.", validation: "Visible dans les documents et le suivi du stage." },
            { name: "Dates et semaines", type: "Date / nombre", expected: "Date debut, date fin et duree en semaines.", validation: "Alimente les attestations, statistiques et controles de planning." },
            { name: "Presence quotidienne", type: "Liste", expected: "Present, absent, retard ou excuse.", validation: "Permet le controle d'assiduite en entreprise." },
            { name: "Carnet de stage", type: "Texte long", expected: "Taches realisees, competences acquises, difficultes, solutions et heures.", validation: "Doit etre valide par le superviseur ou referent autorise." },
            { name: "Note finale", type: "Nombre", expected: "Score final du stage.", validation: "Lorsque la note finale est saisie, le stage peut passer au statut evalue." },
            { name: "Document de stage", type: "Fichier reference", expected: "Convention, assurance, rapport, presentation ou annexe.", validation: "Les fichiers restent soumis a la securite, aux permissions et a l'audit." },
        ],
        result: "Le stage est suivi de bout en bout, les portails des utilisateurs autorises sont mis a jour, les documents sont disponibles, et chaque action sensible est journalisee.",
    },
    {
        id: "settings",
        title: "Paramètres établissement, rôles et permissions",
        icon: Settings,
        purpose: "Configurer l'établissement, les langues, devises, pays, rôles, permissions, utilisateurs et modèles académiques.",
        steps: [
            "Ouvrez Paramètres depuis la sidebar ou le menu utilisateur.",
            "Cliquez sur Modifier dans les informations établissement.",
            "Renseignez le nom, type, pays, devise, langue, adresse, téléphone, logo et coordonnées GPS.",
            "Cliquez sur Enregistrer pour appliquer immédiatement ces informations dans les documents et rapports.",
            "Dans Gestion des rôles, sélectionnez une catégorie de permissions puis cochez les droits nécessaires.",
            "Enregistrez la matrice pour appliquer les restrictions côté interface et API.",
        ],
        fields: [
            { name: "Nom établissement", type: "Texte", expected: "Nom officiel.", validation: "Obligatoire pour documents et exports." },
            { name: "Pays", type: "Liste", expected: "Pays de l'établissement.", validation: "Détermine devise, langue, fuseau horaire et formats." },
            { name: "Latitude / Longitude", type: "Nombre décimal", expected: "Coordonnées GPS.", validation: "Peuvent être saisies ou ajustées sur la carte." },
            { name: "Rôle actif", type: "Liste", expected: "Rôle utilisé dans la session.", validation: "Les permissions associées contrôlent les actions visibles." },
            { name: "Permissions", type: "Cases à cocher", expected: "Voir, créer, modifier, supprimer, exporter, approuver, etc.", validation: "Appliquées au frontend et au backend." },
        ],
        result: "L'établissement, les rôles, les accès et les données de référence sont alignés avec l'organisation réelle.",
    },
    {
        id: "academics",
        title: "Notes, présences, devoirs et pédagogie",
        icon: GraduationCap,
        purpose: "Suivre les évaluations, absences, supports de cours, devoirs, bulletins et rapports pédagogiques.",
        steps: [
            "Créez les classes, matières et périodes académiques.",
            "Ajoutez une évaluation avec date, matière, classe, barème et coefficient.",
            "Saisissez ou importez les notes puis validez.",
            "Pour la présence, sélectionnez la classe ou le cours, marquez présent/absent/retard et enregistrez.",
            "Les bulletins et rapports utilisent les données validées.",
        ],
        fields: [
            { name: "Type d'évaluation", type: "Liste", expected: "Devoir, examen, contrôle, projet.", validation: "Utilisé dans les moyennes et bulletins." },
            { name: "Note", type: "Nombre", expected: "Score obtenu.", validation: "Doit être compris entre 0 et le barème." },
            { name: "Statut présence", type: "Bouton ou liste", expected: "Présent, absent, retard, excusé.", validation: "Une valeur par élève et par séance." },
            { name: "Instructions devoir", type: "Texte long", expected: "Consignes claires pour les élèves.", validation: "Visible dans le portail élève/parent." },
        ],
        result: "Les notes, absences et contenus sont disponibles dans les portails, rapports et documents générés.",
    },
    {
        id: "enterprise",
        title: "Modules avancés: RH, transport, cantine, comptabilité, diplômes",
        icon: CheckCircle2,
        purpose: "Gérer les opérations métier complémentaires selon le type d'établissement et les permissions accordées.",
        steps: [
            "Ouvrez Opérations ou Enterprise Management.",
            "Choisissez le sous-module: admissions, examens, paie, transport, cantine, comptabilité, inspection, diplômes ou notifications.",
            "Renseignez les champs affichés; les IDs demandés correspondent aux enregistrements existants.",
            "Cliquez sur Enregistrer.",
            "Contrôlez la liste créée, le statut, les workflows d'approbation et les exports disponibles.",
        ],
        fields: [
            { name: "Entity ID / Student profile ID", type: "Nombre", expected: "Identifiant numérique d'un dossier ou élève.", validation: "Doit exister dans l'établissement." },
            { name: "Période", type: "Texte ou date", expected: "Mois, année, semestre ou intervalle.", validation: "Utilisée pour paie, rapports et exports." },
            { name: "Montant", type: "Nombre", expected: "Valeur financière positive.", validation: "Alimente comptabilité, caisse ou factures." },
            { name: "Statut", type: "Liste", expected: "Brouillon, en attente, approuvé, payé, publié.", validation: "Détermine la suite du workflow." },
        ],
        result: "Le module crée l'enregistrement, met à jour les tableaux de bord, déclenche les validations et conserve une trace d'audit.",
    },
]

export default function HelpPage() {
    const searchParams = useSearchParams()
    const [query, setQuery] = useState("")
    const [activeId, setActiveId] = useState(HELP_SECTIONS[0].id)
    const [helpMode, setHelpMode] = useState("page")

    useEffect(() => {
        const section = searchParams.get("section")
        if (section && HELP_SECTIONS.some(item => item.id === section)) setActiveId(section)
        setHelpMode(localStorage.getItem("teducai_help_mode") || "page")
    }, [searchParams])

    const updateHelpMode = (mode: string) => {
        setHelpMode(mode)
        localStorage.setItem("teducai_help_mode", mode)
    }

    const filteredSections = useMemo(() => {
        const search = query.trim().toLowerCase()
        if (!search) return HELP_SECTIONS
        return HELP_SECTIONS.filter(section =>
            [section.title, section.purpose, section.result, ...section.steps, ...section.fields.flatMap(field => [field.name, field.expected, field.validation])]
                .join(" ")
                .toLowerCase()
                .includes(search)
        )
    }, [query])

    const activeSection = filteredSections.find(section => section.id === activeId) || filteredSections[0] || HELP_SECTIONS[0]

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                    <h1 className="apple-page-title">Centre d&apos;aide TeducAI</h1>
                    <p className="apple-page-description max-w-3xl">
                        Guide détaillé pour utiliser les sections de l&apos;application, comprendre les champs à remplir,
                        valider les formulaires et anticiper le résultat attendu après chaque enregistrement.
                    </p>
                </div>
                <div className="relative w-full max-w-md">
                    <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6B7280]" />
                    <input
                        value={query}
                        onChange={event => setQuery(event.target.value)}
                        placeholder="Rechercher une aide, un champ ou un module..."
                        className="apple-input pl-11"
                    />
                    <select
                        value={helpMode}
                        onChange={event => updateHelpMode(event.target.value)}
                        className="mt-3 apple-select"
                        title="Choisissez comment le bouton Aide ouvre les explications depuis les pages du Dashboard."
                    >
                        <option value="page">Ouvrir l&apos;aide dans une page</option>
                        <option value="modal">Ouvrir l&apos;aide dans une modale</option>
                        <option value="drawer">Ouvrir l&apos;aide dans un panneau latéral</option>
                    </select>
                </div>
            </div>

            <div className="grid gap-5 xl:grid-cols-[320px_1fr]">
                <Card className="h-fit">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><CircleHelp className="h-5 w-5" /> Sections</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2">
                        {filteredSections.map(section => {
                            const Icon = section.icon
                            return (
                                <button
                                    key={section.id}
                                    type="button"
                                    onClick={() => setActiveId(section.id)}
                                    className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm transition ${activeSection.id === section.id ? "bg-black text-white" : "bg-[#F5F5F7] text-[#111827] hover:bg-[#EDEEF2]"}`}
                                >
                                    <Icon className="h-5 w-5 shrink-0" />
                                    <span className="font-medium">{section.title}</span>
                                </button>
                            )
                        })}
                        {!filteredSections.length && <p className="text-sm text-[#6B7280]">Aucune section trouvée.</p>}
                    </CardContent>
                </Card>

                <div className="space-y-5">
                    <HelpSectionCard section={activeSection} />
                    <Card>
                        <CardHeader><CardTitle>Cycle standard d&apos;un formulaire</CardTitle></CardHeader>
                        <CardContent>
                            <div className="grid gap-3 md:grid-cols-5">
                                {[
                                    ["1", "Lire l'aide du champ", "Survolez le champ pour voir les consignes et formats attendus."],
                                    ["2", "Saisir les données", "Utilisez des valeurs exactes, officielles et vérifiables."],
                                    ["3", "Contrôler les erreurs", "Les champs obligatoires, formats et permissions sont vérifiés."],
                                    ["4", "Enregistrer", "Cliquez sur Enregistrer pour créer ou mettre à jour la donnée."],
                                    ["5", "Vérifier le résultat", "La donnée apparaît dans les listes, rapports, documents, portails ou notifications."],
                                ].map(([step, title, text]) => (
                                    <div key={step} className="rounded-2xl border border-[#E5E7EB] bg-white p-4">
                                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-black text-sm font-semibold text-white">{step}</span>
                                        <p className="mt-3 font-semibold text-[#111827]">{title}</p>
                                        <p className="mt-1 text-sm text-[#6B7280]">{text}</p>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    )
}

function HelpSectionCard({ section }: { section: HelpSection }) {
    const Icon = section.icon
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-3">
                    <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-black text-white"><Icon className="h-5 w-5" /></span>
                    {section.title}
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="rounded-2xl border border-[#E5E7EB] bg-[#F8FAFC] p-4">
                    <p className="text-sm font-semibold text-[#111827]">Objectif</p>
                    <p className="mt-1 text-sm text-[#4B5563]">{section.purpose}</p>
                </div>

                <div>
                    <h2 className="text-lg font-semibold text-[#111827]">Étapes d&apos;utilisation</h2>
                    <ol className="mt-3 space-y-2">
                        {section.steps.map((step, index) => (
                            <li key={step} className="flex gap-3 rounded-xl border border-[#E5E7EB] bg-white p-3 text-sm">
                                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#F5F5F7] text-xs font-semibold">{index + 1}</span>
                                <span>{step}</span>
                            </li>
                        ))}
                    </ol>
                </div>

                <div>
                    <h2 className="text-lg font-semibold text-[#111827]">Champs, types de données et validations</h2>
                    <div className="mt-3 overflow-x-auto rounded-2xl border border-[#E5E7EB]">
                        <table className="w-full min-w-[760px] text-sm">
                            <thead className="bg-[#F8FAFC]">
                                <tr className="border-b">
                                    <th className="px-4 py-3 text-left">Champ</th>
                                    <th className="px-4 py-3 text-left">Type</th>
                                    <th className="px-4 py-3 text-left">Donnée à saisir</th>
                                    <th className="px-4 py-3 text-left">Validation</th>
                                </tr>
                            </thead>
                            <tbody>
                                {section.fields.map(field => (
                                    <tr key={field.name} className="border-b last:border-0">
                                        <td className="px-4 py-3 font-medium text-[#111827]">{field.name}</td>
                                        <td className="px-4 py-3 text-[#4B5563]">{field.type}</td>
                                        <td className="px-4 py-3 text-[#4B5563]">{field.expected}</td>
                                        <td className="px-4 py-3 text-[#4B5563]">{field.validation}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4">
                    <p className="text-sm font-semibold text-emerald-950">Résultat attendu après Enregistrer</p>
                    <p className="mt-1 text-sm text-emerald-900">{section.result}</p>
                </div>
            </CardContent>
        </Card>
    )
}
