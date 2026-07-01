'use client';

import { useState, useEffect } from 'react';
import { getLookups } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, Upload, Activity, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export default function ModelTrainingTab() {
  const [batches, setBatches] = useState<{ batch_name: string }[]>([]);
  const [selectedBatch, setSelectedBatch] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLookups()
      .then((data) => {
        setBatches(data.batches ?? []);
        if (data.batches && data.batches.length > 0) {
          setSelectedBatch(data.batches[0].batch_name);
        }
      })
      .catch((err) => {
        console.error('Failed to fetch batches', err);
      });
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleTrain = async () => {
    if (!selectedBatch || !file) {
      setError('Please select a batch and upload a target CSV file.');
      return;
    }

    setIsTraining(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('batch_name', selectedBatch);
    formData.append('target_csv', file);

    try {
      const mlUrl = process.env.NEXT_PUBLIC_ML_URL || 'http://localhost:8001';
      const response = await fetch(`${mlUrl}/ml/train/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Training failed due to a server error.');
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'An unexpected error occurred during training.');
    } finally {
      setIsTraining(false);
    }
  };

  return (
    <div className="space-y-6 p-6 pb-16">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Model Training</h2>
        <p className="text-muted-foreground">
          Incrementally refine the placement model: new batch labels are merged into the
          training store and XGBoost continues from the prior model when available.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-2 border-primary/10 shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5 text-primary" />
              Training Configuration
            </CardTitle>
            <CardDescription>
              Select the batch to extract features from, and upload the target labels CSV.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="batch">Select Batch (Feature Data)</Label>
              <Select value={selectedBatch} onValueChange={setSelectedBatch}>
                <SelectTrigger id="batch" className="w-full">
                  <SelectValue placeholder="Select a batch" />
                </SelectTrigger>
                <SelectContent>
                  {batches.map((b) => (
                    <SelectItem key={b.batch_name} value={b.batch_name}>
                      {b.batch_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="targetCsv">Target Labels (CSV)</Label>
              <div className="grid w-full items-center gap-1.5">
                <Input
                  id="targetCsv"
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="cursor-pointer file:cursor-pointer"
                />
                <p className="text-xs text-muted-foreground">
                  Must contain `prn` and `placement_status` columns.
                </p>
              </div>
            </div>

            <Button
              className="w-full font-semibold transition-all hover:scale-[1.02]"
              onClick={handleTrain}
              disabled={isTraining || !file}
            >
              {isTraining ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Extracting & Training Model...
                </>
              ) : (
                'Start Model Training'
              )}
            </Button>
          </CardContent>
        </Card>

        <div className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Training Failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {result && (
            <Card className="border-2 border-green-500/20 bg-green-50/50 dark:bg-green-950/10 shadow-md animate-in fade-in slide-in-from-bottom-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-400">
                  <CheckCircle2 className="h-5 w-5" />
                  Training Successful
                </CardTitle>
                <CardDescription className="text-green-600/80 dark:text-green-500/80">
                  {result.message}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {result.metrics?.merge_stats && (
                  <div className="rounded-lg border border-green-500/20 bg-background/60 p-4 text-sm">
                    <p className="font-semibold mb-2">
                      Mode: {result.metrics.mode ?? 'unknown'}
                      {result.metrics.xgb_continued ? ' (XGBoost continued from prior model)' : ''}
                    </p>
                    <ul className="space-y-1 text-muted-foreground">
                      <li>Total training records: {result.metrics.merge_stats.total}</li>
                      <li>New PRNs this run: {result.metrics.merge_stats.added_prns}</li>
                      <li>Updated PRNs this run: {result.metrics.merge_stats.updated_prns}</li>
                    </ul>
                  </div>
                )}
                {result.metrics?.metrics && Object.entries(result.metrics.metrics).map(([modelName, metrics]: [string, any]) => (
                  <div key={modelName} className="space-y-2">
                    <h4 className="font-semibold capitalize text-foreground/90 border-b pb-1">
                      {modelName} Model Metrics
                    </h4>
                    <div className="grid grid-cols-2 gap-4">
                      {Object.entries(metrics).map(([metricKey, metricVal]: [string, any]) => (
                        <div key={metricKey} className="flex flex-col rounded-lg bg-background/50 p-3 shadow-sm border border-border/50">
                          <span className="text-xs uppercase text-muted-foreground font-medium mb-1">
                            {metricKey.replace(/_/g, ' ')}
                          </span>
                          <span className="text-lg font-bold text-foreground">
                            {typeof metricVal === 'number' ? (metricVal * 100).toFixed(1) + '%' : metricVal}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {!result && !error && !isTraining && (
            <Card className="border-dashed border-2 bg-muted/30 flex flex-col items-center justify-center p-10 text-center text-muted-foreground h-full min-h-[300px]">
              <Activity className="h-10 w-10 mb-4 opacity-20" />
              <p>Upload a target CSV and start training to see model metrics here.</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
