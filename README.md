# Doctrace
Doctrace is an Evidence Integrity & Chain of Custody platform designed for digital forensics, combining two major systems:

## Evidence Chain
1. **Evidence Intake** -> SHA-256 Seal
2. **Custody Events** -> Hash-Chained Provenance
3. **Verification** -> Ensure original collection matches current
4. **Court-Readable Report** -> Generate logs for magistrates

## Document Provenance
1. **Document** -> Invisible Watermark
2. **Verification** -> Identify source of leak
3. **Registry** -> Track document copies

## Architecture

React Frontend -> FastAPI Bridge -> Existing Doctrace Python Core -> SQLite and filesystem artifacts
