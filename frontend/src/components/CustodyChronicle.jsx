import React from 'react';
import { cn } from '../lib/utils';
import { formatDateTime } from '../lib/utils';

export function CustodyChronicle({ events }) {
  return (
    <div className="relative pl-6 border-l-2 border-silver space-y-6">
      {events.map((event, index) => {
        const isNewest = index === events.length - 1;
        
        let dotColor = 'bg-cyan';
        if (event.status === 'VALID' || event.status === 'resolved') dotColor = 'bg-emerald';
        if (event.status === 'INVALID' || event.status === 'attention') dotColor = 'bg-gold';

        return (
          <div key={event.event_id || index} className={cn("relative glass-card p-4 rounded-xl border border-silver/50", !isNewest && "opacity-70")}>
            {/* Timeline Dot */}
            <div className={cn(
              "absolute -left-[31px] top-4 w-3 h-3 rounded-full border-2 border-white",
              dotColor,
              isNewest && "animate-pulse-ring"
            )} />
            
            <div className="flex justify-between items-start mb-2">
              <span className="font-semibold text-ink">{event.event_type}</span>
              <span className="font-mono text-xs text-muted-ink">
                {formatDateTime(event.timestamp)}
              </span>
            </div>
            
            <div className="text-sm text-ink mb-1">
              <span className="font-medium">{event.actor_id}</span>
              {event.device_id && <span className="text-muted-ink"> via {event.device_id}</span>}
            </div>
            
            {event.recipient_id && (
              <div className="text-sm text-muted-ink mb-1">
                To: <span className="text-ink">{event.recipient_id}</span>
              </div>
            )}
            
            {event.notes && (
              <p className="text-sm text-muted-ink mt-2 italic border-l-2 border-silver/50 pl-2">
                {event.notes}
              </p>
            )}
          </div>
        );
      })}
    </div>
  );
}
