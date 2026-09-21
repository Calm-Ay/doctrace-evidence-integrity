import React from 'react';

export function MetadataPanel({ items, metadata }) {
  // Support both items array [{label, value}] and metadata object {key: value}
  let resolvedItems = items;
  if (!resolvedItems && metadata) {
    resolvedItems = Object.entries(metadata).map(([label, value]) => ({ label, value: value || 'N/A' }));
  }
  if (!resolvedItems) resolvedItems = [];

  return (
    <div className="grid grid-cols-2 gap-4">
      {resolvedItems.map((item, i) => (
        <div key={i} className="flex flex-col">
          <span className="text-xs uppercase text-muted-ink tracking-wider mb-1">{item.label}</span>
          <span className="text-sm font-medium text-ink">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
