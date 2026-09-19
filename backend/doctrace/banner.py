from rich.console import Console

console = Console()

BANNER = r"""
  _____             _______
 |  __ \           |__   __|
 | |  | | ___   ___   | |_ __ __ _  ___ ___
 | |  | |/ _ \ / __|  | | '__/ _` |/ __/ _ \
 | |__| | (_) | (__   | | | | (_| | (_|  __/
 |_____/ \___/ \___|  |_|_|  \__,_|\___\___|
"""

def print_banner(version="0.1.0"):
    console.print(BANNER, style="bold green")
    console.print(f"                         Version : {version}\n", style="green")
    console.print(" [+] Tool Created by [bold bright_green]Frost-Ordixian[/bold bright_green]", style="green")
    console.print(" [+] Invisible Document Watermarking & Leak Tracing\n", style="green")
