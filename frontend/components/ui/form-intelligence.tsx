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
  const label = inferLabel(field)
  const localizedPlaceholder = field.getAttribute("placeholder")
  if (localizedPlaceholder) field.setAttribute("placeholder", localizeUiText(localizedPlaceholder))
  if (!field.getAttribute("title")) field.setAttribute("title", helpForLabel(label))
  if (!field.getAttribute("aria-label")) field.setAttribute("aria-label", localizeUiText(label))
  field.dataset.teducaiEnhanced = "true"
}

function enhanceLabels(root: ParentNode) {
  root.querySelectorAll("label").forEach(label => {
    const text = textFromElement(label)
    if (!text) return
    label.querySelectorAll("[data-teducai-info]").forEach(node => node.remove())
    const localized = localizeUiText(text)
    if (localized !== text) {
      for (const node of Array.from(label.childNodes)) {
        if (node.nodeType === Node.TEXT_NODE && node.textContent?.trim()) node.textContent = node.textContent.replace(text.trim(), localized)
      }
    }
    ;(label as HTMLElement).dataset.teducaiHelp = "true"
  })
}

function localizeTextElement(element: HTMLElement) {
  if (element.dataset.teducaiTextLocalized === "true") return
  if (element.children.length > 0) return
  const text = element.textContent?.replace(/\s+/g, " ").trim()
  if (!text) return
  const localized = localizeUiText(text)
  if (localized !== text) element.textContent = localized
  element.dataset.teducaiTextLocalized = "true"
}

function enhanceButtons(root: ParentNode) {
  root.querySelectorAll("button").forEach(button => {
    const text = button.textContent?.replace(/\s+/g, " ").trim()
    if (!text) return
    const localized = localizeUiText(text)
    if (localized !== text && button.childElementCount === 0) button.textContent = localized
    const normalized = localized.toLowerCase()
    const isPrimaryAction = /^(enregistrer|save|guardar|hifadhi|ajouter|add|agregar|ongeza)/i.test(localized)
      || normalized.includes("enregistrer")
      || normalized.includes("save")
      || normalized.includes("ajouter")
      || normalized.includes("add")
    if (isPrimaryAction) {
      button.classList.add("teducai-primary-action")
      button.title ||= helpForLabel(localized)
    }
  })
}

function enhanceStaticText(root: ParentNode) {
  root.querySelectorAll("th, caption, h1, h2, h3, h4, p, span").forEach(node => {
    const element = node as HTMLElement
    if (element.closest("svg, [data-teducai-no-localize]")) return
    localizeTextElement(element)
  })
}

function enhance(root: ParentNode = document) {
  root.querySelectorAll("input, select, textarea").forEach(field => {
    enhanceField(field as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement)
  })
  enhanceLabels(root)
  enhanceButtons(root)
  enhanceStaticText(root)
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
