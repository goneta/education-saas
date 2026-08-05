"use client"

// Gestion → Santé scolaire : dossiers médicaux des élèves (visites,
// vaccinations, allergies…). Données sensibles : lecture ET écriture
// réservées à l'administration (contrôlé côté backend).

import { SchoolLifeModulePage, type ModuleConfig } from "@/components/school-life/module-page"

const config: ModuleConfig = {
    slug: "health",
    title: "Santé scolaire",
    subtitle: "Dossiers santé des élèves (visites, vaccinations, allergies, urgences) — données confidentielles réservées à l'administration.",
    createLabel: "Nouveau dossier",
    typeFilterKey: "record_type_code",
    columns: [
        { key: "student_name", label: "Élève" },
        { key: "record_type_code", label: "Type" },
        { key: "title", label: "Titre" },
        { key: "severity", label: "Gravité" },
        { key: "record_date", label: "Date" },
        { key: "status", label: "Statut" },
    ],
    statusOptions: [
        { value: "open", label: "Ouvert" },
        { value: "closed", label: "Clôturé" },
    ],
    fields: [
        { key: "student_id", label: "Élève", type: "student", required: true, createHref: "/dashboard/students", createLabel: "Créer un élève", missingMessage: "Impossible de continuer. Vous devez d'abord créer au moins un élève avant d'ouvrir un dossier santé." },
        { key: "record_type_code", label: "Type (référentiel)", type: "reference", refCategory: "health_record_type", createHref: "/dashboard/reference-data?category=health_record_type", createLabel: "Gérer les types" },
        { key: "title", label: "Titre", type: "text", required: true, placeholder: "ex. Allergie à l'arachide" },
        { key: "severity", label: "Gravité", type: "select", options: [
            { value: "low", label: "Faible" },
            { value: "medium", label: "Moyenne" },
            { value: "high", label: "Élevée" },
        ] },
        { key: "record_date", label: "Date", type: "date" },
        { key: "follow_up_date", label: "Suivi prévu le", type: "date" },
        { key: "treated_by", label: "Pris en charge par", type: "text", placeholder: "ex. Infirmerie / Dr Kouassi" },
        { key: "status", label: "Statut", type: "select", options: [
            { value: "open", label: "Ouvert" },
            { value: "closed", label: "Clôturé" },
        ] },
        { key: "is_confidential", label: "Confidentiel", type: "checkbox", placeholder: "Dossier confidentiel" },
        { key: "details", label: "Détails", type: "textarea", placeholder: "Observations, traitement, consignes…" },
    ],
}

export default function HealthPage() {
    return <SchoolLifeModulePage config={config} />
}
