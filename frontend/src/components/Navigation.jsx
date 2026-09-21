import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, Database, UploadCloud, ShieldCheck, FileText,
  Stamp, FileSearch, Camera, BookOpen, Activity, Settings
} from 'lucide-react';
import { cn } from '../lib/utils';

const navItems1 = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Cases' },
  { to: '/evidence', icon: Database, label: 'Evidence' },
  { to: '/intake', icon: UploadCloud, label: 'Intake' },
  { to: '/verify', icon: ShieldCheck, label: 'Verify' },
  { to: '/report', icon: FileText, label: 'Report' },
];

const navItems2 = [
  { to: '/stamp', icon: Stamp, label: 'Stamp' },
  { to: '/verify-digital', icon: FileSearch, label: 'Verify PDF' },
  { to: '/identify', icon: Camera, label: 'Identify' },
  { to: '/registry', icon: BookOpen, label: 'Registry' },
];

function NavItem({ to, icon: Icon, label }) {
  const [hover, setHover] = useState(false);
  return (
    <div 
      className="relative flex items-center justify-center my-2 w-full"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <NavLink
        aria-label={label}
        to={to}
        className={({ isActive }) => cn(
          "w-10 h-10 rounded-full flex items-center justify-center transition-colors text-muted-ink hover:text-ink hover:bg-silver/30",
          isActive && "border-[1.5px] border-cyan text-cyan bg-cyan/10 hover:bg-cyan/20"
        )}
      >
        <Icon size={20} />
      </NavLink>
      {hover && (
        <div className="absolute left-[68px] bg-ink text-white text-xs px-2 py-1 rounded whitespace-nowrap shadow-md z-50">
          {label}
        </div>
      )}
    </div>
  );
}

export function Navigation() {
  const [settingsHover, setSettingsHover] = useState(false);
  const [syncHover, setSyncHover] = useState(false);

  return (
    <nav className="glass-nav fixed top-0 left-0 h-screen w-[72px] z-50 flex flex-col items-center py-4 border-r border-silver bg-white/80 backdrop-blur-md">
      <div className="flex flex-col w-full items-center">
        {navItems1.map(item => (
          <NavItem key={item.to} {...item} />
        ))}
      </div>
      
      <div className="w-8 h-px bg-silver my-4" />
      
      <div className="flex flex-col w-full items-center">
        {navItems2.map(item => (
          <NavItem key={item.to} {...item} />
        ))}
      </div>
      
      <div className="mt-auto flex flex-col w-full items-center">
        <div 
          className="relative flex items-center justify-center my-2 w-full"
          onMouseEnter={() => setSyncHover(true)}
          onMouseLeave={() => setSyncHover(false)}
        >
          <NavLink
            aria-label="Sync status"
            to="/sync"
            className={({ isActive }) => cn(
              "w-10 h-10 rounded-full flex items-center justify-center transition-colors text-muted-ink hover:text-ink hover:bg-silver/30",
              isActive && "border-[1.5px] border-cyan text-cyan bg-cyan/10 hover:bg-cyan/20"
            )}
          >
            <Activity size={20} />
          </NavLink>
          {syncHover && (
            <div className="absolute left-[68px] bg-ink text-white text-xs px-2 py-1 rounded whitespace-nowrap shadow-md z-50">
              Sync Indicator
            </div>
          )}
        </div>

        <div 
          className="relative flex items-center justify-center my-2 w-full"
          onMouseEnter={() => setSettingsHover(true)}
          onMouseLeave={() => setSettingsHover(false)}
        >
          <button disabled aria-label="Settings unavailable in this demo" className="w-10 h-10 rounded-full flex items-center justify-center text-muted-ink opacity-40">
            <Settings size={20} />
          </button>
          {settingsHover && (
            <div className="absolute left-[68px] bg-ink text-white text-xs px-2 py-1 rounded whitespace-nowrap shadow-md z-50">
              Settings unavailable in this demo
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
