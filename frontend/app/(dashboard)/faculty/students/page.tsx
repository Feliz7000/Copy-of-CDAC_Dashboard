import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import FacultyStudentsClient from '@/components/dashboard/FacultyStudentsClient';

export default async function FacultyStudentsPage() {
  const session = await auth();

  if (!session || session.user.role !== 'faculty') {
    redirect('/login');
  }

  return <FacultyStudentsClient />;
}
