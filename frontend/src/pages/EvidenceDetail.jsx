import React from 'react';
import { useParams } from 'react-router-dom';
import { StatusRing } from '../components/StatusRing';
import { EvidenceIdBadge } from '../components/EvidenceIdBadge';
import { HashDisplay } from '../components/HashDisplay';
import { MetadataPanel } from '../components/MetadataPanel';
import { CustodyChronicle } from '../components/CustodyChronicle';
import { formatBytes, formatDateTime } from '../lib/utils';
import { fetchEvidenceDetail } from '../lib/api';
import { cn } from '../lib/utils';

export const EvidenceDetail = () => {
  const { id } = useParams();
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetchEvidenceDetail(id).then(res => {
      setData(res);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <div className="p-8">Loading Evidence...</div>;
  if (!data) return <div className="p-8">Evidence not found</div>;

  const evidence = data;
  const events = data.events || [];

  const ringStatus = evidence.status === 'VERIFIED' ? 'verified' : evidence.status === 'MISMATCH' ? 'mismatch' : 'pending';

  return (
    <div className="grid grid-cols-12 gap-8 p-8">
      <div className="col-span-7 flex flex-col gap-8">
        <div className="surface rounded-2xl p-8 flex flex-col items-center text-center shadow-sm">
          <StatusRing size="hero" status={ringStatus}>
            <span className={cn(
              "font-heading text-2xl font-bold tracking-widest",
              evidence.status === 'VERIFIED' ? 'text-cyan' : 'text-gold'
            )}>
              {evidence.status}
            </span>
          </StatusRing>
          <div className="mt-6 flex flex-col items-center gap-2">
            <EvidenceIdBadge id={evidence.evidence_id} />
            <div className="text-lg text-ink font-medium">{evidence.original_filename}</div>
          </div>
        </div>

        <div className="surface rounded-2xl p-6 shadow-sm">
          <h3 className="font-heading text-lg font-semibold mb-4 text-ink">Integrity Verification</h3>
          <HashDisplay mode="compare" original={evidence.original_hash} current={evidence.current_hash} />
        </div>

        <div className="flex gap-4">
          <button className="rounded-full px-6 py-2.5 bg-cyan text-white font-medium hover:bg-cyan/90 transition-colors shadow-sm">
            Verify Now
          </button>
          <button className="rounded-full px-6 py-2.5 surface text-ink font-medium hover:bg-canvas transition-colors shadow-sm">
            Log Action
          </button>
          <button className="rounded-full px-6 py-2.5 surface text-ink font-medium hover:bg-canvas transition-colors shadow-sm">
            Generate Report
          </button>
          <button className="rounded-full px-6 py-2.5 surface text-ink font-medium hover:bg-canvas transition-colors shadow-sm">
            Export
          </button>
        </div>

        <div className="surface rounded-2xl p-6 shadow-sm">
          <MetadataPanel 
            metadata={{
              Collector: evidence.collector_id,
              Device: evidence.collection_device_id,
              Timestamp: formatDateTime(evidence.collection_timestamp),
              'File Type': evidence.file_type,
              'File Size': formatBytes(evidence.file_size),
              'Case ID': evidence.case_id,
              Description: evidence.description
            }} 
          />
        </div>
        
        <div className="surface rounded-2xl p-6 shadow-sm flex justify-between items-center">
          <div>
            <div className="text-sm text-muted-ink">Current Custodian</div>
            <div className="text-ink font-medium">{evidence.current_custodian}</div>
          </div>
          <div>
            <div className="text-sm text-muted-ink">Sync Status</div>
            <div className={cn(
              "font-medium",
              evidence.sync_status === 'SYNCED' ? "text-emerald" : "text-gold"
            )}>
              {evidence.sync_status}
            </div>
          </div>
        </div>
      </div>
      
      <div className="col-span-5 relative">
        <div className="sticky top-20">
          <h2 className="font-heading text-xl text-ink font-semibold mb-6">Custody Chronicle</h2>
          <div className="glass-panel p-6 rounded-2xl shadow-sm">
             <CustodyChronicle events={events} />
          </div>
        </div>
      </div>
    </div>
  );
};
