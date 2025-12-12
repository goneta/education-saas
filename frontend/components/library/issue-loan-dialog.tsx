"use client"

import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/components/ui/form"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { Input } from "@/components/ui/input"

const formSchema = z.object({
    book_id: z.string().min(1, "Book is required"),
    user_id: z.string().min(1, "User is required"),
    due_date: z.string().min(1, "Due date is required"),
    notes: z.string().optional(),
})

interface Book {
    id: number;
    title: string;
    available_quantity: number;
}

interface Student {
    id: number;
    full_name: string;
    email: string;
    // We deal with User ID here, so we need to map Student Profile -> User ID or just list Users
}

// Simplified User interface for selection
interface UserOption {
    id: number;
    name: string;
    role: string;
}

interface IssueLoanDialogProps {
    onSuccess: () => void
}

export function IssueLoanDialog({ onSuccess }: IssueLoanDialogProps) {
    const [open, setOpen] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    const [books, setBooks] = useState<Book[]>([])
    const [users, setUsers] = useState<UserOption[]>([])

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            notes: "",
            due_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // Default 14 days
        },
    })

    // Fetch Books and Users on Open
    useEffect(() => {
        if (open) {
            fetchData();
        }
    }, [open])

    const fetchData = async () => {
        try {
            const token = localStorage.getItem("token");
            const headers = { "Authorization": `Bearer ${token}` };

            // Fetch Books (available ones)
            const booksRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/library/books?limit=100`, { headers });
            if (booksRes.ok) {
                const data = await booksRes.json();
                setBooks(data.filter((b: Book) => b.available_quantity > 0));
            }

            // Fetch Students (and Teachers ideally) - For now just Students endpoint which returns User+Profile?
            // Actually /students endpoint returns StudentResponse which extends UserResponse
            const studentsRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/students?limit=100`, { headers });
            if (studentsRes.ok) {
                const data = await studentsRes.json();
                setUsers(data.map((s: any) => ({ id: s.id, name: s.full_name, role: "Student" })));
            }
        } catch (e) {
            console.error("Failed to fetch data for loan dialog", e);
        }
    }

    async function onSubmit(values: z.infer<typeof formSchema>) {
        try {
            setIsLoading(true)
            const token = localStorage.getItem("token")

            const payload = {
                book_id: parseInt(values.book_id),
                user_id: parseInt(values.user_id),
                due_date: new Date(values.due_date).toISOString(),
                notes: values.notes
            }

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/library/loans`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            })

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Failed to issue loan")
            }

            form.reset()
            setOpen(false)
            onSuccess()
        } catch (error) {
            console.error(error)
            alert("Failed to issue loan"); // Simple alert for now
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button>Issue Book</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Issue Book Loan</DialogTitle>
                    <DialogDescription>
                        Select a student and a book to issue.
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">

                        <FormField
                            control={form.control}
                            name="user_id"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Borrower (Student)</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select Student" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {users.map((user) => (
                                                <SelectItem key={user.id} value={user.id.toString()}>
                                                    {user.name} ({user.role})
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="book_id"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Book</FormLabel>
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                            <SelectTrigger>
                                                <SelectValue placeholder="Select Book" />
                                            </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                            {books.map((book) => (
                                                <SelectItem key={book.id} value={book.id.toString()}>
                                                    {book.title} (Available: {book.available_quantity})
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="due_date"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Due Date</FormLabel>
                                    <FormControl>
                                        <Input type="date" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <FormField
                            control={form.control}
                            name="notes"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>Notes (Optional)</FormLabel>
                                    <FormControl>
                                        <Input placeholder="e.g. Book cover slightly torn" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />

                        <DialogFooter>
                            <Button type="submit" disabled={isLoading}>
                                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                Issue Loan
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    )
}
