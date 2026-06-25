#!/usr/bin/env python3
"""
ARIA - Automated Resolution & IT Assistant
An interactive terminal chatbot for IT support issues.
Powered by Anthropic Claude API.

Install dependency:  pip install anthropic
Set API key:         export ANTHROPIC_API_KEY="your-key-here"
"""

import os
import sys
import time
import textwrap
import re
from datetime import datetime

# ──────────────────────────── Dependency Check ────────────────────────────────
try:
    import anthropic
except ImportError:
    print("\n  [!] Missing dependency: anthropic")
    print("      Run:  pip install anthropic\n")
    sys.exit(1)

# ──────────────────────────── ANSI Colors & Styles ────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    # Foreground
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"
    # Background
    BG_BLUE = "\033[44m"
    BG_CYAN = "\033[46m"

TERM_WIDTH = min(os.get_terminal_size().columns, 90) if hasattr(os, 'get_terminal_size') else 80

# ──────────────────────────── System Prompt ───────────────────────────────────
SYSTEM_PROMPT = """You are ARIA (Automated Resolution & IT Assistant), an expert IT support specialist chatbot running in a terminal. You help users diagnose and fix all kinds of technical problems.

Your expertise covers:
- Networking (WiFi, LAN, VPN, DNS, firewalls, routers)
- Operating Systems (Windows, macOS, Linux)
- Hardware (CPU, RAM, storage, GPU, peripherals)
- Security (malware, viruses, phishing, hardening)
- Software (installation errors, crashes, updates, drivers)
- Cloud services (AWS, Azure, Google Cloud, Office 365)
- Servers & databases (Apache, Nginx, MySQL, PostgreSQL)
- Active Directory, email systems, printers

Response style for TERMINAL output:
- Use plain text — no markdown, no asterisks, no hashtags
- For steps use:  [1] [2] [3] numbering
- For commands use:  >>> command here
- For warnings use:  !! WARNING: message
- For success tips:  >> TIP: message
- Use ALL CAPS for section headings: DIAGNOSIS, SOLUTION, QUICK FIX, etc.
- Rate severity at top of reply: [LOW] [MEDIUM] [HIGH] [CRITICAL]
- Keep responses focused and actionable
- End every reply with a line: FOLLOW-UP: question1 | question2 | question3
  (exactly 3 follow-up questions separated by | pipe characters)
"""

# ──────────────────────────── UI Helpers ──────────────────────────────────────
def clear():
    os.system("cls" if sys.platform == "win32" else "clear")

def hr(char="─", color=C.CYAN):
    print(f"{color}{char * TERM_WIDTH}{C.RESET}")

def typing_effect(text: str, delay: float = 0.012, color: str = ""):
    """Print text with a typewriter effect."""
    for ch in text:
        print(f"{color}{ch}{C.RESET}", end="", flush=True)
        time.sleep(delay)
    print()

def wrap_print(text: str, indent: int = 4, color: str = "", width: int = None):
    """Word-wrap and print a block of text."""
    w = (width or TERM_WIDTH) - indent
    lines = text.split("\n")
    for line in lines:
        if len(line) <= w:
            print(f"{' ' * indent}{color}{line}{C.RESET}")
        else:
            for wrapped in textwrap.wrap(line, w):
                print(f"{' ' * indent}{color}{wrapped}{C.RESET}")

def spinner(message: str, duration: float = 1.5):
    """Show a spinner animation while 'thinking'."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    start = time.time()
    i = 0
    while time.time() - start < duration:
        print(f"\r  {C.CYAN}{frames[i % len(frames)]}{C.RESET}  {C.DIM}{message}{C.RESET}", end="", flush=True)
        time.sleep(0.08)
        i += 1
    print("\r" + " " * (TERM_WIDTH - 1) + "\r", end="")

def get_timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")

# ──────────────────────────── Response Renderer ───────────────────────────────
SEVERITY_STYLES = {
    "[LOW]":      (C.GREEN,   "🟢 LOW"),
    "[MEDIUM]":   (C.YELLOW,  "🟡 MEDIUM"),
    "[HIGH]":     (C.RED,     "🔴 HIGH"),
    "[CRITICAL]": (C.MAGENTA, "🚨 CRITICAL"),
}

def render_response(text: str) -> list:
    """
    Render ARIA's response with colored formatting.
    Returns list of follow-up suggestions.
    """
    suggestions = []

    # Extract follow-up line
    lines = text.strip().split("\n")
    filtered_lines = []
    for line in lines:
        if line.strip().startswith("FOLLOW-UP:"):
            raw = line.replace("FOLLOW-UP:", "").strip()
            suggestions = [s.strip() for s in raw.split("|") if s.strip()]
        else:
            filtered_lines.append(line)

    print()
    for line in filtered_lines:
        line_s = line.strip()

        # Severity badge
        for key, (color, label) in SEVERITY_STYLES.items():
            if key in line_s:
                line_s = line_s.replace(key, "")
                print(f"\n    {color}{C.BOLD}◆ SEVERITY: {label}{C.RESET}")
                continue

        # Section headings (all caps words followed by colon or standalone)
        if re.match(r'^[A-Z][A-Z\s&/]{3,}:?\s*$', line_s) and line_s:
            print(f"\n    {C.CYAN}{C.BOLD}{'─'*40}{C.RESET}")
            print(f"    {C.CYAN}{C.BOLD}{line_s.upper()}{C.RESET}")
            print(f"    {C.CYAN}{C.BOLD}{'─'*40}{C.RESET}")

        # Numbered steps [1] [2] ...
        elif re.match(r'^\[\d+\]', line_s):
            num = re.match(r'^\[(\d+)\]', line_s).group(1)
            rest = re.sub(r'^\[\d+\]\s*', '', line_s)
            wrap_print(
                f"  [{C.YELLOW}{C.BOLD}{num}{C.RESET}]  {rest}",
                indent=2
            )

        # Command lines >>>
        elif line_s.startswith(">>>"):
            cmd = line_s[3:].strip()
            print(f"\n    {C.DIM}┌─ command ──────────────────────────{C.RESET}")
            print(f"    {C.GREEN}{C.BOLD}  $ {cmd}{C.RESET}")
            print(f"    {C.DIM}└────────────────────────────────────{C.RESET}\n")

        # Warnings !!
        elif line_s.startswith("!!"):
            msg = line_s[2:].strip()
            print(f"\n    {C.RED}⚠  {msg}{C.RESET}\n")

        # Tips >>
        elif line_s.startswith(">>"):
            msg = line_s[2:].strip()
            print(f"\n    {C.BLUE}💡 {msg}{C.RESET}\n")

        # Empty line
        elif not line_s:
            print()

        # Normal text
        else:
            wrap_print(line_s, indent=4, color=C.WHITE)

    return suggestions


# ──────────────────────────── Banner ──────────────────────────────────────────
def print_banner():
    clear()
    banner = f"""
{C.CYAN}{C.BOLD}
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║    ██████╗   ██╗    ██╗██╗   ██╗ █████╗              ║
    ║   ██╔═══██╗ ██║    ██║██║   ██║██╔══██╗             ║
    ║   ███████║ ██████╗ ██████╗  ██║███████║      ▄▄▄     ║
    ║   ██╔══██║ ██╔══╝  ██╔══╝  ██║██╔══██║     ▀▀▀▀▀    ║
    ║   ██║  ██║ ██║     ██║     ██║██║  ██║    ▐██████▌   ║
    ║   ╚═╝  ╚═╝ ╚═╝     ╚═╝     ╚═╝╚═╝  ╚═╝    ▝████▘    ║
    ║                                                       ║
    ║   Automated Resolution & IT Assistant  v3.0           ║
    ║   Powered by Anthropic Claude                         ║
    ╚═══════════════════════════════════════════════════════╝
{C.RESET}"""
    print(banner)
    print(f"    {C.GREEN}●{C.RESET} {C.DIM}System Online  ·  {get_timestamp()}{C.RESET}")
    print(f"    {C.CYAN}●{C.RESET} {C.DIM}AI Engine: claude-sonnet-4-20250514{C.RESET}")
    print(f"    {C.YELLOW}●{C.RESET} {C.DIM}Type 'help' for commands  ·  'quit' to exit{C.RESET}\n")
    hr()


# ──────────────────────────── Quick Topics ────────────────────────────────────
QUICK_TOPICS = [
    ("1", "WiFi / Network Issues",      "My WiFi is not connecting"),
    ("2", "Slow Computer",              "My computer is extremely slow and lagging"),
    ("3", "Blue Screen of Death",       "I am getting a blue screen of death BSOD error"),
    ("4", "Forgot Password",            "I forgot my password and cannot login to my account"),
    ("5", "Virus / Malware",            "I think my computer has a virus or malware"),
    ("6", "Printer Not Working",        "My printer is not printing and shows offline"),
    ("7", "Software Won't Install",     "Software installation keeps failing with an error"),
    ("8", "Screen / Display Issues",    "My screen is flickering or showing a black screen"),
    ("9", "Email Problems",             "My email is not sending or receiving messages"),
    ("0", "VPN Connection Failed",      "My VPN connection keeps dropping or failing"),
]

def show_help():
    print(f"\n{C.CYAN}{C.BOLD}  ── COMMANDS ─────────────────────────────────────────{C.RESET}")
    cmds = [
        ("help",    "Show this help menu"),
        ("topics",  "Show quick topic shortcuts"),
        ("history", "Show conversation summary"),
        ("clear",   "Clear the screen"),
        ("new",     "Start a fresh conversation"),
        ("quit",    "Exit the chatbot"),
    ]
    for cmd, desc in cmds:
        print(f"  {C.YELLOW}{cmd:<12}{C.RESET}{C.DIM}{desc}{C.RESET}")
    print()

def show_topics():
    print(f"\n{C.CYAN}{C.BOLD}  ── QUICK TOPICS ──────────────────────────────────────{C.RESET}")
    for num, label, _ in QUICK_TOPICS:
        print(f"  {C.YELLOW}[{num}]{C.RESET}  {label}")
    print(f"\n  {C.DIM}Type a number to jump straight to that topic.{C.RESET}\n")

def show_history(history: list):
    if not history:
        print(f"\n  {C.DIM}No conversation history yet.{C.RESET}\n")
        return
    print(f"\n{C.CYAN}{C.BOLD}  ── CONVERSATION HISTORY ─────────────────────────────{C.RESET}")
    for i, msg in enumerate(history, 1):
        role = msg["role"]
        snippet = msg["content"][:80].replace("\n", " ")
        if len(msg["content"]) > 80:
            snippet += "…"
        color = C.BLUE if role == "user" else C.GREEN
        label = "YOU " if role == "user" else "ARIA"
        print(f"  {color}{C.BOLD}{label}{C.RESET}  {C.DIM}[{i}]{C.RESET}  {snippet}")
    print(f"\n  {C.DIM}Total messages: {len(history)}{C.RESET}\n")


# ──────────────────────────── Follow-up Suggestions ───────────────────────────
def show_suggestions(suggestions: list):
    if not suggestions:
        return
    print(f"\n    {C.DIM}{'─'*50}{C.RESET}")
    print(f"    {C.CYAN}{C.BOLD}FOLLOW-UP QUESTIONS:{C.RESET}")
    for i, s in enumerate(suggestions[:3], 1):
        print(f"    {C.YELLOW}[{i}]{C.RESET}  {C.DIM}{s}{C.RESET}")
    print(f"    {C.DIM}(Type a number 1-3 to ask, or type your own question){C.RESET}")
    print()


# ──────────────────────────── Core Chat Function ──────────────────────────────
def chat(client: anthropic.Anthropic, history: list, user_message: str) -> tuple[str, list]:
    """
    Send a message to Claude and get a response.
    Returns (response_text, suggestions).
    """
    history.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        reply = response.content[0].text
        history.append({"role": "assistant", "content": reply})
        return reply, history

    except anthropic.AuthenticationError:
        return "ERROR: Invalid API key. Set ANTHROPIC_API_KEY environment variable.", history
    except anthropic.RateLimitError:
        return "ERROR: Rate limit reached. Please wait a moment and try again.", history
    except anthropic.APIConnectionError:
        return "ERROR: Cannot connect to Anthropic API. Check your internet connection.", history
    except Exception as e:
        return f"ERROR: Unexpected error — {str(e)}", history


# ──────────────────────────── Input Prompt ────────────────────────────────────
def get_input(suggestions: list) -> str:
    """Show the input prompt and get user input."""
    print(f"  {C.CYAN}┌─{C.RESET} {C.BOLD}You{C.RESET}  {C.DIM}{get_timestamp()}{C.RESET}")
    try:
        user_in = input(f"  {C.CYAN}└▶{C.RESET} ").strip()
    except (KeyboardInterrupt, EOFError):
        return "quit"

    # Check if user picked a suggestion number
    if user_in in ("1", "2", "3") and suggestions:
        idx = int(user_in) - 1
        if idx < len(suggestions):
            chosen = suggestions[idx]
            print(f"     {C.DIM}▶ {chosen}{C.RESET}\n")
            return chosen

    return user_in


# ──────────────────────────── Main ────────────────────────────────────────────
def main():
    # ── API Key Check ──
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(f"\n{C.YELLOW}  ⚠  ANTHROPIC_API_KEY not set.{C.RESET}")
        print(f"  {C.DIM}Enter your key now, or press Enter to use demo mode.{C.RESET}")
        api_key = input(f"  API Key: ").strip()
        if not api_key:
            print(f"\n  {C.RED}No API key provided. Exiting.{C.RESET}\n")
            sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print_banner()

    # ── Welcome Message ──
    print(f"\n  {C.GREEN}{C.BOLD}ARIA{C.RESET}  {C.DIM}{get_timestamp()}{C.RESET}")
    aria_welcome = (
        "Hello! I'm ARIA, your dedicated IT support specialist.\n\n"
        "I can help you diagnose and fix issues with:\n"
        "  • Networks & WiFi  • Windows / macOS / Linux\n"
        "  • Hardware & drivers  • Security & malware\n"
        "  • Software errors  • Printers & peripherals\n"
        "  • Servers, cloud & more\n\n"
        "What technical issue can I help you resolve today?\n"
        "Type 'topics' to see quick shortcuts or 'help' for commands."
    )
    print()
    for line in aria_welcome.split("\n"):
        print(f"    {C.WHITE}{line}{C.RESET}")
    print()
    hr(char="─", color=C.GRAY)

    history: list = []
    suggestions: list = []

    # ── Main Loop ──
    while True:
        print()
        user_in = get_input(suggestions)
        suggestions = []

        if not user_in:
            continue

        lower = user_in.lower()

        # ── Commands ──
        if lower in ("quit", "exit", "q", "bye"):
            hr()
            print(f"\n  {C.CYAN}Thanks for using ARIA. Stay secure! 👋{C.RESET}\n")
            break

        elif lower == "clear":
            print_banner()
            continue

        elif lower == "help":
            show_help()
            continue

        elif lower == "topics":
            show_topics()
            continue

        elif lower == "history":
            show_history(history)
            continue

        elif lower == "new":
            if input(f"\n  {C.YELLOW}Start a new conversation? All history will be lost. [y/N]: {C.RESET}").lower() == "y":
                history = []
                suggestions = []
                print_banner()
                print(f"\n  {C.GREEN}New session started.{C.RESET}\n")
            continue

        # ── Quick Topic Shortcuts ──
        for num, label, prompt in QUICK_TOPICS:
            if user_in == num:
                user_in = prompt
                print(f"     {C.DIM}▶ {label}{C.RESET}\n")
                break

        # ── Send to Claude ──
        print()
        spinner("ARIA is thinking...", duration=0.8)

        reply, history = chat(client, history, user_in)

        # ── Render Response ──
        print(f"\n  {C.GREEN}{C.BOLD}ARIA{C.RESET}  {C.DIM}{get_timestamp()}{C.RESET}")
        hr(char="·", color=C.GRAY)

        if reply.startswith("ERROR:"):
            print(f"\n    {C.RED}{reply}{C.RESET}\n")
        else:
            suggestions = render_response(reply)
            show_suggestions(suggestions)

        hr(char="─", color=C.GRAY)


# ──────────────────────────── Entry Point ─────────────────────────────────────
if __name__ == "__main__":
    main()
