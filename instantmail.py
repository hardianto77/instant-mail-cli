#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  INSTANT MAIL CLI — Temp Email + OTP Watcher (Termux Ready)      ║
║  Reverse-engineered client for "Instant Mail" (com.temporary.   ║
║  email.pro) — 4 services, real Gmail support, zero dependencies ║
║                                                                  ║
║  Run:   python instantmail.py                                    ║
║  Test:  python instantmail.py --test                             ║
╚══════════════════════════════════════════════════════════════════╝
"""
import json, ssl, sys, os, re, time, base64, random, string, urllib.request, urllib.error

# ───────────────────────── CONFIG (app se nikala hua) ─────────────────────────
APP_KEY      = "b9db03078622"
ENC_KEY      = "ao-sq-=x-5b-4*-Bz".split("-")
HD_BASE      = "https://mail-server.1timetech.com/api"
HD_GMAIL     = "https://mail-server-2.1timetech.com/api"
TMIO_BASE    = "https://api.internal.temp-mail.io/api"
TMORG_BASE   = "https://mob2.temp-mail.org"
HD_DOMAINS   = ["gmail10p.com","oletters.com","oemails.com","oegmail.com","suiemail.com",
                "voewo.com","yanemail.com","tempmail.edu.pl","rommiui.com"]
TMIO_DOMAINS = ["bltiwd.com","bwmyga.com","ozsaip.com","yzcalo.com","lnovic.com",
                "ruutukf.com","gmeenramy.com","olipii.com"]
STATE_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".instantmail_state.json")
UA_WEB  = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36"
UA_TM   = "TempMail/1022 CFNetwork/1568.100.1 Darwin/24.0.0"

# ───────────────────────── ANSI COLORS ─────────────────────────
class C:
    R  = "\033[0m";   B = "\033[1m";    DIM = "\033[2m"
    RED= "\033[91m"; GRN= "\033[92m";  YEL = "\033[93m"
    BLU= "\033[94m"; MAG= "\033[95m";  CYN = "\033[96m"; WHT = "\033[97m"
    BG = "\033[100m"; BGR = "\033[101m"; BGG = "\033[102m"; BGB = "\033[104m"; BGM = "\033[105m"; BGC = "\033[106m"
def enabled_colors():
    return sys.stdout.isatty() or os.environ.get("FORCE_COLOR")
if not enabled_colors():
    for k in vars(C):
        if not k.startswith("_"): setattr(C, k, "")

# ───────────────────────── CRYPTO (app ka custom encryption, cracked) ─────────
def _swap(s):
    for p in ENC_KEY:
        if len(p) == 2:
            a, b = p[0], p[1]
            s = s.replace(a, "\x00").replace(b, a).replace("\x00", b)
    return s
def enc(obj):
    if not isinstance(obj, str): obj = json.dumps(obj)
    return _swap(base64.b64encode(obj.encode()).decode()[::-1])
def dec(t):
    if t is None or isinstance(t, (dict, list, int)): return t
    try: raw = base64.b64decode(_swap(t[::-1]).encode()).decode()
    except Exception: return t
    try: return json.loads(raw)
    except Exception: return raw

# ───────────────────────── HTTP ─────────────────────────
def http(url, method="GET", body=None, headers=None, timeout=15):
    data = body.encode() if isinstance(body, str) else (json.dumps(body).encode() if body else None)
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("accept", "application/json")
    r.add_header("user-agent", UA_WEB)
    for k, v in (headers or {}).items(): r.add_header(k, v)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=ssl.create_default_context()) as resp:
            return resp.status, resp.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as e:
        return 0, f"{e}"

def rnd(n=12): return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

# ───────────────────────── SERVICE LAYER ─────────────────────────
def gen_gmail(custom=None):
    """HD_GMAIL — REAL @gmail.com (dot-trick pool). custom ignored by server."""
    st, txt = http(HD_GMAIL + "/g-mail", "POST", body=enc({"email": None}),
                   headers={"x-app-key": APP_KEY, "content-type": "text/plain"})
    if st != 200: raise RuntimeError(f"HTTP {st}")
    d = dec(json.loads(txt)["data"])
    return {"service": "HD_GMAIL", "email": d["email"], "id": d["id"], "token": None}

def gen_hd():
    """HD — 9 domains ka random pool (server random deta hai)."""
    st, txt = http(HD_BASE + "/email", "POST", body=enc({"email": None}),
                   headers={"x-app-key": APP_KEY, "content-type": "text/plain"})
    if st != 200: raise RuntimeError(f"HTTP {st}")
    d = dec(json.loads(txt)["data"])
    return {"service": "HD", "email": d["email"], "id": d["id"], "token": None}

def gen_tmio(name=None, domain=None):
    """temp-mail.io — custom naam + domain choose ho sakta hai."""
    payload = {}
    if name:   payload["name"] = name
    if domain: payload["domain"] = domain
    if not payload: payload = {"min_name_length": 10, "max_name_length": 10}
    hdr = {"authority": "api.internal.temp-mail.io", "application-name": "web",
           "application-version": "2.2.29", "origin": "https://temp-mail.io",
           "referer": "https://temp-mail.io/", "content-type": "application/json"}
    st, txt = http(TMIO_BASE + "/v3/email/new", "POST", body=payload, headers=hdr)
    if st != 200: raise RuntimeError(f"HTTP {st}: {txt[:80]}")
    d = json.loads(txt)
    return {"service": "temp-mail-io", "email": d["email"], "id": d["email"], "token": d["token"]}

def gen_tmorg():
    """temp-mail.org — pura random."""
    hdr = {"user-agent": UA_TM, "accept-encoding": "identity"}
    st, txt = http(TMORG_BASE + "/mailbox", "POST", headers=hdr)
    if st != 200: raise RuntimeError(f"HTTP {st}")
    d = json.loads(txt)
    return {"service": "temp-mail", "email": d["mailbox"], "id": d["mailbox"], "token": d["token"]}

def fetch_messages(mb):
    """Unified inbox fetch → [{id, from, subject, text, html, date}]"""
    svc = mb["service"]
    if svc in ("HD", "HD_GMAIL"):
        base = HD_BASE if svc == "HD" else HD_GMAIL
        st, txt = http(f"{base}/email/{mb['id']}/messages?" + enc({}),
                       headers={"x-app-key": APP_KEY})
        if st != 200: raise RuntimeError(f"HTTP {st}")
        data = json.loads(txt).get("data")
        msgs = dec(data) or []
        out = []
        for m in msgs:
            out.append({"id": m.get("_id") or m.get("id"), "from": m.get("from", ""),
                        "subject": m.get("subject", ""),
                        "text": m.get("bodyPreview") or "", "html": m.get("bodyHtml") or "",
                        "date": m.get("receivedAt") or m.get("createdAt")})
        return out
    if svc == "temp-mail-io":
        st, txt = http(f"{TMIO_BASE}/v3/email/{mb['email']}/messages",
                       headers={"authorization": f"Bearer {mb['token']}",
                                "authority": "api.internal.temp-mail.io",
                                "origin": "https://temp-mail.io", "referer": "https://temp-mail.io/"})
        if st != 200: raise RuntimeError(f"HTTP {st}")
        msgs = json.loads(txt) if txt.strip().startswith("[") else json.loads(txt).get("messages", [])
        return [{"id": m.get("id"), "from": m.get("from"), "subject": m.get("subject"),
                 "text": m.get("body_text") or m.get("bodyText") or "",
                 "html": m.get("body_html") or m.get("bodyHtml") or "",
                 "date": m.get("created_at") or m.get("createdAt")} for m in msgs]
    if svc == "temp-mail":
        st, txt = http(TMORG_BASE + "/messages",
                       headers={"user-agent": UA_TM, "authorization": "Bearer " + (mb.get("token") or "")})
        if st != 200: raise RuntimeError(f"HTTP {st}")
        msgs = json.loads(txt).get("messages", [])
        return [{"id": m.get("id") or m.get("uid"), "from": m.get("from") or m.get("mail_from"),
                 "subject": m.get("subject") or m.get("mail_subject"),
                 "text": m.get("body_text") or m.get("bodyText") or m.get("text") or "",
                 "html": m.get("body_html") or m.get("bodyHtml") or m.get("html") or "",
                 "date": m.get("created_at") or m.get("createdAt")} for m in msgs]
    raise RuntimeError("unknown service")

# ───────────────────────── OTP EXTRACTOR ─────────────────────────
OTP_WORDS = re.compile(r"(otp|one[\s\-_.]?time|code|verif|pin|password|passcode|token|confirm)", re.I)
def strip_html(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", h, flags=re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", h.replace("&nbsp;", " ").replace("&#39;", "'"))).strip()
def extract_otp(text):
    """Email text se sabse likely OTP nikalo. Return (best, [all_codes])"""
    t = strip_html(text) if "<" in text and ">" in text else text
    hits = []
    for m in re.finditer(r"(?<!\d)(?<!\d\.)(\d{4,8})(?!\d)(?!\.\d)", t):
        code = m.group(1)
        ctx = t[max(0, m.start() - 70): m.end() + 70].lower()
        score = 0
        if OTP_WORDS.search(ctx): score += 10
        if len(code) == 6: score += 4
        elif len(code) == 4: score += 1
        elif len(code) == 8: score += 2
        elif len(code) == 5: score += 1
        if re.match(r"^(19|20)\d{2}$", code) and "year" in ctx: score -= 8
        if re.search(r"[₹$€£]\s*$", t[max(0, m.start()-3):m.start()]): score -= 5
        if re.search(r"\d{1,2}[:/]\d{2}", ctx) and len(code) in (4,) and re.search(r"\d:\d", code): score -= 9
        hits.append((score, code))
    hits.sort(key=lambda x: (-x[0], -len(x[1])))
    best = hits[0][1] if hits and hits[0][0] >= 4 else None
    return best, [h[1] for h in hits]

# ───────────────────────── STATE ─────────────────────────
def load_state():
    try: return json.load(open(STATE_FILE))
    except Exception: return {"current": None, "history": []}
def save_state(s):
    try: json.dump(s, open(STATE_FILE, "w"), indent=1)
    except Exception: pass

# ───────────────────────── UI HELPERS ─────────────────────────
def banner():
    print(f"""{C.CYN}{C.B}
    _              _       _       __  __                                    _
   (_) ___ _   _  (_)     (_)___  |  \\/  | ___  ___ _ __ ___  _   _ ___  __| |
   | |/ _ \\ | | | | |____| / __| | |\\/| |/ _ \\/ __| '_ ` _ \\| | | / __| / _` |
   | |  __/ |_| | | |____| \\__ \\ | |  | |  __/\\__ \\ | | | | | |_| \\__ \\| (_| |
  _/ |\\___|\\__, |_/      | |___/ |_|  |_|\\___||___/_| |_| |_|\\__,_|___/ \\__,_|
 |__/       |___/       |_|  {C.MAG}Temp Email + OTP Watcher{C.R}  {C.DIM}(Instant Mail 8.0 reverse-eng){C.R}
""")
def line(ch="─", n=64): print(C.DIM + ch * n + C.R)
def box(txt, color=C.CYN):
    l = len(txt) + 4
    print(color + f"┌{'─'*l}┐")
    print(f"│  {txt}  │")
    print(f"└{'─'*l}┘" + C.R)
def ok(msg):   print(f"  {C.GRN}✔{C.R} {msg}")
def bad(msg):  print(f"  {C.RED}✘ {msg}{C.R}")
def info(msg): print(f"  {C.CYN}➜{C.R} {msg}")
def warn(msg): print(f"  {C.YEL}⚠ {msg}{C.R}")
def spinner_i(sec, msg=""):
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    t0 = time.time(); i = 0
    while time.time() - t0 < sec:
        print(f"\r  {C.CYN}{frames[i % 10]}{C.R} {msg}   ", end="", flush=True)
        time.sleep(0.08); i += 1
    print("\r" + " " * (len(msg) + 10) + "\r", end="")
def copy_clipboard(txt):
    import subprocess, shutil
    for cmd, args in (("termux-clipboard-set", [txt]), ("pbcopy", [])):
        if shutil.which(cmd):
            try:
                subprocess.run([cmd] + args, input=txt.encode() if cmd == "pbcopy" else None,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               **({"input": txt.encode()} if cmd == "pbcopy" else {}))
                return True
            except Exception: pass
    return False
def read_choice(prompt, lo, hi):
    try:
        v = input(f"{C.B}{C.CYN}{prompt}{C.R} ").strip()
        if v == "": return None
        v = int(v)
        return v if lo <= v <= hi else None
    except (ValueError, KeyboardInterrupt, EOFError): return None
def pause():
    try: input(f"\n{C.DIM}Enter dabao continue ke liye...{C.R}")
    except (KeyboardInterrupt, EOFError): pass

# ───────────────────────── MAIN ACTIONS ─────────────────────────
def show_current(st):
    cur = st.get("current")
    if not cur:
        warn("Abhi koi email generate nahi hui — pehle menu se banao")
        return
    line()
    print(f"  {C.B}📧 Current Email:{C.R} {C.BGG}{C.B} {cur['email']} {C.R}")
    print(f"  {C.DIM}Service: {cur['service']}   |   Banaya: {time.strftime('%H:%M:%S', time.localtime(cur.get('ts', 0)))}{C.R}")
    line()

def do_generate(st, kind):
    try:
        if kind == "gmail":
            box("⚡ REAL GMAIL generate ho raha hai...", C.MAG)
            mb = gen_gmail()
        elif kind == "hd":
            box("🎲 HD random email (9 domains pool)...", C.CYN)
            mb = gen_hd()
        elif kind == "tmio":
            box("🎯 Custom email (temp-mail.io)", C.YEL)
            print(f"  {C.DIM}Domains: {', '.join(TMIO_DOMAINS[:4])} ...{C.R}")
            name = input("  Username chaho to likho (Enter = random): ").strip().lower()
            name = re.sub(r"[^a-z0-9._-]", "", name) or None
            print(f"  {C.DIM}1.bltiwd 2.bwmyga 3.ozsaip 4.yzcalo 5.lnovic 6.ruutukf 7.gmeenramy 8.olipii{C.R}")
            c = read_choice("  Domain no. (Enter = random):", 1, 8)
            if c: dom = TMIO_DOMAINS[c - 1]
            mb = gen_tmio(name, dom)
        elif kind == "tmorg":
            box("🎲 temp-mail.org random...", C.GRN)
            mb = gen_tmorg()
        mb["ts"] = time.time()
        st["current"] = mb
        st.setdefault("history", []).insert(0, mb)
        st["history"] = st["history"][:20]
        save_state(st)
        ok(f"Email ready: {C.B}{C.BGG} {mb['email']} {C.R}")
        if copy_clipboard(mb["email"]):
            ok("Clipboard me copy ho gaya ✂  (Termux)")
        else:
            info(f"Copy kar lo: {mb['email']}")
        warn("Ab is email se kahin bhi signup karo — phir menu [2] OTP Watcher chalao")
    except KeyboardInterrupt: print()
    except Exception as e:
        bad(f"Generate fail: {e}")

def do_watch(st):
    cur = st.get("current")
    if not cur:
        bad("Pehle email generate karo (menu 1)"); return
    box(f"📥 OTP WATCHER — {cur['email']}", C.MAG)
    info(f"Inbox har 5 sec me check ho raha hai... (Ctrl+C = stop)")
    print(f"  {C.DIM}Kisi bhi website/app pe is email se login/signup karo{C.R}")
    line()
    seen = set()
    for attempt in range(1, 241):  # ~20 min max
        try:
            msgs = fetch_messages(cur)
        except KeyboardInterrupt: raise
        except Exception as e:
            print(f"\r  {C.YEL}retrying... ({e}){C.R}"); time.sleep(5); continue
        fresh = [m for m in msgs if m["id"] not in seen]
        for m in fresh:
            seen.add(m["id"])
            body = m["text"] or strip_html(m["html"] or "")
            best, allc = extract_otp((m["subject"] or "") + "\n" + body)
            print(f"\n  {C.B}{C.GRN}📨 NEW MAIL!{C.R}  {C.DIM}{time.strftime('%H:%M:%S')}{C.R}")
            print(f"  {C.CYN}From:{C.R} {m['from'][:48]}")
            print(f"  {C.CYN}Subj:{C.R} {(m['subject'] or '(none)')[:60]}")
            if best:
                print(f"\n  {C.B}{C.BGR}{C.B} 🔑 OTP CODE:  {best}  {C.R}\n")
                if copy_clipboard(best): ok(f"OTP '{best}' clipboard me copy! ✂")
                line(); return
            elif allc:
                print(f"  {C.YEL}Candidate codes:{C.R} {', '.join(allc[:8])}")
        left = 300 - (attempt % 300)
        print(f"\r  {C.DIM}⏳ {attempt*5:>4d}s  |  mails: {len(seen)}  |  waiting...{C.R}   ", end="", flush=True)
        for _ in range(10):
            time.sleep(0.5)
    print("\n"); warn("20 min ho gaye, koi OTP nahi aya. Menu [3] se messages padh sakta hai")

def do_messages(st):
    cur = st.get("current")
    if not cur:
        bad("Pehle email generate karo"); return
    try:
        msgs = fetch_messages(cur)
    except Exception as e:
        bad(f"Fetch fail: {e}"); return
    if not msgs:
        warn("Inbox khali hai — koi mail nahi aya abhi"); return
    box(f"📨 {len(msgs)} message(s) — {cur['email']}", C.CYN)
    for i, m in enumerate(msgs[:15], 1):
        body = m["text"] or strip_html(m["html"] or "")
        best, allc = extract_otp((m["subject"] or "") + "\n" + body)
        print(f"\n  {C.B}[{i}]{C.R} {C.CYN}From:{C.R} {(m['from'] or '?')[:45]}")
        print(f"      {C.CYN}Subj:{C.R} {(m['subject'] or '(none)')[:65]}")
        preview = body.replace("\n", " ")[:110]
        print(f"      {C.DIM}{preview}...{C.R}")
        if best: print(f"      {C.B}{C.BGR}{C.B} 🔑 OTP: {best} {C.R}")
        elif allc: print(f"      {C.YEL}codes: {', '.join(allc[:6])}{C.R}")
    if len(msgs) > 15: info(f"...aur {len(msgs)-15} messages")
    n = read_choice(f"\nFull message padhna hai? number (Enter = no):", 1, min(15, len(msgs)))
    if n:
        m = msgs[n - 1]
        body = m["text"] or strip_html(m["html"] or "")
        line()
        print(f"  {C.B}From:{C.R} {m['from']}\n  {C.B}Subj:{C.R} {m['subject']}\n  {C.B}Body:{C.R}")
        print("  " + body[:2500].replace("\n", "\n  "))
        line()
        best, _ = extract_otp((m["subject"] or "") + "\n" + body)
        if best:
            print(f"  {C.B}{C.BGR}{C.B} 🔑 OTP: {best} {C.R}")
            if copy_clipboard(best): ok("copied ✂")

def do_switch(st):
    hist = [h for h in st.get("history", []) if h.get("email") != (st.get("current") or {}).get("email")]
    if not hist:
        warn("Koi purani email nahi"); return
    box("🕘 History — purani emails", C.YEL)
    for i, h in enumerate(hist[:10], 1):
        mark = f"{C.GRN}●{C.R}" if h is (st.get("current")) else " "
        print(f"  {mark} [{i}] {h['email']}  {C.DIM}({h['service']}){C.R}")
    n = read_choice("Switch karne ka number (Enter = cancel):", 1, min(10, len(hist)))
    if n:
        st["current"] = hist[n - 1]; save_state(st)
        ok(f"Current: {st['current']['email']}")

def do_test():
    box("🧪 SELF-TEST chal raha hai...", C.YEL)
    print(f"\n{C.B}[1/4] Crypto roundtrip:{C.R}")
    sample = {"email": "test123@gmail.com", "otp": 987654}
    if dec(enc(sample)) == sample: ok(f"encode/decode perfect  {C.DIM}{enc(sample)[:34]}...{C.R}")
    else: bad("crypto fail!"); return
    print(f"\n{C.B}[2/4] OTP extractor:{C.R}")
    cases = [
        ("Your verification code is 582914. Do not share", "582914"),
        ("Bhai OTP: 7732 batao", "7732"),
        ("WhatsApp code 449-928? nope — Your WhatsApp code is 508221", "508221"),
        ("Order #12345 shipped, tracking 991234567890", None),
        ("<p>Your login <b>code</b>: <span>30471</span> valid 10 min</p>", "30471"),
    ]
    for txt, want in cases:
        got, _ = extract_otp(txt)
        mark = ok if got == want else bad
        mark(f"{str(got):>8}  (expect {want})  {C.DIM}{txt[:44]}{C.R}")
    print(f"\n{C.B}[3/4] Live email generation (4 services):{C.R}")
    live = 0
    for name, fn in (("HD_GMAIL (real gmail)", gen_gmail), ("HD (9 domains)", gen_hd),
                     ("temp-mail.io", gen_tmio), ("temp-mail.org", gen_tmorg)):
        try:
            mb = fn(); live += 1
            ok(f"{name:22s} → {mb['email']}")
        except Exception as e:
            bad(f"{name:22s} → {e}")
    print(f"\n{C.B}[4/4] Inbox fetch check:{C.R}")
    try:
        mb = gen_gmail(); m = fetch_messages(mb)
        ok(f"Gmail inbox readable ({len(m)} messages — naya inbox khali hona normal hai)")
    except Exception as e:
        bad(f"inbox fail: {e}")
    line()
    box(f"RESULT: {live}/4 services live  |  Tool ready hai ✅", C.GRN if live else C.RED)

# ───────────────────────── MENU ─────────────────────────
def menu():
    st = load_state()
    while True:
        cur = st.get("current")
        print("\033[2J\033[H", end="")  # ANSI clear (Termux-safe)
        banner()
        if cur:
            print(f"  {C.B}📧 Current:{C.R} {C.BGG}{C.B} {cur['email']} {C.R}  {C.DIM}({cur['service']}){C.R}\n")
        print(f"""  {C.B}{C.MAG}[1] ⚡ Gmail generate{C.R}        — REAL @gmail.com (sabse powerful)
  {C.B}[2] 📥 OTP Watcher{C.R}           — live inbox + auto OTP nikalega
  {C.B}[3] 📨 Messages padho{C.R}        — inbox list + full body
  {C.B}[4] 🎲 Random email (HD){C.R}     — 9 domains pool
  {C.B}[5] 🎯 Custom email{C.R}          — apna username+domain (temp-mail.io)
  {C.B}[6] 🎲 temp-mail.org{C.R}         — pura random
  {C.B}[7] 🕘 History / switch{C.R}      — purani emails wapas lo
  {C.B}[8] 📋 Email copy/info{C.R}       — current email dikhao/copy
  {C.B}[9] 🧪 Self-test{C.R}             — sab kuch verify karo
  {C.B}[0] ❌ Exit{C.R}
""")
        c = ""
        try:
            c = input(f"{C.B}{C.CYN}Choice daalo [0-9]:{C.R} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C.YEL}bye 👋{C.R}"); break
        print()
        if c == "1": do_generate(st, "gmail")
        elif c == "2": do_watch(st)
        elif c == "3": do_messages(st)
        elif c == "4": do_generate(st, "hd")
        elif c == "5": do_generate(st, "tmio")
        elif c == "6": do_generate(st, "tmorg")
        elif c == "7": do_switch(st)
        elif c == "8":
            show_current(st)
            if st.get("current") and copy_clipboard(st["current"]["email"]):
                ok("email clipboard me copy ✂")
        elif c == "9": do_test()
        elif c == "0":
            box("Bye! 👋  (emails ~2 din me expire ho jayengi)", C.CYN)
            break
        else: continue
        pause()

def wait_for_otp(mb, timeout=120, interval=3):
    t0 = time.time()
    seen = set()
    while time.time() - t0 < timeout:
        try:
            msgs = fetch_messages(mb)
            for m in msgs:
                if m.get("id") not in seen:
                    seen.add(m.get("id"))
                    body = m.get("text") or strip_html(m.get("html") or "")
                    best, allc = extract_otp((m.get("subject") or "") + "\n" + body)
                    if best:
                        return {"otp": best, "candidates": allc, "from": m.get("from"), "subject": m.get("subject")}
        except Exception:
            pass
        time.sleep(interval)
    return None

if __name__ == "__main__":
    try:
        import argparse
        parser = argparse.ArgumentParser(description="Instant Mail CLI & OTP Resolver", add_help=False)
        parser.add_argument("--test", action="store_true", help="Run self-test")
        parser.add_argument("--gen", choices=["gmail", "hd", "tmio", "tmorg"], help="Generate email")
        parser.add_argument("--wait-otp", type=int, nargs="?", const=120, default=None, help="Poll inbox for OTP")
        parser.add_argument("--inbox", action="store_true", help="Fetch current messages")
        parser.add_argument("--raw", action="store_true", help="Print raw email or OTP only")
        parser.add_argument("--json", action="store_true", help="Print JSON output")
        parser.add_argument("-h", "--help", action="store_true", help="Show help")
        args, _ = parser.parse_known_args()

        if args.help:
            parser.print_help()
            sys.exit(0)
        elif args.test:
            do_test()
        elif args.gen:
            st = load_state()
            fns = {"gmail": gen_gmail, "hd": gen_hd, "tmio": gen_tmio, "tmorg": gen_tmorg}
            mb = fns[args.gen]()
            mb["ts"] = int(time.time())
            st["current"] = mb
            st.setdefault("history", []).insert(0, mb)
            st["history"] = st["history"][:20]
            save_state(st)
            if args.raw:
                print(mb["email"])
            elif args.json:
                print(json.dumps(mb, indent=2))
            else:
                ok(f"Generated ({mb['service']}): {mb['email']}")
        elif args.wait_otp is not None:
            st = load_state()
            cur = st.get("current")
            if not cur:
                if args.json: print(json.dumps({"error": "No current mailbox. Run --gen first."})); sys.exit(1)
                bad("No current mailbox. Run --gen first."); sys.exit(1)
            res = wait_for_otp(cur, timeout=args.wait_otp)
            if res:
                if args.raw:
                    print(res["otp"])
                elif args.json:
                    print(json.dumps(res, indent=2))
                else:
                    ok(f"OTP Received: {res['otp']} (From: {res['from']})")
            else:
                if args.json: print(json.dumps({"error": "Timeout waiting for OTP"})); sys.exit(1)
                bad("Timeout waiting for OTP"); sys.exit(1)
        elif args.inbox:
            st = load_state()
            cur = st.get("current")
            if not cur:
                bad("No current mailbox. Run --gen first."); sys.exit(1)
            msgs = fetch_messages(cur)
            if args.json:
                print(json.dumps(msgs, indent=2))
            else:
                ok(f"Found {len(msgs)} message(s)")
                for m in msgs:
                    print(f"- From: {m['from']} | Subj: {m['subject']}")
        else:
            menu()
    except KeyboardInterrupt:
        print(f"\n{C.YEL}Ctrl+C — bye! 👋{C.R}")
