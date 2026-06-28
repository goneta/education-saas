"use client"

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react"
import { CheckCircle2, Download, FileText, RefreshCw, Search, Send, ShieldCheck, Trash2, XCircle } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"
import { useAuth } from "@/contexts/auth-context"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"

type SecureFile = {
    id: number
    original_filename: string
    display_name?: string | null
    category?: string | null
    content_type: string
    size_bytes: number
    visibility: string
    is_shareable: boolean
    approval_status: string
    uploaded_by_id: number
    created_at: string
    access_count: number
}

type Recipient = {
    id: number
    type: "user" | "school"
    name: string
    role?: string | null
    school_name?: string | null
    numref?: string | null
    subtitle?: string | null
}

type DocumentShare = {
    id: number
    file_id: number
    share_type: string
    mode: string
    status: string
    recipient_user_id?: number | null
    recipient_school_id?: number | null
    recipient_numref?: string | null
    download_count: number
    download_limit?: number | null
    expires_at?: string | null
    created_at: string
}

const COPY = {
    fr: {
        title: "Partage de documents",
        subtitle: "Partage B2B, B2P et P2P avec NumRef, approbation, audit et controle des acces.",
        upload: "Ajouter un document",
        documentName: "Nom du document",
        documentNameTip: "Nom obligatoire du document. Il sert a generer le fichier selon la convention NomDocument_userID.ext.",
        category: "Categorie",
        categoryTip: "Categorie fonctionnelle du document: scolarite, finance, RH, pedagogie, administratif ou autre.",
        visibility: "Visibilite",
        visibilityTip: "Definit qui peut voir le document: prive, public interne a l'etablissement ou public externe apres approbation.",
        shareable: "Document partageable",
        shareableTip: "Autorise les destinataires disposant du droit de repartage a transmettre ce document a d'autres utilisateurs.",
        file: "Fichier",
        fileTip: "Formats acceptes: PDF, Word, Excel, CSV, XML et images. Les fichiers executables sont bloques et un scan antivirus est applique.",
        save: "Enregistrer",
        refresh: "Actualiser",
        share: "Partager",
        download: "Telecharger",
        approve: "Approuver",
        delete: "Supprimer",
        documents: "Documents",
        recipients: "Destinataires",
        search: "Rechercher",
        numref: "NumRef",
        role: "Role",
        classId: "Classe ID",
        level: "Niveau",
        shareType: "Type de partage",
        mode: "Mode d'acces",
        expiresAt: "Expiration",
        limit: "Limite de telechargement",
        canReshare: "Autoriser le repartage",
        sendShare: "Envoyer le partage",
        selected: "Selectionnes",
        sharedWith: "Partages existants",
        close: "Fermer",
        empty: "Aucun document disponible.",
        noRecipients: "Aucun destinataire trouve.",
        successUpload: "Document enregistre.",
        successShare: "Document partage.",
        successApprove: "Document approuve.",
        successDelete: "Document supprime.",
        error: "Operation impossible. Verifiez vos permissions et les donnees saisies.",
    },
    en: {
        title: "Document sharing",
        subtitle: "B2B, B2P and P2P sharing with NumRef, approval, audit and access control.",
        upload: "Add document",
        documentName: "Document name",
        documentNameTip: "Required document name. It is used to generate the file name with NomDocument_userID.ext.",
        category: "Category",
        categoryTip: "Functional document category: school admin, finance, HR, pedagogy, administration or another area.",
        visibility: "Visibility",
        visibilityTip: "Defines who can view the document: private, internal public or external public after approval.",
        shareable: "Shareable document",
        shareableTip: "Allows recipients with reshare rights to forward this document.",
        file: "File",
        fileTip: "Accepted formats: PDF, Word, Excel, CSV, XML and images. Executables are blocked and antivirus scanning is applied.",
        save: "Save",
        refresh: "Refresh",
        share: "Share",
        download: "Download",
        approve: "Approve",
        delete: "Delete",
        documents: "Documents",
        recipients: "Recipients",
        search: "Search",
        numref: "NumRef",
        role: "Role",
        classId: "Class ID",
        level: "Level",
        shareType: "Share type",
        mode: "Access mode",
        expiresAt: "Expiration",
        limit: "Download limit",
        canReshare: "Allow reshare",
        sendShare: "Send share",
        selected: "Selected",
        sharedWith: "Existing shares",
        close: "Close",
        empty: "No document available.",
        noRecipients: "No recipient found.",
        successUpload: "Document saved.",
        successShare: "Document shared.",
        successApprove: "Document approved.",
        successDelete: "Document deleted.",
        error: "Operation failed. Check your permissions and entered data.",
    },
}

function prettySize(size: number) {
    if (size < 1024) return `${size} o`
    if (size < 1024 * 1024) return `${Math.round(size / 1024)} Ko`
    return `${(size / (1024 * 1024)).toFixed(1)} Mo`
}

export default function DocumentsPage({ params: { locale } }: { params: { locale: string } }) {
    const copy = COPY[locale as keyof typeof COPY] || COPY.fr
    const { token, user } = useAuth()
    const [files, setFiles] = useState<SecureFile[]>([])
    const [recipients, setRecipients] = useState<Recipient[]>([])
    const [shares, setShares] = useState<DocumentShare[]>([])
    const [selectedFile, setSelectedFile] = useState<SecureFile | null>(null)
    const [selectedRecipients, setSelectedRecipients] = useState<Recipient[]>([])
    const [status, setStatus] = useState("")
    const [loading, setLoading] = useState(false)
    const [form, setForm] = useState({
        documentName: "",
        category: "",
        visibility: "private",
        isShareable: true,
        file: null as File | null,
    })
    const [recipientSearch, setRecipientSearch] = useState({
        shareType: "B2P",
        q: "",
        numref: "",
        role: "",
        level: "",
        classId: "",
        mode: "private",
        expiresAt: "",
        downloadLimit: "",
        canReshare: false,
    })

    const headers = useMemo(() => token ? { Authorization: `Bearer ${token}` } : undefined, [token])

    const loadFiles = useCallback(async () => {
        if (!headers) return
        setLoading(true)
        try {
            const response = await fetch(`${API_BASE_URL}/files/`, { headers })
            if (!response.ok) throw new Error("files")
            setFiles(await response.json())
        } catch {
            setStatus(copy.error)
        } finally {
            setLoading(false)
        }
    }, [copy.error, headers])

    useEffect(() => {
        void loadFiles()
    }, [loadFiles])

    const uploadDocument = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault()
        if (!headers || !form.file) return
        const body = new FormData()
        body.append("document_name", form.documentName)
        body.append("category", form.category)
        body.append("visibility", form.visibility)
        body.append("is_shareable", String(form.isShareable))
        body.append("file", form.file)
        const response = await fetch(`${API_BASE_URL}/files/`, { method: "POST", headers, body })
        if (!response.ok) {
            setStatus(copy.error)
            return
        }
        setForm({ documentName: "", category: "", visibility: "private", isShareable: true, file: null })
        setStatus(copy.successUpload)
        await loadFiles()
    }

    const searchRecipients = async () => {
        if (!headers) return
        const params = new URLSearchParams()
        params.set("share_type", recipientSearch.shareType)
        if (recipientSearch.q) params.set("q", recipientSearch.q)
        if (recipientSearch.numref) params.set("numref", recipientSearch.numref)
        if (recipientSearch.role) params.set("role", recipientSearch.role)
        if (recipientSearch.level) params.set("level", recipientSearch.level)
        if (recipientSearch.classId) params.set("class_id", recipientSearch.classId)
        const response = await fetch(`${API_BASE_URL}/files/recipients/search?${params.toString()}`, { headers })
        if (!response.ok) {
            setStatus(copy.error)
            return
        }
        setRecipients(await response.json())
    }

    const openShare = async (file: SecureFile) => {
        setSelectedFile(file)
        setSelectedRecipients([])
        setRecipients([])
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/files/${file.id}/shares`, { headers })
        setShares(response.ok ? await response.json() : [])
    }

    const sendShare = async () => {
        if (!headers || !selectedFile) return
        const payload = {
            file_id: selectedFile.id,
            share_type: recipientSearch.shareType,
            mode: recipientSearch.mode,
            can_reshare: recipientSearch.canReshare,
            recipient_user_ids: selectedRecipients.filter(item => item.type === "user").map(item => item.id),
            recipient_school_ids: selectedRecipients.filter(item => item.type === "school").map(item => item.id),
            recipient_numrefs: recipientSearch.numref ? [recipientSearch.numref] : [],
            expires_at: recipientSearch.expiresAt ? new Date(recipientSearch.expiresAt).toISOString() : null,
            download_limit: recipientSearch.downloadLimit ? Number(recipientSearch.downloadLimit) : null,
        }
        const response = await fetch(`${API_BASE_URL}/files/share`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        })
        if (!response.ok) {
            setStatus(copy.error)
            return
        }
        setStatus(copy.successShare)
        await openShare(selectedFile)
    }

    const downloadFile = async (file: SecureFile) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/files/${file.id}/download`, { headers })
        if (!response.ok) {
            setStatus(copy.error)
            return
        }
        const contentType = response.headers.get("content-type") || ""
        if (contentType.includes("application/json")) {
            const payload = await response.json()
            if (payload.signed_url) window.open(payload.signed_url, "_blank")
            return
        }
        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        const anchor = document.createElement("a")
        anchor.href = url
        anchor.download = file.original_filename
        anchor.click()
        URL.revokeObjectURL(url)
    }

    const approveFile = async (file: SecureFile) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/files/${file.id}/approve`, { method: "POST", headers })
        setStatus(response.ok ? copy.successApprove : copy.error)
        await loadFiles()
    }

    const deleteFile = async (file: SecureFile) => {
        if (!headers) return
        const response = await fetch(`${API_BASE_URL}/files/${file.id}`, { method: "DELETE", headers })
        setStatus(response.ok ? copy.successDelete : copy.error)
        await loadFiles()
    }

    const toggleRecipient = (recipient: Recipient) => {
        setSelectedRecipients(previous => previous.some(item => item.type === recipient.type && item.id === recipient.id)
            ? previous.filter(item => !(item.type === recipient.type && item.id === recipient.id))
            : [...previous, recipient]
        )
    }

    const fileFilterColumns = useMemo<FilterColumn<SecureFile>[]>(() => [
        { key: "name", label: "Nom", accessor: file => file.display_name || file.original_filename },
        { key: "category", label: "Categorie", accessor: file => file.category },
        { key: "visibility", label: "Visibilite", accessor: file => file.visibility },
        { key: "status", label: "Statut", accessor: file => file.approval_status },
    ], [])
    const fileFilter = useTableFilter(files, fileFilterColumns, { storageKey: "documents-files" })

    return (
        <div className="min-h-full space-y-6 bg-[#F5F5F7] p-6 text-[#111827]">
            <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-semibold tracking-tight">{copy.title}</h1>
                    <p className="mt-1 text-sm text-[#6B7280]">{copy.subtitle}</p>
                </div>
                <button onClick={loadFiles} className="inline-flex items-center gap-2 rounded-full border border-[#D1D5DB] bg-white px-4 py-2 text-sm font-medium hover:bg-[#F5F5F7]">
                    <RefreshCw className="h-4 w-4" /> {copy.refresh}
                </button>
            </div>

            {status && <div className="rounded-[20px] border border-[#E5E7EB] bg-white px-4 py-3 text-sm text-[#374151]">{status}</div>}

            <form onSubmit={uploadDocument} className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                <h2 className="text-xl font-semibold">{copy.upload}</h2>
                <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                    <input required value={form.documentName} onChange={event => setForm({ ...form, documentName: event.target.value })} placeholder={copy.documentName} title={copy.documentNameTip} className="apple-input" />
                    <input value={form.category} onChange={event => setForm({ ...form, category: event.target.value })} placeholder={copy.category} title={copy.categoryTip} className="apple-input" />
                    <select value={form.visibility} onChange={event => setForm({ ...form, visibility: event.target.value })} title={copy.visibilityTip} className="apple-select">
                        <option value="private">Prive</option>
                        <option value="public_internal">Public interne</option>
                        <option value="public_external">Public externe</option>
                    </select>
                    <input required type="file" onChange={event => setForm({ ...form, file: event.target.files?.[0] || null })} title={copy.fileTip} className="apple-input" />
                    <label className="flex items-center gap-3 rounded-[18px] border border-[#D1D5DB] bg-white px-4 py-3 text-sm" title={copy.shareableTip}>
                        <input type="checkbox" checked={form.isShareable} onChange={event => setForm({ ...form, isShareable: event.target.checked })} />
                        {copy.shareable}
                    </label>
                    <button type="submit" className="inline-flex w-fit items-center justify-center gap-2 rounded-full bg-black px-5 py-3 font-medium text-white hover:bg-black/90">
                        <FileText className="h-4 w-4" /> {copy.save}
                    </button>
                </div>
            </form>

            <section className="rounded-[28px] border border-[#E5E7EB] bg-white p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3">
                    <h2 className="text-xl font-semibold">{copy.documents}</h2>
                    {loading && <span className="text-sm text-[#6B7280]">...</span>}
                </div>
                <div className="mt-4 max-w-2xl">
                    <TableFilter {...fileFilter.controls} />
                </div>
                <div className="mt-4 overflow-x-auto">
                    <table className="w-full min-w-[900px] text-left text-sm">
                        <thead>
                            <tr className="border-b border-[#E5E7EB] text-[#6B7280]">
                                <th className="py-3">Nom</th>
                                <th className="py-3">Categorie</th>
                                <th className="py-3">Visibilite</th>
                                <th className="py-3">Statut</th>
                                <th className="py-3">Taille</th>
                                <th className="py-3">Acces</th>
                                <th className="py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {fileFilter.filtered.map(file => (
                                <tr key={file.id} className="border-b border-[#F3F4F6]">
                                    <td className="py-3 font-medium">{file.display_name || file.original_filename}</td>
                                    <td className="py-3">{file.category || "-"}</td>
                                    <td className="py-3">{file.visibility}</td>
                                    <td className="py-3">{file.approval_status}</td>
                                    <td className="py-3">{prettySize(file.size_bytes)}</td>
                                    <td className="py-3">{file.access_count}</td>
                                    <td className="py-3">
                                        <div className="flex justify-end gap-2">
                                            <button onClick={() => downloadFile(file)} className="rounded-full border px-3 py-2 hover:bg-[#F5F5F7]" title={copy.download}><Download className="h-4 w-4" /></button>
                                            <button onClick={() => openShare(file)} className="rounded-full border px-3 py-2 hover:bg-[#F5F5F7]" title={copy.share}><Send className="h-4 w-4" /></button>
                                            {file.approval_status === "pending" && <button onClick={() => approveFile(file)} className="rounded-full border px-3 py-2 hover:bg-[#F5F5F7]" title={copy.approve}><ShieldCheck className="h-4 w-4" /></button>}
                                            {file.uploaded_by_id === user?.id && <button onClick={() => deleteFile(file)} className="rounded-full border px-3 py-2 hover:bg-[#F5F5F7]" title={copy.delete}><Trash2 className="h-4 w-4" /></button>}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {!files.length && <p className="py-8 text-center text-sm text-[#6B7280]">{copy.empty}</p>}
                </div>
            </section>

            {selectedFile && (
                <div className="fixed inset-0 z-[1200] flex items-center justify-center bg-black/30 p-4">
                    <div className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-[28px] bg-white p-6 shadow-[0_30px_90px_rgba(15,23,42,0.25)]">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h2 className="text-2xl font-semibold">{copy.share}: {selectedFile.display_name || selectedFile.original_filename}</h2>
                                <p className="text-sm text-[#6B7280]">B2B, B2P, P2P, NumRef, expiration et limite de telechargement.</p>
                            </div>
                            <button onClick={() => setSelectedFile(null)} className="rounded-full p-2 hover:bg-[#F5F5F7]"><XCircle className="h-6 w-6" /></button>
                        </div>

                        <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_1fr]">
                            <div className="rounded-[24px] border border-[#E5E7EB] p-4">
                                <h3 className="font-semibold">{copy.recipients}</h3>
                                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                                    <select value={recipientSearch.shareType} onChange={event => setRecipientSearch({ ...recipientSearch, shareType: event.target.value })} className="apple-select" title="Type de partage: B2B entre etablissements, B2P de l'etablissement vers ses utilisateurs, P2P entre utilisateurs autorises.">
                                        <option value="B2P">B2P</option>
                                        <option value="B2B">B2B</option>
                                        <option value="P2P">P2P</option>
                                    </select>
                                    <select value={recipientSearch.mode} onChange={event => setRecipientSearch({ ...recipientSearch, mode: event.target.value })} className="apple-select" title="Mode d'acces: prive, public interne ou public externe selon les autorisations.">
                                        <option value="private">Private</option>
                                        <option value="public_internal">Public internal</option>
                                        <option value="public_external">Public external</option>
                                    </select>
                                    <input value={recipientSearch.q} onChange={event => setRecipientSearch({ ...recipientSearch, q: event.target.value })} placeholder={copy.search} title="Recherche: nom, email ou etablissement destinataire." className="apple-input" />
                                    <input value={recipientSearch.numref} onChange={event => setRecipientSearch({ ...recipientSearch, numref: event.target.value })} placeholder={copy.numref} title="NumRef: reference unique de l'utilisateur destinataire pour un partage precis." className="apple-input" />
                                    <input value={recipientSearch.role} onChange={event => setRecipientSearch({ ...recipientSearch, role: event.target.value })} placeholder={copy.role} title="Role: filtre les destinataires par role, par exemple teacher, parent ou student." className="apple-input" />
                                    <input value={recipientSearch.classId} onChange={event => setRecipientSearch({ ...recipientSearch, classId: event.target.value })} placeholder={copy.classId} title="Classe ID: filtre les eleves d'une classe precise." className="apple-input" />
                                    <input value={recipientSearch.level} onChange={event => setRecipientSearch({ ...recipientSearch, level: event.target.value })} placeholder={copy.level} title="Niveau: filtre les eleves selon le niveau scolaire configure." className="apple-input" />
                                    <button onClick={searchRecipients} className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-3 text-white"><Search className="h-4 w-4" />{copy.search}</button>
                                </div>
                                <div className="mt-4 grid gap-2">
                                    {recipients.map(recipient => {
                                        const active = selectedRecipients.some(item => item.type === recipient.type && item.id === recipient.id)
                                        return (
                                            <button key={`${recipient.type}-${recipient.id}`} onClick={() => toggleRecipient(recipient)} className="flex items-center justify-between rounded-[18px] border border-[#E5E7EB] px-4 py-3 text-left hover:bg-[#F5F5F7]">
                                                <span>
                                                    <span className="block font-medium">{recipient.name}</span>
                                                    <span className="text-sm text-[#6B7280]">{recipient.subtitle || recipient.school_name || recipient.numref}</span>
                                                </span>
                                                {active ? <CheckCircle2 className="h-5 w-5 text-green-600" /> : <span className="text-xs text-[#6B7280]">{recipient.type}</span>}
                                            </button>
                                        )
                                    })}
                                    {!recipients.length && <p className="rounded-[18px] bg-[#F5F5F7] p-4 text-sm text-[#6B7280]">{copy.noRecipients}</p>}
                                </div>
                            </div>

                            <div className="rounded-[24px] border border-[#E5E7EB] p-4">
                                <h3 className="font-semibold">{copy.selected}</h3>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    {selectedRecipients.map(item => <span key={`${item.type}-${item.id}`} className="rounded-full bg-[#F5F5F7] px-3 py-1 text-sm">{item.name}</span>)}
                                </div>
                                <div className="mt-4 grid gap-3">
                                    <input type="datetime-local" value={recipientSearch.expiresAt} onChange={event => setRecipientSearch({ ...recipientSearch, expiresAt: event.target.value })} className="apple-input" title="Expiration: date et heure apres lesquelles le partage n'est plus accessible." />
                                    <input type="number" value={recipientSearch.downloadLimit} onChange={event => setRecipientSearch({ ...recipientSearch, downloadLimit: event.target.value })} placeholder={copy.limit} className="apple-input" title="Limite: nombre maximal de telechargements autorises pour ce partage." />
                                    <label className="flex items-center gap-3 rounded-[18px] border border-[#D1D5DB] px-4 py-3 text-sm" title="Repartage: autorise le destinataire a partager a son tour si son role le permet.">
                                        <input type="checkbox" checked={recipientSearch.canReshare} onChange={event => setRecipientSearch({ ...recipientSearch, canReshare: event.target.checked })} />
                                        {copy.canReshare}
                                    </label>
                                    <button onClick={sendShare} className="inline-flex w-fit items-center gap-2 rounded-full bg-black px-5 py-3 font-medium text-white"><Send className="h-4 w-4" /> {copy.sendShare}</button>
                                </div>

                                <h3 className="mt-6 font-semibold">{copy.sharedWith}</h3>
                                <div className="mt-3 space-y-2">
                                    {shares.map(share => (
                                        <div key={share.id} className="rounded-[18px] border border-[#E5E7EB] px-4 py-3 text-sm">
                                            <div className="flex justify-between gap-3">
                                                <span>{share.share_type} / {share.mode}</span>
                                                <span>{share.status}</span>
                                            </div>
                                            <p className="text-[#6B7280]">User #{share.recipient_user_id || "-"} School #{share.recipient_school_id || "-"} Downloads {share.download_count}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
