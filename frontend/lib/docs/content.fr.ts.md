# content.fr.ts — French translation of the docs content

Full French translation of the TeducAI Platform Docs, mirroring `content.ts`
exactly: all 26 `DOC_PAGES_FR`, the 9 `DOC_GROUPS_FR` (localized group titles +
item labels), `TAB_LABELS_FR` (tab display labels) and `DOCS_UI_FR` (chrome
strings: search, copy-page, on-this-page, etc.).

Invariants that MUST hold:
- Same slugs as `content.ts` (the registry keys pages by slug).
- Group `tab` fields stay ENGLISH — they are identity keys shared with the
  header/sidebar `activeTab` state; only `title` and item `label` are translated.
- Inside blocks, only the visible label of a `[label](/href)` link is translated;
  the `href` is kept identical, and `code` blocks are byte-identical to English.

Consumed only through `registry.ts` — never imported directly by components.
Adding a new English page? Add its French entry here too (or it falls back to
English via the registry, which is acceptable but should be avoided for parity).
