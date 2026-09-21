import React, { useState } from 'react';
import { ClipboardCopy, Check, AlertCircle } from 'lucide-react';

function HashBlock({ label, hash }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { setCopied(false); }
  };

  return (
    <div className="flex-1 min-w-0">
      <div className="text-xs font-semibold text-muted-ink uppercase tracking-wider mb-2">{label}</div>
      <div className="flex items-center justify-between bg-canvas p-3 rounded-lg border border-silver">
        <span className="font-mono text-xs text-ink break-all mr-3">{hash || 'Not yet verified'}</span>
        <button aria-label={`Copy ${label}`} disabled={!hash} onClick={handleCopy} className="text-muted-ink hover:text-ink transition-colors flex-shrink-0">
          {copied ? <Check size={16} className="text-emerald" /> : <ClipboardCopy size={16} />}
        </button>
      </div>
    </div>
  );
}

export function HashDisplay({ original, current, originalHash, currentHash, mode = 'single' }) {
  // Support both prop naming conventions
  const origVal = original || originalHash || '';
  const currVal = current || currentHash || '';

  if (mode === 'single') {
    return <HashBlock label="Hash Fingerprint" hash={origVal} />;
  }

  const match = origVal === currVal;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-4 items-start">
        <HashBlock label="Original Fingerprint" hash={origVal} />
        <HashBlock label="Current Fingerprint" hash={currVal} />
      </div>
      <div className="flex items-center justify-center">
        {!origVal || !currVal ? <span className="text-muted-ink text-sm">Pending verification</span> : match ? (
          <div className="flex items-center gap-2 text-emerald text-sm font-medium bg-emerald/10 px-3 py-1 rounded-full border border-emerald/20">
            <Check size={16} /> Matches Original
          </div>
        ) : (
          <div className="flex items-center gap-2 text-gold text-sm font-medium bg-gold/10 px-3 py-1 rounded-full border border-gold/20">
            <AlertCircle size={16} /> Hash Mismatch
          </div>
        )}
      </div>
    </div>
  );
}
