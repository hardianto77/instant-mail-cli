# 🔍 Instant Mail 8.0.0 — Full Reverse-Engineering Analysis

**Target app:** `com.temporary.email.pro` ("Instant Mail") by 1timetech
**Version analyzed:** 8.0.0 (APK, 107 MB)
**Method:** apktool decompile → Hermes bytecode (v96) disassembly via `hermes-dec` → live API verification

---

## 1. App anatomy

| Layer | Finding |
|---|---|
| Framework | React Native (Expo 54), Hermes bytecode `assets/index.android.bundle` (4.8 MB, 26,138 functions, 47,906 strings) |
| Business logic | 100% JavaScript (Hermes), not smali — smali only contains RN/native libs |
| Monetization | RevenueCat (`goog_XzoXtKPXiaxCpjIdtLSgvucXbSe`), Paddle/Stripe, AdMob (`ca-app-pub-2528767647739792`), Amazon IAP |
| Remote config | Firebase Remote Config controls **all** domains/URLs/keys — they rotate server-side |

### Embedded config (recovered from the Hermes string table)

```json
{
  "appName": "Instant Mail", "appId": "com.temporary.email.pro",
  "encryptKey": "ao-sq-=x-5b-4*-Bz",
  "hdDomainsStr": "gmail10p.com,oletters.com,oemails.com,oegmail.com,suiemail.com,voewo.com,yanemail.com,tempmail.edu.pl,rommiui.com",
  "hdGmailDomainsStr": "+gmail.com,gmail.com,googlemail.com,+googlemail.com",
  "hdServiceURL": "https://mail-server.1timetech.com/api",
  "hdGmailServiceURL": "https://mail-server-2.1timetech.com/api",
  "mailServicesStr": "temp-mail,HD,HD_GMAIL,temp-mail-io",
  "mailServiceDefaultStr": "HD",
  "mailDomainsPremiumStr": "HD_GMAIL[gmail.com],HD_GMAIL[outlook.com],HD_GMAIL[protonmail.com],HD_GMAIL[icloud.com],HD[tempmail.edu.pl],HD[rommiui.com]",
  "hdServiceKey": "b9db03078622", "hdGmailServiceKey": "b9db03078622"
}
```

---

## 2. The four mail services

| # | Service | Base URL | Create | Inbox |
|---|---|---|---|---|
| 1 | `temp-mail` | `https://mob2.temp-mail.org` — spoofs the official iOS app UA `TempMail/1022 CFNetwork/1568.100.1 Darwin/24.0.0` | `POST /mailbox` → `{mailbox, token(JWT)}` | `GET /messages` (Bearer) |
| 2 | `temp-mail-io` | `https://api.internal.temp-mail.io/api` — spoofs temp-mail.io browser headers | `POST /v3/email/new` `{name?, domain?, min/max_name_length}` | `GET /v3/email/{email}/messages` (Bearer) |
| 3 | `HD` | `https://mail-server.1timetech.com/api` | `POST /email` (encrypted) | `GET /email/{id}/messages?<enc>` |
| 4 | `HD_GMAIL` | `https://mail-server-2.1timetech.com/api` | `POST /g-mail` (encrypted) | `GET /email/{id}/messages?<enc>` |

Live-verified behaviors (all tested 2026-08-22):

- **HD** — requested address is *ignored*; the server returns a random `user@<one-of-9-domains>`. All 9 domains generated successfully.
- **HD_GMAIL** — requested address *ignored*; always returns a real `@gmail.com` alias. Works with `email: null` (random). Requests for outlook/protonmail/icloud (premium tier in-app) also return gmail aliases over the public API.
- **temp-mail.io** — full custom control: `{name, domain}` honored exactly (`meratest99@ozsaip.com` ✅).
- **temp-mail.org** — fully random mailbox + JWT.

---

## 3. Custom transport encryption (fully broken)

Both 1timetech servers require header `x-app-key: b9db03078622` and encrypt request **bodies and query-string params**:

```
encrypt(x):
  1. x = JSON.stringify(x)
  2. b64 = Base64(x)                 # js-base64
  3. rev = reverse(b64)              # string reversed
  4. for each pair p in "ao-sq-=x-5b-4*-Bz".split("-"):
       swap every p[0] ↔ p[1] in rev
  → send as text/plain body (or append raw to URL as ?<enc> for GETs)
```

Why it's trivially reversible: character substitution is position-independent, so *reverse* and *swap* commute — **the same operation is its own inverse**. `decrypt = swap∘reverse` then Base64-decode. (The app's `replaceChars(text, flag)` "direction" flag doesn't change the result — a↔b swap is symmetric.)

Response bodies come back as `{data: "<encrypted>", ...}` and decrypt with the same scheme.

> Gotcha: the body must be sent with `Content-Type: text/plain` (or no CT). Sending it unquoted with `application/json` makes Express's JSON body-parser return `400 Bad Request`.

Functions in the bytecode: `encodeStr` (#17981), `decodeStr` (#17980), `replaceChars` (#17983) inside modules #16015 (HD) and #17978 (HD_GMAIL).

---

## 4. The real-Gmail trick 💌

Live generations from `POST /g-mail`:

```
gmail.com       → lyy.e.nh.o.ng.5.8579@gmail.com
googlemail.com  → t.abicht.h.ao.6336.6@gmail.com
outlook.com     → rss.ll.m.c.l@gmail.com        (premium tier)
protonmail.com  → d.a.n.g.d.uc.cao4.9771@gmail.com
icloud.com      → p.h.an.don.g.n.h.i.1.95.85@gmail.com
(email: null)   → kilia.n.ok.o.ndur.u@gmail.com
```

**Mechanism — Gmail dot-aliasing:**
1. The operator owns a pool of **real Gmail accounts** (usernames look like Vietnamese names: `lyyenhong58579`, `truonghienmai2385`, `dangquangchien9771`…).
2. Gmail ignores dots in the local part: `j.o.h.n@gmail.com` ≡ `john@gmail.com`.
3. For every user the server inserts random dots into a pool account's username → an endless stream of "unique" addresses that all deliver to the same real inbox.
4. The backend reads that inbox (IMAP) and serves messages over the API.
5. `+gmail.com` entries in `hdGmailDomainsStr` show plus-alias mode (`base+tag@gmail.com`) is also supported.

This is why "Gmail unblocked" marketing works — sites that block disposable domains still accept `@gmail.com`. It is, however, against Google's ToS; expect periodic account loss (hence a rotating pool).

---

## 5. How OTP delivery actually works

The app contains **no OTP parser at all** (no digit-regex over message bodies, no `otpauth://` handling — only a WebView autocomplete map `'one-time-code' → 'sms-otp'`). The real flow:

```
user signs up somewhere with the temp address
        → site sends verification email
        → lands in real backend inbox (Gmail pool / temp server)
        → FCM push wakes the app ("You have a new message" toast)
        → app polls GET /email/{id}/messages (encrypted query)
        → user opens message → {subject, from, bodyHtml, bodyPreview, attachments, createdAt, receivedAt, _id}
        → user reads/copies the code manually
```

Mailbox cloud-sync across devices via Firebase Auth (`getCloudEmails(uid)`).

Our CLI (`instantmail.py`) adds what the app lacks: **automatic OTP extraction** with a keyword-scoring parser, so the code is surfaced the moment the email arrives.

---

## 6. Message schema (HD / HD_GMAIL)

`GET /email/{id}/messages` returns per message (after decryption):

```json
{
  "_id": "...", "subject": "...", "from": "...", "mailbox": "...",
  "bodyPreview": "plain text", "bodyHtml": "<html>...",
  "attachments": [...], "attachmentsCount": 0,
  "createdAt": 1690000000000, "receivedAt": ...
}
```

---

## 7. Tooling & reproduction

```
apktool d Instant_Mail_8.0.0.apk                     # resources + smali
pip install hermes-dec                                # Hermes disassembler
hbc-disassembler assets/index.android.bundle out.hasm # 52 MB of disassembly
```

Search strategy: dump the Hermes string table → locate remote-config object (`NewObjectWithBufferLong` in module #16540) → follow `hdServiceURL`/`hdGmailServiceKey` references to the two axios client modules → read interceptors for the crypto → replay with curl/Python.

Verified live on 2026-08-22: all 4 services generating, inboxes readable, Gmail aliases confirmed.

---

*⚠️ Educational research only. Don't abuse OTP/verification systems or violate any service's terms.*
