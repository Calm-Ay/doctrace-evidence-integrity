import React, { useState, useEffect } from 'react';

export function HeaderBar({ title }) {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const formattedTime = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <header className="h-14 border-b border-silver bg-white sticky top-0 z-40 flex items-center justify-between px-6">
      <h1 className="font-heading font-semibold text-ink text-lg">{title}</h1>
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 px-3 py-1 bg-canvas rounded-full border border-silver">
          <div className="w-2 h-2 rounded-full bg-cyan"></div>
          <span className="text-xs font-semibold tracking-wider text-ink">LOCAL DEMO</span>
        </div>
        <div className="font-mono text-muted-ink text-sm">
          {formattedTime}
        </div>
      </div>
    </header>
  );
}
