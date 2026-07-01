import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import RoleDashboardClient from '@/components/dashboard/RoleDashboardClient';

export default async function HODDashboard() {
  const session = await auth();

  if (!session || session.user.role !== 'hod') {
    redirect('/login');
  }

  return (
    <RoleDashboardClient
      title="Course Dashboard"
      subtitle="Live performance overview for your assigned courses."
    />
  );
}
