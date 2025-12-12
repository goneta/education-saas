"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"

interface AddBookModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
}

export function AddBookModal({ open, onOpenChange, onSuccess }: AddBookModalProps) {
    const { token } = useAuth()
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const [formData, setFormData] = useState({
        title: "",
        author: "",
        isbn: "",
        category: "",
        location: "",
        quantity: 1
    })

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target
        setFormData(prev => ({
            ...prev,
            [name]: name === "quantity" ? parseInt(value) || 0 : value
        }))
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setError(null)
        setIsLoading(true)

        try {
            const response = await fetch(`${API_BASE_URL}/library/books`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            })

            if (!response.ok) {
                const data = await response.json()
                throw new Error(data.detail || "Failed to add book")
            }

            onSuccess()
            onOpenChange(false)
            // Reset form
            setFormData({
                title: "",
                author: "",
                isbn: "",
                category: "",
                location: "",
                quantity: 1
            })
        } catch (err: any) {
            setError(err.message)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Add New Book</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm">
                            {error}
                        </div>
                    )}

                    <div className="grid gap-2">
                        <Label htmlFor="title">Title</Label>
                        <Input id="title" name="title" value={formData.title} onChange={handleChange} required />
                    </div>

                    <div className="grid gap-2">
                        <Label htmlFor="author">Author</Label>
                        <Input id="author" name="author" value={formData.author} onChange={handleChange} required />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label htmlFor="isbn">ISBN</Label>
                            <Input id="isbn" name="isbn" value={formData.isbn} onChange={handleChange} />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="category">Category</Label>
                            <Input id="category" name="category" value={formData.category} onChange={handleChange} />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="grid gap-2">
                            <Label htmlFor="location">Location / Shelf</Label>
                            <Input id="location" name="location" value={formData.location} onChange={handleChange} />
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="quantity">Quantity</Label>
                            <Input
                                id="quantity"
                                name="quantity"
                                type="number"
                                min="1"
                                value={formData.quantity}
                                onChange={handleChange}
                                required
                            />
                        </div>
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                            Cancel
                        </Button>
                        <Button type="submit" disabled={isLoading} className="bg-black text-white hover:bg-black/90">
                            {isLoading ? "Adding..." : "Add Book"}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
