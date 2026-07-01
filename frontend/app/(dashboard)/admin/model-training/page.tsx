import { auth } from '@/auth';
import { redirect } from 'next/navigation';
import ModelTrainingTab from '@/components/ModelTrainingTab';

export const metadata = {
  title: 'Model Training | Admin Dashboard',
  description: 'Train the placement prediction ML model with a custom target CSV.',
};

export default async function AdminModelTrainingPage() {
  const session = await auth();
  if (!session || session.user.role !== 'admin') {
    redirect('/login');
  }
  return <ModelTrainingTab />;
}
