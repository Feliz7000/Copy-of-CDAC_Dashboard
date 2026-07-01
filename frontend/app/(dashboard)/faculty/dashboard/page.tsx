import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import RoleDashboardClient from '@/components/dashboard/RoleDashboardClient';

export default async function FacultyDashboard() {
  const session = await auth();

  if (!session || session.user.role !== 'faculty') {
    redirect('/login');
  }

  return (
    <RoleDashboardClient
      title="Batch Dashboard"
      subtitle="Aggregated performance metrics from live student score data."
    />
  );
}
