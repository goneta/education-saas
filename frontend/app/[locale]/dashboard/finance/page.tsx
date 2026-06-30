"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { API_BASE_URL } from "@/lib/config"
import { formatCurrency } from "@/lib/format"
import { tx } from "@/lib/product-copy"

// Types (should ideally be in a types file)
interface Payment {
    id: number
    amount: number
}

interface Fee {
    id: number
    amount: number
    status: string
    payments: Payment[]
}

interface Expense {
    id: number
    amount: number
}

export default function FinanceDashboard({ params: { locale } }: { params: { locale: string } }) {
    const [fees, setFees] = useState<Fee[]>([])
    const [expenses, setExpenses] = useState<Expense[]>([])

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch Fees
                const feesRes = await fetch(`${API_BASE_URL}/finance/fees`, {
                    headers: {
                        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
                    }
                })
                if (feesRes.ok) {
                    const feesData = await feesRes.json()
                    setFees(Array.isArray(feesData) ? feesData : [])
                }

                // Fetch Expenses
                const expRes = await fetch(`${API_BASE_URL}/finance/expenses`, {
                    headers: {
                        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
                    }
                })
                if (expRes.ok) {
                    const expData = await expRes.json()
                    setExpenses(Array.isArray(expData) ? expData : [])
                }

            } catch (error) {
                console.error("Failed to fetch finance data", error)
            } finally {
                }
        }

        fetchData()
    }, [])

    // Calculations
    const totalExpected = fees.reduce((acc, fee) => acc + fee.amount, 0)
    const totalCollected = fees.reduce((acc, fee) => {
        // Assuming fee.payments is populated in the response
        const paid = fee.payments ? fee.payments.reduce((pAcc, p) => pAcc + p.amount, 0) : 0
        return acc + paid
    }, 0)
    const totalExpenses = expenses.reduce((acc, exp) => acc + exp.amount, 0)
    const netIncome = totalCollected - totalExpenses

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold tracking-tight">{tx(locale, "financeManagement")}</h1>
                <div className="space-x-2">
                    <Link href={`/${locale}/dashboard/finance/fees`}>
                        <Button variant="outline">{tx(locale, "manageFees")}</Button>
                    </Link>
                    <Link href={`/${locale}/dashboard/finance/expenses`}>
                        <Button variant="outline">{tx(locale, "manageExpenses")}</Button>
                    </Link>
                    <Link href={`/${locale}/dashboard/finance/reports`}>
                        <Button variant="outline">{tx(locale, "reports")}</Button>
                    </Link>
                    <Link href={`/${locale}/dashboard/finance/cash-journal`}>
                        <Button variant="outline">{tx(locale, "cashJournal")}</Button>
                    </Link>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{tx(locale, "totalRevenue")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                            {formatCurrency(totalCollected, locale)}
                        </div>
                        <p className="text-xs text-muted-foreground">{tx(locale, "collectedFromFees")}</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{tx(locale, "totalExpenses")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                            {formatCurrency(totalExpenses, locale)}
                        </div>
                        <p className="text-xs text-muted-foreground">{tx(locale, "operationalCosts")}</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{tx(locale, "netIncome")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(netIncome, locale)}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">{tx(locale, "outstandingFees")}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-yellow-600">
                            {formatCurrency(totalExpected - totalCollected, locale)}
                        </div>
                        <p className="text-xs text-muted-foreground">{tx(locale, "pendingCollection")}</p>
                    </CardContent>
                </Card>
            </div>

            {/* Add Charts or Recent Transactions here later */}
        </div>
    )
}
