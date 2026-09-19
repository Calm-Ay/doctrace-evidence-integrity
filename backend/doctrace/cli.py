import os
import sys
import click
import hashlib
from rich.console import Console
from rich.table import Table

from doctrace.registry import Registry
from doctrace.evidence.custody import intake_evidence, log_event
from doctrace.evidence.verification import verify_evidence
from doctrace.evidence.reporting import generate_report
from doctrace.evidence.sync import sync_events

console = Console()

def calculate_file_hash(filepath: str) -> str:
    """Calculates SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

from doctrace.banner import print_banner

@click.group(invoke_without_command=True)
@click.version_option(
    version="0.1.0",
    prog_name="DocTrace",
    message="%(prog)s %(version)s — by Frost-Ordixian"
)
@click.pass_context
def cli(ctx):
    """DocTrace: Invisible Document Watermarking & Leak-Source Identification."""
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo(ctx.get_help())

from doctrace.stampers.zerowidth import ZeroWidthStamper
from doctrace.stampers.microspacing import MicroSpacingStamper
from doctrace.stampers.structural import StructuralStamper
from doctrace.extractors.pdf_extract import extract_digital_watermarks
from doctrace.extractors.photo_extract import extract_from_photo
from doctrace.utils.bitops import generate_random_bitstring, find_best_matches

@cli.command()
@click.argument("original_pdf", type=click.Path(exists=True, dir_okay=False))
@click.option("--recipients", "-r", required=True, type=click.Path(exists=True, dir_okay=False), help="Path to recipients CSV file.")
@click.option("--out", "-o", default="./stamped", type=click.Path(), help="Output directory for stamped PDFs.")
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
@click.option("--bits", "-b", type=int, default=32, help="Number of bits for fingerprint (default: 32).")
def stamp(original_pdf, recipients, out, db_path, bits):
    """Stamp copies of a document for multiple recipients."""
    import csv
    from doctrace.registry import Registry
    
    os.makedirs(out, exist_ok=True)
    registry = Registry(db_path)
    doc_hash = calculate_file_hash(original_pdf)
    doc_name = os.path.basename(original_pdf)
    
    zw_stamper = ZeroWidthStamper()
    ms_stamper = MicroSpacingStamper()
    struct_stamper = StructuralStamper()
    
    # Normalize original PDF so all spaces are broken out into TJ array elements
    console.print("[dim]Normalizing PDF text streams...[/dim]")
    norm_pdf = os.path.join(out, ".normalized.pdf")
    if not ms_stamper.stamp(original_pdf, norm_pdf, ""):
        console.print("[red]Failed to normalize PDF.[/red]")
        return
    
    import json
    # Generate Layer 2 Layout Map
    console.print("[dim]Analyzing document layout for Layer 2 structural watermarks...[/dim]")
    layout_map_json = struct_stamper.generate_layout_map(norm_pdf, bits)
    if not layout_map_json:
        console.print("[red]Failed to generate structural layout map.[/red]")
        if os.path.exists(norm_pdf): os.remove(norm_pdf)
        return
        
    layout_map = json.loads(layout_map_json)
    actual_bits = layout_map.get('actual_bits', bits)
    if actual_bits < bits:
        max_recipients = 2 ** actual_bits
        console.print(f"[bold yellow]Warning: Only {actual_bits} valid anchors found. Downgrading Layer 2 fingerprint from {bits}-bit to {actual_bits}-bit.[/bold yellow]")
        console.print(f"[yellow]An {actual_bits}-bit fingerprint supports up to {max_recipients:,} recipients. Ensure this avoids collisions for your batch size.[/yellow]")
        bits = actual_bits
        
    registry.save_layout_map(doc_hash, layout_map_json)
    
    success_count = 0
    with open(recipients, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recipient_id = row['id']
            name = row['name']
            email = row['email']
            
            bitstring = generate_random_bitstring(bits)
            out_pdf = os.path.join(out, f"recipient_{recipient_id}.pdf")
            temp_pdf1 = os.path.join(out, f".temp1_{recipient_id}.pdf")
            temp_pdf2 = os.path.join(out, f".temp2_{recipient_id}.pdf")
            
            console.print(f"[dim]Stamping copy for {name} ({recipient_id})...[/dim]")
            
            # Chain stampers
            if zw_stamper.stamp(norm_pdf, temp_pdf1, bitstring):
                if ms_stamper.stamp(temp_pdf1, temp_pdf2, bitstring):
                    if struct_stamper.stamp_with_map(temp_pdf2, out_pdf, bitstring, layout_map_json):
                        registry.add_copy(doc_hash, doc_name, recipient_id, name, email, bitstring)
                        success_count += 1
                    else:
                        console.print(f"[red]Failed structural stamp for {recipient_id}[/red]")
                else:
                    console.print(f"[red]Failed microspacing stamp for {recipient_id}[/red]")
            else:
                console.print(f"[red]Failed zero-width stamp for {recipient_id}[/red]")
                
            for temp in [temp_pdf1, temp_pdf2]:
                if os.path.exists(temp):
                    os.remove(temp)
                    
    if os.path.exists(norm_pdf):
        os.remove(norm_pdf)
                
    console.print(f"[bold green]Successfully stamped {success_count} copies to {out}/[/bold green]")

@cli.command()
@click.argument("suspicious_pdf", type=click.Path(exists=True, dir_okay=False))
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def verify(suspicious_pdf, db_path):
    """Verify a digital PDF to extract its fingerprint directly."""
    from doctrace.registry import Registry
    console.print(f"[bold yellow]Verifying digital file {suspicious_pdf}...[/bold yellow]")
    
    registry = Registry(db_path)
    codebook = registry.get_all_copies()
    
    extracted = extract_digital_watermarks(suspicious_pdf)
    zw_bits = extracted["zerowidth"]
    ms_bits = extracted["microspacing"]
    
    console.print(f"Extracted Zero-Width Payload:  [cyan]{zw_bits if zw_bits else 'None'}[/cyan]")
    console.print(f"Extracted Micro-Spacing Payload: [magenta]{ms_bits if ms_bits else 'None'}[/magenta]")
    
    if not codebook:
        console.print("[red]Registry is empty. Cannot match.[/red]")
        return
        
    for name, bits in [("Zero-Width", zw_bits), ("Micro-Spacing", ms_bits)]:
        if bits:
            matches = find_best_matches(bits, codebook)
            if matches:
                console.print(f"\n[bold]{name} Match Results:[/bold]")
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Rank")
                table.add_column("Recipient")
                table.add_column("Email")
                table.add_column("Confidence")
                table.add_column("Distance")
                
                for i, (m, c, d) in enumerate(matches[:3]):
                    table.add_row(str(i+1), m['name'], m['email'], f"{c:.1f}%", str(d))
                console.print(table)

@cli.command()
@click.argument("leaked_photo", type=click.Path(exists=True, dir_okay=False))
@click.option("--original", required=False, type=click.Path(exists=True, dir_okay=False), help="Original PDF file for layout map.")
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
@click.option("--bits", "-b", type=int, default=32, help="Number of bits for fingerprint (default: 32).")
@click.option("--psm", type=int, default=3, help="Tesseract Page Segmentation Mode. Default 3. Try 6 for single block of text or 11 for sparse text.")
def identify(leaked_photo, original, db_path, bits, psm):
    """Extract and identify the leak source from a photo of a printed document."""
    from doctrace.registry import Registry
    console.print(f"[bold yellow]Analyzing physical photo {leaked_photo}...[/bold yellow]")
    
    registry = Registry(db_path)
    codebook = registry.get_all_copies()
    if not codebook:
        console.print("[red]Registry is empty. Cannot match.[/red]")
        return
        
    layout_map_json = None
    if original:
        doc_hash = calculate_file_hash(original)
        layout_map_json = registry.get_layout_map(doc_hash)
        
        if not layout_map_json:
            console.print("[yellow]Layout map not found in registry. Regenerating from original PDF...[/yellow]")
            ms_stamper = MicroSpacingStamper()
            struct_stamper = StructuralStamper()
            
            norm_pdf = ".temp_identify_norm.pdf"
            if ms_stamper.stamp(original, norm_pdf, ""):
                layout_map_json = struct_stamper.generate_layout_map(norm_pdf, bits)
                os.remove(norm_pdf)
            
            if not layout_map_json:
                console.print("[red]Failed to generate structural layout map.[/red]")
                return
    else:
        # If no original provided, just get the first layout map available in DB as a fallback
        # In a real system, we'd prompt or require original.
        with registry._get_connection() as conn:
            cursor = conn.execute("SELECT layout_json FROM layout_maps LIMIT 1")
            row = cursor.fetchone()
            if row:
                layout_map_json = row['layout_json']
                
    if not layout_map_json:
        console.print("[red]No layout map available. Provide --original to generate one.[/red]")
        return
        
    import json
    layout_map = json.loads(layout_map_json)
    bits = layout_map.get('actual_bits', bits)
    
    console.print("[dim]Running OpenCV/Tesseract extraction...[/dim]")
    extracted_bits = extract_from_photo(leaked_photo, layout_map_json, bits)
    
    console.print(f"Extracted Structural Payload: [green]{extracted_bits}[/green]")
    
    # Check valid bits
    valid_bits = extracted_bits.replace('_', '')
    if len(valid_bits) == 0:
        console.print("[red]Could not extract any structural bits from the photo.[/red]")
        return
        
    matches = find_best_matches(extracted_bits, codebook)
    if matches:
        console.print(f"\n[bold]Structural Match Results:[/bold]")
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Rank")
        table.add_column("Recipient")
        table.add_column("Email")
        table.add_column("Confidence")
        table.add_column("Distance")
        
        for i, (m, c, d) in enumerate(matches[:3]):
            if i == 0 and c >= 75.0:
                table.add_row(f"[green]{i+1}[/green]", f"[green]{m['name']}[/green]", f"[green]{m['email']}[/green]", f"[green]{c:.1f}%[/green]", f"[green]{d}[/green]")
            elif i == 0:
                table.add_row(f"[yellow]{i+1}[/yellow]", f"[yellow]{m['name']}[/yellow]", f"[yellow]{m['email']}[/yellow]", f"[yellow]{c:.1f}%[/yellow]", f"[yellow]{d}[/yellow]")
            else:
                table.add_row(str(i+1), m['name'], m['email'], f"{c:.1f}%", str(d))
        console.print(table)
        
        top_match_conf = matches[0][1]
        if top_match_conf < 75.0:
            console.print(f"\n[bold red]No reliable match found. Top confidence ({top_match_conf:.1f}%) is below the safe threshold (75%).[/bold red]")
        else:
            console.print(f"\n[bold green]Success! Safely identified {matches[0][0]['name']}.[/bold green]")

@cli.command()
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def list(db_path):
    """List all stamped copies and their recipients."""
    registry = Registry(db_path)
    copies = registry.get_all_copies()
    
    if not copies:
        console.print("[yellow]No copies found in the registry.[/yellow]")
        return
        
    table = Table(title="Stamped Document Copies")
    table.add_column("Recipient ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Email", style="green")
    table.add_column("Document Name", style="blue")
    table.add_column("Bitstring", style="white")
    table.add_column("Timestamp", style="dim")
    
    for copy in copies:
        table.add_row(
            copy["recipient_id"],
            copy["name"],
            copy["email"],
            copy["doc_name"],
            copy["bitstring"],
            copy["timestamp"]
        )
    
    console.print(table)

@cli.command()
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
@click.option("--out", "-o", default="doctrace_log.csv", type=click.Path(), help="Output file path.")
def export_log(db_path, out):
    """Export the stamped copies registry to a CSV file."""
    import csv
    registry = Registry(db_path)
    copies = registry.get_all_copies()
    
    if not copies:
        console.print("[yellow]No records to export.[/yellow]")
        return
        
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["recipient_id", "name", "email", "doc_name", "bitstring", "timestamp"])
        writer.writeheader()
        for c in copies:
            writer.writerow({
                "recipient_id": c["recipient_id"],
                "name": c["name"],
                "email": c["email"],
                "doc_name": c["doc_name"],
                "bitstring": c["bitstring"],
                "timestamp": c["timestamp"]
            })
            
            console.print(f"[bold green]Successfully exported registry log to {out}[/bold green]")

@cli.command()
def doctor():
    """Check system dependencies for doctrace."""
    import subprocess
    console.print("[bold]Checking dependencies...[/bold]\n")
    
    # Check Ghostscript
    try:
        res = subprocess.run(["gs", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            console.print(f"[green]✓ Ghostscript installed (v{res.stdout.strip()})[/green]")
        else:
            console.print("[yellow]! Ghostscript installed but returned non-zero[/yellow]")
    except FileNotFoundError:
        console.print("[red]✗ Ghostscript not found.[/red] Required for Layer 1 simulation/testing.")
        
    # Check Tesseract
    try:
        res = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if res.returncode == 0:
            version = res.stdout.split('\n')[0]
            console.print(f"[green]✓ Tesseract OCR installed ({version})[/green]")
        else:
            console.print("[yellow]! Tesseract OCR installed but returned non-zero[/yellow]")
    except FileNotFoundError:
        console.print("[red]✗ Tesseract OCR not found.[/red] Required for Layer 2 identify (extraction).")
        console.print("  [dim]Linux: sudo apt-get install tesseract-ocr[/dim]")
        console.print("  [dim]Mac: brew install tesseract[/dim]")
        
    # Check Registry Encryption
    db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    if os.path.exists(db_path):
        import sqlite3
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT layout_json FROM layout_maps")
            rows = cursor.fetchall()
            has_encrypted = False
            for r in rows:
                if r['layout_json'] and not (r['layout_json'].startswith('{') or r['layout_json'].startswith('[')):
                    has_encrypted = True
                    break
            
            if has_encrypted:
                secret = os.getenv("DOCTRACE_SECRET_KEY")
                if not secret:
                    console.print("\n[bold red]CRITICAL: Encrypted layout maps found in registry, but DOCTRACE_SECRET_KEY is not set![/bold red]")
                    console.print("[red]Without this environment variable, you cannot extract or identify leaks for these documents.[/red]")
                else:
                    console.print("\n[bold green]✓ DOCTRACE_SECRET_KEY is set and encrypted layout maps exist.[/bold green]")
                    console.print("[bold yellow]WARNING: Back up your DOCTRACE_SECRET_KEY securely (e.g. password manager)! If lost, all stamped documents become permanently untraceable.[/bold yellow]")
        except sqlite3.OperationalError:
            pass # Tables might not exist yet

if __name__ == "__main__":
    cli()

@cli.group()
def evidence():
    """Evidence Chain: Manage and verify digital evidence integrity."""
    pass

@evidence.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
@click.option("--case", "case_id", help="Case ID.")
@click.option("--collector", "collector_id", help="Collector ID.")
@click.option("--device", "device_id", help="Device ID.")
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def intake(path, case_id, collector_id, device_id, db_path):
    """Intake digital evidence and start the chain of custody."""
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    console.print(f"[bold yellow]Intaking evidence from {path}...[/bold yellow]")
    
    ev, event = intake_evidence(path, db_path, collector_id, device_id, case_id)
    
    console.print(f"[bold green]Evidence successfully registered![/bold green]")
    console.print(f"Evidence ID: [cyan]{ev.evidence_id}[/cyan]")
    console.print(f"SHA-256 Hash: [magenta]{ev.original_hash}[/magenta]")
    console.print(f"Status: [green]{ev.status}[/green]")

@evidence.command()
@click.argument("evidence_id")
@click.option("--path", required=True, type=click.Path(exists=True, dir_okay=False), help="Path to the file to verify.")
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def verify(evidence_id, path, db_path):
    """Verify evidence integrity and custody chain."""
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    
    console.print(f"[bold yellow]Verifying evidence {evidence_id} against file {path}...[/bold yellow]")
    
    res = verify_evidence(path, evidence_id, db_path)
    
    console.print(f"Original fingerprint: {res.get('expected_hash', 'N/A')}")
    console.print(f"Current fingerprint:  {res.get('actual_hash', 'N/A')}")
    
    if res.get('evidence_result') == "NOT_FOUND":
        console.print(f"[bold red]Evidence {evidence_id} not found.[/bold red]")
        sys.exit(1)
    
    if res.get('evidence_result') == "MATCH":
        console.print("[bold green]INTEGRITY VERIFIED[/bold green]")
    else:
        console.print("[bold red]INTEGRITY MISMATCH DETECTED[/bold red]")
        
    if res.get('chain_result') == "VALID":
        console.print("[bold green]CUSTODY CHAIN VALID[/bold green]")
    else:
        console.print("[bold red]CUSTODY CHAIN INVALID[/bold red]")

@evidence.command()
@click.argument("evidence_id")
@click.option("--action", required=True, help="Action type (e.g. TRANSFERRED).")
@click.option("--actor", "actor_id", help="Actor ID.")
@click.option("--recipient", "recipient_id", help="Recipient ID.")
@click.option("--note", "notes", help="Notes.")
@click.option("--device", "device_id", help="Device ID.")
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def log(evidence_id, action, actor_id, recipient_id, notes, device_id, db_path):
    """Log a new event in the evidence custody chain."""
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    console.print(f"[bold yellow]Logging {action} event for evidence {evidence_id}...[/bold yellow]")
    
    event = log_event(evidence_id, action, db_path, actor_id, recipient_id, notes, device_id)
    
    console.print(f"[bold green]Event logged successfully![/bold green]")
    console.print(f"Event ID: [cyan]{event.event_id}[/cyan]")
    console.print(f"Event Hash: [magenta]{event.event_hash}[/magenta]")

@evidence.command()
@click.argument("evidence_id")
@click.option("--out", "out_path", type=click.Path(), help="Output report file path.")
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def report(evidence_id, out_path, db_path):
    """Generate a court-readable evidence integrity report."""
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    console.print(f"[bold yellow]Generating report for evidence {evidence_id}...[/bold yellow]")
    
    rep = generate_report(evidence_id, db_path, out_path)
    if not out_path:
        console.print(rep)
    else:
        console.print(f"[bold green]Report saved to {out_path}[/bold green]")

@evidence.command()
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def sync(db_path):
    """Sync pending custody events."""
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    console.print("[bold yellow]Syncing offline events...[/bold yellow]")
    count = sync_events(db_path)
    console.print(f"[bold green]Successfully synced {count} events.[/bold green]")

@evidence.command()
@click.argument("evidence_id")
@click.option("--db", "db_path", type=click.Path(), help="Path to SQLite registry database.")
def status(evidence_id, db_path):
    """Display the current status of an evidence item."""
    if not db_path:
        db_path = os.getenv("DOCTRACE_DB", "doctrace.db")
    from doctrace.evidence.storage import EvidenceDB
    db = EvidenceDB(db_path)
    ev = db.get_latest_event(evidence_id)
    if not ev:
        console.print(f"[bold red]No custody events found for evidence {evidence_id}[/bold red]")
        return
    console.print(f"Evidence ID: [cyan]{evidence_id}[/cyan]")
    console.print(f"Current state: [green]{ev['event_type']}[/green]")
    console.print(f"Last Actor: [cyan]{ev.get('actor_id') or 'N/A'}[/cyan]")
