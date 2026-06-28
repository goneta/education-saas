"use client"

import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Edit } from "lucide-react"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { AddBookModal } from "./add-book-modal"

interface Book {
    id: number
    title: string
    author: string
    isbn?: string
    category?: string
    location?: string
    quantity: number
    available_quantity: number
}

interface BookListProps {
    books: Book[]
    onRefresh: () => void
}

export function BookList({ books, onRefresh }: BookListProps) {
    const [showAddModal, setShowAddModal] = useState(false)

    const filterColumns = useMemo<FilterColumn<Book>[]>(() => [
        { key: "title", label: "Title", accessor: book => book.title },
        { key: "author", label: "Author", accessor: book => book.author },
        { key: "isbn", label: "ISBN", accessor: book => book.isbn },
        { key: "category", label: "Category", accessor: book => book.category },
    ], [])
    const filter = useTableFilter(books, filterColumns, { storageKey: "library-books" })
    const filteredBooks = filter.filtered

    return (
        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-[#111827]">Book Inventory</CardTitle>
                <div className="flex gap-2">
                    <div className="w-80">
                        <TableFilter {...filter.controls} />
                    </div>
                    <Button onClick={() => setShowAddModal(true)} className="bg-black text-white hover:bg-black/90">
                        <Plus className="mr-2 h-4 w-4" /> Add Book
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-[#E5E7EB]">
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Title</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Author</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Category</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Location</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Total</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Available</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredBooks.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="text-center py-8 text-muted-foreground">
                                        No books found.
                                    </td>
                                </tr>
                            ) : (
                                filteredBooks.map((book) => (
                                    <tr key={book.id} className="border-b border-[#E5E7EB] hover:bg-gray-50">
                                        <td className="py-3 px-4 text-sm font-medium">{book.title}</td>
                                        <td className="py-3 px-4 text-sm text-gray-500">{book.author}</td>
                                        <td className="py-3 px-4 text-sm text-gray-500">{book.category || "-"}</td>
                                        <td className="py-3 px-4 text-sm text-gray-500">{book.location || "-"}</td>
                                        <td className="py-3 px-4 text-sm text-gray-500">{book.quantity}</td>
                                        <td className="py-3 px-4 text-sm">
                                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${book.available_quantity > 0 ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                                                }`}>
                                                {book.available_quantity}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-sm">
                                            <Button variant="ghost" size="sm">
                                                <Edit className="h-4 w-4 text-blue-600" />
                                            </Button>
                                            {/* Delete button can be added here */}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </CardContent>

            <AddBookModal
                open={showAddModal}
                onOpenChange={setShowAddModal}
                onSuccess={onRefresh}
            />
        </Card>
    )
}
