// Server-side helper to read the public Site CMS content managed by the Super Admin.
// Falls back to built-in defaults so the marketing site always renders, even if
// the backend is unreachable at build/render time.

export interface SiteHero {
    badge: string
    title: string
    subtitle: string
    primary_cta_label: string
    primary_cta_href: string
    secondary_cta_label: string
    secondary_cta_href: string
}

export interface SiteFaqItem {
    question: string
    answer: string
}

export interface SiteTestimonial {
    quote: string
    author: string
    role: string
}

export interface SiteContent {
    hero: SiteHero
    partners: string[]
    faq: SiteFaqItem[]
    testimonials: SiteTestimonial[]
    pricing: { note: string }
    seo: { meta_title: string; meta_description: string }
    footer: { tagline: string }
}

export const DEFAULT_SITE_CONTENT: SiteContent = {
    hero: {
        badge: "SaaS multi-établissements, sécurisé et international",
        title: "TeducAI – La Plateforme Intelligente de Gestion des Établissements d’Enseignement et de Formation",
        subtitle: "Automatisez la gestion administrative, académique et financière de votre établissement grâce à l’Intelligence Artificielle.",
        primary_cta_label: "Essayer Gratuitement",
        primary_cta_href: "/contact",
        secondary_cta_label: "Demander une Démonstration",
        secondary_cta_href: "/contact",
    },
    partners: [
        "Écoles primaires",
        "Collèges et lycées",
        "Formation professionnelle",
        "Établissements techniques",
        "Universités et grandes écoles",
        "Instituts de recherche",
        "Formation continue",
        "Organismes de certification",
    ],
    faq: [],
    testimonials: [],
    pricing: { note: "" },
    seo: {
        meta_title: "TeducAI – Gestion intelligente des établissements d’enseignement",
        meta_description: "Automatisez la gestion administrative, académique et financière de votre établissement grâce à l’Intelligence Artificielle.",
    },
    footer: {
        tagline: "La plateforme intelligente de gestion des établissements d’enseignement et de formation.",
    },
}

const SERVER_API_BASE_URL = process.env.BACKEND_INTERNAL_URL || "http://127.0.0.1:8000"

export async function getSiteContent(): Promise<SiteContent> {
    try {
        const response = await fetch(`${SERVER_API_BASE_URL}/site/content`, {
            // Revalidate periodically so Super Admin edits propagate without a redeploy.
            next: { revalidate: 60 },
        })
        if (!response.ok) return DEFAULT_SITE_CONTENT
        const data = (await response.json()) as Partial<SiteContent>
        return {
            ...DEFAULT_SITE_CONTENT,
            ...data,
            hero: { ...DEFAULT_SITE_CONTENT.hero, ...(data.hero || {}) },
            pricing: { ...DEFAULT_SITE_CONTENT.pricing, ...(data.pricing || {}) },
            seo: { ...DEFAULT_SITE_CONTENT.seo, ...(data.seo || {}) },
            footer: { ...DEFAULT_SITE_CONTENT.footer, ...(data.footer || {}) },
            partners: Array.isArray(data.partners) ? data.partners : DEFAULT_SITE_CONTENT.partners,
            faq: Array.isArray(data.faq) ? data.faq : [],
            testimonials: Array.isArray(data.testimonials) ? data.testimonials : [],
        }
    } catch {
        return DEFAULT_SITE_CONTENT
    }
}
