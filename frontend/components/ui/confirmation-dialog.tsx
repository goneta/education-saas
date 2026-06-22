"use client"

import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog"

interface ConfirmationDialogProps {
    open: boolean
    title: string
    description: string
    confirmLabel?: string
    cancelLabel?: string
    destructive?: boolean
    loading?: boolean
    onOpenChange: (open: boolean) => void
    onConfirm: () => void | Promise<void>
}

export function ConfirmationDialog({
    open,
    title,
    description,
    confirmLabel = "Confirmer",
    cancelLabel = "Annuler",
    destructive = false,
    loading = false,
    onOpenChange,
    onConfirm,
}: ConfirmationDialogProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="dark:border-[#3b4248] dark:bg-[#202528]">
                <DialogHeader>
                    <DialogTitle>{title}</DialogTitle>
                    <DialogDescription className="dark:text-[#b9c2cd]">{description}</DialogDescription>
                </DialogHeader>
                <DialogFooter>
                    <Button variant="outline" disabled={loading} onClick={() => onOpenChange(false)}>
                        {cancelLabel}
                    </Button>
                    <Button
                        disabled={loading}
                        onClick={() => void onConfirm()}
                        className={destructive ? "bg-red-600 text-white hover:bg-red-700" : ""}
                    >
                        {loading ? "Traitement..." : confirmLabel}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}
