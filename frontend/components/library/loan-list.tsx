"use client"

import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, CheckCircle } from "lucide-react"
import { TableFilter, useTableFilter, type FilterColumn } from "@/components/ui/table-filter"
import { IssueLoanModal, type LibraryBook } from "./issue-loan-modal"
import { useAuth } from "@/contexts/auth-context"
import { API_BASE_URL } from "@/lib/config"

interface Loan {
    id: number
    book_id: number
    user_id: number
    book_title: string
    user_full_name: string
    issue_date: string
    due_date: string
    return_date?: string
    status: "active" | "returned" | "overdue"
}

interface LoanListProps {
    loans: Loan[]
    onRefresh: () => void
    books?: LibraryBook[]
}

import { Badge } from "@/components/ui/badge"

export function LoanList({ loans, onRefresh, books = [] }: LoanListProps) {
    const { token } = useAuth()
    const [showIssueModal, setShowIssueModal] = useState(false)
    const [processingId, setProcessingId] = useState<number | null>(null)

    const handleReturn = async (loanId: number) => {
        setProcessingId(loanId)
        try {
            const response = await fetch(`${API_BASE_URL}/library/loans/${loanId}/return`, {
                method: "PUT",
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            })
            if (response.ok) {
                onRefresh()
            }
        } catch (error) {
            console.error("Return failed", error)
        } finally {
            setProcessingId(null)
        }
    }

    const filterColumns = useMemo<FilterColumn<Loan>[]>(() => [
        { key: "book", label: "Book", accessor: loan => loan.book_title },
        { key: "borrower", label: "Borrower", accessor: loan => loan.user_full_name },
        { key: "status", label: "Status", accessor: loan => loan.status },
    ], [])
    const filter = useTableFilter(loans, filterColumns, { storageKey: "library-loans" })
    const filteredLoans = filter.filtered

    return (
        <Card className="rounded-xl border border-[#E5E7EB] bg-white shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-[#111827]">Loan History</CardTitle>
                <div className="flex gap-2">
                    <div className="w-80">
                        <TableFilter {...filter.controls} />
                    </div>
                    <Button onClick={() => setShowIssueModal(true)} className="bg-black text-white hover:bg-black/90">
                        <Plus className="mr-2 h-4 w-4" /> Issue Book
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-[#E5E7EB]">
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Book</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Borrower</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Issue Date</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Due Date</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Status</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-[#6B7280]">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredLoans.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="text-center py-8 text-muted-foreground">
                                        No loans found.
                                    </td>
                                </tr>
                            ) : (
                                filteredLoans.map((loan) => (
                                    <tr key={loan.id} className="border-b border-[#E5E7EB] hover:bg-gray-50">
                                        <td className="py-3 px-4 text-sm font-medium">{loan.book_title}</td>
                                        <td className="py-3 px-4 text-sm text-gray-500">{loan.user_full_name}</td>
                                        <td className="py-3 px-4 text-sm text-gray-500">
                                            {new Date(loan.issue_date).toLocaleDateString()}
                                        </td>
                                        <td className="py-3 px-4 text-sm text-gray-500">
                                            {new Date(loan.due_date).toLocaleDateString()}
                                        </td>
                                        <td className="py-3 px-4 text-sm">
                                            <Badge variant={loan.status === 'active' ? 'default' : loan.status === 'returned' ? 'secondary' : 'destructive'}>
                                                {loan.status}
                                            </Badge>
                                        </td>
                                        <td className="py-3 px-4 text-sm">
                                            {loan.status !== 'returned' && (
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleReturn(loan.id)}
                                                    disabled={processingId === loan.id}
                                                    className="text-green-600 hover:text-green-700 hover:bg-green-50"
                                                >
                                                    <CheckCircle className="h-4 w-4 mr-1" />
                                                    Return
                                                </Button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </CardContent>

            <IssueLoanModal
                open={showIssueModal}
                onOpenChange={setShowIssueModal}
                onSuccess={onRefresh}
                books={books}
            />
        </Card>
    )
}
