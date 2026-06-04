const TRANSLATIONS: Record<string, Record<string, string>> = {
  "AI Agent": { fr: "Agent IA", es: "Agente IA", sw: "Wakala wa IA" },
  Actions: { fr: "Actions", es: "Acciones", sw: "Vitendo" },
  Active: { fr: "Actif", es: "Activo", sw: "Hai" },
  Add: { fr: "Ajouter", es: "Agregar", sw: "Ongeza" },
  "Add Teacher": { fr: "Ajouter un enseignant", es: "Agregar docente", sw: "Ongeza mwalimu" },
  "Add Student": { fr: "Ajouter un eleve", es: "Agregar estudiante", sw: "Ongeza mwanafunzi" },
  Address: { fr: "Adresse", es: "Direccion", sw: "Anwani" },
  Apply: { fr: "Appliquer", es: "Aplicar", sw: "Tumia" },
  Author: { fr: "Auteur", es: "Autor", sw: "Mwandishi" },
  Book: { fr: "Livre", es: "Libro", sw: "Kitabu" },
  "Borrower (Student)": { fr: "Emprunteur (eleve)", es: "Prestatario (estudiante)", sw: "Mkopaji (mwanafunzi)" },
  Cancel: { fr: "Annuler", es: "Cancelar", sw: "Ghairi" },
  Category: { fr: "Categorie", es: "Categoria", sw: "Kategoria" },
  Class: { fr: "Classe", es: "Clase", sw: "Darasa" },
  Close: { fr: "Fermer", es: "Cerrar", sw: "Funga" },
  Date: { fr: "Date", es: "Fecha", sw: "Tarehe" },
  Delete: { fr: "Supprimer", es: "Eliminar", sw: "Futa" },
  "Due Date": { fr: "Date d'echeance", es: "Fecha limite", sw: "Tarehe ya mwisho" },
  Edit: { fr: "Modifier", es: "Editar", sw: "Hariri" },
  Email: { fr: "Email", es: "Correo", sw: "Barua pepe" },
  "Full Name": { fr: "Nom complet", es: "Nombre completo", sw: "Jina kamili" },
  Gender: { fr: "Genre", es: "Genero", sw: "Jinsia" },
  Location: { fr: "Emplacement", es: "Ubicacion", sw: "Mahali" },
  "Location / Shelf": { fr: "Emplacement / rayon", es: "Ubicacion / estante", sw: "Mahali / rafu" },
  Message: { fr: "Message", es: "Mensaje", sw: "Ujumbe" },
  Name: { fr: "Nom", es: "Nombre", sw: "Jina" },
  Notes: { fr: "Notes", es: "Notas", sw: "Maelezo" },
  "Notes (Optional)": { fr: "Notes (facultatif)", es: "Notas (opcional)", sw: "Maelezo (hiari)" },
  Optional: { fr: "Facultatif", es: "Opcional", sw: "Hiari" },
  Password: { fr: "Mot de passe", es: "Contrasena", sw: "Nenosiri" },
  Phone: { fr: "Telephone", es: "Telefono", sw: "Simu" },
  Print: { fr: "Imprimer", es: "Imprimir", sw: "Chapisha" },
  Quantity: { fr: "Quantite", es: "Cantidad", sw: "Idadi" },
  Save: { fr: "Enregistrer", es: "Guardar", sw: "Hifadhi" },
  Search: { fr: "Rechercher", es: "Buscar", sw: "Tafuta" },
  "Select Book": { fr: "Selectionner un livre", es: "Seleccionar libro", sw: "Chagua kitabu" },
  "Select Student": { fr: "Selectionner un eleve", es: "Seleccionar estudiante", sw: "Chagua mwanafunzi" },
  "Select class": { fr: "Selectionner une classe", es: "Seleccionar clase", sw: "Chagua darasa" },
  "Select subject": { fr: "Selectionner une matiere", es: "Seleccionar asignatura", sw: "Chagua somo" },
  "Select term": { fr: "Selectionner une periode", es: "Seleccionar periodo", sw: "Chagua muhula" },
  Status: { fr: "Statut", es: "Estado", sw: "Hali" },
  Student: { fr: "Eleve", es: "Estudiante", sw: "Mwanafunzi" },
  Subject: { fr: "Matiere", es: "Asignatura", sw: "Somo" },
  Teacher: { fr: "Enseignant", es: "Docente", sw: "Mwalimu" },
  Title: { fr: "Titre", es: "Titulo", sw: "Kichwa" },
  Type: { fr: "Type", es: "Tipo", sw: "Aina" },
}

export function currentLocale() {
  if (typeof window === "undefined") return "fr"
  const segment = window.location.pathname.split("/").filter(Boolean)[0]
  return ["fr", "en", "es", "sw"].includes(segment) ? segment : "fr"
}

export function localizeUiText(value: string | undefined | null, locale = currentLocale()) {
  if (!value) return value || ""
  const normalized = value.replace(/\s+\*/g, "").trim()
  const suffix = value.includes("*") ? " *" : ""
  if (locale === "en") return value
  return (TRANSLATIONS[normalized]?.[locale] || value) + (TRANSLATIONS[normalized]?.[locale] ? suffix : "")
}

export function helpForLabel(value: string | undefined | null) {
  const label = (value || "Ce champ").replace(/\s+\*/g, "").trim()
  return `${label}: saisissez une information exacte. Cette donnee est utilisee pour les controles, rapports, documents et actions autorisees selon votre role. Respectez le format indique par le champ.`
}
