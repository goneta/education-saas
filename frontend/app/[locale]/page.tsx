import { redirect } from 'next/navigation';

export default function Home({ params }: { params: { locale: string } }) {
  const locale = params?.locale || 'fr';
  redirect(`/${locale}/dashboard`);
}
