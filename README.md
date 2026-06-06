# 🕵️ OSINT Tool — by Og-py3

![Build & Release](https://github.com/og-py3/osint-tool/actions/workflows/build-release.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-informational)
![License](https://img.shields.io/badge/License-MIT-green)
![Async](https://img.shields.io/badge/Engine-Async%20%2B%20Concurrent-orange)
![No API Keys](https://img.shields.io/badge/API%20Keys-None%20Required-brightgreen)
![Platforms](https://img.shields.io/badge/Platforms%20Checked-30%2B-purple)

> **Fast, accurate, async OSINT intelligence tool — zero API keys required.**  
> Built by [Og-py3](https://github.com/og-py3) for open-source intelligence gathering.

---

## ⬇️ Download

👉 **[Latest Windows .exe Release](https://github.com/og-py3/osint-tool/releases/latest)**

No Python install needed. Just download and run.

---

## 🚀 Features

| Module | What it does |
|--------|-------------|
| 📧 **Email OSINT** | Reputation check (EmailRep.io), Gravatar lookup, GitHub profile, MX/DNS validation, Spotify registration check, WHOIS, domain IP geo |
| 📱 **Phone OSINT** | Carrier detection, country/region, line type (mobile/VoIP/landline), timezone, local time display — all via phonenumbers library (no API key) |
| 🌍 **IP OSINT** | Full geolocation, ISP, ASN, proxy/VPN/hosting detection, latency test — via ip-api.com (free) |
| 🌐 **Domain OSINT** | WHOIS, full DNS (A/AAAA/MX/NS/TXT/CNAME), IP resolution, auto geolocation, phone scraping from domain pages |
| 🔎 **Username OSINT** | 30+ verified platforms: GitHub, Reddit, GitLab, HackerNews, Chess.com, Lichess, Dev.to, Mastodon, NPM, Keybase, PyPI, HuggingFace, Last.fm, Vimeo, Medium, Steam, Tumblr, Substack + more |
| 🚀 **All-in-One** | Auto-detects input type, runs all relevant checks, Email→Phone hunting |

---

## 🎯 Accuracy — How Platform Detection Works

| Tier | Method | Examples |
|------|--------|---------|
| **Tier 1** | JSON API — real HTTP 404 on miss | GitHub API, Reddit, HackerNews (null body), Chess.com, Lichess, Dev.to, Mastodon, NPM, Keybase |
| **Tier 2** | HTML — server returns real 404 | GitLab, PyPI, HuggingFace, CodePen, Last.fm, Vimeo, Medium, Letterboxd, MyAnimeList, AO3, Wattpad |
| **Tier 3** | Body pattern detection | Steam ("profile not found"), Tumblr, Substack, Gravatar |

> **Excluded intentionally:** Instagram, Twitter/X, TikTok, LinkedIn, YouTube — these return HTTP 200 for ALL usernames and render "not found" in JavaScript only, causing 100% false positives.

---

## 🛠️ Run from Source

```bash
pip install aiohttp phonenumbers dnspython python-whois rich
python osint_tool.py
```

---

## 📸 Modes

```
[1] 📧  Email OSINT
[2] 📱  Phone OSINT
[3] 🌍  IP OSINT
[4] 🌐  Domain OSINT
[5] 🔎  Username Check
[6] 🚀  All-in-One (auto-detect + Email→Phone hunt)
[7] 🚪  Exit
```

---

## ⚡ Built With

- `aiohttp` — async HTTP, concurrent requests
- `phonenumbers` — Google's libphonenumber (carrier, geo, type)
- `dnspython` — DNS resolution
- `python-whois` — WHOIS lookups
- `rich` — terminal UI

**No API keys. No paid tiers. No bullshit.**

---

*Made with ❤️ by [Og-py3](https://github.com/og-py3)*
