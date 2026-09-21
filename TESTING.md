# Regression checks

Backend, from `backend` with the virtual environment active:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_api_regressions.py -q
```

Frontend, from `frontend`:

```bash
npm ci
npm test
npm run build
npm run lint
```

The API tests use temporary databases and synthetic text/PDFs. Frontend tests render React components with mocked API responses. Neither substitutes for a real-browser walkthrough. Legacy `test_layer*`, `test_e2e`, `test_shift_sweep`, and `test_simulation` scripts are research experiments, not evidence that all features pass; see AUDIT.md.

## Manual demo checklist

1. Start both servers using SETUP.md. Check the dashboard with an empty database.
2. Intake a synthetic text file with a synthetic case ID, collector and notes. Confirm its filename, SHA-256, Evidence ID and COLLECTED timeline entry.
3. Open evidence details, choose Log Action, select TRANSFERRED, enter actor and recipient, and save. Expand event hashes; check the current custodian.
4. Choose Verify Now. The Evidence ID should be prefilled. Upload the untouched file: expect MATCH / VALID.
5. Make a separate copy and change its contents. Choose Verify Another File and upload the changed copy: expect MISMATCH / VALID and differing hashes.
6. Generate Report. Confirm the selected Evidence ID and last verification result. Try a second evidence record and use the report selector. Use Print / Save as PDF and check print preview; Export in evidence details downloads a text report.
7. Stamp a synthetic, unencrypted PDF for DEMO-RECIPIENT-001. Download the PDF and use Verify Document: expect VERIFIED and that recipient. Upload the original unstamped PDF: expect NO WATERMARK.
8. Open Registry, search for the PDF and export CSV. Repeat stamping the same original/recipient and confirm previously downloaded copies still verify.
9. Try an invalid PDF and a nonexistent Evidence ID. Errors should appear without success screens. Stop the backend and check that the app reports connection failures.
10. Sync must not claim data was transmitted. Photo identification must be marked experimental/unavailable. Do not demonstrate these as working features.

Never imply MISMATCH proves who changed a file or when. Use synthetic data only.
