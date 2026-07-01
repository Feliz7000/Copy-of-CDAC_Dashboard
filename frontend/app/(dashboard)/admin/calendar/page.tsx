'use client';

import { useState, useEffect } from 'react';
import Calendar from 'react-calendar';
import 'react-calendar/dist/Calendar.css';
import { 
  getExamSchedules, 
  createExamSchedule, 
  deleteExamSchedule, 
  getLookups,
  getSubTests
} from '@/lib/api';
import { 
  Calendar as CalendarIcon, 
  Plus, 
  Trash2, 
  MapPin, 
  Clock, 
  FileText,
  Loader2,
  X,
  AlertCircle
} from 'lucide-react';
import { format, isSameDay, parseISO } from 'date-fns';
import { roleDashboardPath } from "@/lib/dashboard-utils";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";

export default function ExamCalendarPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  const [schedules, setSchedules] = useState<any[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const [lookups, setLookups] = useState<any>({});
  const [subtests, setSubtests] = useState<any[]>([]);
  
  const [formData, setFormData] = useState({
    tprn: '',
    scheduled_date: format(new Date(), 'yyyy-MM-dd'),
    venue: '',
    notes: '',
    is_confirmed: true
  });

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    } else if (status === "authenticated" && session?.user?.role !== "admin") {
      router.push(roleDashboardPath(session.user.role));
    }
  }, [status, session, router]);

  useEffect(() => {
    if (status === "authenticated") {
      fetchInitialData();
    }
  }, [status]);

  const fetchInitialData = async () => {
    try {
      setIsLoading(true);
      const [schedulesData, lookupsData, subtestsData] = await Promise.all([
        getExamSchedules(),
        getLookups(),
        getSubTests()
      ]);
      setSchedules(schedulesData);
      setLookups(lookupsData);
      setSubtests(subtestsData);
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('Failed to load scheduling data');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDateChange = (value: any) => {
    setSelectedDate(value);
    setFormData(prev => ({ ...prev, scheduled_date: format(value, 'yyyy-MM-dd') }));
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      setError('');
      await createExamSchedule(formData);
      setSuccess('Exam scheduled successfully');
      
      // Refresh schedules
      const updatedSchedules = await getExamSchedules();
      setSchedules(updatedSchedules);
      
      setIsModalOpen(false);
      setFormData({
        tprn: '',
        scheduled_date: format(selectedDate, 'yyyy-MM-dd'),
        venue: '',
        notes: '',
        is_confirmed: true
      });
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to schedule exam');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to cancel this exam schedule?')) return;
    try {
      await deleteExamSchedule(id);
      setSchedules(prev => prev.filter(s => s.schedule_id !== id));
      setSuccess('Schedule cancelled');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Failed to delete schedule');
    }
  };

  // Get schedules for selected date
  const daySchedules = schedules.filter(s => isSameDay(parseISO(s.scheduled_date), selectedDate));

  // Calendar tile content (dot for days with exams)
  const tileContent = ({ date, view }: any) => {
    if (view === 'month') {
      const hasExams = schedules.some(s => isSameDay(parseISO(s.scheduled_date), date));
      return hasExams ? (
        <div className="flex justify-center mt-1">
          <div className="h-1.5 w-1.5 bg-primary rounded-full" />
        </div>
      ) : null;
    }
    return null;
  };

  if (status === "loading" || isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 pb-20 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Exam Scheduling</h1>
          <p className="text-muted-foreground mt-1">Plan and manage examination dates across all centres.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition shadow-lg font-medium"
        >
          <Plus size={20} /> Schedule Exam
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 animate-in fade-in slide-in-from-top-2">
          <AlertCircle size={20} />
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-500 animate-in fade-in slide-in-from-top-2 font-medium">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Calendar Section */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-card border border-white/10 rounded-2xl p-6 shadow-xl backdrop-blur-md">
            <style>{`
              .react-calendar {
                width: 100%;
                border: none;
                background: transparent;
                font-family: inherit;
              }
              .react-calendar__tile--active {
                background: hsl(var(--primary)) !important;
                border-radius: 12px;
              }
              .react-calendar__tile--now {
                background: hsl(var(--muted));
                border-radius: 12px;
              }
              .react-calendar__tile:hover {
                background: hsl(var(--accent));
                border-radius: 12px;
              }
              .react-calendar__navigation button:hover {
                background: hsl(var(--accent));
                border-radius: 8px;
              }
              .react-calendar__month-view__weekdays__weekday {
                text-decoration: none;
                font-weight: 600;
                color: hsl(var(--muted-foreground));
                padding-bottom: 1rem;
              }
            `}</style>
            <Calendar 
              onChange={handleDateChange} 
              value={selectedDate}
              tileContent={tileContent}
              className="rounded-xl"
            />
          </div>

          <div className="bg-card/50 border border-white/10 rounded-2xl p-6">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-4">Upcoming Overview</h3>
            <div className="space-y-4">
              {schedules.filter(s => parseISO(s.scheduled_date) >= new Date()).slice(0, 3).map(s => (
                <div key={s.schedule_id} className="flex items-center gap-3 text-sm">
                  <div className="h-2 w-2 rounded-full bg-primary" />
                  <span className="font-medium">{format(parseISO(s.scheduled_date), 'MMM d')}</span>
                  <span className="text-muted-foreground">— {s.subtest_name || s.tprn}</span>
                </div>
              ))}
              {schedules.length === 0 && <p className="text-xs text-muted-foreground italic">No upcoming exams scheduled.</p>}
            </div>
          </div>
        </div>

        {/* Schedule Details Section */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-card border border-white/10 rounded-2xl shadow-xl overflow-hidden min-h-[400px]">
            <div className="bg-muted/30 p-6 border-b border-white/5 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <CalendarIcon className="text-primary" />
                <h2 className="text-xl font-bold">{format(selectedDate, 'EEEE, MMMM do')}</h2>
              </div>
              <span className="text-xs bg-primary/20 text-primary px-3 py-1 rounded-full font-bold">
                {daySchedules.length} Scheduled
              </span>
            </div>

            <div className="p-6">
              {daySchedules.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center opacity-50">
                  <Clock size={48} className="mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium">No exams scheduled for this date.</p>
                  <button 
                    onClick={() => setIsModalOpen(true)}
                    className="mt-4 text-primary hover:underline text-sm font-semibold"
                  >
                    Click here to schedule one
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  {daySchedules.map((s) => (
                    <div key={s.schedule_id} className="group p-5 bg-muted/20 border border-white/5 rounded-2xl hover:bg-muted/30 transition-all">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h4 className="text-lg font-bold text-foreground">{s.subtest_name || s.tprn}</h4>
                          <p className="text-xs font-mono text-primary">{s.tprn}</p>
                        </div>
                        <button 
                          onClick={() => handleDelete(s.schedule_id)}
                          className="p-2 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-2">
                          <MapPin size={16} className="text-primary" />
                          <span>{s.venue || 'No venue specified'}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <FileText size={16} className="text-primary" />
                          <span>{s.notes || 'No extra notes'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Schedule Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-white/10 rounded-2xl shadow-2xl w-full max-w-lg p-8 animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Schedule Examination</h2>
              <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-muted rounded-full transition">
                <X size={24} className="text-muted-foreground" />
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="space-y-5">
              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Target Test (SubTest)</label>
                <select 
                  required
                  className="w-full bg-background border border-border rounded-xl px-4 py-2.5 focus:ring-2 focus:ring-primary/50 outline-none appearance-none"
                  value={formData.tprn}
                  onChange={(e) => setFormData({...formData, tprn: e.target.value})}
                >
                  <option value="">Select a test...</option>
                  {subtests.map(t => (
                    <option key={t.tprn} value={t.tprn}>{t.tprn} - {t.subtest_name}</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Scheduled Date</label>
                <input 
                  type="date" 
                  required
                  className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none"
                  value={formData.scheduled_date}
                  onChange={(e) => setFormData({...formData, scheduled_date: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Venue</label>
                <input 
                  type="text" 
                  placeholder="e.g. Lab 101, Main Block"
                  className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none"
                  value={formData.venue}
                  onChange={(e) => setFormData({...formData, venue: e.target.value})}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-muted-foreground">Notes</label>
                <textarea 
                  placeholder="Additional instructions..."
                  className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none min-h-[100px] resize-none"
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 px-4 py-3 border border-border rounded-xl hover:bg-muted font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition disabled:opacity-50"
                >
                  {isSubmitting ? 'Scheduling...' : 'Confirm Schedule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
