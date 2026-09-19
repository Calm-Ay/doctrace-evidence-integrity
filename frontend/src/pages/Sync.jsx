import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { cn } from '../lib/utils';
import { fetchSyncStatus, triggerSync } from '../lib/api';

export const Sync = () => {
  const [syncQueue, setSyncQueue] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [syncing, setSyncing] = React.useState(false);

  const loadStatus = () => {
    setLoading(true);
    fetchSyncStatus().then(data => {
      // If API returns an array, use it; otherwise fallback to empty
      setSyncQueue(Array.isArray(data) ? data : (data.queue || []));
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  };

  React.useEffect(() => {
    loadStatus();
  }, []);

  const handleForceSync = async () => {
    setSyncing(true);
    try {
      await triggerSync();
      loadStatus();
    } catch (e) {
      console.error(e);
    } finally {
      setSyncing(false);
    }
  };
  const stats = {
    synced: syncQueue.filter(i => i.sync_status === 'SYNCED').length,
    pending: syncQueue.filter(i => i.sync_status === 'PENDING').length,
    local: syncQueue.filter(i => i.sync_status === 'LOCAL').length,
    conflicts: syncQueue.filter(i => i.sync_status === 'CONFLICT').length,
  };

  if (loading && syncQueue.length === 0) return <div className="p-8">Loading Sync Status...</div>;

  const getStatusColor = (status) => {
    switch (status) {
      case 'SYNCED': return 'text-emerald bg-emerald/10 border-emerald/20';
      case 'PENDING': return 'text-gold bg-gold/10 border-gold/20';
      case 'LOCAL': return 'text-muted-ink bg-silver/20 border-silver/50';
      case 'CONFLICT': return 'text-gold bg-gold/10 border-gold/30';
      default: return 'text-ink bg-canvas border-silver';
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="font-heading text-3xl font-semibold text-ink">Synchronization</h1>
          <p className="text-muted-ink mt-2">
            {stats.synced} synced, {stats.pending} pending, {stats.local} local, {stats.conflicts} conflicts
          </p>
        </div>
        <button 
          onClick={handleForceSync}
          disabled={syncing}
          className="rounded-full px-6 py-2.5 bg-cyan text-white font-medium hover:bg-cyan/90 transition-colors shadow-sm disabled:opacity-50">
          {syncing ? 'Syncing...' : 'Force Sync'}
        </button>
      </div>

      <div className="flex flex-col gap-3">
        {syncQueue.length === 0 && <div className="text-muted-ink">No items in sync queue.</div>}
        {syncQueue.map((item) => (
          <div key={item.event_id} className={cn(
            "surface p-4 rounded-xl shadow-sm border-l-4 flex items-center justify-between",
            item.sync_status === 'SYNCED' ? "border-emerald" : 
            (item.sync_status === 'CONFLICT' || item.sync_status === 'PENDING') ? "border-gold" : 
            "border-deep-silver"
          )}>
            
            <div className="flex items-center gap-6">
              {item.sync_status === 'CONFLICT' && <AlertTriangle className="text-gold h-5 w-5" />}
              <div>
                <div className="font-mono text-xs text-muted-ink mb-1">{item.event_id}</div>
                <div className="font-medium text-ink">{item.action}</div>
              </div>
              <div className="pl-6 border-l border-silver">
                <div className="text-xs text-muted-ink mb-1">Evidence ID</div>
                <div className="font-mono text-sm">{item.evidence_id}</div>
              </div>
            </div>
            
            <div className={cn("px-3 py-1 rounded-full text-xs font-bold tracking-wider border", getStatusColor(item.sync_status))}>
              {item.sync_status}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
