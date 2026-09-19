import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { StatusRing } from '../components/StatusRing';
import { StatusPill } from '../components/StatusPill';
import { HashDisplay } from '../components/HashDisplay';
import { verifyEvidence } from '../lib/api';
import { DropZone } from '../components/DropZone';

export const Verification = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [evidenceId, setEvidenceId] = useState('');

  const handleVerify = async () => {
    if (!file || !evidenceId) return;
    setLoading(true);
    try {
      const res = await verifyEvidence(evidenceId, file);
      setData(res);
    } catch (err) {
      console.error(err);
      alert('Verification failed. See console.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="p-12 text-center">Verifying Integrity...</div>;

  if (!data) return (
    <div className="max-w-2xl mx-auto p-12">
      <div className="surface rounded-3xl p-10 flex flex-col items-center text-center shadow-sm">
        <h1 className="font-heading text-3xl font-bold mb-6">Verify Evidence Integrity</h1>
        <div className="w-full mb-6 text-left">
          <label className="block text-sm font-medium text-ink mb-1">Evidence ID</label>
          <input type="text" placeholder="EV-202X-XXXXXX" value={evidenceId} onChange={e => setEvidenceId(e.target.value)} className="w-full border border-silver rounded-lg p-3 bg-white focus:outline-none focus:border-cyan" />
        </div>
        <div className="w-full mb-6">
          <DropZone onFile={setFile} label="Upload evidence file to verify" />
        </div>
        <button onClick={handleVerify} disabled={!file || !evidenceId} className="rounded-full px-8 py-3 bg-cyan text-white font-medium hover:bg-cyan/90 transition-colors shadow-sm disabled:opacity-50">
          Verify Integrity
        </button>
      </div>
    </div>
  );

  const isVerified = data.evidence_result === 'MATCH';
  const ringStatus = isVerified ? 'verified' : 'mismatch';
  
  return (
    <div className="max-w-2xl mx-auto p-12">
      <div className="surface rounded-3xl p-10 flex flex-col items-center text-center shadow-sm">
        <StatusRing size="md" status={ringStatus}>
          <span className={`font-heading text-lg font-bold ${isVerified ? 'text-cyan' : 'text-gold'}`}>
            {isVerified ? '✓' : '✗'}
          </span>
        </StatusRing>
        
        <h1 className={`font-heading text-3xl font-bold mt-6 mb-4 tracking-wide ${isVerified ? 'text-emerald' : 'text-gold'}`}>
          {isVerified ? 'INTEGRITY VERIFIED' : 'INTEGRITY MISMATCH DETECTED'}
        </h1>
        
        <StatusPill status={data.chain_result} />
        
        <div className="w-full mt-10 mb-8 text-left">
          <HashDisplay mode="compare" original={data.expected_hash} current={data.actual_hash} />
        </div>
        
        <p className="text-ink leading-relaxed mb-10 bg-canvas p-6 rounded-xl border border-silver text-left">
          {isVerified 
            ? "The cryptographic hash of the current file perfectly matches the original hash generated at the time of collection. The chain of custody is intact with no unauthorized modifications detected."
            : "The current file's cryptographic hash does not match the original collection hash. This indicates the file has been modified or corrupted since it was initially sealed."
          }
        </p>
        
        <button onClick={() => { setData(null); setFile(null); setEvidenceId(''); }} className="inline-block rounded-full px-8 py-3 surface border border-silver text-ink font-medium hover:bg-canvas transition-colors mt-4">
          Verify Another File
        </button>
      </div>
    </div>
  );
};
