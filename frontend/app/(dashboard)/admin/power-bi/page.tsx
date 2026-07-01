import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import PowerBIAnalyticsPage from '@/components/powerbi/PowerBIAnalyticsPage';

export const metadata = {
  title: 'Power BI Analytics | Admin',
  description: 'Embedded Power BI CDAC report for executive analytics.',
};

export default async function AdminPowerBIPage() {
  const session = await auth();
  if (!session || session.user.role !== 'admin') {
    redirect('/login');
  }
  return <PowerBIAnalyticsPage />;
}
