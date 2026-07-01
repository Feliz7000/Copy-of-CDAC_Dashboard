import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import PlacementReportPage from '@/components/PlacementReportPage';

export const metadata = {
  title: 'Placement Report | Admin Dashboard',
  description: 'Student placement eligibility report across all assessment categories.',
};

export default async function AdminPlacementReportPage() {
  const session = await auth();
  if (!session || session.user.role !== 'admin') {
    redirect('/login');
  }
  return <PlacementReportPage />;
}
