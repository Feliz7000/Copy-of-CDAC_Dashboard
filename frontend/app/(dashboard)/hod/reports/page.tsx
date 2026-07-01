import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import HODReportsClient from '@/components/dashboard/HODReportsClient';

export default async function HODReportsPage() {
  const session = await auth();

  if (!session || session.user.role !== 'hod') {
    redirect('/login');
  }

  return <HODReportsClient />;
}
