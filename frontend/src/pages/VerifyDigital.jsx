import React, { useState } from 'react';
import { DropZone } from '../components/DropZone';
import { verifyDigital } from '../lib/api';
export const VerifyDigital = () => {
  const [view, setView] = useState('upload'); // 'upload' | 'loading' | 'results'
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    if (!file) return;
    setView('loading');
    setError('');
    try {
      const data = await verifyDigital(file);
      setResult(data);
      setView('results');
    } catch (e) {
      console.error(e);
      setError(e.message);
      setView('upload');
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 font-sans">
      {view === 'upload' ? (
        <div className="flex flex-col items-center gap-8 mt-12">
          {error && <p role="alert" className="text-red-700">{error}</p>}
          <div className="w-full">
            <DropZone label="Upload leaked PDF for verification" onFile={setFile} />
          </div>
          {file && <div className="text-sm text-cyan text-center">Selected: {file.name}</div>}
          <button
            onClick={handleVerify}
            disabled={!file}
            className="bg-cyan text-white rounded-full px-8 py-3 font-medium hover:bg-cyan/90 transition-colors disabled:opacity-50"
          >
            Verify Document
          </button>
        </div>
      ) : view === 'loading' ? (
        <div className="mt-12 text-center text-ink">Verifying document...</div>
      ) : (
        <div className="mt-8">
          <h2 className="text-2xl font-heading text-ink mb-6">Verification Result</h2>
          <div className={`rounded-xl border p-6 ${result?.status === 'VERIFIED' ? 'border-emerald bg-emerald/5' : 'border-silver bg-canvas'}`}>
            <div className="text-xl font-bold mb-3">{result?.status?.replace('_', ' ')}</div>
            {result?.copy_id && <div className="text-sm mb-2"><span className="text-muted-ink">Copy ID:</span> <span className="font-mono break-all">{result.copy_id}</span></div>}
            {result?.recipient && <div className="text-sm mb-2"><span className="text-muted-ink">Recipient:</span> {result.recipient}</div>}
            {result?.document && <div className="text-sm"><span className="text-muted-ink">Document:</span> {result.document}</div>}
          </div>
          <p className="text-sm text-muted-ink mt-6 text-center italic">
            {result?.status === 'VERIFIED' ? 'The identifier matches a registry entry. This does not prove who disclosed the document or verify its contents.' : 'No registered copy was identified from this PDF.'}
          </p>
          <div className="mt-8 text-center">
            <button
              onClick={() => { setView('upload'); setFile(null); }}
              className="text-cyan text-sm font-medium hover:underline"
            >
              Verify Another Document
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
