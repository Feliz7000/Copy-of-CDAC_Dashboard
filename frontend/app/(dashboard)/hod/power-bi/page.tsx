import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import PowerBIAnalyticsPage from '@/components/powerbi/PowerBIAnalyticsPage';

export const metadata = {
  title: 'Power BI Analytics | HOD',
  description: 'Embedded Power BI CDAC report for course-level analytics.',
};

export default async function HODPowerBIPage() {
  const session = await auth();
  if (!session || session.user.role !== 'hod') {
    redirect('/login');
  }
  return <PowerBIAnalyticsPage title="Power BI Reports" />;
}
