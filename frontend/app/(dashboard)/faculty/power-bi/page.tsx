import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import PowerBIAnalyticsPage from '@/components/powerbi/PowerBIAnalyticsPage';

export const metadata = {
  title: 'Power BI Analytics | Faculty',
  description: 'Embedded Power BI CDAC report for course-level analytics.',
};

export default async function FacultyPowerBIPage() {
  const session = await auth();
  if (!session || session.user.role !== 'faculty') {
    redirect('/login');
  }
  return <PowerBIAnalyticsPage title="Power BI Reports" />;
}
