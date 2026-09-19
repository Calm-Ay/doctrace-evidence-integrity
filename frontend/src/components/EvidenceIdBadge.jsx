import React, { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { cn } from '../lib/utils';

export function EvidenceIdBadge({ id }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className={cn(
        "flex items-center gap-2 font-mono text-sm bg-canvas px-3 py-1 rounded-full border border-silver transition-colors hover:bg-silver/20",
        copied ? "text-emerald border-emerald/50" : "text-ink"
      )}
      title="Copy to clipboard"
    >
      <span>{id}</span>
      {copied ? <Check size={14} className="text-emerald" /> : <Copy size={14} className="text-muted-ink" />}
    </button>
  );
}
