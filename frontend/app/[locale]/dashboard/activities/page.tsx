"use client"

// Gestion → Activités : sorties, clubs, événements de l'établissement.

import { SchoolLifeModulePage, type ModuleConfig } from "@/components/school-life/module-page"

const config: ModuleConfig = {
    slug: "activities",
    title: "Activités",
    subtitle: "Sorties scolaires, clubs, compétitions et événements — types issus du référentiel Types d'activités (global + établissement).",
    createLabel: "Nouvelle activité",
    typeFilterKey: "activity_type_code",
    columns: [
        { key: "name", label: "Activité" },
        { key: "activity_type_code", label: "Type" },
        { key: "location", label: "Lieu" },
        { key: "start_date", label: "Début" },
        { key: "class_id", label: "Classe" },
        { key: "status", label: "Statut" },
    ],
    statusOptions: [
        { value: "planned", label: "Planifiée" },
        { value: "ongoing", label: "En cours" },
        { value: "completed", label: "Terminée" },
        { value: "cancelled", label: "Annulée" },
    ],
    fields: [
        { key: "name", label: "Nom de l'activité", type: "text", required: true, placeholder: "ex. Sortie au musée national" },
        { key: "activity_type_code", label: "Type (référentiel)", type: "reference", refCategory: "activity_type", createHref: "/dashboard/reference-data?category=activity_type", createLabel: "Gérer les types" },
        { key: "location", label: "Lieu", type: "text", placeholder: "ex. Abidjan — Plateau" },
        { key: "start_date", label: "Date de début", type: "date" },
        { key: "end_date", label: "Date de fin", type: "date" },
        { key: "class_id", label: "Classe concernée", type: "class", createHref: "/dashboard/education/classes", createLabel: "Créer une classe", missingMessage: "Aucune classe n'existe encore. Créez une classe pour cibler l'activité (facultatif)." },
        { key: "capacity", label: "Capacité", type: "number", placeholder: "40" },
        { key: "fee_amount", label: "Participation (FCFA)", type: "number", placeholder: "0" },
        { key: "status", label: "Statut", type: "select", options: [
            { value: "planned", label: "Planifiée" },
            { value: "ongoing", label: "En cours" },
            { value: "completed", label: "Terminée" },
            { value: "cancelled", label: "Annulée" },
        ] },
        { key: "description", label: "Description", type: "textarea", placeholder: "Programme, encadrement, transport…" },
    ],
}

export default function ActivitiesPage() {
    return <SchoolLifeModulePage config={config} />
}
