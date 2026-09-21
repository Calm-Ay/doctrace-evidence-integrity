import React, { useState } from 'react';
import { DropZone } from '../components/DropZone';
import { stampDocument, stampedDownloadUrl } from '../lib/api';
export const StampDocuments = () => {
  const [file, setFile] = useState(null);
  const [recipient, setRecipient] = useState('');
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  async function stamp() {
    if (!file || !recipient.trim()) return;
    setBusy(true); setError(''); setResult(null);
    try { setResult(await stampDocument(file, recipient.trim())); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  return <div className="grid grid-cols-12 gap-6 p-6 font-sans">
    <div className="col-span-7 surface rounded-xl p-6">
      <h2 className="text-xl font-heading mb-4">Original Document</h2>
      <DropZone label="Upload original PDF" onFile={f => {setFile(f); setResult(null); setError('');}} />
      {file && <p className="my-4">Selected: {file.name}</p>}
      <label className="block mt-6">Recipient ID (use synthetic data)
        <input aria-label="Recipient ID" value={recipient} onChange={e => {setRecipient(e.target.value); setResult(null);}} placeholder="DEMO-RECIPIENT-001" className="block border border-silver rounded-lg p-3 w-full mt-2" />
      </label>
      <button disabled={busy || !file || !recipient.trim()} onClick={stamp} className="bg-cyan text-white rounded-full px-8 py-3 mt-6 disabled:opacity-50">{busy ? 'Stamping PDF…' : 'Stamp Document'}</button>
      {error && <p role="alert" className="text-red-700 mt-4">{error}</p>}
      {result && <div className="mt-6"><p>1 stamped copy created and registered</p><p className="font-mono text-xs break-all my-3">Copy ID: {result.copy_id}</p><a className="text-cyan underline" href={stampedDownloadUrl(result.download_url)}>Download stamped PDF</a></div>}
    </div>
    <div className="col-span-5 surface rounded-xl p-6"><h2 className="text-xl font-heading mb-4">Digital provenance</h2><p>Embeds an invisible text identifier in a new PDF copy. The original file is not modified.</p><p className="mt-4">Registry matching identifies a registered copy, not who disclosed it. It does not verify file integrity. Use Evidence Verification for SHA-256 comparison.</p><p className="mt-4">One recipient per upload. Encryption and photo recovery are not available in this demo.</p></div>
  </div>;
};
