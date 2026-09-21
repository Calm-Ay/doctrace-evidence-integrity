# Doctrace
Doctrace is an Evidence Integrity & Chain of Custody platform designed for digital forensics, combining two major systems:

## Evidence Chain
1. **Evidence Intake** -> SHA-256 Seal
2. **Custody Events** -> Hash-Chained Provenance
3. **Verification** -> Ensure original collection matches current
4. **Court-Readable Report** -> Generate logs for magistrates

## Document Provenance
1. **Document** -> Invisible Watermark
2. **Verification** -> Match the embedded identifier to a registered copy
3. **Registry** -> Track document copies

## Architecture

React Frontend -> FastAPI Bridge -> Existing Doctrace Python Core -> SQLite and filesystem artifacts

## Run and test

See [SETUP.md](SETUP.md) for Linux/macOS and Windows commands, [TESTING.md](TESTING.md) for regression checks, and [AUDIT.md](AUDIT.md) for the September 2026 fixes and known limitations.

This is a **local hackathon prototype**, not a production forensic system. Use synthetic data only and bind the API to `127.0.0.1`. No authentication or authorization is implemented. Do not expose the API publicly.

File hashes detect differences relative to the stored fingerprint; they do not establish who changed a file or when. Custody hashes detect inconsistent recorded links but are not externally anchored or digitally signed. Someone with database access can rewrite and rehash history, and deletion of a valid chain suffix cannot be detected without an external checkpoint.

Digital PDF stamping adds invisible text to a new copy. Registry matching is not proof of disclosure by the associated recipient, nor a guarantee that the PDF contents are unchanged. Photo recovery, encryption controls, and remote synchronization are not available in the web demo; local queue entries are retained without claiming transmission.
