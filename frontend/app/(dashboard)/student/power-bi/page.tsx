import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import PowerBIAnalyticsPage from '@/components/powerbi/PowerBIAnalyticsPage';

export const metadata = {
  title: 'My Marks | Student',
  description: 'Embedded Power BI student marks view (My Marks).',
};

export default async function StudentPowerBIPage() {
  const session = await auth();
  if (!session || session.user.role !== 'student') {
    redirect('/login');
  }
  return (
    <PowerBIAnalyticsPage
      title="My Marks"
      description="Your test marks from the CDAC report. Row-level security limits this view to your PRN only."
      studentScoped
    />
  );
}
