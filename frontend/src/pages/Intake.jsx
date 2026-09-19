import React, { useState, useEffect } from 'react';
import { DropZone } from '../components/DropZone';
import { ProgressRing } from '../components/ProgressRing';
import { StatusRing } from '../components/StatusRing';
import { EvidenceIdBadge } from '../components/EvidenceIdBadge';
import { Check } from 'lucide-react';
import { cn } from '../lib/utils';
import { intakeEvidence } from '../lib/api';

export const Intake = () => {
  const [step, setStep] = useState(1);
  const [progress, setProgress] = useState(0);
  const [file, setFile] = useState(null);
  const [caseId, setCaseId] = useState('');
  const [collectorName, setCollectorName] = useState('');
  const [deviceId, setDeviceId] = useState('');
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (step === 2 && !isSubmitting) {
      setProgress(0);
      const interval = setInterval(() => {
        setProgress(p => {
          if (p >= 100) {
            clearInterval(interval);
            setTimeout(() => setStep(3), 500);
            return 100;
          }
          return p + 5;
        });
      }, 100);
      return () => clearInterval(interval);
    }
  }, [step, isSubmitting]);

  const handleSeal = async () => {
    if (!file) return;
    setIsSubmitting(true);
    try {
      const res = await intakeEvidence(file, caseId, collectorName, deviceId);
      setResult(res);
      setStep(4);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const steps = [
    { id: 1, title: 'Select File' },
    { id: 2, title: 'Hash & Verify' },
    { id: 3, title: 'Metadata' },
    { id: 4, title: 'Seal' }
  ];

  return (
    <div className="max-w-4xl mx-auto p-8 flex gap-12">
      <div className="w-48 shrink-0">
        <div className="sticky top-24 flex flex-col gap-8 relative">
          <div className="absolute left-[11px] top-4 bottom-4 w-0.5 bg-silver -z-10" />
          {steps.map(s => (
            <div key={s.id} className="flex items-center gap-4">
              <div className={cn(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-colors",
                step > s.id ? "bg-emerald border-emerald text-white" :
                step === s.id ? "bg-white border-cyan text-cyan ring-4 ring-cyan/20" :
                "bg-canvas border-silver text-silver"
              ) }>
                {step > s.id ? <Check size={12} /> : s.id}
              </div>
              <span className={cn(
                "font-medium",
                step >= s.id ? "text-ink" : "text-muted-ink"
              )}>
                {s.title}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1">
        <div className="surface p-8 rounded-3xl shadow-sm min-h-[400px] flex flex-col justify-center">
          {step === 1 && (
            <div className="animate-fade-in-up">
              <h2 className="font-heading text-2xl mb-6">Select Evidence</h2>
              <DropZone onFile={(f) => { setFile(f); setStep(2); }} label="Drag evidence file here or browse" />
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col items-center animate-fade-in-up">
              <ProgressRing progress={progress} size={160} />
              <h2 className="font-heading text-xl mt-6">Generating Cryptographic Hash</h2>
              <p className="text-muted-ink mt-2">Calculating SHA-256 for integrity verification...</p>
            </div>
          )}

          {step === 3 && (
            <div className="animate-fade-in-up">
              <h2 className="font-heading text-2xl mb-6">Enter Metadata</h2>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Case ID</label>
                  <input type="text" value={caseId} onChange={e => setCaseId(e.target.value)} className="w-full border border-silver rounded-lg p-3 bg-white focus:outline-none focus:border-cyan" placeholder="CASE-YYYY-XXXX" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Collector Name</label>
                  <input type="text" value={collectorName} onChange={e => setCollectorName(e.target.value)} className="w-full border border-silver rounded-lg p-3 bg-white focus:outline-none focus:border-cyan" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Device ID</label>
                  <input type="text" value={deviceId} onChange={e => setDeviceId(e.target.value)} className="w-full border border-silver rounded-lg p-3 bg-white focus:outline-none focus:border-cyan" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-1">Notes</label>
                  <textarea value={notes} onChange={e => setNotes(e.target.value)} className="w-full border border-silver rounded-lg p-3 bg-white h-24 focus:outline-none focus:border-cyan" placeholder="Description or circumstances..." />
                </div>
                <div className="pt-4 flex justify-end">
                  <button onClick={handleSeal} disabled={isSubmitting} className="rounded-full px-8 py-3 bg-cyan text-white font-medium hover:bg-cyan/90 transition-colors shadow-sm disabled:opacity-50">
                    {isSubmitting ? 'Sealing...' : 'Seal Evidence'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="flex flex-col items-center text-center animate-fade-in-up">
              <StatusRing status="verified" size="md">
                <Check size={32} className="text-emerald" />
              </StatusRing>
              <h2 className="font-heading text-3xl font-bold mt-6 mb-2 text-ink">Evidence Sealed</h2>
              <p className="text-muted-ink mb-8">The digital evidence has been cryptographically sealed and logged.</p>
              
              <div className="bg-canvas p-6 rounded-2xl w-full max-w-md border border-silver">
                <div className="text-sm text-muted-ink mb-2">Generated ID</div>
                <EvidenceIdBadge id={result?.evidence?.evidence_id || 'EV-000'} />
                
                <div className="mt-6 text-sm text-muted-ink mb-1">SHA-256 Hash</div>
                <div className="font-mono text-xs text-ink break-all p-3 bg-white rounded border border-silver">
                  {result?.evidence?.current_hash || 'hash_unavailable'}
                </div>
              </div>

              <button onClick={() => { setStep(1); setProgress(0); setFile(null); setResult(null); }} className="mt-8 rounded-full px-8 py-3 surface border border-silver text-ink font-medium hover:bg-canvas transition-colors">
                Process Another File
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
