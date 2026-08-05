"use client"

// Gestion → Internat : affectation des élèves internes aux chambres
// (réutilise les salles du module Bâtiments & Salles — zéro duplication).

import { SchoolLifeModulePage, type ModuleConfig } from "@/components/school-life/module-page"

const config: ModuleConfig = {
    slug: "boarding",
    title: "Internat",
    subtitle: "Affectation des élèves internes aux chambres — les chambres sont les salles du module Bâtiments & Salles.",
    createLabel: "Nouvelle affectation",
    columns: [
        { key: "student_name", label: "Élève" },
        { key: "room_id", label: "Chambre" },
        { key: "start_date", label: "Entrée" },
        { key: "end_date", label: "Sortie" },
        { key: "status", label: "Statut" },
    ],
    statusOptions: [
        { value: "active", label: "Actif" },
        { value: "ended", label: "Terminé" },
        { value: "cancelled", label: "Annulé" },
    ],
    fields: [
        { key: "student_id", label: "Élève", type: "student", required: true, createHref: "/dashboard/students", createLabel: "Créer un élève", missingMessage: "Impossible de continuer. Vous devez d'abord créer au moins un élève avant de l'affecter à l'internat." },
        { key: "room_id", label: "Chambre (salle)", type: "room", createHref: "/dashboard/rooms", createLabel: "Créer une salle", missingMessage: "Aucune salle n'existe. Créez d'abord une salle (chambre) dans Bâtiments & Salles." },
        { key: "start_date", label: "Date d'entrée", type: "date" },
        { key: "end_date", label: "Date de sortie", type: "date" },
        { key: "status", label: "Statut", type: "select", options: [
            { value: "active", label: "Actif" },
            { value: "ended", label: "Terminé" },
            { value: "cancelled", label: "Annulé" },
        ] },
        { key: "notes", label: "Notes", type: "textarea", placeholder: "Régime, consignes, trousseau…" },
    ],
}

export default function BoardingSchoolPage() {
    return <SchoolLifeModulePage config={config} />
}
