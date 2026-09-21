import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { HeaderBar } from './components/HeaderBar';

// Evidence Chain Pages
import { Dashboard } from './pages/Dashboard';
import { EvidenceList } from './pages/EvidenceList';
import { EvidenceDetail } from './pages/EvidenceDetail';
import { Intake } from './pages/Intake';
import { Verification } from './pages/Verification';
import { Report } from './pages/Report';
import { Sync } from './pages/Sync';

// Document Provenance Pages
import { StampDocuments } from './pages/StampDocuments';
import { VerifyDigital } from './pages/VerifyDigital';
import { IdentifyPhoto } from './pages/IdentifyPhoto';
import { Registry } from './pages/Registry';

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-canvas font-sans text-ink">
        <Navigation />
        <div className="flex-1 ml-[72px] flex flex-col">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<><HeaderBar title="Cases Dashboard" /><Dashboard /></>} />
            <Route path="/evidence" element={<><HeaderBar title="Evidence Register" /><EvidenceList /></>} />
            <Route path="/evidence/:id" element={<><HeaderBar title="Evidence Detail" /><EvidenceDetail /></>} />
            <Route path="/intake" element={<><HeaderBar title="Evidence Intake" /><Intake /></>} />
            <Route path="/verify" element={<><HeaderBar title="Verification" /><Verification /></>} />
            <Route path="/report" element={<><HeaderBar title="Court Report" /><Report /></>} />
            <Route path="/sync" element={<><HeaderBar title="Sync Status" /><Sync /></>} />
            <Route path="/stamp" element={<><HeaderBar title="Stamp Documents" /><StampDocuments /></>} />
            <Route path="/verify-digital" element={<><HeaderBar title="Verify Document" /><VerifyDigital /></>} />
            <Route path="/identify" element={<><HeaderBar title="Identify Source" /><IdentifyPhoto /></>} />
            <Route path="/registry" element={<><HeaderBar title="Document Registry" /><Registry /></>} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;
