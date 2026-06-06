# OSINT Tool — Made by Og-py3

> **Ultimate open-source intelligence tool** — async, concurrent, and faster than most Go implementations.

```
 ██████╗ ███████╗██╗███╗   ██╗████████╗
██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██║   ██║███████╗██║██╔██╗ ██║   ██║   
██║   ██║╚════██║██║██║╚██╗██║   ██║   
╚██████╔╝███████║██║██║ ╚████║   ██║   
 ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  
```

## Features

| Module | Capabilities |
|---|---|
| 📧 **Email OSINT** | HaveIBeenPwned breach check, Gravatar profile, GitHub lookup, WHOIS, DNS (A/MX/NS/TXT/AAAA/CNAME), IP geolocation + ASN, 100+ platform scan |
| 📱 **Phone OSINT** | E.164/international format, carrier detection, line type (mobile/VoIP/landline/toll-free), country + timezone + local time, multi-host latency testing |
| 🌍 **IP OSINT** | Full geolocation, ISP, ASN, continent/city/ZIP, proxy/VPN detection, hosting flag, live ping latency |
| 🌐 **Domain OSINT** | WHOIS registration details, full DNS records, IP resolution → auto IP geolocation |
| 🔎 **Username** | 100+ platforms: GitHub, Instagram, TikTok, LinkedIn, Twitch, Reddit, Steam, Spotify, Discord, Telegram, PayPal, Roblox, Chess.com, and many more |
| 🚀 **All-in-One** | Auto-detects input type (email/phone/IP/domain/username) and runs every relevant check — including **Email → Phone extraction** |

## Email → Phone Hunt

When given an email, the All-in-One scanner attempts to extract linked phone numbers from:
- WHOIS registration records
- GitHub profile + linked personal website
- Domain pages (`/`, `/contact`, `/about`, `/team`)
- LinkedIn, Twitter, About.me, Keybase profiles

Valid numbers are parsed with `phonenumbers` (carrier + location + E.164) and automatically trigger a full Phone OSINT deep-dive.

## Speed

- Fully async with `aiohttp` — 50–80 concurrent HTTP requests
- `ThreadPoolExecutor` for blocking calls (DNS, WHOIS, socket)
- Semaphore-gated concurrency for zero rate-limit crashes
- 100 platform scan completes in ~5–8 seconds depending on network

## Install

```bash
pip install aiohttp phonenumbers rich dnspython python-whois
```

## Run

```bash
python3 osint_tool.py
```

## Menu

```
[1] Email OSINT
[2] Phone OSINT
[3] IP OSINT
[4] Domain OSINT
[5] Username check (100+ platforms)
[6] ALL-IN-ONE — auto-detect & run everything + Email→Phone hunt
[7] Exit
```

## Disclaimer

This tool is intended for **legal, ethical OSINT** purposes only — security research, penetration testing with permission, or finding your own exposed data. Never use it against individuals without consent. The author is not responsible for misuse.

---

**Made by Og-py3** | Python 3.9+ | Async Engine | Zero dependencies on paid APIs
