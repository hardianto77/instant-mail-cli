# ⚡ Instant Mail CLI

**Temporary Email + OTP Watcher — right in your terminal (Termux / Android, Linux, macOS)**

A single-file Python tool that generates disposable email addresses (including **real `@gmail.com`** addresses), watches the inbox live, and **automatically extracts OTP / verification codes** from incoming emails.

> Reverse-engineered & rebuilt from the Android app **"Instant Mail 8.0.0"** (`com.temporary.email.pro`). Works with the same 4 mail backends the app uses — no app install needed.
> See [`docs/ANALYSIS.md`](docs/ANALYSIS.md) for the full technical breakdown.

---

## ✨ Features

| Feature | Details |
|---|---|
| ⚡ **Real Gmail** | Generates real `@gmail.com` addresses (dot-trick alias pool) — works on sites that block temp-mail domains |
| 🎲 4 mail services | HD_GMAIL (gmail), HD (9 domains), temp-mail.io (8 domains + custom), temp-mail.org |
| 🎯 Custom address | Choose your own **username + domain** (temp-mail.io service) |
| 📥 **OTP Watcher** | Live inbox polling every 5s — new mail arrives → code is auto-extracted, highlighted & copied to clipboard |
| 🔑 Smart OTP parser | Keyword-scoring engine (`otp`, `code`, `verification`, `pin`…) — picks the right number, ignores order numbers / prices / dates |
| 📋 Clipboard | Auto-copy email & OTP (uses `termux-clipboard-set` on Android) |
| 🕘 History | Last 20 mailboxes saved locally — switch back anytime |
| 🧪 Built-in self-test | `python instantmail.py --test` verifies crypto, OTP parser and all 4 live services |
| 🪶 Zero dependencies | Pure Python 3 standard library — nothing to `pip install` |

---

## 🚀 Quick Start (Termux — 30 seconds)

Open **Termux** and paste:

```bash
pkg install python git -y
git clone https://github.com/Saurabh-gzp/instant-mail-cli.git
cd instant-mail-cli
python instantmail.py
```

That's it. No pip, no config. ✅

### Full Termux Setup (fresh phone)

1. **Install Termux** — download from [F-Droid](https://f-droid.org/en/packages/com.termux/) (recommended) or GitHub Releases. *(Play Store version is outdated — avoid)*
2. **Update packages**
   ```bash
   pkg update && pkg upgrade -y
   ```
3. **Install Python + Git**
   ```bash
   pkg install python git -y
   ```
4. **(Optional but recommended) Clipboard support**
   ```bash
   pkg install termux-api -y
   ```
   Also install the **Termux:API app** from F-Droid — this lets the tool auto-copy emails/OTPs to your phone's clipboard. Without it everything still works, you just copy manually.
5. **Clone & run**
   ```bash
   git clone https://github.com/Saurabh-gzp/instant-mail-cli.git
   cd instant-mail-cli
   python instantmail.py
   ```

### Linux / macOS / Windows

```bash
git clone https://github.com/Saurabh-gzp/instant-mail-cli.git
cd instant-mail-cli
python3 instantmail.py        # (Windows: python instantmail.py)
```

---

## 📖 How To Use (step by step)

### The typical OTP flow

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│ 1. Generate email    │ ──▶ │ 2. Sign up anywhere  │ ──▶ │ 3. OTP auto-appears │
│    menu → [1]        │     │    with that email   │     │    menu → [2]       │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
```

1. **`[1] ⚡ Gmail generate`** — creates one real `@gmail.com` address, copies it to your clipboard.
2. Go to any website/app, paste this email in their **sign-up / login** page, and ask them to send a verification code.
3. **`[2] 📥 OTP Watcher`** — the tool checks the inbox every 5 seconds. The moment the email arrives:
   ```
   📨 NEW MAIL!  14:32:07
   From: noreply@somesite.com
   Subj: Verify your email

    🔑 OTP CODE:  738291     ← highlighted + copied to clipboard
   ```
4. Paste the code back on the website. Done. 🎉

### Menu reference

| Key | Action | Notes |
|---|---|---|
| `1` | ⚡ Gmail generate | **Real @gmail.com** — one at a time, most powerful option |
| `2` | 📥 OTP Watcher | Live inbox watch (5s interval, ~20 min). Stops automatically once an OTP is found |
| `3` | 📨 Messages | Full inbox list + read any message body |
| `4` | 🎲 Random email (HD) | Random address from the 9-domain pool |
| `5` | 🎯 Custom email | **Your own username + pick one of 8 domains** (temp-mail.io) |
| `6` | 🎲 temp-mail.org | Fully random from temp-mail.org |
| `7` | 🕘 History | Switch back to a previous mailbox (last 20 saved) |
| `8` | 📋 Email copy/info | Show & copy the current email address |
| `9` | 🧪 Self-test | Verifies crypto, OTP parser and all 4 live services |
| `0` | ❌ Exit | |

### Domain catalog (21+ domains)

| Service | Domains | Custom? |
|---|---|---|
| **HD_GMAIL** | `gmail.com`, `googlemail.com` *(+ premium outlook/protonmail/icloud via the app)* | server picks a random alias |
| **HD** | `gmail10p.com` `oletters.com` `oemails.com` `oegmail.com` `suiemail.com` `voewo.com` `yanemail.com` `tempmail.edu.pl` `rommiui.com` | server picks randomly |
| **temp-mail.io** | `bltiwd.com` `bwmyga.com` `ozsaip.com` `yzcalo.com` `lnovic.com` `ruutukf.com` `gmeenramy.com` `olipii.com` | ✅ **full custom** (menu 5) |
| **temp-mail.org** | random (e.g. `tangvlog.com`, `seakol.com`, …) | ❌ random only |

---

## 🧪 Test it first (optional)

```bash
python instantmail.py --test
```

Checks, in order: crypto round-trip → OTP parser (5 cases) → live generation on all 4 services → inbox readability. If you see `4/4 services live`, everything works.

---

## 🔧 How It Works (technical)

- The original app is a React Native (Hermes) client for **4 mail APIs**. Two of them (`mail-server.1timetech.com`, `mail-server-2.1timetech.com`) use a lightweight custom body encryption, reverse-engineered from the bytecode:
  ```
  payload → JSON → Base64 → reverse string → swap 6 char-pairs
            ('ao','sq','=x','5b','4*','Bz')  →  send as text/plain
  ```
  plus the header `x-app-key: b9db03078622`. The same operation decrypts responses.
- **Real Gmail trick:** the backend owns a pool of genuine Gmail accounts; it inserts random dots into the username (`lyyenhong58579` → `lyy.e.nh.o.ng.5.8579`). Gmail ignores dots, so every variant delivers to the same real inbox, which the backend reads out to you via API.
- **OTP extraction:** every 4–8 digit number in the subject/body is scored (+10 if an OTP keyword appears within ±70 chars, +4 if 6-digit, penalties for years/prices/timestamps). Highest score wins; ties favor longer codes. Plain text and HTML bodies are both handled.

Full details, API maps and evidence: [`docs/ANALYSIS.md`](docs/ANALYSIS.md).

### For developers / AI agents

Single file `instantmail.py`, no classes you need to learn:

| Function | Purpose |
|---|---|
| `enc(obj)` / `dec(str)` | the custom API crypto (both directions) |
| `http(url, method, body, headers)` | stdlib HTTPS helper |
| `gen_gmail()` `gen_hd()` `gen_tmio(name, domain)` `gen_tmorg()` | mailbox creation, one per service |
| `fetch_messages(mb)` | unified inbox → normalized `[{id, from, subject, text, html, date}]` |
| `extract_otp(text)` | `(best_code_or_None, [all_candidate_codes])` |
| `do_watch(state)` | the live OTP watcher loop |
| `do_test()` | the self-test |

State lives in `.instantmail_state.json` next to the script. Adding a new mail service = write one `gen_*` + extend `fetch_messages`.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | `pkg install python -y` (Termux) / install Python 3.7+ |
| OTP not copying to clipboard | `pkg install termux-api -y` **and** install the *Termux:API* companion app, then restart Termux |
| `Generate fail: HTTP 4xx/5xx` | That backend is temporarily down — try another service (menu 4/5/6). Domains rotate from the server's remote config |
| Gmail not arriving | The Gmail pool is best-effort; some providers throttle. Watch for ~2 min, then generate a fresh address |
| OTP found but wrong number | Open menu `3`, read the full email — all candidate codes are listed; pick manually |
| Colors look broken | run `export TERM=xterm-256color` |
| Terms of Use / login expired errors from the site | temp mails are rejected by some services — use the Gmail option (menu 1) |

## ❓ FAQ

**Q: Is my current email saved between runs?**
Yes — in `.instantmail_state.json` (same folder). Menu `7` lists the last 20.

**Q: How long do addresses live?**
temp-mail addresses ≈ 2 days. HD / Gmail mailboxes are designed for longer use and can be restored.

**Q: Can I send email from these addresses?**
No — receive only (like every temp-mail service).

**Q: Does it need root?**
No. Works on any stock Android with Termux.

**Q: Is this legal?**
The tool only talks to public temp-mail APIs that the original app itself uses. What *you* do with it is your responsibility — see the disclaimer.

---

## ⚠️ Disclaimer

This project is for **educational & research purposes** (interoperability analysis of a published Android app). Using disposable emails to create fake accounts, bypass signup limits, or defraud any service violates those services' Terms of Use and possibly local law. The Gmail alias pool operates against Google's ToS and availability is not guaranteed. Use responsibly. **No warranty** — MIT License.

---

## 🙏 Credits

- Built by reverse-engineering **Instant Mail 8.0.0** (`com.temporary.email.pro`, 1timetech) — apktool + Hermes bytecode analysis. Full write-up in [`docs/ANALYSIS.md`](docs/ANALYSIS.md).
- Backends: temp-mail.org, temp-mail.io, and 1timetech mail servers (as used by the original app).
