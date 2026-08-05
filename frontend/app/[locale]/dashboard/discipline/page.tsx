"use client"

// Gestion → Discipline : sanctions, récompenses et incidents des élèves.
// Config-only page — all behavior comes from SchoolLifeModulePage.

import { SchoolLifeModulePage, type ModuleConfig } from "@/components/school-life/module-page"

const config: ModuleConfig = {
    slug: "discipline",
    title: "Discipline",
    subtitle: "Sanctions, récompenses et incidents disciplinaires des élèves — types issus des référentiels globaux TeducAI et de l'établissement.",
    createLabel: "Nouvel enregistrement",
    typeFilterKey: "type_code",
    columns: [
        { key: "student_name", label: "Élève" },
        { key: "record_kind", label: "Nature" },
        { key: "type_code", label: "Type" },
        { key: "title", label: "Titre" },
        { key: "record_date", label: "Date" },
        { key: "status", label: "Statut" },
    ],
    statusOptions: [
        { value: "open", label: "Ouvert" },
        { value: "resolved", label: "Résolu" },
        { value: "cancelled", label: "Annulé" },
    ],
    fields: [
        { key: "student_id", label: "Élève", type: "student", required: true, createHref: "/dashboard/students", createLabel: "Créer un élève", missingMessage: "Impossible de continuer. Vous devez d'abord créer au moins un élève avant d'enregistrer un fait disciplinaire." },
        { key: "record_kind", label: "Nature", type: "select", required: true, options: [
            { value: "sanction", label: "Sanction" },
            { value: "reward", label: "Récompense" },
            { value: "incident", label: "Incident" },
        ] },
        { key: "type_code", label: "Type (référentiel)", type: "reference", refCategory: "sanction_type", createHref: "/dashboard/reference-data?category=sanction_type", createLabel: "Gérer les types" },
        { key: "title", label: "Titre", type: "text", required: true, placeholder: "ex. Avertissement pour retards répétés" },
        { key: "record_date", label: "Date", type: "date" },
        { key: "status", label: "Statut", type: "select", options: [
            { value: "open", label: "Ouvert" },
            { value: "resolved", label: "Résolu" },
            { value: "cancelled", label: "Annulé" },
        ] },
        { key: "description", label: "Description", type: "textarea", placeholder: "Faits, contexte, décision…" },
    ],
}

export default function DisciplinePage() {
    return <SchoolLifeModulePage config={config} />
}
