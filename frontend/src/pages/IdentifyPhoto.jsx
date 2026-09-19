import React, { useState } from 'react';
import { cn } from '../lib/utils';
import { DropZone } from '../components/DropZone';
import { ResultCard } from '../components/ResultCard';
import { AlertTriangle } from 'lucide-react';
import { identifyPhoto } from '../lib/api';

export const IdentifyPhoto = () => {
  const [view, setView] = useState('upload'); // 'upload' | 'loading' | 'results'
  const [file, setFile] = useState(null);
  const [results, setResults] = useState([]);

  const handleIdentify = async () => {
    if (!file) return;
    setView('loading');
    try {
      const data = await identifyPhoto(file);
      // Ensure data is an array
      setResults(Array.isArray(data) ? data : (data.results || []));
      setView('results');
    } catch (e) {
      console.error(e);
      setView('upload');
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 font-sans">
      {view === 'upload' ? (
        <div className="flex flex-col items-center gap-8 mt-12">
          <div className="grid grid-cols-2 gap-6 w-full">
            <DropZone label="Upload photo of leaked page" required onFile={setFile} />
            <DropZone label="Upload original PDF (optional)" hint="(for alignment)" />
          </div>
          {file && <div className="text-sm text-cyan text-center">Selected: {file.name}</div>}
          <button
            onClick={handleIdentify}
            disabled={!file}
            className="bg-cyan text-white rounded-full px-8 py-3 font-medium hover:bg-cyan/90 transition-colors disabled:opacity-50"
          >
            Identify Source
          </button>
        </div>
      ) : view === 'loading' ? (
        <div className="mt-12 text-center text-ink">Analyzing photo...</div>
      ) : (
        <div className="mt-8">
          <div className="bg-pale-gold/30 border border-gold/30 rounded-xl p-4 mb-6 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-gold shrink-0 mt-0.5" />
            <p className="text-sm text-ink font-medium">
              Layer 2 identification can be unreliable on low-resolution photos. Results with confidence below 70% should be treated with caution.
            </p>
          </div>
          <h2 className="text-2xl font-heading text-ink mb-6">Match Results</h2>
          <div className="space-y-4">
            {results.map((result, idx) => (
              <div key={idx} className={cn(
                "rounded-xl overflow-hidden border-2",
                result.confidence >= 90 ? "border-emerald/50" : (result.confidence < 70 ? "border-gold/50" : "border-transparent")
              )}>
                <ResultCard result={result} />
              </div>
            ))}
          </div>
          <div className="mt-8 text-center">
            <button
              onClick={() => { setView('upload'); setFile(null); }}
              className="text-cyan text-sm font-medium hover:underline"
            >
              Identify Another Photo
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
