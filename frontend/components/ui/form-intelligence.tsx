"use client"

import { useEffect } from "react"

import { helpForLabel, localizeUiText } from "@/lib/ui-localization"

function textFromElement(element: Element | null) {
  return element?.textContent?.replace(/\s+/g, " ").trim() || ""
}

function inferLabel(field: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) {
  const id = field.id
  const explicit = id ? textFromElement(document.querySelector(`label[for="${CSS.escape(id)}"]`)) : ""
  const wrapper = field.closest("label")
  const wrapped = textFromElement(wrapper)
  const placeholder = field.getAttribute("placeholder") || field.getAttribute("aria-label") || field.name || ""
  return explicit || wrapped || placeholder || "Ce champ"
}

function enhanceField(field: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) {
  if (field.dataset.teducaiEnhanced === "true") return
  const label = inferLabel(field)
  const localizedPlaceholder = field.getAttribute("placeholder")
  if (localizedPlaceholder) field.setAttribute("placeholder", localizeUiText(localizedPlaceholder))
  if (!field.getAttribute("title")) field.setAttribute("title", helpForLabel(label))
  if (!field.getAttribute("aria-label")) field.setAttribute("aria-label", localizeUiText(label))
  field.dataset.teducaiEnhanced = "true"
}

function enhanceLabels(root: ParentNode) {
  root.querySelectorAll("label").forEach(label => {
    if ((label as HTMLElement).dataset.teducaiHelp === "true") return
    const text = textFromElement(label)
    if (!text || label.querySelector("[data-teducai-info]")) return
    const localized = localizeUiText(text)
    if (localized !== text) {
      for (const node of Array.from(label.childNodes)) {
        if (node.nodeType === Node.TEXT_NODE && node.textContent?.trim()) node.textContent = node.textContent.replace(text.trim(), localized)
      }
    }
    const info = document.createElement("span")
    info.dataset.teducaiInfo = "true"
    info.textContent = "i"
    info.title = helpForLabel(localized)
    info.setAttribute("aria-label", helpForLabel(localized))
    info.className = "ml-1 inline-flex h-4 w-4 items-center justify-center rounded-full bg-[#0066cc] text-[10px] font-semibold text-white"
    label.appendChild(info)
    ;(label as HTMLElement).dataset.teducaiHelp = "true"
  })
}

function enhance(root: ParentNode = document) {
  root.querySelectorAll("input, select, textarea").forEach(field => {
    enhanceField(field as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement)
  })
  enhanceLabels(root)
}

export function FormIntelligence() {
  useEffect(() => {
    enhance()
    const observer = new MutationObserver(mutations => {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach(node => {
          if (node instanceof HTMLElement) enhance(node)
        })
      }
    })
    observer.observe(document.body, { childList: true, subtree: true })
    return () => observer.disconnect()
  }, [])

  return null
}
