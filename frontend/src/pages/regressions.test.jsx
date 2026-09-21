// @vitest-environment jsdom
import React from 'react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, cleanup, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StampDocuments } from './StampDocuments';
import { Registry } from './Registry';
import { Verification } from './Verification';
import { Report } from './Report';
import { EvidenceDetail } from './EvidenceDetail';
import { HashDisplay } from '../components/HashDisplay';
import * as api from '../lib/api';
vi.mock('../lib/api', () => ({stampDocument:vi.fn(), stampedDownloadUrl:p=>p, fetchRegistry:vi.fn(), verifyEvidence:vi.fn(), fetchEvidenceList:vi.fn(), fetchEvidenceDetail:vi.fn(), logCustody:vi.fn(), getReport:vi.fn(), downloadText:vi.fn()}));
afterEach(() => {cleanup(); vi.clearAllMocks();});
const record = {evidence_id:'EV-ONE', original_filename:'demo.txt', original_hash:'a'.repeat(64), file_size:4, collection_timestamp:'2026-09-21T00:00:00Z', status:'REGISTERED', chain_status:'VALID', events:[]};

describe('demo screen regressions', () => {
  it('does not label an unverified hash as a mismatch', () => {
    render(<HashDisplay mode="compare" original="abc" />);
    expect(screen.getByText('Pending verification')).toBeTruthy();
    expect(screen.queryByText('Hash Mismatch')).toBeNull();
  });
  it('does not fabricate a selected file when the PDF picker is cancelled', () => {
    render(<StampDocuments />);
    fireEvent.click(screen.getByText('Upload original PDF'));
    expect(screen.getByRole('button', {name:'Stamp Document'}).disabled).toBe(true);
    expect(screen.queryByText(/document-to-stamp.pdf/)).toBeNull();
  });
  it('stamps the actual selected file and entered recipient', async () => {
    api.stampDocument.mockResolvedValue({copy_id:'1010',download_url:'/copy.pdf'});
    const {container} = render(<StampDocuments />);
    const file = new File(['synthetic'], 'demo.pdf', {type:'application/pdf'});
    fireEvent.change(container.querySelector('input[type=file]'), {target:{files:[file]}});
    fireEvent.change(screen.getByLabelText('Recipient ID'), {target:{value:'DEMO-42'}});
    fireEvent.click(screen.getByRole('button', {name:'Stamp Document'}));
    await screen.findByText('1 stamped copy created and registered');
    expect(api.stampDocument).toHaveBeenCalledWith(file,'DEMO-42');
    expect(screen.getByRole('link', {name:'Download stamped PDF'}).getAttribute('href')).toBe('/copy.pdf');
  });
  it('shows stamping failures instead of success', async () => {
    api.stampDocument.mockRejectedValue(new Error('Invalid PDF'));
    const {container} = render(<StampDocuments />);
    fireEvent.change(container.querySelector('input[type=file]'), {target:{files:[new File(['x'],'bad.pdf')]}});
    fireEvent.change(screen.getByLabelText('Recipient ID'), {target:{value:'DEMO'}});
    fireEvent.click(screen.getByRole('button', {name:'Stamp Document'}));
    expect((await screen.findByRole('alert')).textContent).toBe('Invalid PDF');
    expect(screen.queryByText('1 stamped copy created and registered')).toBeNull();
  });
  it('renders and searches the actual registry API fields', async () => {
    api.fetchRegistry.mockResolvedValue([{doc_name:'demo.pdf',recipient_id:'DEMO',name:'DEMO',email:'',bitstring:'1010',timestamp:'2026-09-21'}]);
    render(<Registry />);
    await screen.findByRole('cell', {name:'demo.pdf'});
    fireEvent.change(screen.getByPlaceholderText('Search by document or recipient...'),{target:{value:'missing'}});
    expect(screen.getByText('No matching records found.')).toBeTruthy();
  });
  it('prefills evidence and separates MATCH from an INVALID chain', async () => {
    api.verifyEvidence.mockResolvedValue({evidence_result:'MATCH',chain_result:'INVALID',expected_hash:'a',actual_hash:'a'});
    const {container} = render(<MemoryRouter initialEntries={['/verify?evidence=EV-ONE']}><Verification /></MemoryRouter>);
    expect(screen.getByPlaceholderText('EV-202X-XXXXXX').value).toBe('EV-ONE');
    fireEvent.change(container.querySelector('input[type=file]'),{target:{files:[new File(['a'],'original.txt')]}});
    fireEvent.click(screen.getByRole('button',{name:'Verify Integrity'}));
    await screen.findByRole('heading',{name:'MATCH'});
    expect(screen.getByText('Invalid')).toBeTruthy();
    expect(screen.queryByText(/chain of custody is intact/)).toBeNull();
  });
  it('reports the requested evidence, not the first inventory record', async () => {
    api.fetchEvidenceList.mockResolvedValue([{...record,evidence_id:'EV-TWO'},record]);
    api.fetchEvidenceDetail.mockResolvedValue(record);
    render(<MemoryRouter initialEntries={['/report?evidence=EV-ONE']}><Report /></MemoryRouter>);
    await screen.findByText('Evidence Integrity Report');
    expect(api.fetchEvidenceDetail).toHaveBeenCalledWith('EV-ONE');
    expect(screen.getByLabelText('Report evidence').value).toBe('EV-ONE');
  });
  it('opens and saves the custody form', async () => {
    api.fetchEvidenceDetail.mockResolvedValue(record); api.logCustody.mockResolvedValue({event_id:'EVT-ONE'});
    render(<MemoryRouter><EvidenceDetail /></MemoryRouter>);
    fireEvent.click(await screen.findByRole('button',{name:'Log Action'}));
    fireEvent.change(screen.getByLabelText('Actor'),{target:{value:'DEMO-A'}});
    fireEvent.change(screen.getByLabelText('Recipient'),{target:{value:'DEMO-B'}});
    fireEvent.click(screen.getByRole('button',{name:'Save Action'}));
    await waitFor(() => expect(api.logCustody).toHaveBeenCalled());
    expect(api.logCustody.mock.calls[0][1]).toMatchObject({action:'TRANSFERRED',actor_id:'DEMO-A',recipient_id:'DEMO-B'});
  });
});
