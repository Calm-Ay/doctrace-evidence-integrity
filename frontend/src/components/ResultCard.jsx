import React from 'react';
import { cn } from '../lib/utils';

export function ResultCard({ name, recipientId, confidence, extra, result }) {
  // Support both direct props and a result object
  const rName = name || (result && result.name) || 'Unknown';
  const rId = recipientId || (result && result.recipient_id) || '';
  const rConf = confidence ?? (result && result.confidence) ?? 0;
  const rExtra = extra || (result && { method: result.method, date: result.date_stamped });

  let barColor = 'bg-gold';
  if (rConf >= 90) barColor = 'bg-emerald';
  else if (rConf >= 70) barColor = 'bg-cyan';

  return (
    <div className="surface p-4 rounded-xl border border-silver flex flex-col gap-3">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-heading font-semibold text-ink text-lg">{rName}</h3>
          <p className="font-mono text-sm text-muted-ink">{rId}</p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-mono font-bold text-ink">{rConf}%</div>
          {rConf < 70 && <div className="text-xs font-semibold text-gold uppercase tracking-wider">Low confidence</div>}
        </div>
      </div>
      
      <div className="w-full h-2 bg-canvas rounded-full overflow-hidden">
        <div 
          className={cn("h-full transition-all duration-500", barColor)} 
          style={{ width: `${rConf}%` }} 
        />
      </div>

      {rExtra && Object.keys(rExtra).filter(k => rExtra[k]).length > 0 && (
        <div className="grid grid-cols-2 gap-2 mt-2 pt-3 border-t border-silver/50">
          {Object.entries(rExtra).filter(([, v]) => v).map(([k, v]) => (
            <div key={k} className="flex flex-col">
              <span className="text-[10px] uppercase text-muted-ink tracking-wider">{k}</span>
              <span className="text-xs font-medium text-ink truncate">{String(v)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
