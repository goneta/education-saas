"use client"

import { useState, useEffect } from "react"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useAuth } from "@/contexts/auth-context"
import { Loader2 } from "lucide-react"
import { API_BASE_URL } from "@/lib/config"

const assessmentSchema = z.object({
    title: z.string().min(3, "Title must be at least 3 characters"),
    type: z.enum(["exam", "homework", "quiz", "project", "participation"]),
    date: z.string().refine((val) => !isNaN(Date.parse(val)), "Invalid date"),
    max_score: z.number().min(1, "Max score must be at least 1"),
    weight: z.number().min(1, "Weight must be at least 1"),
    class_id: z.number().min(1, "Class is required"),
    subject_id: z.number().min(1, "Subject is required"),
    term_id: z.number().min(1, "Term is required")
})

type AssessmentFormValues = z.infer<typeof assessmentSchema>

type ClassOption = {
    id: number
    name: string
}

type SubjectOption = {
    id: number
    name: string
    code: string
}

type TermOption = {
    id: number
    name: string
}

interface CreateAssessmentModalProps {
    open: boolean
    onOpenChange: (open: boolean) => void
    onSuccess: () => void
}

export function CreateAssessmentModal({ open, onOpenChange, onSuccess }: CreateAssessmentModalProps) {
    const { token } = useAuth()
    const [loading, setLoading] = useState(false)
    const [classes, setClasses] = useState<ClassOption[]>([])
    const [subjects, setSubjects] = useState<SubjectOption[]>([])
    const [terms, setTerms] = useState<TermOption[]>([])

    const { register, control, handleSubmit, formState: { errors } } = useForm<AssessmentFormValues>({
        resolver: zodResolver(assessmentSchema),
        defaultValues: {
            type: "exam",
            max_score: 20,
            weight: 1
        }
    })

    useEffect(() => {
        if (open && token) {
            fetchOptions()
        }
    // Options are intentionally loaded when the modal opens with an available auth token.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [open, token])

    const fetchOptions = async () => {
        const headers = { Authorization: `Bearer ${token}` }
        try {
            const [clsRes, subRes, termRes] = await Promise.all([
                fetch(`${API_BASE_URL}/education/classes`, { headers }),
                fetch(`${API_BASE_URL}/education/subjects`, { headers }),
                fetch(`${API_BASE_URL}/education/terms`, { headers })
            ])

            if (clsRes.ok) setClasses(await clsRes.json())
            if (subRes.ok) setSubjects(await subRes.json())
            if (termRes.ok) setTerms(await termRes.json())

        } catch (e) {
            console.error(e)
        }
    }

    const onSubmit = async (data: AssessmentFormValues) => {
        setLoading(true)
        try {
            const res = await fetch(`${API_BASE_URL}/grades/assessments`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify(data)
            })
            if (res.ok) {
                onSuccess()
                onOpenChange(false)
            } else {
                console.error("Failed to create assessment")
            }
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Create New Assessment</DialogTitle>
                    <DialogDescription>Add an exam, homework, or project.</DialogDescription>
                </DialogHeader>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
                    <div className="space-y-2">
                        <Label htmlFor="title">Title</Label>
                        <Input id="title" {...register("title")} placeholder="e.g. Math Exam 1" />
                        {errors.title && <p className="text-sm text-red-500">{errors.title.message}</p>}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label>Type</Label>
                            <Controller
                                control={control}
                                name="type"
                                render={({ field }) => (
                                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select type" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="exam">Exam</SelectItem>
                                            <SelectItem value="homework">Homework</SelectItem>
                                            <SelectItem value="quiz">Quiz</SelectItem>
                                            <SelectItem value="project">Project</SelectItem>
                                            <SelectItem value="participation">Participation</SelectItem>
                                        </SelectContent>
                                    </Select>
                                )}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="date">Date</Label>
                            <Input id="date" type="date" {...register("date")} />
                            {errors.date && <p className="text-sm text-red-500">{errors.date.message}</p>}
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="max_score">Max Score</Label>
                            <Input id="max_score" type="number" {...register("max_score", { valueAsNumber: true })} />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="weight">Weight (Coeff)</Label>
                            <Input id="weight" type="number" {...register("weight", { valueAsNumber: true })} />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label>Class</Label>
                        <Controller
                            control={control}
                            name="class_id"
                            render={({ field }) => (
                                <Select onValueChange={(val) => field.onChange(Number(val))} value={field.value?.toString()}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select class" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {classes.map(c => (
                                            <SelectItem key={c.id} value={c.id.toString()}>{c.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        />
                        {errors.class_id && <p className="text-sm text-red-500">{errors.class_id.message}</p>}
                    </div>

                    <div className="space-y-2">
                        <Label>Subject</Label>
                        <Controller
                            control={control}
                            name="subject_id"
                            render={({ field }) => (
                                <Select onValueChange={(val) => field.onChange(Number(val))} value={field.value?.toString()}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select subject" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {subjects.map(s => (
                                            <SelectItem key={s.id} value={s.id.toString()}>{s.name} ({s.code})</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        />
                        {errors.subject_id && <p className="text-sm text-red-500">{errors.subject_id.message}</p>}
                    </div>

                    <div className="space-y-2">
                        <Label>Term</Label>
                        <Controller
                            control={control}
                            name="term_id"
                            render={({ field }) => (
                                <Select onValueChange={(val) => field.onChange(Number(val))} value={field.value?.toString()}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select term" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {terms.map(t => (
                                            <SelectItem key={t.id} value={t.id.toString()}>{t.name}</SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            )}
                        />
                        {errors.term_id && <p className="text-sm text-red-500">{errors.term_id.message}</p>}
                    </div>

                    <DialogFooter>
                        <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
                        <Button type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Create
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    )
}
