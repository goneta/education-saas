"use client"

import { useEffect, useMemo, useState } from "react"
import { ExternalLink, Plus, RefreshCw, Save, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"

type Hero = {
    badge: string
    title: string
    subtitle: string
    primary_cta_label: string
    primary_cta_href: string
    secondary_cta_label: string
    secondary_cta_href: string
}
type FaqItem = { question: string; answer: string }
type Testimonial = { quote: string; author: string; role: string }
type SiteContent = {
    hero: Hero
    partners: string[]
    faq: FaqItem[]
    testimonials: Testimonial[]
    pricing: { note: string }
    seo: { meta_title: string; meta_description: string }
    footer: { tagline: string }
}

export default function SiteCmsPage() {
    const { token, user } = useAuth()
    const [content, setContent] = useState<SiteContent | null>(null)
    const [status, setStatus] = useState("")
    const [saving, setSaving] = useState(false)
    const headers = useMemo(() => token ? { "Content-Type": "application/json", Authorization: `Bearer ${token}` } : null, [token])

    const load = () => {
        fetch(`${API_BASE_URL}/site/content`)
            .then(response => response.ok ? response.json() : null)
            .then(data => { if (data) setContent(data) })
            .catch(() => setStatus("Chargement du contenu impossible."))
    }
    useEffect(load, [])

    if (user && user.role !== "super_admin") {
        return <p className="text-sm text-[#64748B] dark:text-[#dce3eb]">Accès réservé au Super Administrateur.</p>
    }
    if (!content) {
        return <p className="text-sm text-[#64748B] dark:text-[#dce3eb]">Chargement du contenu du site…</p>
    }

    const patch = (next: Partial<SiteContent>) => setContent({ ...content, ...next })

    const save = async () => {
        if (!headers) return
        setSaving(true)
        setStatus("")
        try {
            const response = await fetch(`${API_BASE_URL}/site/content`, {
                method: "PUT",
                headers,
                body: JSON.stringify(content),
            })
            const payload = await response.json().catch(() => null)
            if (!response.ok) {
                setStatus(payload?.detail || "Enregistrement impossible.")
                return
            }
            setContent(payload)
            setStatus("Contenu du site enregistré. Les pages publiques se mettent à jour sous une minute.")
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="mx-auto max-w-5xl space-y-5 text-[#111827] dark:text-white">
            <header className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <p className="text-sm font-semibold text-[#0F766E] dark:text-[#5eead4]">Super Admin</p>
                    <h1 className="text-2xl font-bold">Site TeducAI — Contenus publics</h1>
                    <p className="mt-1 max-w-3xl text-sm text-[#64748B] dark:text-[#dce3eb]">Hero, FAQ, témoignages, tarifs, partenaires, SEO et footer de la page d&apos;accueil.</p>
                </div>
                <div className="flex gap-2">
                    <Button type="button" variant="outline" onClick={load}><RefreshCw className="h-4 w-4" /> Recharger</Button>
                    <Button type="button" className="bg-black text-white dark:bg-white dark:text-black" disabled={saving} onClick={save}><Save className="h-4 w-4" /> {saving ? "Enregistrement…" : "Enregistrer"}</Button>
                </div>
            </header>

            <Section title="Hero">
                <Field label="Badge"><input className="cms-input" value={content.hero.badge} onChange={e => patch({ hero: { ...content.hero, badge: e.target.value } })} /></Field>
                <Field label="Titre"><textarea className="cms-input min-h-20" value={content.hero.title} onChange={e => patch({ hero: { ...content.hero, title: e.target.value } })} /></Field>
                <Field label="Sous-titre"><textarea className="cms-input min-h-20" value={content.hero.subtitle} onChange={e => patch({ hero: { ...content.hero, subtitle: e.target.value } })} /></Field>
                <div className="grid gap-3 sm:grid-cols-2">
                    <Field label="Bouton principal (texte)"><input className="cms-input" value={content.hero.primary_cta_label} onChange={e => patch({ hero: { ...content.hero, primary_cta_label: e.target.value } })} /></Field>
                    <Field label="Bouton principal (lien)"><input className="cms-input" value={content.hero.primary_cta_href} onChange={e => patch({ hero: { ...content.hero, primary_cta_href: e.target.value } })} /></Field>
                    <Field label="Bouton secondaire (texte)"><input className="cms-input" value={content.hero.secondary_cta_label} onChange={e => patch({ hero: { ...content.hero, secondary_cta_label: e.target.value } })} /></Field>
                    <Field label="Bouton secondaire (lien)"><input className="cms-input" value={content.hero.secondary_cta_href} onChange={e => patch({ hero: { ...content.hero, secondary_cta_href: e.target.value } })} /></Field>
                </div>
            </Section>

            <Section title="Partenaires / Types d'établissements">
                <ListEditor
                    items={content.partners}
                    onChange={partners => patch({ partners })}
                    addLabel="Ajouter un partenaire"
                    render={(value, onChange) => <input className="cms-input" value={value} onChange={e => onChange(e.target.value)} placeholder="Nom" />}
                    empty=""
                />
            </Section>

            <Section title="FAQ">
                <ListEditor
                    items={content.faq}
                    onChange={faq => patch({ faq })}
                    addLabel="Ajouter une question"
                    empty={{ question: "", answer: "" }}
                    render={(item, onChange) => (
                        <div className="grid gap-2">
                            <input className="cms-input" value={item.question} onChange={e => onChange({ ...item, question: e.target.value })} placeholder="Question" />
                            <textarea className="cms-input min-h-16" value={item.answer} onChange={e => onChange({ ...item, answer: e.target.value })} placeholder="Réponse" />
                        </div>
                    )}
                />
            </Section>

            <Section title="Témoignages">
                <ListEditor
                    items={content.testimonials}
                    onChange={testimonials => patch({ testimonials })}
                    addLabel="Ajouter un témoignage"
                    empty={{ quote: "", author: "", role: "" }}
                    render={(item, onChange) => (
                        <div className="grid gap-2">
                            <textarea className="cms-input min-h-16" value={item.quote} onChange={e => onChange({ ...item, quote: e.target.value })} placeholder="Citation" />
                            <div className="grid gap-2 sm:grid-cols-2">
                                <input className="cms-input" value={item.author} onChange={e => onChange({ ...item, author: e.target.value })} placeholder="Auteur" />
                                <input className="cms-input" value={item.role} onChange={e => onChange({ ...item, role: e.target.value })} placeholder="Rôle / établissement" />
                            </div>
                        </div>
                    )}
                />
            </Section>

            <Section title="Tarifs">
                <Field label="Note tarifaire"><textarea className="cms-input min-h-20" value={content.pricing.note} onChange={e => patch({ pricing: { note: e.target.value } })} /></Field>
            </Section>

            <Section title="SEO">
                <Field label="Meta title"><input className="cms-input" value={content.seo.meta_title} onChange={e => patch({ seo: { ...content.seo, meta_title: e.target.value } })} /></Field>
                <Field label="Meta description"><textarea className="cms-input min-h-20" value={content.seo.meta_description} onChange={e => patch({ seo: { ...content.seo, meta_description: e.target.value } })} /></Field>
            </Section>

            <Section title="Footer">
                <Field label="Slogan du footer"><textarea className="cms-input min-h-16" value={content.footer.tagline} onChange={e => patch({ footer: { tagline: e.target.value } })} /></Field>
            </Section>

            {status && <p className="text-sm font-medium text-[#0F766E] dark:text-[#5eead4]">{status}</p>}

            <p className="flex items-center gap-2 text-sm text-[#64748B] dark:text-[#dce3eb]">
                <ExternalLink className="h-4 w-4" /> Prévisualisez les changements sur la page d&apos;accueil publique.
            </p>

            <style jsx global>{`
                .cms-input {
                    width: 100%;
                    border-radius: 0.5rem;
                    border: 1px solid #cbd5e1;
                    background: #ffffff;
                    padding: 0.5rem 0.75rem;
                    font-size: 0.875rem;
                    color: #111827;
                }
                .dark .cms-input {
                    border-color: #56616a;
                    background: #252b30;
                    color: #ffffff;
                }
            `}</style>
        </div>
    )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <section className="space-y-3 rounded-lg border bg-white p-5 dark:border-[#3b4248] dark:bg-[#202528]">
            <h2 className="text-lg font-semibold">{title}</h2>
            {children}
        </section>
    )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
    return <label className="grid gap-1 text-sm font-semibold">{label}{children}</label>
}

function ListEditor<T>({ items, onChange, render, addLabel, empty }: {
    items: T[]
    onChange: (next: T[]) => void
    render: (item: T, onChange: (next: T) => void) => React.ReactNode
    addLabel: string
    empty: T
}) {
    return (
        <div className="grid gap-3">
            {items.map((item, index) => (
                <div key={index} className="flex items-start gap-2 rounded-lg border p-3 dark:border-[#56616a]">
                    <div className="flex-1">{render(item, next => onChange(items.map((value, i) => i === index ? next : value)))}</div>
                    <Button type="button" variant="outline" onClick={() => onChange(items.filter((_, i) => i !== index))}><Trash2 className="h-4 w-4" /></Button>
                </div>
            ))}
            <Button type="button" variant="outline" className="w-fit" onClick={() => onChange([...items, structuredClone(empty)])}><Plus className="h-4 w-4" /> {addLabel}</Button>
        </div>
    )
}
