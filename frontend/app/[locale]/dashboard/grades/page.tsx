import { redirect } from "next/navigation";

export default function GradesPage({ params: { locale } }: { params: { locale: string } }) {
    redirect(`/${locale}/dashboard/grades/assessments`);
}
