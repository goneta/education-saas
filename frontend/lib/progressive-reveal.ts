// Progressively reveals already-received text so the AI preview panel renders
// gradually instead of appearing as a single block. This is a client-side
// rendering effect (the /chat response is not token-streamed), kept cancellable
// so a new message immediately supersedes an in-flight reveal.

export function revealProgressively(
    fullText: string,
    onUpdate: (partial: string) => void,
    options: { steps?: number; intervalMs?: number } = {},
): () => void {
    const steps = options.steps ?? 16
    const intervalMs = options.intervalMs ?? 35
    if (!fullText) {
        onUpdate("")
        return () => {}
    }
    const chunkSize = Math.max(1, Math.ceil(fullText.length / steps))
    let index = 0
    let cancelled = false
    let timer: ReturnType<typeof setTimeout>

    const tick = () => {
        if (cancelled) return
        index = Math.min(fullText.length, index + chunkSize)
        onUpdate(fullText.slice(0, index))
        if (index < fullText.length) {
            timer = setTimeout(tick, intervalMs)
        }
    }
    timer = setTimeout(tick, intervalMs)

    return () => {
        cancelled = true
        clearTimeout(timer)
    }
}
