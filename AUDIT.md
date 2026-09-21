# Doctrace bug-fix audit — 21 September 2026

The supplied ZIP's application source matched the public repository at the start of this audit. The existing design and core workflows were retained.

## Corrections

- Preserve API error status codes and display failures in the main intake, verification, stamping, registry and report screens.
- Separate SHA-256 comparison against the intake record from custody-chain validation; a damaged or missing first event no longer crashes verification.
- Compute current chain status instead of hardcoding VALID; persist and display the latest file verification.
- Replace millisecond-based IDs with UUIDs. Intake and custody append transactions include their queue entries; concurrent appends are serialized.
- Validate custody actions and transfer recipients, reject appends to corrupted chains, and show the recipient as current custodian.
- Connect evidence-detail actions to verification, custody entry, selected-evidence reports and text export; show event hashes in the timeline.
- Fix registry field mapping/search and CSV export. Escape spreadsheet formula prefixes in CSV cells.
- Remove the dummy upload value and fictitious recipients from stamping. Accept an actual recipient ID, preserve an existing document/recipient identifier on repeated stamping, use unique output filenames, validate PDFs and verify extraction before reporting success.
- Remove the fake dashboard percentage and simulated intake hashing step. Save intake notes and populate cases from actual intake records.
- Make API base URL configurable, narrow default CORS origins, fix backend dependency installation and document virtual-environment commands.
- Mark unsupported remote sync/photo identification explicitly unavailable; do not discard pending queue entries or fabricate results.

## Checks

Run the commands in TESTING.md for reproducible regression results. Tests use temporary SQLite databases and synthetic files. The API suite checks successful and failed workflows, damaged chains, repeated stamping, unsafe upload names, missing IDs, invalid requests and concurrent custody appends. The frontend component suite checks actual handler behavior with mocked API responses; it is not a browser end-to-end test.

The production frontend build was checked. A full visual browser walkthrough could not be performed: the provided browser blocked this environment's localhost URL. Before recording, run the manual checklist in TESTING.md on the machine used for the demo.

## Remaining limitations

- Local, single-user prototype; no authentication, authorization, external timestamping or signed/externally anchored custody ledger. Do not expose publicly or use real sensitive evidence.
- Evidence intake stores metadata and hashes, not original evidence bytes. Keep the original and verify uploaded copies explicitly.
- Watermarks can be removed, copied, or changed; they are not cryptographic signatures and have no guaranteed survival through screenshots, printing or copy/paste.
- Restamping an already digitally stamped PDF is rejected; use its original. Repeating an original/recipient pair intentionally retains its identifier.
- Print / Save as PDF uses the browser's print dialog; it is not server-side PDF generation.
- An earlier technical write-up that claims all features work, guaranteed photo recovery, or a different test count should not be submitted unchanged.
