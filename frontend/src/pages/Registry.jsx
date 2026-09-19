import React, { useState, useMemo } from 'react';
import { cn } from '../lib/utils';
import { formatDateTime } from '../lib/utils';
import { fetchRegistry } from '../lib/api';
import { Search, Download } from 'lucide-react';

export const Registry = () => {
  const [search, setSearch] = useState('');
  const [filterDoc, setFilterDoc] = useState('All Documents');
  const [registry, setRegistry] = useState([]);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    fetchRegistry().then(data => {
      setRegistry(data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const uniqueDocs = useMemo(() => {
    return Array.from(new Set(registry.map(item => item.document)));
  }, [registry]);

  const filteredRegistry = useMemo(() => {
    return registry.filter(item => {
      const matchesSearch = item.document.toLowerCase().includes(search.toLowerCase()) ||
                            item.name.toLowerCase().includes(search.toLowerCase()) ||
                            item.email.toLowerCase().includes(search.toLowerCase());
      const matchesDoc = filterDoc === 'All Documents' || item.document === filterDoc;
      return matchesSearch && matchesDoc;
    });
  }, [search, filterDoc, registry]);

  if (loading) return <div className="p-8">Loading Registry...</div>;

  return (
    <div className="w-full bg-white surface border border-silver rounded-xl p-6 font-sans">
      <div className="flex flex-wrap gap-4 items-center justify-between mb-6">
        <div className="flex gap-4 flex-1">
          <div className="relative max-w-xs w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-ink" />
            <input
              type="text"
              placeholder="Search by document or recipient..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-silver rounded-lg text-sm text-ink focus:outline-none focus:border-cyan"
            />
          </div>
          <select
            value={filterDoc}
            onChange={e => setFilterDoc(e.target.value)}
            className="border border-silver rounded-lg px-4 py-2 text-sm text-ink focus:outline-none focus:border-cyan bg-white"
          >
            <option value="All Documents">All Documents</option>
            {uniqueDocs.map(doc => (
              <option key={doc} value={doc}>{doc}</option>
            ))}
          </select>
        </div>
        <button className="bg-canvas border border-silver text-ink px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-silver/20 transition-colors">
          <Download className="w-4 h-4" /> Export CSV
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-silver text-muted-ink text-sm">
              <th className="pb-3 px-4 font-medium">Document</th>
              <th className="pb-3 px-4 font-medium">Recipient ID</th>
              <th className="pb-3 px-4 font-medium">Name</th>
              <th className="pb-3 px-4 font-medium">Email</th>
              <th className="pb-3 px-4 font-medium">Bitstring</th>
              <th className="pb-3 px-4 font-medium">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {filteredRegistry.map((item, idx) => (
              <tr key={idx} className="border-b border-silver/30 last:border-0 hover:bg-canvas/50 transition-colors even:bg-canvas/30 text-sm">
                <td className="py-3 px-4 font-medium text-ink">{item.document}</td>
                <td className="py-3 px-4 font-mono text-xs text-muted-ink">{item.recipient_id}</td>
                <td className="py-3 px-4 text-ink">{item.name}</td>
                <td className="py-3 px-4 text-muted-ink">{item.email}</td>
                <td className="py-3 px-4 font-mono text-xs text-ink">
                  {item.bitstring.substring(0, 12)}...
                </td>
                <td className="py-3 px-4 font-mono text-xs text-muted-ink">
                  {formatDateTime ? formatDateTime(item.timestamp) : item.timestamp}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredRegistry.length === 0 && (
          <div className="text-center py-12 text-muted-ink text-sm">
            No matching records found.
          </div>
        )}
      </div>
    </div>
  );
};
