import React from 'react';
import { Link } from 'react-router-dom';
import { EvidenceIdBadge } from '../components/EvidenceIdBadge';
import { StatusPill } from '../components/StatusPill';
import { formatBytes, formatDate } from '../lib/utils';
import { fetchEvidenceList } from '../lib/api';

export const EvidenceList = () => {
  const [evidenceList, setEvidenceList] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetchEvidenceList().then(data => {
      setEvidenceList(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <div className="surface rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-silver bg-canvas/30 flex justify-between items-center">
          <h1 className="font-heading text-2xl text-ink font-semibold">Evidence Inventory</h1>
        </div>
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-silver bg-canvas/50 text-muted-ink text-sm">
              <th className="py-4 px-6 font-medium">Evidence ID</th>
              <th className="py-4 px-6 font-medium">Filename</th>
              <th className="py-4 px-6 font-medium">Size</th>
              <th className="py-4 px-6 font-medium">Integrity</th>
              <th className="py-4 px-6 font-medium">Chain</th>
              <th className="py-4 px-6 font-medium">Last Action</th>
              <th className="py-4 px-6 font-medium">Collection Date</th>
            </tr>
          </thead>
          <tbody>
            {evidenceList.map((ev) => (
              <tr key={ev.evidence_id} className="border-b border-silver/50 hover:bg-canvas/50 transition-colors group">
                <td className="py-4 px-6">
                  <Link to={`/evidence/${ev.evidence_id}`} className="block">
                    <EvidenceIdBadge id={ev.evidence_id} />
                  </Link>
                </td>
                <td className="py-4 px-6 text-ink font-medium">
                  <Link to={`/evidence/${ev.evidence_id}`} className="block">{ev.original_filename}</Link>
                </td>
                <td className="py-4 px-6 text-muted-ink text-sm">{formatBytes(ev.file_size)}</td>
                <td className="py-4 px-6">
                  <StatusPill status={ev.status} />
                </td>
                <td className="py-4 px-6">
                  <StatusPill status={ev.chain_status} />
                </td>
                <td className="py-4 px-6 text-sm">
                  <div className="text-ink">{ev.last_action}</div>
                  <div className="text-muted-ink">{ev.last_actor}</div>
                </td>
                <td className="py-4 px-6 text-muted-ink text-sm">{formatDate(ev.collection_timestamp)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
