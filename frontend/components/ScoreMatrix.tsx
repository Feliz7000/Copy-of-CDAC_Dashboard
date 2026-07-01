'use client';

import { useState, useEffect } from 'react';
import { Loader2, Save, AlertCircle, CheckCircle2, User, Info } from 'lucide-react';
import { getTestMappings, getBatchScores, updateStudentScore } from '@/lib/api';

interface ScoreMatrixProps {
  categoryCode: string;
  courseCode: string;
  batchName: string;
}

export const ScoreMatrix = ({
  categoryCode,
  courseCode,
  batchName
}: ScoreMatrixProps) => {
  const [mappings, setMappings] = useState<any[]>([]);
  const [students, setStudents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Track changes: { prn: { test_logical_name: score } }
  const [changes, setChanges] = useState<Record<string, any>>({});

  useEffect(() => {
    loadData();
  }, [categoryCode, courseCode, batchName]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const [mappingsData, scoresData] = await Promise.all([
        getTestMappings(batchName, categoryCode),
        getBatchScores(categoryCode, courseCode, batchName)
      ]);
      
      setMappings(mappingsData);
      setStudents(scoresData);
      setChanges({});
    } catch (err: any) {
      setError('Failed to load score matrix. Ensure Test Mappings are defined for this category.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleScoreChange = (prn: string, logicalName: string, value: string) => {
    const val = value === '' ? null : parseFloat(value);
    
    setChanges(prev => ({
      ...prev,
      [prn]: {
        ...(prev[prn] || {}),
        [logicalName]: val
      }
    }));
  };

  const handleSave = async () => {
    const prnsToUpdate = Object.keys(changes);
    if (prnsToUpdate.length === 0) return;

    try {
      setIsSaving(true);
      setError('');
      
      // Update each student sequentially or in parallel
      await Promise.all(
        prnsToUpdate.map(prn => updateStudentScore(categoryCode, prn, changes[prn]))
      );
      
      setSuccess('Scores updated successfully!');
      setChanges({});
      setTimeout(() => setSuccess(''), 3000);
      await loadData(); // Refresh data
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save scores');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 gap-4">
        <Loader2 className="animate-spin text-primary" size={48} />
        <p className="text-muted-foreground font-medium animate-pulse">Loading score matrix...</p>
      </div>
    );
  }

  if (mappings.length === 0) {
    return (
      <div className="text-center py-20 bg-muted/20 rounded-3xl border border-dashed border-white/10">
        <Info size={48} className="mx-auto text-muted-foreground opacity-20 mb-4" />
        <h3 className="text-xl font-bold text-foreground mb-2">No Test Mappings Found</h3>
        <p className="text-muted-foreground max-w-md mx-auto">
          Please define subtests for this category/batch in the **Subtests** tab before entering scores.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Matrix Controls */}
      <div className="flex justify-between items-center bg-card/30 p-4 rounded-2xl border border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex -space-x-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="w-8 h-8 rounded-full border-2 border-background bg-primary/20 flex items-center justify-center">
                <User size={14} className="text-primary" />
              </div>
            ))}
          </div>
          <span className="text-sm font-bold text-muted-foreground">
            {students.length} Students Found
          </span>
        </div>
        
        <button
          onClick={handleSave}
          disabled={isSaving || Object.keys(changes).length === 0}
          className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-700 transition shadow-lg font-bold disabled:opacity-50 disabled:grayscale"
        >
          {isSaving ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
          {isSaving ? 'Saving Changes...' : `Save ${Object.keys(changes).length} Changes`}
        </button>
      </div>

      {/* Error/Success Alerts */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500">
          <AlertCircle size={20} />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}
      {success && (
        <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-500">
          <CheckCircle2 size={20} />
          <p className="text-sm font-medium">{success}</p>
        </div>
      )}

      {/* The Matrix Table */}
      <div className="bg-card/50 backdrop-blur-sm border border-white/10 rounded-3xl shadow-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-muted/50">
                <th className="sticky left-0 z-20 bg-muted/90 backdrop-blur-sm px-6 py-5 text-left font-black text-muted-foreground uppercase tracking-widest text-[10px] border-r border-white/5">
                  Student Details
                </th>
                {mappings.map((tm) => (
                  <th key={tm.id} className="px-6 py-5 text-center min-w-[150px] group border-r border-white/5">
                    <div className="flex flex-col items-center gap-1">
                      <span className="font-black text-foreground uppercase tracking-tighter text-xs">
                        {tm.logical_name}
                      </span>
                      <span className="text-[10px] font-bold text-primary opacity-60">
                        Max: {tm.max_marks}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {students.map((student) => (
                <tr key={student.prn} className="hover:bg-primary/5 transition-colors group">
                  <td className="sticky left-0 z-10 bg-card/90 backdrop-blur-sm px-6 py-4 border-r border-white/5">
                    <div className="flex flex-col">
                      <span className="font-bold text-foreground">{student.prn}</span>
                      <span className="text-xs text-muted-foreground line-clamp-1">
                        Student Master Record
                      </span>
                    </div>
                  </td>
                  {mappings.map((tm) => {
                    const isChanged = changes[student.prn]?.[tm.logical_name] !== undefined;
                    const currentValue = isChanged 
                      ? changes[student.prn][tm.logical_name] 
                      : student.scores[tm.logical_name];
                    
                    const isOverMax = currentValue > tm.max_marks;

                    return (
                      <td key={tm.id} className="px-4 py-3 text-center border-r border-white/5">
                        <div className="relative group">
                          <input
                            type="number"
                            step="0.01"
                            value={currentValue === null ? '' : currentValue}
                            onChange={(e) => handleScoreChange(student.prn, tm.logical_name, e.target.value)}
                            placeholder="-"
                            className={`w-full max-w-[80px] bg-background/50 border rounded-lg px-3 py-2 text-center font-black transition-all outline-none focus:ring-2 ${
                              isOverMax 
                                ? 'border-red-500 text-red-500 focus:ring-red-500/50 animate-shake' 
                                : isChanged 
                                  ? 'border-emerald-500/50 text-emerald-500 focus:ring-emerald-500/30' 
                                  : 'border-white/5 text-foreground focus:ring-primary/50'
                            }`}
                          />
                          {isOverMax && (
                            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-red-500 text-white text-[10px] px-2 py-1 rounded shadow-lg z-30 whitespace-nowrap">
                              Exceeds {tm.max_marks}
                            </div>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="flex items-center gap-2 text-muted-foreground text-xs font-medium px-4">
        <Info size={14} className="text-primary" />
        <p>Tip: You can use the TAB key to quickly navigate between score inputs.</p>
      </div>
    </div>
  );
};
