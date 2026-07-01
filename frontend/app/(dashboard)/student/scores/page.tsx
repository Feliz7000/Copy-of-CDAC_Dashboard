import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import StudentScoresClient from '@/components/dashboard/StudentScoresClient';

export default async function StudentScoresPage() {
  const session = await auth();

  if (!session || session.user.role !== 'student') {
    redirect('/login');
  }

  return <StudentScoresClient />;
}
