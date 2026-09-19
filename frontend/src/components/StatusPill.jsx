import React from 'react';
import { cn } from '../lib/utils';

const variantClasses = {
  cyan: 'bg-cyan/10 text-cyan border-cyan/20',
  emerald: 'bg-emerald/10 text-emerald border-emerald/20',
  gold: 'bg-gold/10 text-gold border-gold/20',
  silver: 'bg-silver/10 text-muted-ink border-silver/50',
};

// Maps raw status values to (variant, label) so pages can pass status strings directly
const statusMap = {
  VERIFIED: { variant: 'cyan', label: 'Verified' },
  MATCH: { variant: 'cyan', label: 'Match' },
  VALID: { variant: 'emerald', label: 'Valid' },
  MISMATCH: { variant: 'gold', label: 'Mismatch' },
  INVALID: { variant: 'gold', label: 'Invalid' },
  PENDING: { variant: 'gold', label: 'Pending' },
  SYNCED: { variant: 'emerald', label: 'Synced' },
  LOCAL: { variant: 'silver', label: 'Local' },
  CONFLICT: { variant: 'gold', label: 'Conflict' },
};

export function StatusPill({ variant, status, children, className }) {
  // Allow direct variant + children OR automatic from status string
  let resolvedVariant = variant || 'silver';
  let resolvedLabel = children;

  if (status && statusMap[status]) {
    resolvedVariant = statusMap[status].variant;
    resolvedLabel = resolvedLabel || statusMap[status].label;
  }

  // If variant is a raw color name (cyan/emerald/gold/silver), use it directly
  if (!variantClasses[resolvedVariant]) {
    resolvedVariant = 'silver';
  }

  return (
    <span className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border",
      variantClasses[resolvedVariant],
      className
    )}>
      {resolvedLabel || status || 'Unknown'}
    </span>
  );
}
