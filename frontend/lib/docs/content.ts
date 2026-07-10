import type { DocBlock } from "@/components/docs/doc-blocks"

export interface DocPage {
    slug: string
    label: string
    title: string
    description: string
    breadcrumb: string
    blocks: DocBlock[]
}

export interface DocGroup {
    tab: string
    title: string
    items: { slug: string; label: string }[]
}

// Top-level tabs shown in the docs header.
export const DOC_TABS = ["Guides", "Features", "Admin", "Resources"] as const

// Left-sidebar navigation tree.
export const DOC_GROUPS: DocGroup[] = [
    { tab: "Guides", title: "Getting started", items: [
        { slug: "intro", label: "Intro to TeducAI" },
        { slug: "quickstart", label: "Quickstart" },
        { slug: "platform-overview", label: "Platform overview" },
    ]},
    { tab: "Features", title: "Academic management", items: [
        { slug: "students", label: "Students & enrollment" },
        { slug: "classes-levels", label: "Classes, levels & rooms" },
        { slug: "assignments", label: "Homework & exercises" },
        { slug: "grades", label: "Grades & report cards" },
        { slug: "timetable-engine", label: "AI Timetable Engine" },
    ]},
    { tab: "Features", title: "AI platform", items: [
        { slug: "ai-agents", label: "AI agents & chat" },
        { slug: "ai-learning", label: "AI learning generators" },
        { slug: "ai-credits", label: "AI credits" },
    ]},
    { tab: "Features", title: "Finance", items: [
        { slug: "fees-payments", label: "Fees & payments" },
        { slug: "cash-payments", label: "Cash payments & AI credits" },
        { slug: "payroll", label: "Payroll" },
        { slug: "billing", label: "Billing & subscriptions" },
    ]},
    { tab: "Features", title: "Smart Transport", items: [
        { slug: "transport-overview", label: "Overview" },
        { slug: "transport-fleet", label: "Fleet, drivers & routes" },
        { slug: "transport-boarding", label: "Boarding, GPS & safety" },
    ]},
    { tab: "Features", title: "Automations", items: [
        { slug: "automations", label: "Automation suite" },
        { slug: "esignature", label: "E-signature & documents" },
    ]},
    { tab: "Features", title: "Communication & HR", items: [
        { slug: "announcements", label: "Announcements" },
        { slug: "leave", label: "Leave management" },
    ]},
    { tab: "Admin", title: "Platform & administration", items: [
        { slug: "multi-tenant", label: "Institutions & context" },
        { slug: "roles-permissions", label: "Roles & permissions" },
        { slug: "personnel", label: "School staff" },
        { slug: "document-verification", label: "Document QR & verification" },
        { slug: "help-center", label: "In-app Help Center" },
    ]},
    { tab: "Resources", title: "Developers", items: [
        { slug: "api-webhooks", label: "API & webhooks" },
        { slug: "extensibility", label: "Extensibility" },
    ]},
]

const P = (...blocks: DocBlock[]) => blocks

export const DOC_PAGES: Record<string, DocPage> = {
    "automations": {
        slug: "automations", label: "Automation suite", breadcrumb: "Features / Automations",
        title: "Automation suite",
        description: "19 automations across every user group — school staff, teachers, students, parents, recruiters and job-seekers — built on the platform's real data, idempotent by design and credit-gated when AI is involved.",
        blocks: P(
            { k: "p", text: "TeducAI ships a complete automation program. Every automation follows the same principles: it works on **real data** (never invented), it is **idempotent** (safe to re-run manually or from a cron — anti-spam tracking prevents any double-send), AI generations are **credit-gated** on the caller's wallet, and anything that needs a decision or credentials refuses honestly instead of faking a result." },
            { k: "h2", text: "School staff & administrators" },
            { k: "table", headers: ["Automation", "What it does"], rows: [
                ["Rentrée wizard", "One flow rolls the academic year over: preview first (nothing written), then run — students promoted level→level into the least-filled classes, leavers archived with history kept, fee schedules cloned onto the new year. The same year can never be rolled over twice."],
                ["Fee reminders", "Scans overdue fees and sends escalating reminders (gentle → firm → urgent + admin escalation) with SMS to the parent phone. Cooldown + level tracking make re-runs safe."],
                ["Self-service documents", "Students and parents generate certificats de scolarité, attestations and payment receipts themselves — unique verifiable references, print-ready, no staff involvement."],
                ["Anomaly brief", "A per-window operational brief: absence spike vs the previous period, unpaid ratio above threshold, class-size imbalance — delivered to the administrator."],
            ]},
            { k: "h2", text: "Teachers" },
            { k: "table", headers: ["Automation", "What it does"], rows: [
                ["Grade entry by photo", "Photograph a marked list; a vision provider (OpenAI/Anthropic) transcribes name–score pairs, deterministically matched onto the class roster with confidence badges. Nothing is saved until the teacher reviews and confirms."],
                ["Sequence builder", "A whole term's lesson plan generated in one AI call, calibrated on the pair's REAL weekly timetable slots × the term's weeks — refused when no slots exist."],
                ["AI remediation", "After an assessment, every student below the threshold receives a personalized practice set (3–5 progressive exercises grounded in their score and the teacher's comment), delivered as a notification. Re-runs only serve newly graded students."],
                ["Absence follow-up", "Each unfollowed absence triggers the parent message (notification in the parent's language + SMS when a phone is on file) — exactly once per absence."],
            ]},
            { k: "h2", text: "Students & pupils" },
            { k: "table", headers: ["Automation", "What it does"], rows: [
                ["Revision planner", "Built from the student's real timetable, upcoming assessments and unsubmitted homework: spaced revision slots at D-5 (overview), D-2 (practice) and D-1 (final review)."],
                ["Homework reminders", "Spaced nudges at D-7 / D-3 / D-1 to students who have not submitted — one reminder per bucket per student."],
                ["Explain my grade", "An AI walk-through of any of the student's own grades: class average, best score, rank, a reading of the teacher's comment and concrete improvement tips, in the student's language."],
            ]},
            { k: "h2", text: "Parents" },
            { k: "table", headers: ["Automation", "What it does"], rows: [
                ["Weekly child digest", "One notification per (parent, child) in the PARENT'S language compiling the week's grades, absences and payments due."],
                ["Threshold alerts", "Instant alerts riding the digest: average below the bar, repeated absences."],
                ["One-tap actions", "Straight from the notification bell: justify an absence (flips it to excused, teacher notified), pay a fee (finance deep-link), and e-sign documents — see [E-signature](/docs/esignature)."],
            ]},
            { k: "h2", text: "Recruiters & job-seekers (TeducAI Emploi)" },
            { k: "table", headers: ["Automation", "What it does"], rows: [
                ["Candidate matching + reasons", "CVs ranked against an offer by the deterministic match engine; a per-candidate AI explanation grounded strictly in the match details."],
                ["Saved-search agents", "Stored criteria re-scored against CVs updated since the last run — only NEW matching graduates are notified. Cron-friendly run-all endpoint."],
                ["Screening questionnaires", "An AI questionnaire per offer (knowledge, scenario, motivation) stored on the offer for reuse."],
                ["CV auto-refresh", "The student's real academic record flows into their CV on demand."],
                ["Gap analysis", "Deterministic offer-vs-profile diff (missing skills, languages, experience) + AI advice on acquiring each missing item."],
                ["AI cover letters", "Drafts grounded strictly in the CV's real data — the prompt forbids inventing diplomas or employers."],
            ]},
            { k: "h2", text: "Running and scheduling" },
            { k: "p", text: "Staff automations live on the **System → Automations** page (thresholds, run-now, result summaries, per-run history). Every runner is idempotent, so an external cron can hit the endpoints directly:" },
            { k: "code", lang: "bash", code: "POST /automations/fee-reminders/run\nPOST /automations/parent-digest/run\nPOST /automations/absence-followup/run\nPOST /automations/anomaly-digest/run\nPOST /automations/homework-reminders/run\nPOST /employment/recruiter/saved-searches/run-all" },
            { k: "h2", text: "AI providers" },
            { k: "p", text: "AI-backed automations route through the platform provider layer: **OpenAI and Anthropic are the primary providers**; OpenRouter, Manus and Genspark act as fallbacks in that order. Keys go in `.env.production` (auto-registered at startup) or in **System → AI providers** (stored encrypted). Vision features (grade entry by photo) require a vision-capable model and refuse with an explicit error when no provider is reachable — results are never fabricated." },
            { k: "callout", tone: "note", title: "Credits", text: "Every AI generation checks and debits the caller's AI-credit wallet — see [AI credits](/docs/ai-credits)." },
        ),
    },

    "esignature": {
        slug: "esignature", label: "E-signature & documents", breadcrumb: "Features / Automations",
        title: "E-signature & self-service documents",
        description: "Families generate official documents themselves and sign them electronically — cryptographically verifiable and tamper-evident, with no external signing provider.",
        blocks: P(
            { k: "h2", text: "Self-service documents" },
            { k: "p", text: "From **Mes documents**, a student (or a parent for a linked child) generates a certificat de scolarité, an attestation de fréquentation or a payment receipt in one click. Each document carries a unique reference (CERT-…, ATT-…, REC-…), prints with the school header and can be re-displayed identically forever — the full payload is stored at generation time." },
            { k: "h2", text: "How the e-signature works" },
            { k: "ol", items: [
                "When a signer clicks **Sign**, the document's content is canonicalized and hashed (SHA-256) — this freezes exactly what was signed.",
                "The signature itself is an HMAC-SHA256, keyed from a domain-separated derivation of the platform secret, over the document id, reference, content hash, signer and timestamp.",
                "Verification recomputes both: a signature mismatch means the signature row was forged; a content-hash mismatch means the document was modified after signing (tampering).",
            ]},
            { k: "p", text: "The document's student and a linked parent can each sign once. Valid signatures print on the document as a verified block with a short code (XXXX-XXXX-XXXX), and the by-reference verification endpoint returns every signature with live authenticity and integrity checks." },
            { k: "callout", tone: "warn", title: "Scope", text: "This is an integrity/authenticity signature bound to the authenticated platform account — a full audit trail of who signed what and when, with tamper evidence. It is not a qualified electronic signature in the eIDAS sense." },
        ),
    },

    intro: {
        slug: "intro", label: "Intro to TeducAI", breadcrumb: "Guides / Getting started",
        title: "Intro to TeducAI",
        description: "TeducAI is an AI-first, enterprise, multi-tenant education platform. One platform where every module shares the same authentication, RBAC, AI services, notifications and master data — with zero data duplication.",
        blocks: P(
            { k: "callout", tone: "tip", title: "One platform, every module", items: [
                "`Academic` — students, teachers, classes, subjects, the AI timetable engine, grades and report cards.",
                "`AI` — 41 specialised agents, a chat assistant, and AI lesson / quiz / exam generators.",
                "`Finance` — fees, a centralized Payment Service (Stripe, CinetPay, Djamo, cash), payroll and AI credits.",
                "`Smart Transport` — fleet, drivers, routes, GPS, boarding attendance and AI route optimization.",
                "`Operations` — communication, HR/leave, analytics and extensibility (webhooks + API keys).",
            ]},
            { k: "h2", text: "What makes TeducAI different" },
            { k: "p", text: "Unlike point solutions (an SIS here, a payment tool there, a separate transport app), TeducAI is a single system. A student created once flows into enrollment, grading, billing, transport and the parent portal — there is no second login, no second database and no duplicate master data." },
            { k: "ul", items: [
                "**Multi-tenant by design** — many institutions coexist with strict data isolation; every query is school-scoped.",
                "**RBAC everywhere** — every write is role-gated; Super Admin, School Admin, teachers, students and parents each see a tailored experience.",
                "**AI-first** — AI is woven through the product: timetable generation, lesson content, pedagogical assistance and decision insights.",
                "**Bilingual** — the entire interface localizes to French and English (with Spanish and Swahili scaffolding).",
            ]},
            { k: "h2", text: "Who uses it" },
            { k: "table", headers: ["Role", "What they do"], rows: [
                ["Super Admin", "Manages the platform: institutions, the global levels referential, AI credit offers, cross-tenant administration."],
                ["School Admin", "Runs a school: students, staff, classes, finance, timetable, communication."],
                ["Teacher", "Courses, classes, homework, grades, AI generation tools, payslips and leave — admin menus hidden."],
                ["Student", "Homework, grades, timetable, documents, report cards, payments and notifications."],
                ["Parent", "Sees each child, switches between them, and reviews the child's full school record."],
            ]},
            { k: "callout", tone: "note", title: "Looking for the app?", text: "Open the [Console](/dashboard) to use TeducAI, or read the [Quickstart](/docs/quickstart) to set up your first institution." },
        ),
    },

    quickstart: {
        slug: "quickstart", label: "Quickstart", breadcrumb: "Guides / Getting started",
        title: "Quickstart",
        description: "Set up your institution and reach a working dashboard in a few steps.",
        blocks: P(
            { k: "h2", text: "1. Create your institution" },
            { k: "p", text: "A Super Admin creates the institution, its **establishment models** (e.g. General, Technical, Vocational) and its **academic years**. These three values form the active working context selected from the top bar." },
            { k: "h2", text: "2. Pick the working context" },
            { k: "p", text: "From the top navigation, choose the **institution**, **model** and **academic year**. Everything you see and create is scoped to that context. Users only see the establishments they are linked to." },
            { k: "h2", text: "3. Build the academic structure" },
            { k: "ol", items: [
                "Super Admin defines reusable **levels** (CP1, CE1, 6ème, Terminale, BTS…) in the global referential.",
                "Create **classes** from those levels (e.g. `CP1 A`, `2nde Technique A`).",
                "Add **buildings** and **rooms** (with capacity and type), and **subjects**.",
                "Enroll **students** and add **teachers** and **staff**.",
            ]},
            { k: "h2", text: "4. Generate the timetable" },
            { k: "p", text: "Configure pedagogical constraints, then let the [AI Timetable Engine](/docs/timetable-engine) produce optimized, conflict-free schedules." },
            { k: "callout", tone: "tip", text: "Every page has a contextual **Help** button that opens the in-app documentation for the current screen — see [In-app Help Center](/docs/help-center)." },
        ),
    },

    "platform-overview": {
        slug: "platform-overview", label: "Platform overview", breadcrumb: "Guides / Getting started",
        title: "Platform overview",
        description: "The module map and the shared services every module builds on.",
        blocks: P(
            { k: "h2", text: "Shared foundation" },
            { k: "p", text: "Every module consumes the same core services rather than re-implementing them: identity & RBAC, the active context (organization / school / model / year), the centralized Payment Service, the AI platform, notifications and analytics." },
            { k: "h2", text: "Module map" },
            { k: "table", headers: ["Area", "Modules"], rows: [
                ["Core", "Auth, context, system, site (CMS), platform (departments, feature flags, global search)"],
                ["SIS", "Students, student lifecycle, guardians, emergency contacts, medical records"],
                ["Academic", "Classes, subjects, the timetable engine, pedagogy, grades, attendance, GPA"],
                ["AI", "41 agents + LLM router, chat, automation, credits, AI learning generators"],
                ["Finance", "Fees, the centralized Payment Service, payroll, AI credits"],
                ["Smart Transport", "Fleet, drivers, vehicles, routes, stops, GPS, boarding, incidents, fuel, AI optimizer"],
                ["Operations", "Communication, HR/leave, analytics, extensibility"],
            ]},
            { k: "callout", tone: "note", title: "Zero data duplication", text: "Modules never copy each other's data. Transport reads students from the SIS; billing reads fees from Finance; the parent app reads grades from the academic module — all through well-defined, school-scoped APIs." },
        ),
    },

    students: {
        slug: "students", label: "Students & enrollment", breadcrumb: "Features / Academic management",
        title: "Students & enrollment",
        description: "The master student lifecycle — one record that follows a student across establishments and academic years.",
        blocks: P(
            { k: "h2", text: "Student records" },
            { k: "p", text: "Each student has a single profile (personal info, registration number, photo, guardians, emergency contacts and medical data). Creating a student auto-provisions the login account." },
            { k: "h2", text: "Enrollment & history" },
            { k: "p", text: "A student can belong to several establishments over their schooling. Each enrollment is historised with the establishment, academic year, class, level, status, and entry/exit dates — so the full school history is preserved across transfers." },
            { k: "h2", text: "Level → class on the form" },
            { k: "p", text: "The Add Student form has an **Informations sur la Classe** section: pick a **level** first, then the class list filters to only the classes belonging to that level. The class read-only details modal shows the enrolled-students count and a scrollable list (full name, age, sex) — each row links to the student profile." },
            { k: "callout", tone: "tip", text: "Lists across TeducAI share one filter component: a column selector plus debounced, accent- and case-insensitive search." },
        ),
    },

    "classes-levels": {
        slug: "classes-levels", label: "Classes, levels & rooms", breadcrumb: "Features / Academic management",
        title: "Classes, levels & rooms",
        description: "A central levels referential, classes built from it, and the buildings & rooms that host them — with smart occupancy rules.",
        blocks: P(
            { k: "h2", text: "Levels referential" },
            { k: "p", text: "The Super Admin maintains a global list of **levels** (e.g. `CP1`, `CE1`, `6ème`, `Terminale`, `BTS Informatique`). Every school then builds its classes by choosing from this list — for example `CP1 A`, `2nde Technique A`, `BTS COMPTA A`. A level can be deleted only when no class uses it." },
            { k: "h2", text: "Buildings & rooms" },
            { k: "p", text: "Under **Management**, create **buildings** (name, description, campus, status) and **rooms**. To add a room you select its building, then set the name, capacity and type (classroom, laboratory, computer room, workshop, gym, other)." },
            { k: "h2", text: "Smart occupancy rules" },
            { k: "ul", items: [
                "A class of 30 cannot be scheduled into a 25-seat room — the assignment is blocked.",
                "A room used in a timetable cannot be deleted; the rooms list shows a **Classes** count with a **View** modal listing the classes (and their level) scheduled there.",
                "The classes list shows an **Nb Élèves** count with a **View** modal of the enrolled students; a class that still has students cannot be deleted.",
            ]},
            { k: "callout", tone: "warn", text: "Capacity and in-use guards return a clear `409` conflict instead of silently failing, so administrators always understand why an action was blocked." },
        ),
    },

    "assignments": {
        slug: "assignments", label: "Homework & exercises", breadcrumb: "Features / Academic management",
        title: "Homework, exercises, corrections & assessment",
        description: "A complete assignments module — creation (manual or AI, with an auto-generated answer key), online and paper delivery, submissions, manual and AI grading, a gradebook bridge, statistics and notifications — all inside TeducAI.",
        blocks: P(
            { k: "p", text: "The module runs the entire pedagogical loop on one platform, from creating a piece of work to correcting, marking and archiving it. It reuses the platform's classes, subjects, gradebook, notifications, AI credits and AI services (zero data duplication)." },
            { k: "h2", text: "Creating assignments" },
            { k: "p", text: "Teachers create eleven work types — homework, exercise, quiz, class test, assessment, exam, take-home, practical work, project, presentation and short quiz-test — either **manually** or with the **AI generator**." },
            { k: "ul", items: [
                "**AI generation** produces the questions AND the corrigé (answer key) from the subject, chapter, level, difficulty and question count — expected answers, explanations, per-question points and a rubric.",
                "Mixed question types: MCQ, true/false, short/long answer, fill-in-the-blank, matching, ordering, calculation, problem, case study, programming, essay and reading comprehension.",
                "Generation is credit-gated on the teacher's AI wallet; the teacher reviews and adjusts before publishing.",
            ]},
            { k: "h2", text: "Two delivery modes" },
            { k: "table", headers: ["Mode", "How it works"], rows: [
                ["Online", "Students answer inside TeducAI — autosave, resume after an interruption, and the copy locks after the due date (unless a late penalty is configured)."],
                ["Paper", "The assignment is downloadable/printable; students complete it and hand it in physically for the teacher to grade."],
            ]},
            { k: "h2", text: "Assigning & submitting" },
            { k: "p", text: "An assignment targets a whole class or a subset of students, with an open date, due date, attempt limit and optional late penalty. On publish, targeted students (and, on grading, their parents) are notified. Students submit online answers and/or file attachments." },
            { k: "h2", text: "Grading" },
            { k: "ul", items: [
                "The **“Grade”** roster shows every student and who submitted, is late or is absent.",
                "The teacher opens a copy, marks it by hand (score + feedback + annotations), or runs **AI grading** — the AI scores the copy against the answer key and returns a comment, detected errors, strengths, weaknesses and advice.",
                "AI grading is always a **proposal**: the teacher confirms, edits or rejects the score. Late penalties are applied automatically.",
            ]},
            { k: "h2", text: "Gradebook, statistics & access" },
            { k: "p", text: "“Push to gradebook” creates the matching assessment and posts the marks, feeding report cards, averages and statistics. Per-assignment stats show submitted/graded counts, class average, success rate and late count. The answer key is released to students by rule — never, after the due date, or immediately — while teachers always see it. Students and parents review the corrected copy, feedback and (when released) the corrigé." },
            { k: "callout", tone: "note", title: "Foundation + roadmap", text: "This is the module's core (creation incl. AI + corrigé, online/paper modes, submissions, manual + AI grading, gradebook bridge, stats, notifications, access control). Roadmap: rich-media question editor, paper-scan OCR correction wired to this module (the [grade-scan](/docs/automations) OCR engine already exists), plagiarism / AI-answer detection, differentiated & variant generation, voice annotations, and the full analytics dashboards." },
        ),
    },

    "billing": {
        slug: "billing", label: "Billing & subscriptions", breadcrumb: "Features / Finance",
        title: "Billing & subscription management",
        description: "One enterprise Billing page for the TeducAI plan, AI credits, invoices, usage, promotions, tax and audit — a unified surface over the platform's subscription, credit and payment infrastructure.",
        blocks: P(
            { k: "p", text: "The Billing module (Finance → Billing) brings school subscriptions, AI credits and platform payments into a single Stripe-/OpenAI-style dashboard. It does not re-implement money handling: it is a unified surface over the existing subscription engine, AI credit wallets and the centralized Payment Service (zero data duplication)." },
            { k: "h2", text: "Tabs" },
            { k: "table", headers: ["Tab", "What it does"], rows: [
                ["Overview", "Current plan (name, price, cycle, status, renewal), credit balance, auto-recharge status, quick access and recent activity. Super-Admins also see revenue KPIs (MRR/ARR, outstanding, failed payments)."],
                ["Subscription", "Plan catalog (Starter / Professional / Enterprise / Custom) with included credits, storage, users, schools and support level; switching routes through the existing subscription-change flow (with checkout when a provider is set)."],
                ["Payment methods", "Save, nickname, set-default and remove payment methods (card / mobile-money / bank / wallet) across all supported providers (CinetPay — Orange/Wave/MTN/Moov, Djamo, Stripe, Visa, Mastercard, Amex, PayPal, Apple/Google Pay, bank transfer), with expiry warnings. PCI-safe: only the brand, last 4 digits and expiry are stored — never the full card number."],
                ["Billing history / Transactions", "Invoices and transactions projected from platform payments, with status badges, filtering, CSV export, one-click invoice PDF download (a real reportlab-generated PDF with issuer, bill-to, tax breakdown, totals and a verifiable QR reference) and e-mailing the invoice PDF to the billing recipients via SMTP."],
                ["Credits / Usage", "Credit balance and consumption with live charts: a per-day trend (credits, AI tokens, requests or spend) over 7/30/90 days plus a credits-by-module breakdown; the credit store opens the AI credits page."],
                ["Promotions", "Enter a coupon, promo, gift or referral code — validated then redeemed; credit-type codes top up the school wallet immediately."],
                ["Preferences / Tax & VAT", "Currency, timezone, invoice language, e-mail invoices, payment/renewal reminders, auto-renew and recipients; VAT/GST/Sales-tax identity, tax rate, exemption and billing address."],
                ["Audit logs", "Every billing action (preferences, tax, auto-recharge, promo redemption, subscription change, payment) with actor and timestamp."],
                ["AI billing assistant", "Ask questions about your bill, usage, invoices or plan (\"why is my bill higher?\", \"recommend a cheaper plan\", \"why did my payment fail?\") — answered strictly from your school's real billing data, credit-gated on your AI wallet."],
            ]},
            { k: "h2", text: "Security" },
            { k: "p", text: "Billing management is restricted to admin, direction and accounting roles; revenue analytics and promo-code authoring are Super-Admin only. Every mutation is audit-logged and school-scoped." },
            { k: "callout", tone: "note", title: "Foundation + roadmap", text: "Shipped: the unified page and API (overview, subscription switching, preferences, tax, auto-recharge config, promo validate/redeem, projected invoices/transactions, usage, audit, super-admin revenue) plus one-click invoice PDF download, e-mailing invoices as a PDF attachment (SMTP), full saved payment-method management, an AI billing assistant grounded in your real data, and live usage charts. All four former roadmap items are now built." },
        ),
    },

    grades: {
        slug: "grades", label: "Grades & report cards", breadcrumb: "Features / Academic management",
        title: "Grades & report cards",
        description: "Assessments, grade entry and per-term report cards with automatic averages.",
        blocks: P(
            { k: "h2", text: "Assessments" },
            { k: "p", text: "Create assessments (exams, tests, quizzes) for a class, subject and term, each with a max score and weight. A dedicated grade-entry screen lists the class's students for fast score and comment entry." },
            { k: "h2", text: "Report cards" },
            { k: "p", text: "Generate a student's report card for a term: per-subject averages out of 20, the subject coefficient, the contributing assessments, and an overall average — all computed automatically." },
            { k: "callout", tone: "note", text: "Grades feed GPA computation and the student/parent portals; teachers can also draft assessment content with the [AI learning generators](/docs/ai-learning)." },
        ),
    },

    "timetable-engine": {
        slug: "timetable-engine", label: "AI Timetable Engine", breadcrumb: "Features / Academic management",
        title: "AI Timetable Engine",
        description: "An intelligent, fully configurable scheduling engine — comparable to Untis or aSc Timetables, but AI-native and integrated with the rest of TeducAI.",
        blocks: P(
            { k: "p", text: "The engine generates optimized, conflict-free timetables from a set of configurable constraints. No rule is hard-coded: every constraint lives in the database and is administrable from the interface, so each school sets its own pedagogical policy." },
            { k: "h2", text: "What it solves" },
            { k: "ul", items: [
                "Internal vs. external teachers, including teachers who teach across several establishments and transfers between schools.",
                "Teacher availability and weekly hours per subject.",
                "No teacher in two classes at once; no class with two simultaneous courses.",
                "Available classrooms and laboratories, with equipment awareness.",
                "Subject constraints — e.g. don't teach a subject on two consecutive days.",
                "Precedence rules — some subjects must never come after others (e.g. physics not right after PE).",
                "Balanced spread of heavy vs. light subjects, and a cap on consecutive hours of the same subject.",
                "Breaks, recess and lunch; holidays and non-working days; locked time slots.",
            ]},
            { k: "h2", text: "Configurable constraint rules" },
            { k: "p", text: "Schools express policy as data. For example:" },
            { k: "ul", items: [
                "“Mathematics cannot be scheduled on two consecutive days.”",
                "“Physics can never immediately follow PE.”",
                "“French must always be taught before 11:00.”",
                "“A lab course must always be preceded by a theory course.”",
                "“An external teacher only teaches on Tuesday and Thursday.”",
                "“Primary pupils never have more than two heavy subjects in the same day.”",
                "“Computer rooms stay free on Friday afternoons.”",
            ]},
            { k: "h2", text: "Beyond classic schedulers" },
            { k: "table", headers: ["Capability", "What it does"], rows: [
                ["AI-optimized generation", "Produces several scored timetables ranked by quality, then resolves conflicts automatically."],
                ["Explainable AI", "Explains the decisions behind a generated schedule so administrators understand the trade-offs."],
                ["Scenario simulation", "Answers “what if a teacher is absent?” or “what if school opens on Saturday?”."],
                ["Substitutions", "Generates replacements automatically when a teacher is absent."],
                ["Energy & travel", "Groups courses to cut running costs and minimizes teacher movement between buildings or campuses."],
                ["Hybrid & multi-campus", "Handles in-person/remote delivery and multiple campuses, adapting to per-country school calendars."],
            ]},
            { k: "callout", tone: "tip", title: "Integrated, not isolated", text: "The timetable is the heart of the platform: attendance is recorded against timetable entries, changes and substitutions notify the affected users, and it consumes teachers, rooms and subjects from the shared master data. Recalculating transport pickup times from timetable changes is on the roadmap." },
        ),
    },

    "ai-agents": {
        slug: "ai-agents", label: "AI agents & chat", breadcrumb: "Features / AI platform",
        title: "AI agents & chat",
        description: "41 specialised AI agents behind a unified chat assistant, routed to the most capable model for each task.",
        blocks: P(
            { k: "p", text: "TeducAI ships a fleet of role- and domain-specific agents (teacher assistant, student tutor, HR, finance, decisioning, research and more) behind a single chat surface. An LLM router selects the right model per task and the conversation is logged for auditability." },
            { k: "h2", text: "Highlights" },
            { k: "ul", items: [
                "Pedagogical assistance for teachers; tutoring and study planning for students.",
                "Multilingual responses; explanations grounded in educational context.",
                "Powered by AI credits (see [AI credits](/docs/ai-credits)).",
            ]},
            { k: "callout", tone: "note", text: "The latest and most capable Claude models power AI features; the router can fall back across tiers for cost and latency." },
        ),
    },

    "ai-learning": {
        slug: "ai-learning", label: "AI learning generators", breadcrumb: "Features / AI platform",
        title: "AI learning generators",
        description: "Generate lessons, quizzes, exams and homework adapted to the student level and subject.",
        blocks: P(
            { k: "ul", items: [
                "**AI Lesson Generator** — structured lesson content for a subject and level.",
                "**AI Quiz / Exam Generator** — assessments with answer keys.",
                "**AI Homework Generator** — practice tasks aligned to the curriculum.",
                "**AI feedback & recommendations** — adapts to the learner.",
            ]},
            { k: "callout", tone: "tip", text: "Teachers reach these tools from their own dashboard; generated material plugs into the [grades](/docs/grades) workflow. AI usage consumes credits." },
        ),
    },

    "ai-credits": {
        slug: "ai-credits", label: "AI credits", breadcrumb: "Features / AI platform",
        title: "AI credits",
        description: "Credits meter AI usage. They can be bought online or in cash, granted for free, and distributed by a school to its users.",
        blocks: P(
            { k: "h2", text: "Credit offers" },
            { k: "p", text: "The Super Admin creates AI credit offers — each with a name, price, currency, credit amount, description, active status, and target (individual user, institution, or both). For example:" },
            { k: "table", headers: ["Pack", "Price", "Credits"], rows: [
                ["Pack Starter", "3 000 F", "1 000 AI credits"],
                ["Pack Standard", "5 000 F", "2 500 AI credits"],
                ["Pack École", "50 000 F", "50 000 AI credits"],
            ]},
            { k: "h2", text: "School-level distribution" },
            { k: "p", text: "When a school buys a pack, the credits go to the school's global balance. From **AI Credit Management**, the School Admin sees the balance, picks which users may use AI, assigns a precise number of credits to each, and tracks per-user consumption. Distribution can never exceed the credits the school purchased." },
            { k: "callout", tone: "note", text: "Cash and free top-ups are recorded with full history; see [Cash payments & AI credits](/docs/cash-payments)." },
        ),
    },

    "fees-payments": {
        slug: "fees-payments", label: "Fees & payments", breadcrumb: "Features / Finance",
        title: "Fees & payments",
        description: "A centralized Payment Service that every billable module uses — no module implements its own payment logic.",
        blocks: P(
            { k: "p", text: "Tuition, transport, exams, canteen and any other billable activity route through one Payment Service. It supports multiple providers behind a single business flow, with idempotent confirmation, signed webhooks, receipts and a full audit trail." },
            { k: "h2", text: "Payment methods" },
            { k: "table", headers: ["Method", "Supports"], rows: [
                ["Stripe", "Cards, Apple Pay, Google Pay, hosted checkout, subscriptions, refunds, webhooks"],
                ["CinetPay", "Mobile Money (Orange, MTN), Wave, bank & card payments, QR, refunds"],
                ["Djamo", "Virtual & physical cards, wallet payments, status sync"],
                ["Cash", "Manual recording by a cashier or administrator, with receipt generation"],
            ]},
            { k: "callout", tone: "tip", text: "Institutions enable or disable specific gateways. Every confirmed payment updates the corresponding module automatically and keeps financial reports in sync." },
        ),
    },

    "cash-payments": {
        slug: "cash-payments", label: "Cash payments & AI credits", breadcrumb: "Features / Finance",
        title: "Cash payments & AI credits",
        description: "Record cash payments for school fees and AI credits with full traceability — for students, staff and whole institutions.",
        blocks: P(
            { k: "h2", text: "Cash payment of school fees" },
            { k: "p", text: "Students can pay any fee type in cash: registration, tuition, exams, activities, transport, canteen and more. When a student pays cash, the School Admin:" },
            { k: "ol", items: [
                "selects the student,",
                "chooses the fee type,",
                "enters the amount paid,",
                "sets the method to **Cash** and validates,",
                "the student's account updates automatically and the payment appears in their payment list.",
            ]},
            { k: "p", text: "Each payment records the student name, fee type, amount, date, method, status, the admin who validated it, and an optional internal note or reference." },
            { k: "h2", text: "Cash payment of AI credits" },
            { k: "p", text: "Students, teachers, staff and school admins can buy AI credits to use the AI agent. For a cash purchase the Super Admin opens **AI Credit Management**, finds the user (organized by role), picks a credit offer, sets the method to Cash, validates, and the credits are added to the user's account and logged in the purchase/grant history." },
            { k: "h2", text: "Credits for a whole school" },
            { k: "p", text: "A School Admin can pay cash for a pack destined to the whole school. The Super Admin selects the institution, the offer and Cash, validates — and the credits land in the school's global balance, which the School Admin then distributes to authorized users." },
            { k: "h2", text: "Supported methods" },
            { k: "ul", items: [
                "**Cash** — validated manually by the Super Admin or an authorized admin.",
                "**Free** — the Super Admin can grant credits for free, with a note explaining the reason (promotion, gesture, test, bonus).",
                "**Online** — Stripe, Djamo and CinetPay add credits automatically once payment is confirmed.",
            ]},
            { k: "h2", text: "History & traceability" },
            { k: "p", text: "The system keeps a complete history of fee payments, credit purchases, manual top-ups, free grants, consumption, and school-to-user distributions. Every operation records the user, institution (if any), amount, credits, method, status, date, validator, transaction reference and an optional comment." },
            { k: "callout", tone: "note", title: "Permissions", items: [
                "**Super Admin** — sees all users and institutions, creates credit offers, validates cash payments, grants free credits, tops up any account, reads every history.",
                "**School Admin** — manages cash fee payments for its students, sees its school's AI balance and distributes credits to authorized users.",
                "**User** — sees their own balance, purchase and consumption history, and buys credits if enabled.",
            ]},
        ),
    },

    payroll: {
        slug: "payroll", label: "Payroll", breadcrumb: "Features / Finance",
        title: "Payroll",
        description: "A real payroll system under Finance: salary profiles, a country-extensible calculation engine, payslips and self-service.",
        blocks: P(
            { k: "h2", text: "Salary profiles" },
            { k: "p", text: "Each employee (staff or teacher) has a salary profile: employee type (permanent, contract, temp, consultant), pay type (hourly, daily, weekly, monthly), base rate, currency, and contribution & tax rates." },
            { k: "h2", text: "Generate payslips" },
            { k: "p", text: "Generate a payslip for a period with itemised lines (allowances, bonuses, overtime, deductions, advances). The engine computes the full breakdown — base, gross, social contributions, taxable base, income tax, deductions and net — and is extensible per country." },
            { k: "h2", text: "Approve, pay & self-service" },
            { k: "ul", items: [
                "Admins/accountants approve and pay payslips (bank transfer, cash, Stripe, CinetPay, Djamo).",
                "Employees and teachers see only their own payslips under **Finance → My payslips**, with a print-friendly view.",
            ]},
        ),
    },

    "transport-overview": {
        slug: "transport-overview", label: "Overview", breadcrumb: "Features / Smart Transport",
        title: "Smart Transport — overview",
        description: "School transport built into TeducAI as a fully integrated module — one login, one database, one source of truth.",
        blocks: P(
            { k: "p", text: "Rather than another app with its own login and database, Smart Transport consumes the platform's shared data: students from the SIS, the academic calendar, the timetable, parents, finance and attendance. This removes duplicate data and creates a single source of truth." },
            { k: "h2", text: "Shared master data" },
            { k: "table", headers: ["Reads from", "To produce"], rows: [
                ["Students", "Transport assignments"],
                ["Classes & timetable", "Pickup schedules & arrival-time calculation"],
                ["Academic calendar", "Bus calendar"],
                ["Parents", "Notifications"],
                ["Finance", "Transport fees on the monthly invoice"],
                ["Attendance", "Boarding attendance reconciled with school attendance"],
            ]},
            { k: "h2", text: "Multi-school" },
            { k: "p", text: "One transport company can serve many schools: each school sees only its own students, while the company manages all contracts, fleets, drivers and routes from a centralized dashboard." },
            { k: "callout", tone: "tip", text: "See [Fleet, drivers & routes](/docs/transport-fleet) and [Boarding, GPS & safety](/docs/transport-boarding) for the operational detail." },
        ),
    },

    "transport-fleet": {
        slug: "transport-fleet", label: "Fleet, drivers & routes", breadcrumb: "Features / Smart Transport",
        title: "Fleet, drivers & routes",
        description: "Vehicles, drivers, routes, stops and AI route optimization.",
        blocks: P(
            { k: "h2", text: "Fleet management" },
            { k: "p", text: "Manage buses, minibuses, vans, motorcycles, boats and electric buses, each with registration, insurance, maintenance, mileage, fuel and documents." },
            { k: "h2", text: "Drivers & staff" },
            { k: "p", text: "Driver profiles hold license & expiry, certificates, background checks, medical records and availability. Transport staff include conductors, assistants, supervisors and inspectors." },
            { k: "h2", text: "Routes & stops" },
            { k: "ul", items: [
                "Unlimited routes, each with distance, estimated duration, GPS path, an assigned bus and driver.",
                "Each bus stop stores GPS coordinates, address, radius, assigned students and arrival time.",
                "Students are assigned a route, bus, seat, pickup and drop stops and a schedule.",
            ]},
            { k: "h2", text: "AI route optimizer" },
            { k: "p", text: "AI optimizes routes for fuel, distance, traffic, weather and road closures, and can regenerate routes each morning. Transport fees flow into Finance as another fee category." },
        ),
    },

    "transport-boarding": {
        slug: "transport-boarding", label: "Boarding, GPS & safety", breadcrumb: "Features / Smart Transport",
        title: "Boarding, GPS & safety",
        description: "Boarding attendance, live GPS tracking, AI safety monitoring and notifications.",
        blocks: P(
            { k: "h2", text: "Boarding attendance" },
            { k: "p", text: "Students board via QR code, RFID or face recognition; attendance is recorded and parents are notified. Boarding attendance reconciles with school attendance." },
            { k: "h2", text: "AI safety monitoring" },
            { k: "p", text: "The AI detects a student missing, on the wrong bus, who never boarded, who left early, or an unauthorized passenger — and alerts parents immediately. It can also flag “boarded the bus but never entered school”." },
            { k: "h2", text: "GPS & notifications" },
            { k: "ul", items: [
                "Every vehicle streams GPS to the dashboard and parent app for live tracking and ETA.",
                "Automatic notifications: bus arriving, delayed, student boarded/dropped, driver or route changed, emergency.",
                "Channels: push, SMS, email and WhatsApp.",
            ]},
            { k: "h2", text: "Analytics" },
            { k: "p", text: "KPIs include vehicles, students transported, average occupancy, fuel and maintenance cost, route efficiency, driver performance, late arrivals, safety incidents, revenue and expenses." },
            { k: "callout", tone: "warn", text: "Real-time GPS push (MQTT/WebSocket), facial recognition and native mobile apps are roadmap items that require additional infrastructure." },
        ),
    },

    announcements: {
        slug: "announcements", label: "Announcements", breadcrumb: "Features / Communication & HR",
        title: "Announcements",
        description: "Publish announcements to the school community with audience targeting, emergency flagging and scheduling.",
        blocks: P(
            { k: "ol", items: [
                "Write a title and message and choose the audience (everyone, teachers, students or parents).",
                "Optionally mark it as an emergency and schedule a publication date.",
                "Create it as a draft or scheduled item, then Publish to broadcast via the notification layer.",
            ]},
            { k: "p", text: "Track each announcement's status (draft, scheduled, published) in the list." },
        ),
    },

    leave: {
        slug: "leave", label: "Leave management", breadcrumb: "Features / Communication & HR",
        title: "Leave management",
        description: "Self-service leave requests with administrator approval.",
        blocks: P(
            { k: "ol", items: [
                "Any employee or teacher submits a request: type (annual, sick, unpaid, maternity/paternity, other), start and end dates, and an optional reason.",
                "Administrators see every request in the school and approve or reject it; other staff see only their own.",
                "The requester is notified; the status becomes Approved or Rejected and the decision is historised.",
            ]},
            { k: "callout", tone: "note", text: "The end date cannot precede the start date, and only administrators can decide on a request." },
        ),
    },

    "multi-tenant": {
        slug: "multi-tenant", label: "Institutions & context", breadcrumb: "Admin / Platform & administration",
        title: "Institutions & context",
        description: "Multi-tenant architecture and the active working context that scopes everything you do.",
        blocks: P(
            { k: "h2", text: "The working context" },
            { k: "p", text: "Every session has an active context: organization → school → establishment model → academic year. All reads and writes are scoped to it. The top-bar selector lets you switch context, and users only see establishments they are linked to (memberships + their home school)." },
            { k: "h2", text: "Isolation" },
            { k: "ul", items: [
                "Strict data isolation between tenants — every query is school-scoped.",
                "Teachers, students and parents select the establishment, model and year, and see only the establishments they taught at / attended.",
            ]},
        ),
    },

    "roles-permissions": {
        slug: "roles-permissions", label: "Roles & permissions", breadcrumb: "Admin / Platform & administration",
        title: "Roles & permissions",
        description: "Role-based access control with tailored dashboards per role.",
        blocks: P(
            { k: "p", text: "Teachers, students and parents never see the administration menus (Management, Academic admin, Finance, Operations, System) — those are reserved for Super Admin and School Admin. Each restricted role gets its own sidebar:" },
            { k: "ul", items: [
                "**Teacher** — courses, classes, subjects, grades, documents, library, portal and AI generation tools.",
                "**Student** — timetable, grades, documents, library, internships, payments, portal.",
                "**Parent** — lists each child, switches between them, and reviews the child's full record (grades, documents, payments, report cards, certificates).",
            ]},
            { k: "callout", tone: "tip", text: "Writes are role-gated server-side, so hiding a menu is defense-in-depth rather than the only control." },
        ),
    },

    "document-verification": {
        slug: "document-verification", label: "Document QR & verification", breadcrumb: "Admin / Platform & administration",
        title: "Document QR authentication & verification",
        description: "Every generated TeducAI document carries a QR code that encodes a verifiable JSON snapshot and a public verification URL, so anyone can confirm the document is authentic.",
        blocks: P(
            { k: "p", text: "TeducAI keeps a universal authenticity registry: when a document is generated (invoice, receipt, report card, certificate, diploma, payslip, …), a record is created with a public UUID, a content hash and a type-specific JSON snapshot. The document embeds a QR — top-right, without disturbing the layout — encoding that JSON plus a public verification URL." },
            { k: "h2", text: "Verifying a document" },
            { k: "p", text: "Scanning the QR (or opening /verify/{uuid}) resolves the public verification page, which shows whether the document is authentic, revoked or unknown, along with its main information — type, reference, institution, who it was issued to, generation date and status. The page is public and needs no login." },
            { k: "h2", text: "What the QR encodes" },
            { k: "p", text: "The JSON adapts to the document type. For an invoice it includes the school name, invoice number, customer name, generation date, who generated it, the document UUID and the verification URL; a report card adds student name/ID/matricule, academic year, class and term; a diploma adds the diploma name/number and graduation date; a payslip adds the employee, payroll number and month." },
            { k: "callout", tone: "note", title: "How it stays trustworthy", text: "The registry stores a SHA-256 hash of the snapshot and a status flag; an institution can revoke a document, after which verification reports it as revoked. Registration is idempotent per source document, so re-downloading the same invoice keeps the same UUID. Wired first for invoices; other generators are being connected to the same registry." },
        ),
    },

    personnel: {
        slug: "personnel", label: "School staff", breadcrumb: "Admin / Platform & administration",
        title: "School staff",
        description: "Create and manage staff accounts; postings are historised across establishments.",
        blocks: P(
            { k: "p", text: "Under **Management → School staff**, create a staff account with personal info, primary role, additional roles, department, function and status. Creation auto-provisions the user account and shows a one-time temporary password." },
            { k: "h2", text: "Multi-establishment history" },
            { k: "p", text: "A staff member can work in several establishments. Each posting is historised (role, dates, status); a School Admin posts within their own school and the Super Admin anywhere. Deleting a staff member deactivates the account without destroying it." },
        ),
    },

    "help-center": {
        slug: "help-center", label: "In-app Help Center", breadcrumb: "Admin / Platform & administration",
        title: "In-app Help Center",
        description: "Context-aware help: the Help button opens the documentation for the current page.",
        blocks: P(
            { k: "p", text: "Every dashboard page has a Help button that opens the in-app Help Center scrolled to the matching section — no searching required. Each documented feature has its purpose, a step-by-step guide, the key fields (with expected value and validation) and the expected result." },
            { k: "callout", tone: "note", text: "New modules are added to the Help Center as they ship, and the framework is locale-aware." },
        ),
    },

    "api-webhooks": {
        slug: "api-webhooks", label: "API & webhooks", breadcrumb: "Resources / Developers",
        title: "API & webhooks",
        description: "A documented REST API and outbound webhooks so third-party applications can read TeducAI data and react to platform events.",
        blocks: P(
            { k: "p", text: "TeducAI exposes a REST API (FastAPI, described in the OpenAPI schema at `/docs` on the API server). Internally, modules share master data through well-defined, school-scoped endpoints; externally, partners use the **public API v1** below. The Payment Service also processes signed, idempotent webhooks from external payment providers." },
            { k: "h2", text: "Authentication" },
            { k: "p", text: "Third-party access uses **tenant API keys**, managed by a School Admin under **System → API & Integrations**. A key is shown once at creation (only its hash is stored) and can be revoked at any time. Send it on every request:" },
            { k: "code", code: "GET /api/v1/students?limit=50&offset=0\nHost: api.teducai.example\nX-API-Key: tk_xxxxxxxxxxxxxxxxxxxx" },
            { k: "callout", tone: "note", text: "Every key is scoped to one establishment. A partner can only ever read that school's data — tenant isolation is enforced server-side, and `last_used_at` is tracked per key." },
            { k: "h2", text: "Public API v1 endpoints" },
            { k: "p", text: "Read-only, paginated with `limit` (max 200) and `offset`:" },
            { k: "table", headers: ["Endpoint", "Returns"], rows: [
                ["`GET /api/v1/me`", "The calling key's name, prefix and tenant (school) scope"],
                ["`GET /api/v1/students`", "Students with registration number, gender, class and status"],
                ["`GET /api/v1/teachers`", "Teachers, trainers and instructors"],
                ["`GET /api/v1/classes`", "Classes with their level"],
                ["`GET /api/v1/subjects`", "Subjects with their coefficient"],
                ["`GET /api/v1/announcements`", "Published announcements (the outward communication feed)"],
            ]},
            { k: "h2", text: "Outbound webhooks" },
            { k: "p", text: "Register endpoint URLs under **System → API & Integrations** to receive platform events. Each endpoint can subscribe to specific event types, or to everything by leaving the list empty; an optional secret is stored for HMAC signing by the delivery sender. Every event is queued as a delivery with retry bookkeeping (attempts, max attempts, next retry), visible and manually retryable from the same page." },
            { k: "h3", text: "Event types" },
            { k: "table", headers: ["Event", "Fires when", "Payload highlights"], rows: [
                ["`announcement.published`", "An announcement is published to the community", "`announcement_id`, `title`, `audience`, `is_emergency`"],
                ["`leave.decided`", "A leave request is approved or rejected", "`leave_request_id`, `staff_user_id`, `leave_type`, `status`"],
                ["`payslip.paid`", "A payslip is marked paid", "`payroll_record_id`, `staff_user_id`, `period`, `net_amount`, `method`"],
            ]},
            { k: "callout", tone: "tip", text: "Any module can publish additional events through the shared `emit_event` service — more event types will be added as modules adopt it." },
            { k: "callout", tone: "warn", text: "The asynchronous HTTP delivery worker (which posts queued deliveries to your URL and applies the retry schedule) is a runtime component on the roadmap, alongside GraphQL, a marketplace and an SDK. Deliveries are queued, listable and retryable today." },
        ),
    },

    extensibility: {
        slug: "extensibility", label: "Extensibility", breadcrumb: "Resources / Developers",
        title: "Extensibility",
        description: "How TeducAI is built to extend — pluggable AI providers, feature flags and modular services.",
        blocks: P(
            { k: "ul", items: [
                "**Pluggable AI** — the LLM router lets you swap or add model providers without touching callers.",
                "**Feature flags** — enable modules and capabilities per institution.",
                "**Modular services** — independently deployable services (e.g. transport, payments) reuse shared identity and data.",
                "**Country-extensible engines** — payroll and timetable rules are configurable, not hard-coded.",
            ]},
        ),
    },
}

export const DEFAULT_SLUG = "intro"
