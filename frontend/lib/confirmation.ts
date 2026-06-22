"use client"

export interface ConfirmationRequest {
    title: string
    description: string
    confirmLabel?: string
    destructive?: boolean
}

export function requestConfirmation(request: ConfirmationRequest): Promise<boolean> {
    return new Promise(resolve => {
        window.dispatchEvent(new CustomEvent("teducai:confirm", {
            detail: { ...request, resolve },
        }))
    })
}
