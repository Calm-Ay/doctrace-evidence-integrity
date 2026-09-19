import React from 'react';
import { formatBytes, formatDateTime } from '../lib/utils';
import { fetchEvidenceList, fetchEvidenceDetail } from '../lib/api';

export const Report = () => {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetchEvidenceList().then(list => {
      if (list.length > 0) {
        return fetchEvidenceDetail(list[0].evidence_id);
      }
      return null;
    }).then(res => {
      setData(res);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="p-8">Loading Report...</div>;
  if (!data) return <div className="p-8">No evidence found to report on.</div>;

  const ev = data;
  const events = data.events || [];
  const verification = data.latest_verification;
  const matched = verification?.evidence_result === 'MATCH';

  return (
    <div className="max-w-[800px] mx-auto bg-white p-16 surface print-page text-ink my-8 shadow-sm">
      <div className="flex justify-between items-start mb-12 border-b border-silver pb-6">
        <div>
          <h1 className="font-heading text-4xl font-bold tracking-tight">DOCTRACE</h1>
          <h2 className="text-xl text-muted-ink mt-2">Evidence Integrity Report</h2>
        </div>
        <div className="no-print flex gap-3">
          <button className="rounded-full px-4 py-2 text-sm bg-cyan text-white hover:bg-cyan/90 font-medium" onClick={() => window.print()}>
            Print
          </button>
          <button className="rounded-full px-4 py-2 text-sm surface border border-silver font-medium hover:bg-canvas">
            Download PDF
          </button>
        </div>
      </div>

      <section className="mb-10">
        <h3 className="font-heading text-lg font-semibold uppercase tracking-wider text-muted-ink mb-4 border-b border-canvas pb-2">Collection Detail</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-muted-ink mr-2">Evidence ID:</span> <span className="font-mono">{ev.evidence_id}</span></div>
          <div><span className="text-muted-ink mr-2">Case ID:</span> <span>{ev.case_id}</span></div>
          <div><span className="text-muted-ink mr-2">Collector:</span> <span>{ev.collector_id}</span></div>
          <div><span className="text-muted-ink mr-2">Date:</span> <span>{formatDateTime(ev.collection_timestamp)}</span></div>
          <div><span className="text-muted-ink mr-2">Device:</span> <span>{ev.collection_device_id}</span></div>
          <div><span className="text-muted-ink mr-2">Size:</span> <span>{formatBytes(ev.file_size)}</span></div>
        </div>
      </section>

      <section className="mb-10">
        <h3 className="font-heading text-lg font-semibold uppercase tracking-wider text-muted-ink mb-4 border-b border-canvas pb-2">Integrity Status</h3>
        <div className="mb-4">
          <div className={`text-lg font-bold mb-2 ${matched ? 'text-emerald' : 'text-gold'}`}>{verification ? `${verification.evidence_result} / CHAIN ${verification.chain_result}` : 'PENDING VERIFICATION'}</div>
          <p className="text-sm">{verification ? 'This status reflects the most recent verification performed by Doctrace.' : 'Verify the evidence file to create an integrity result.'}</p>
        </div>
        <div className="bg-canvas p-4 rounded text-xs font-mono break-all space-y-4">
          <div>
            <div className="text-muted-ink mb-1">Original SHA-256 (Collection)</div>
            <div className="text-ink">{ev.original_hash}</div>
          </div>
          <div>
            <div className="text-muted-ink mb-1">Current SHA-256 (Verification)</div>
            <div className="text-ink">{verification?.observed_hash || 'Not yet verified'}</div>
          </div>
        </div>
      </section>

      <section className="mb-10">
        <h3 className="font-heading text-lg font-semibold uppercase tracking-wider text-muted-ink mb-4 border-b border-canvas pb-2">Custody Timeline</h3>
        <table className="w-full text-left text-sm border-collapse">
          <thead>
            <tr className="border-b border-silver text-muted-ink">
              <th className="py-2 font-medium">Date / Time</th>
              <th className="py-2 font-medium">Action</th>
              <th className="py-2 font-medium">Actor</th>
              <th className="py-2 font-medium">Location/Device</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e, idx) => (
              <tr key={idx} className="border-b border-canvas">
                <td className="py-3 pr-4 text-muted-ink">{formatDateTime(e.timestamp)}</td>
                <td className="py-3 pr-4 font-medium">{e.event_type}</td>
                <td className="py-3 pr-4">{e.actor_id}</td>
                <td className="py-3">{e.device_id || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="mb-10">
        <h3 className="font-heading text-lg font-semibold uppercase tracking-wider text-muted-ink mb-4 border-b border-canvas pb-2">Conclusion</h3>
        <p className="text-sm leading-relaxed">{verification
          ? `The most recent integrity check returned ${verification.evidence_result}, and the recorded custody chain returned ${verification.chain_result}. A mismatch shows that the submitted file differs from the registered hash; it does not establish who changed it or when.`
          : `No verification has yet been recorded for Evidence ID ${ev.evidence_id}. The report contains the intake record and custody history only.`}
        </p>
      </section>

      <section className="text-xs text-muted-ink border-t border-silver pt-6">
        <h3 className="font-heading font-semibold uppercase mb-2">Technical Appendix</h3>
        <p className="mb-2">Hashing Algorithm: SHA-256 (FIPS 180-4)</p>
        <p>This report was generated from the current Doctrace evidence and custody records.</p>
      </section>
    </div>
  );
};
