import React from 'react';
import { StatusRing } from '../components/StatusRing';
import { StatusPill } from '../components/StatusPill';
import { CustodyChronicle } from '../components/CustodyChronicle';
import { fetchCases, fetchEvidenceList } from '../lib/api';
export const Dashboard = () => {
  const [cases, setCases] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [evidence, setEvidence] = React.useState([]);
  const [error, setError] = React.useState('');
  const recentEvents = evidence.flatMap(e => e.events || []).sort((a,b) => b.timestamp.localeCompare(a.timestamp)).slice(0,5).reverse();
  const matches = evidence.filter(e => e.status === 'MATCH' && e.chain_status === 'VALID').length;

  React.useEffect(() => {
    Promise.all([fetchCases(), fetchEvidenceList()]).then(([data, records]) => {
      setCases(data); setEvidence(records);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setError(err.message);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-8">Loading Dashboard...</div>;
  if (error) return <div role="alert" className="p-8">{error}</div>;

  return (
    <div className="grid grid-cols-12 gap-8 p-8">
      <div className="col-span-8 flex flex-col gap-8">
        <div className="flex items-center gap-6 p-6 bg-white border border-silver rounded-2xl shadow-sm">
          <StatusRing size="hero" status={evidence.length && matches === evidence.length ? 'verified' : 'pending'}>
            <span className="font-heading text-4xl font-bold text-cyan">{evidence.length}</span>
          </StatusRing>
          <div>
            <h2 className="font-heading text-2xl text-ink font-semibold">Registered Evidence</h2>
            <p className="text-muted-ink mt-1">{matches} with a latest MATCH result and a currently valid custody chain. Storage is local; remote sync is unavailable.</p>
          </div>
        </div>
        
        <div className="surface rounded-2xl overflow-hidden shadow-sm">
          <div className="p-6 border-b border-silver bg-canvas/30">
            <h2 className="font-heading text-xl text-ink font-semibold">Active Cases</h2>
          </div>
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-silver bg-canvas/50 text-muted-ink text-sm">
                <th className="py-4 px-6 font-medium">Case ID</th>
                <th className="py-4 px-6 font-medium">Title</th>
                <th className="py-4 px-6 font-medium">Evidence Count</th>
                <th className="py-4 px-6 font-medium">Health</th>
                <th className="py-4 px-6 font-medium">Last Activity</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => (
                <tr key={c.case_id} className="border-b border-silver/50 hover:bg-canvas/50 transition-colors">
                  <td className="py-4 px-6 font-mono text-sm text-ink">{c.case_id}</td>
                  <td className="py-4 px-6 text-ink">{c.title}</td>
                  <td className="py-4 px-6 text-muted-ink">{c.evidenceCount}</td>
                  <td className="py-4 px-6">
                    <StatusPill variant="silver">{c.health}</StatusPill>
                  </td>
                  <td className="py-4 px-6 text-muted-ink text-sm">{c.lastActivity || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      <div className="col-span-4">
        <h2 className="font-heading text-xl text-ink font-semibold mb-6">Recent Activity</h2>
        <CustodyChronicle events={recentEvents} />
      </div>
    </div>
  );
};
