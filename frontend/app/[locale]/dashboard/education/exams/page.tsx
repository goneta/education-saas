"use client"

// Scolarité → Examens : sessions d'examens (réutilise la table exam_sessions
// existante, étendue). Types issus du référentiel « Types d'évaluations ».

import { SchoolLifeModulePage, type ModuleConfig } from "@/components/school-life/module-page"

const config: ModuleConfig = {
    slug: "exams",
    title: "Examens",
    subtitle: "Sessions d'examens : planification, salle, durée et barème — types issus du référentiel Types d'évaluations (global + établissement).",
    createLabel: "Nouvel examen",
    typeFilterKey: "exam_type",
    columns: [
        { key: "name", label: "Examen" },
        { key: "exam_type", label: "Type" },
        { key: "class_id", label: "Classe" },
        { key: "subject_id", label: "Matière" },
        { key: "start_date", label: "Début" },
        { key: "status", label: "Statut" },
    ],
    statusOptions: [
        { value: "planned", label: "Planifié" },
        { value: "completed", label: "Terminé" },
        { value: "graded", label: "Noté" },
        { value: "cancelled", label: "Annulé" },
    ],
    fields: [
        { key: "name", label: "Nom de l'examen", type: "text", required: true, placeholder: "ex. BEPC blanc — session 1" },
        { key: "exam_type", label: "Type (référentiel)", type: "reference", refCategory: "evaluation_type", required: true, createHref: "/dashboard/reference-data?category=evaluation_type", createLabel: "Gérer les types", missingMessage: "Aucun type d'évaluation disponible. Ajoutez d'abord un type au référentiel." },
        { key: "class_id", label: "Classe", type: "class", createHref: "/dashboard/education/classes", createLabel: "Créer une classe", missingMessage: "Aucune classe n'existe. Créez d'abord une classe pour organiser un examen." },
        { key: "subject_id", label: "Matière", type: "subject", createHref: "/dashboard/education/subjects", createLabel: "Créer une matière", missingMessage: "Aucune matière n'a encore été créée. Créez d'abord une matière." },
        { key: "start_date", label: "Date de début", type: "date" },
        { key: "end_date", label: "Date de fin", type: "date" },
        { key: "duration_minutes", label: "Durée (minutes)", type: "number", placeholder: "120" },
        { key: "room", label: "Salle", type: "text", placeholder: "ex. Salle A1" },
        { key: "max_score", label: "Barème (/points)", type: "number", placeholder: "20" },
        { key: "coefficient", label: "Coefficient", type: "number", placeholder: "1" },
        { key: "status", label: "Statut", type: "select", options: [
            { value: "planned", label: "Planifié" },
            { value: "completed", label: "Terminé" },
            { value: "graded", label: "Noté" },
            { value: "cancelled", label: "Annulé" },
        ] },
        { key: "notes", label: "Notes", type: "textarea", placeholder: "Consignes, surveillants, matériel autorisé…" },
    ],
}

export default function ExamsPage() {
    return <SchoolLifeModulePage config={config} />
}
