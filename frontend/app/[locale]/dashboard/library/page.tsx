"use client"

import { useState, useEffect } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { LibraryStats } from "@/components/library/library-stats"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"
import { BookList } from "@/components/library/book-list"
import { LoanList } from "@/components/library/loan-list"

// Placeholder interfaces - will be refined
interface Book {
    id: number
    quantity: number
    available_quantity: number
}

interface Loan {
    id: number
    status: string
}

export default function LibraryPage() {
    const { token } = useAuth()
    const [books, setBooks] = useState<Book[]>([])
    const [loans, setLoans] = useState<Loan[]>([])
    const [loading, setLoading] = useState(true)

    const fetchData = async () => {
        if (!token) return

        try {
            const [booksRes, loansRes] = await Promise.all([
                fetch(`${API_BASE_URL}/library/books`, {
                    headers: { "Authorization": `Bearer ${token}` }
                }),
                fetch(`${API_BASE_URL}/library/loans`, {
                    headers: { "Authorization": `Bearer ${token}` }
                })
            ])

            if (booksRes.ok) {
                const booksData = await booksRes.json()
                setBooks(booksData)
            }
            if (loansRes.ok) {
                const loansData = await loansRes.json()
                setLoans(loansData)
            }
        } catch (error) {
            console.error("Failed to fetch library data", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [token])

    // Calculate stats
    const totalBooks = books.reduce((acc, book) => acc + book.quantity, 0)
    const availableBooks = books.reduce((acc, book) => acc + book.available_quantity, 0)
    const activeLoans = loans.filter(l => l.status === "active").length
    const overdueLoans = loans.filter(l => l.status === "overdue").length // Logic might need adjustment based on date

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-[#111827]">Library Management</h1>
                <p className="text-sm text-[#6B7280] mt-1">
                    Manage books inventory and track student loans
                </p>
            </div>

            <LibraryStats
                totalBooks={totalBooks}
                activeLoans={activeLoans}
                overdueLoans={overdueLoans}
                availableBooks={availableBooks}
            />

            <Tabs defaultValue="books" className="w-full">
                <TabsList>
                    <TabsTrigger value="books">Books Inventory</TabsTrigger>
                    <TabsTrigger value="loans">Loan Management</TabsTrigger>
                </TabsList>
                <TabsContent value="books" className="mt-4">
                    <BookList books={books} onRefresh={fetchData} />
                </TabsContent>
                <TabsContent value="loans" className="mt-4">
                    <LoanList loans={loans} onRefresh={fetchData} />
                </TabsContent>
            </Tabs>
        </div>
    )
}
