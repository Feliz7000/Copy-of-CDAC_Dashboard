import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import StudentDashboardClient from '@/components/dashboard/StudentDashboardClient';

export default async function StudentDashboard() {
  const session = await auth();

  if (!session || session.user.role !== 'student') {
    redirect('/login');
  }

  return <StudentDashboardClient />;
}
