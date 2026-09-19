import React from 'react';
import { cn } from '../lib/utils';

const colorMap = {
  verified: 'text-cyan',
  mismatch: 'text-gold',
  pending: 'text-deep-silver'
};

const sizeMap = {
  sm: { outer: 40, middle: 32, inner: 24, stroke: 1.5 },
  md: { outer: 80, middle: 68, inner: 56, stroke: 2 },
  hero: { outer: 192, middle: 168, inner: 144, stroke: 3 } // w-48 is 192px
};

export function StatusRing({ status = 'pending', size = 'md', children }) {
  const colorClass = colorMap[status];
  const dims = sizeMap[size];
  const center = dims.outer / 2;
  const isHero = size === 'hero';

  return (
    <div className={cn("relative flex items-center justify-center", colorClass)} style={{ width: dims.outer, height: dims.outer }}>
      <svg className="absolute inset-0 w-full h-full" viewBox={`0 0 ${dims.outer} ${dims.outer}`}>
        <circle 
          cx={center} cy={center} r={(dims.outer - dims.stroke) / 2} 
          fill="none" stroke="currentColor" strokeWidth={dims.stroke} strokeOpacity="0.2"
          className={cn(isHero && "animate-pulse-ring")}
        />
        <circle 
          cx={center} cy={center} r={(dims.middle - dims.stroke) / 2} 
          fill="none" stroke="currentColor" strokeWidth={dims.stroke} strokeOpacity="0.5"
        />
        <circle 
          cx={center} cy={center} r={(dims.inner - dims.stroke) / 2} 
          fill="none" stroke="currentColor" strokeWidth={dims.stroke}
        />
      </svg>
      <div className="relative z-10 flex items-center justify-center">
        {children}
      </div>
    </div>
  );
}
