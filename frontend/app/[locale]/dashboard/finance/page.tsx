"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { useTranslations } from "next-intl"
import { API_BASE_URL } from "@/lib/config"

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
    const t = useTranslations("Dashboard") // Assuming a generic namespace or create one
    const [fees, setFees] = useState<Fee[]>([])
    const [expenses, setExpenses] = useState<Expense[]>([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const fetchData = async () => {
            try {
                // Fetch Fees
                const feesRes = await fetch(`${API_BASE_URL}/finance/fees`, {
                    headers: {
                        "Authorization": `Bearer ${localStorage.getItem("token")}`
                    }
                })
                if (feesRes.ok) {
                    const feesData = await feesRes.json()
                    setFees(Array.isArray(feesData) ? feesData : [])
                }

                // Fetch Expenses
                const expRes = await fetch(`${API_BASE_URL}/finance/expenses`, {
                    headers: {
                        "Authorization": `Bearer ${localStorage.getItem("token")}`
                    }
                })
                if (expRes.ok) {
                    const expData = await expRes.json()
                    setExpenses(Array.isArray(expData) ? expData : [])
                }

            } catch (error) {
                console.error("Failed to fetch finance data", error)
            } finally {
                setLoading(false)
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
                <h1 className="text-3xl font-bold tracking-tight">Financial Management</h1>
                <div className="space-x-2">
                    <Link href={`/${locale}/dashboard/finance/fees`}>
                        <Button variant="outline">Manage Fees</Button>
                    </Link>
                    <Link href={`/${locale}/dashboard/finance/expenses`}>
                        <Button variant="outline">Manage Expenses</Button>
                    </Link>
                </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">
                            ${totalCollected.toLocaleString()}
                        </div>
                        <p className="text-xs text-muted-foreground">Collected from fees</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Expenses</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-600">
                            ${totalExpenses.toLocaleString()}
                        </div>
                        <p className="text-xs text-muted-foreground">Operational costs</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Net Income</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className={`text-2xl font-bold ${netIncome >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${netIncome.toLocaleString()}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Outstanding Fees</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-yellow-600">
                            ${(totalExpected - totalCollected).toLocaleString()}
                        </div>
                        <p className="text-xs text-muted-foreground">Pending collection</p>
                    </CardContent>
                </Card>
            </div>

            {/* Add Charts or Recent Transactions here later */}
        </div>
    )
}
