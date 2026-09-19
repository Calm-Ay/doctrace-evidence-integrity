import React, { useState } from 'react';
import { DropZone } from '../components/DropZone';
import { ProgressRing } from '../components/ProgressRing';
import { stampDocument, stampedDownloadUrl } from '../lib/api';

const recipientsList = [
  { id: 'R001', name: 'Adewale Bakare', email: 'a.bakare@firm.ng' },
  { id: 'R002', name: 'Chinyere Okoye', email: 'c.okoye@firm.ng' },
  { id: 'R003', name: 'Emeka Nwosu', email: 'e.nwosu@firm.ng' },
  { id: 'R004', name: 'Fatima Abdullahi', email: 'f.abdullahi@firm.ng' },
  { id: 'R005', name: 'Grace Adekunle', email: 'g.adekunle@firm.ng' },
];

export const StampDocuments = () => {
  const [file, setFile] = useState(null);
  const [isStamping, setIsStamping] = useState(false);
  const [progress, setProgress] = useState(0);
  const [success, setSuccess] = useState(false);
  const [stampResult, setStampResult] = useState(null);
  const [error, setError] = useState('');

  const handleStamp = async () => {
    setIsStamping(true);
    setProgress(0);
    setError('');
    try {
      // Simulate progress for UI purposes while awaiting API
      const interval = setInterval(() => {
        setProgress(p => Math.min(p + 15, 90));
      }, 300);

      if (file) {
        // Just stamping for the first recipient as a demo
        const result = await stampDocument(file, recipientsList[0].id);
        setStampResult(result);
      }
      
      clearInterval(interval);
      setProgress(100);
      setTimeout(() => {
        setIsStamping(false);
        setSuccess(true);
      }, 500);
    } catch (e) {
      console.error(e);
      setError(e.message || 'Stamping failed');
      setIsStamping(false);
    }
  };

  const handleFileDrop = (file) => {
    if (file) {
      setFile(file);
    } else {
      // Dummy object if standard file upload is mocked
      setFile({ name: 'document-to-stamp.pdf' });
    }
  };

  return (
    <div className="grid grid-cols-12 gap-6 p-6 font-sans">
      {/* Left: Original Document */}
      <div className="col-span-4 bg-white border border-silver rounded-xl p-6 surface">
        <h2 className="text-xl font-heading text-ink mb-4">Original Document</h2>
        <div onClick={() => handleFileDrop()}>
          <DropZone label="Upload PDF" onFile={handleFileDrop} />
        </div>
        {file && (
          <div className="mt-4 p-4 border border-silver rounded-lg">
            <p className="text-sm text-ink truncate font-medium">Filename: {file.name}</p>
            <p className="text-xs text-emerald font-medium mt-1">Ready</p>
          </div>
        )}
      </div>

      {/* Center: Recipients */}
      <div className="col-span-5 bg-white border border-silver rounded-xl p-6 surface">
         <h2 className="text-xl font-heading text-ink mb-4">Recipients</h2>
         <div className="overflow-auto max-h-64 mb-4">
           <table className="w-full text-left border-collapse">
             <thead>
               <tr className="border-b border-silver text-muted-ink text-sm">
                 <th className="pb-2 font-medium">ID</th>
                 <th className="pb-2 font-medium">Name</th>
                 <th className="pb-2 font-medium">Email</th>
               </tr>
             </thead>
             <tbody>
               {recipientsList.map(r => (
                 <tr key={r.id} className="border-b border-silver/50 last:border-0 text-sm">
                   <td className="py-2 font-mono text-xs text-muted-ink">{r.id}</td>
                   <td className="py-2 text-ink">{r.name}</td>
                   <td className="py-2 text-ink">{r.email}</td>
                 </tr>
               ))}
             </tbody>
           </table>
         </div>
         <div className="flex gap-4">
           <button className="bg-canvas border border-silver text-ink px-4 py-2 rounded-lg text-sm hover:bg-silver/20 transition-colors">Import CSV</button>
           <button className="bg-canvas border border-silver text-ink px-4 py-2 rounded-lg text-sm hover:bg-silver/20 transition-colors">Add Recipient</button>
         </div>
      </div>

      {/* Right: Options */}
      <div className="col-span-3 bg-white border border-silver rounded-xl p-6 surface">
         <h2 className="text-xl font-heading text-ink mb-4">Options</h2>
         <div className="space-y-4">
           <div>
             <label className="block text-sm text-muted-ink mb-1">Watermark Bits</label>
             <input type="number" defaultValue={32} className="w-full border border-silver rounded-lg px-3 py-2 text-sm text-ink focus:outline-none focus:border-cyan" />
           </div>
           <div>
             <label className="block text-sm text-muted-ink mb-1">Output Directory</label>
             <input type="text" defaultValue="./stamped" className="w-full border border-silver rounded-lg px-3 py-2 text-sm text-ink focus:outline-none focus:border-cyan" />
           </div>
           <div className="flex items-center gap-2 pt-2">
             <input type="checkbox" id="encrypt" className="w-4 h-4 text-cyan border-silver rounded accent-cyan" />
             <label htmlFor="encrypt" className="text-sm text-ink">Encrypt output</label>
           </div>
         </div>
      </div>

      {/* Bottom Action Bar */}
      <div className="col-span-12 flex flex-col items-center justify-center mt-6">
        {error && <p className="text-red-700 text-sm mb-4">{error}</p>}
        {!isStamping && !success && (
          <button
            onClick={handleStamp}
            disabled={!file}
            className="bg-cyan text-white rounded-full px-8 py-3 font-medium hover:bg-cyan/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Stamp Documents
          </button>
        )}
        {isStamping && (
          <div className="flex flex-col items-center gap-4">
            <ProgressRing progress={progress} />
            <p className="text-sm text-muted-ink animate-pulse">Stamping documents...</p>
          </div>
        )}
        {success && (
          <div className="text-center">
            <p className="text-emerald text-lg font-medium mb-2">1 stamped copy created and registered</p>
            <p className="font-mono text-xs text-muted-ink mb-3">Copy ID: {stampResult?.copy_id}</p>
            <div className="flex items-center justify-center gap-4">
              <a href={stampedDownloadUrl(stampResult?.download_url)} className="text-cyan text-sm hover:underline font-medium">Download stamped PDF</a>
              <button onClick={() => { setSuccess(false); setStampResult(null); }} className="text-cyan text-sm hover:underline font-medium">Stamp Another</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
