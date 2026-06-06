#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║          ULTIMATE OSINT TOOL — Made by Og-py3               ║
║          Async | Concurrent | Fast | Comprehensive          ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import aiohttp
import socket
import time
import re
import os
import sys
import json
import ipaddress
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

import phonenumbers
from phonenumbers import geocoder, carrier, timezone as tz_info
import dns.resolver
import whois

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box
from rich.live import Live
from rich.layout import Layout

# ─────────────────────────── SETUP ───────────────────────────
console = Console()
executor = ThreadPoolExecutor(max_workers=64)

# ──────────────────────── BANNER ─────────────────────────────

BANNER = """
[bold red]
 ██████╗ ███████╗██╗███╗   ██╗████████╗
██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
██║   ██║███████╗██║██╔██╗ ██║   ██║   
██║   ██║╚════██║██║██║╚██╗██║   ██║   
╚██████╔╝███████║██║██║ ╚████║   ██║   
 ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  
[/bold red][bold yellow]
  ██████╗ ██╗   ██╗    ██████╗ ██╗   ██╗██████╗
  ██╔══██╗╚██╗ ██╔╝    ██╔══██╗╚██╗ ██╔╝╚════██╗
  ██████╔╝ ╚████╔╝     ██████╔╝ ╚████╔╝   ███╔╝
  ██╔══██╗  ╚██╔╝      ██╔═══╝   ╚██╔╝   ██╔══╝
  ██████╔╝   ██║       ██║        ██║    ███████╗
  ╚═════╝    ╚═╝       ╚═╝        ╚═╝    ╚══════╝
[/bold yellow]"""

CREDITS = "[bold cyan]Made by [bold white]Og-py3[/bold white] | Ultimate OSINT Intelligence Tool[/bold cyan]"
VERSION = "[dim]v4.0 | Async Engine | Accurate Platform Detection | Smart Body Validation[/dim]"

# ────────────────── PLATFORM CHECKS ──────────────────────────
# Format: (name, url_template, not_found_body_patterns)
# Rules:
#   - HTTP 404 always means NOT found, regardless of platform
#   - HTTP 200 + not_found_body_patterns empty  → FOUND
#   - HTTP 200 + body contains any pattern      → NOT found
#   - HackerNews special: body == "null"        → NOT found
# Only platforms with RELIABLE, verifiable detection are listed.
# Platforms that return 200 for any username (Instagram, Twitter, TikTok,
# LinkedIn, etc.) are excluded — they produce false positives.

# ── PLATFORM_CHECKS format: (name, url_template, not_found_body_patterns)
# ONLY platforms where detection is verifiable and accurate:
#   Tier 1 — JSON APIs: return real HTTP 404 when user missing (most accurate)
#   Tier 2 — HTML pages: server returns real HTTP 404 when user missing
#   Tier 3 — Body patterns: server returns 200 but body contains "not found" text
# Platforms excluded: JS-rendered SPAs that return 200 for all URLs (false positives)
PLATFORM_CHECKS = [
    # ── Tier 1: JSON APIs — real 404 / special null response ──────────────────
    # name uses special handler in check_one()
    ("GitHub",          "https://api.github.com/users/{u}",                              []),
    ("Reddit",          "https://www.reddit.com/user/{u}/about.json",                    []),
    ("HackerNews",      "https://hacker-news.firebaseio.com/v0/user/{u}.json",           []),  # null body = not found
    ("Chess.com",       "https://api.chess.com/pub/player/{u}",                          []),
    ("Lichess",         "https://lichess.org/api/user/{u}",                              []),
    ("Dev.to",          "https://dev.to/api/users/by_username?url={u}",                  []),
    ("Mastodon",        "https://mastodon.social/api/v1/accounts/lookup?acct={u}",       []),  # 404/422 = not found
    ("NPM",             "https://registry.npmjs.org/-/user/org.couchdb.user:{u}",        []),
    ("Keybase",         "https://keybase.io/_/api/1.0/user/lookup.json?usernames={u}",   []),  # "them":[] = not found
    # ── Tier 2: HTML pages — reliable HTTP 404 when user missing ──────────────
    ("GitLab",          "https://gitlab.com/{u}",                                        []),
    ("PyPI",            "https://pypi.org/user/{u}/",                                    []),
    ("HuggingFace",     "https://huggingface.co/{u}",                                    []),
    ("Lobsters",        "https://lobste.rs/u/{u}",                                       []),
    ("CodePen",         "https://codepen.io/{u}",                                        []),
    ("Letterboxd",      "https://letterboxd.com/{u}",                                    []),
    ("MyAnimeList",     "https://myanimelist.net/profile/{u}",                           []),
    ("AO3",             "https://archiveofourown.org/users/{u}",                         []),
    ("Wattpad",         "https://www.wattpad.com/user/{u}",                              []),
    ("Last.fm",         "https://www.last.fm/user/{u}",                                  []),
    ("Vimeo",           "https://vimeo.com/{u}",                                         []),
    ("Imgur",           "https://imgur.com/user/{u}",                                    []),
    ("About.me",        "https://about.me/{u}",                                          []),
    ("Medium",          "https://medium.com/@{u}",                                       []),
    ("Flickr",          "https://www.flickr.com/people/{u}",                             []),
    ("AniList",         "https://anilist.co/user/{u}/",                                  []),
    ("Minecraft",       "https://namemc.com/profile/{u}",                                []),
    # ── Tier 3: Body pattern detection ────────────────────────────────────────
    ("Steam",           "https://steamcommunity.com/id/{u}",                             ["the specified profile could not be found"]),
    ("Tumblr",          "https://{u}.tumblr.com",                                        ["there's nothing here.", "404 | not found"]),
    ("Substack",        "https://{u}.substack.com",                                      ["this publication doesn't exist", "page not found"]),
    ("Gravatar",        "https://en.gravatar.com/{u}",                                   ["gravatar profile not found", "no profile found"]),
]

PHONE_CARRIERS = {
    "US": ["api.bandwidth.com", "api.twilio.com", "api.vonage.com"],
    "UK": ["api.vonage.com", "api.twilio.com"],
    "IN": ["api.exotel.com", "api.msg91.com"],
    "Generic": ["api.twilio.com", "api.vonage.com", "api.sinch.com"],
}

# ──────────────────────── UTILITIES ──────────────────────────

def md5_hash(text: str) -> str:
    import hashlib
    return hashlib.md5(text.lower().strip().encode()).hexdigest()

def extract_username(email: str) -> str:
    return email.split("@")[0] if "@" in email else email

def is_valid_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))

def is_valid_phone(phone: str) -> bool:
    try:
        p = phonenumbers.parse(phone, None)
        return phonenumbers.is_valid_number(p)
    except:
        return False

def clean_phone(phone: str) -> str:
    cleaned = re.sub(r'[^\d+]', '', phone)
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    return cleaned

async def measure_latency(host: str, port: int = 443, attempts: int = 3) -> dict:
    latencies = []
    for _ in range(attempts):
        try:
            loop = asyncio.get_event_loop()
            start = time.perf_counter()
            await loop.run_in_executor(executor, socket.getaddrinfo, host, port)
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(round(elapsed, 2))
        except:
            pass
    if latencies:
        return {
            "min": min(latencies),
            "max": max(latencies),
            "avg": round(sum(latencies) / len(latencies), 2),
            "jitter": round(max(latencies) - min(latencies), 2)
        }
    return {"min": None, "max": None, "avg": None, "jitter": None}

async def check_email_reputation(email: str, session: aiohttp.ClientSession) -> dict:
    """EmailRep.io — free, no API key. Returns reputation, breach flags, known profiles."""
    try:
        async with session.get(
            f"https://emailrep.io/{email}",
            headers={"User-Agent": "osint-tool-og-py3", "Accept": "application/json"},
            timeout=aiohttp.ClientTimeout(total=8)
        ) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return {}

async def check_spotify_email(email: str, session: aiohttp.ClientSession) -> dict:
    """Spotify signup endpoint: status 20 = email already registered, 1 = free."""
    try:
        async with session.get(
            f"https://spclient.wg.spotify.com/signup/public/v1/account?validate=1&email={email}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=aiohttp.ClientTimeout(total=6)
        ) as resp:
            if resp.status == 200:
                d = await resp.json()
                return {"registered": d.get("status") == 20, "raw_status": d.get("status")}
    except:
        pass
    return {"registered": None}

async def check_mx_deliverable(domain: str) -> dict:
    """Check if domain has valid MX records — confirms email domain is real."""
    try:
        loop = asyncio.get_event_loop()
        answers = await loop.run_in_executor(executor, lambda: dns.resolver.resolve(domain, "MX", lifetime=4))
        mx = sorted([(r.preference, str(r.exchange).rstrip(".")) for r in answers])
        return {"valid": True, "mx_records": mx, "primary_mx": mx[0][1] if mx else None}
    except:
        return {"valid": False, "mx_records": [], "primary_mx": None}

async def get_ip_info(ip: str) -> dict:
    urls = [
        f"http://ip-api.com/json/{ip}?fields=status,message,continent,continentCode,country,countryCode,region,regionName,city,district,zip,lat,lon,timezone,offset,currency,isp,org,as,asname,mobile,proxy,hosting,query",
        f"https://ipwho.is/{ip}",
    ]
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status") == "success" or data.get("success") is True:
                            return data
            except:
                continue
    return {}

async def get_domain_info(domain: str) -> dict:
    results = {}
    try:
        loop = asyncio.get_event_loop()
        w = await loop.run_in_executor(executor, whois.whois, domain)
        results["whois"] = {
            "registrar": w.registrar,
            "creation_date": str(w.creation_date),
            "expiration_date": str(w.expiration_date),
            "name_servers": w.name_servers,
            "status": w.status,
            "emails": w.emails,
            "org": w.org,
            "country": w.country,
        }
    except:
        results["whois"] = {}

    for record_type in ["A", "MX", "TXT", "NS", "AAAA", "CNAME"]:
        try:
            answers = dns.resolver.resolve(domain, record_type, lifetime=5)
            results[f"dns_{record_type}"] = [str(r) for r in answers]
        except:
            results[f"dns_{record_type}"] = []

    return results

async def check_email_breach(email: str, session: aiohttp.ClientSession) -> dict:
    """Wrapper that calls check_email_reputation — no API key needed."""
    return await check_email_reputation(email, session)

async def get_gravatar_info(email: str, session: aiohttp.ClientSession) -> dict:
    hash_val = md5_hash(email)
    result = {"hash": hash_val, "found": False, "url": None, "profile": None}
    try:
        avatar_url = f"https://www.gravatar.com/avatar/{hash_val}?d=404"
        async with session.get(avatar_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            if resp.status == 200:
                result["found"] = True
                result["url"] = f"https://www.gravatar.com/{hash_val}"
                result["avatar"] = avatar_url
    except:
        pass
    return result

async def get_github_info(username: str, session: aiohttp.ClientSession) -> dict:
    try:
        async with session.get(
            f"https://api.github.com/users/{username}",
            timeout=aiohttp.ClientTimeout(total=6)
        ) as resp:
            if resp.status == 200:
                d = await resp.json()
                return {
                    "found": True,
                    "name": d.get("name"),
                    "bio": d.get("bio"),
                    "location": d.get("location"),
                    "email": d.get("email"),
                    "public_repos": d.get("public_repos"),
                    "followers": d.get("followers"),
                    "following": d.get("following"),
                    "created_at": d.get("created_at"),
                    "blog": d.get("blog"),
                    "company": d.get("company"),
                    "twitter": d.get("twitter_username"),
                    "avatar": d.get("avatar_url"),
                    "url": d.get("html_url"),
                }
    except:
        pass
    return {"found": False}

async def run_username_checks(username: str) -> list:
    """
    Smart per-platform username checker — no API keys.

    Detection rules (in priority order):
      1. HTTP 404 / 410 / 422  → NOT found (hard server-side miss)
      2. HackerNews            → body is literally 'null' → NOT found
      3. Keybase API           → JSON contains '"them":[]' → NOT found
      4. Mastodon API          → 404 or 422 → NOT found
      5. Body patterns present → any pattern found in body → NOT found
      6. HTTP 200 + no patterns → FOUND
    Only PLATFORM_CHECKS entries with verified detection are included.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/json,*/*;q=0.8",
    }
    connector = aiohttp.TCPConnector(limit=60, ssl=False, ttl_dns_cache=300)
    semaphore = asyncio.Semaphore(40)

    async def check_one(name: str, url_tpl: str, not_found_patterns: list):
        async with semaphore:
            url = url_tpl.format(u=username)
            try:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=12, connect=5),
                    allow_redirects=True,
                ) as resp:
                    status = resp.status

                    # ── Hard misses (server confirms absence) ────────────────
                    if status in (404, 410):
                        return {"service": name, "url": url, "found": False, "status": status}

                    # Mastodon returns 422 for invalid/missing usernames
                    if name == "Mastodon" and status == 422:
                        return {"service": name, "url": url, "found": False, "status": status}

                    # Any other non-success, non-redirect → inconclusive
                    if status not in (200, 301, 302, 206):
                        return {"service": name, "url": url, "found": None, "status": status}

                    # ── Platform-specific body checks ────────────────────────
                    # HackerNews Firebase: body is literal JSON value "null" when missing
                    if name == "HackerNews":
                        body = (await resp.text(errors="ignore")).strip()
                        return {"service": name, "url": url,
                                "found": body != "null", "status": status}

                    # Keybase public API: {"them":[]} when user doesn't exist
                    if name == "Keybase":
                        raw = (await resp.text(errors="ignore"))
                        compact = raw.replace(" ", "").replace("\n", "")
                        return {"service": name, "url": url,
                                "found": '"them":[]' not in compact, "status": status}

                    # ── General body-pattern matching ────────────────────────
                    if not_found_patterns:
                        body = (await resp.text(errors="ignore"))[:8000].lower()
                        for pat in not_found_patterns:
                            if pat in body:
                                return {"service": name, "url": url,
                                        "found": False, "status": status}

                    # ── 200 + no disqualifying pattern → FOUND ───────────────
                    return {"service": name, "url": url, "found": True, "status": status}

            except asyncio.TimeoutError:
                return {"service": name, "url": url, "found": None, "status": "timeout"}
            except Exception:
                return {"service": name, "url": url, "found": None, "status": "error"}

    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        coros = [check_one(n, u, p) for n, u, p in PLATFORM_CHECKS]
        return list(await asyncio.gather(*coros))

# ────────────────── PHONE OSINT ──────────────────────────────

def parse_phone_number(phone_input: str) -> dict:
    results = {}
    try:
        cleaned = clean_phone(phone_input)
        parsed = phonenumbers.parse(cleaned, None)
        
        if not phonenumbers.is_valid_number(parsed):
            # Try with country code guess
            for country in ["US", "GB", "IN", "AU", "CA"]:
                try:
                    parsed = phonenumbers.parse(phone_input, country)
                    if phonenumbers.is_valid_number(parsed):
                        break
                except:
                    continue

        country_code = parsed.country_code
        national_number = parsed.national_number
        country = geocoder.description_for_number(parsed, "en")
        carrier_name = carrier.name_for_number(parsed, "en")
        timezones = tz_info.time_zones_for_number(parsed)
        
        results = {
            "raw_input": phone_input,
            "e164": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164),
            "international": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "national": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            "rfc3966": phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.RFC3966),
            "country_code": f"+{country_code}",
            "national_number": str(national_number),
            "country": country,
            "carrier": carrier_name or "Unknown",
            "timezones": list(timezones),
            "is_valid": phonenumbers.is_valid_number(parsed),
            "is_possible": phonenumbers.is_possible_number(parsed),
            "number_type": str(phonenumbers.number_type(parsed)).replace("PhoneNumberType.", ""),
            "line_type": get_line_type(phonenumbers.number_type(parsed)),
            "country_iso": phonenumbers.region_code_for_number(parsed),
        }
    except Exception as e:
        results["error"] = str(e)
    return results

def get_line_type(num_type) -> str:
    from phonenumbers import PhoneNumberType
    mapping = {
        PhoneNumberType.MOBILE: "Mobile",
        PhoneNumberType.FIXED_LINE: "Fixed Line",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fixed/Mobile",
        PhoneNumberType.TOLL_FREE: "Toll Free",
        PhoneNumberType.PREMIUM_RATE: "Premium Rate",
        PhoneNumberType.SHARED_COST: "Shared Cost",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.PERSONAL_NUMBER: "Personal",
        PhoneNumberType.PAGER: "Pager",
        PhoneNumberType.UAN: "Universal Access",
        PhoneNumberType.VOICEMAIL: "Voicemail",
        PhoneNumberType.UNKNOWN: "Unknown",
    }
    return mapping.get(num_type, "Unknown")

async def test_phone_carrier_latency(phone_info: dict) -> dict:
    country_iso = phone_info.get("country_iso", "US")
    carrier_hosts = PHONE_CARRIERS.get(country_iso, PHONE_CARRIERS["Generic"])
    latency_results = {}
    tasks = [measure_latency(host, 443, 3) for host in carrier_hosts]
    results = await asyncio.gather(*tasks)
    for host, result in zip(carrier_hosts, results):
        latency_results[host] = result
    return latency_results

async def numverify_lookup(phone_e164: str, session: aiohttp.ClientSession) -> dict:
    try:
        clean = phone_e164.replace("+", "")
        url = f"https://api.verifyphone.io/phone/{clean}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
            if resp.status == 200:
                return await resp.json()
    except:
        pass
    return {}

async def lookup_phone_online(phone_e164: str, session: aiohttp.ClientSession) -> dict:
    info = {}
    try:
        clean = phone_e164.replace("+", "")
        url = f"https://phoneinfoga.crvx.fr/api/v2/numbers/{clean}/googlesearch"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            if resp.status == 200:
                info["google_search"] = await resp.json()
    except:
        pass
    return info

# ────────────────── IP OSINT ──────────────────────────────────

async def run_ip_osint(ip: str) -> dict:
    results = {}
    async with aiohttp.ClientSession() as session:
        geo = await get_ip_info(ip)
        results["geo"] = geo
        latency = await measure_latency(ip, 80, 3)
        results["latency"] = latency
    return results

async def resolve_host_to_ip(host: str) -> list:
    ips = []
    try:
        infos = await asyncio.get_event_loop().run_in_executor(
            executor, socket.getaddrinfo, host, None
        )
        ips = list(set(info[4][0] for info in infos))
    except:
        pass
    return ips

# ────────────────── EMAIL OSINT (MAIN) ───────────────────────

async def run_email_osint(email: str):
    console.print()
    console.print(Rule(f"[bold cyan]🔍 EMAIL OSINT: {email}[/bold cyan]", style="cyan"))
    console.print()

    username = extract_username(email)
    domain = email.split("@")[1] if "@" in email else ""

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; OSINT-Tool/3.0; +Og-py3)",
        "Accept": "application/json, text/html, */*",
    }
    connector = aiohttp.TCPConnector(limit=100, ssl=False)

    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        with Progress(
            SpinnerColumn(spinner_name="dots12", style="bold cyan"),
            TextColumn("[bold white]{task.description}"),
            BarColumn(style="cyan", complete_style="green"),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            main_task = progress.add_task("Running parallel OSINT checks...", total=7)

            emailrep_task   = asyncio.create_task(check_email_reputation(email, session))
            spotify_task    = asyncio.create_task(check_spotify_email(email, session))
            gravatar_task   = asyncio.create_task(get_gravatar_info(email, session))
            github_task     = asyncio.create_task(get_github_info(username, session))
            domain_task     = asyncio.create_task(get_domain_info(domain))
            ip_resolve_task = asyncio.create_task(resolve_host_to_ip(domain))
            username_task   = asyncio.create_task(run_username_checks(username))

            emailrep, spotify, gravatar, github, domain_info, domain_ips, username_results = await asyncio.gather(
                emailrep_task, spotify_task, gravatar_task, github_task,
                domain_task, ip_resolve_task, username_task
            )
            progress.update(main_task, completed=7)

    # ── Extract EmailRep fields ──
    er_details   = emailrep.get("details", {})
    er_leaked    = er_details.get("credentials_leaked", False)
    er_breached  = er_details.get("data_breach", False)
    er_susp      = emailrep.get("suspicious", False)
    er_rep       = emailrep.get("reputation", "unknown")
    er_disp      = er_details.get("disposable", False)
    er_deliv     = er_details.get("deliverable", None)
    er_free      = er_details.get("free_provider", None)
    er_spam      = er_details.get("spam", False)
    er_profiles  = er_details.get("profiles", [])
    er_first     = er_details.get("first_seen", "")
    er_last      = er_details.get("last_seen", "")

    # ── Summary Panel ──
    summary_table = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 1))
    summary_table.add_column("Field", style="bold cyan", no_wrap=True)
    summary_table.add_column("Value", style="white")

    if er_leaked or er_breached:
        breach_summary = "[bold red]⚠ Credentials / Breach Detected[/bold red]"
    elif emailrep:
        breach_summary = "[bold green]✓ No Known Breaches[/bold green]"
    else:
        breach_summary = "[dim]Check unavailable (rate limited)[/dim]"

    summary_table.add_row("📧 Email",       email)
    summary_table.add_row("👤 Username",    username)
    summary_table.add_row("🌐 Domain",      domain)
    summary_table.add_row("🛡 Reputation",  er_rep.title() if er_rep else "[dim]Unknown[/dim]")
    summary_table.add_row("🔓 Breach",      breach_summary)
    summary_table.add_row("🎵 Spotify",     "[bold green]Registered[/bold green]" if spotify.get("registered") else ("[dim]Not registered[/dim]" if spotify.get("registered") is False else "[dim]Check failed[/dim]"))
    summary_table.add_row("🖼 Gravatar",    "[bold green]YES[/bold green]" if gravatar.get("found") else "[dim]Not found[/dim]")
    summary_table.add_row("🐙 GitHub",      f"[bold green]Found: {github.get('name') or username}[/bold green]" if github.get("found") else "[dim]Not found[/dim]")
    summary_table.add_row("🌍 Domain IPs",  ", ".join(domain_ips) if domain_ips else "[dim]None resolved[/dim]")

    console.print(Panel(summary_table, title="[bold white]📊 EMAIL SUMMARY[/bold white]", border_style="cyan"))

    # ── EmailRep Reputation Panel ──
    if emailrep:
        rep_table = Table(box=box.ROUNDED, show_header=False, border_style="red" if (er_leaked or er_breached or er_susp) else "green", padding=(0, 1))
        rep_table.add_column("Field", style="bold white", no_wrap=True)
        rep_table.add_column("Value", style="white")

        def yn(val, warn=True):
            if val is True:
                return "[bold red]YES[/bold red]" if warn else "[bold green]YES[/bold green]"
            if val is False:
                return "[bold green]No[/bold green]" if warn else "[dim]No[/dim]"
            return "[dim]Unknown[/dim]"

        rep_table.add_row("Reputation",          f"[bold {'red' if er_rep in ('none','low') else 'green'}]{er_rep.title()}[/bold {'red' if er_rep in ('none','low') else 'green'}]" if er_rep else "[dim]Unknown[/dim]")
        rep_table.add_row("Suspicious",          yn(er_susp))
        rep_table.add_row("Credentials Leaked",  yn(er_leaked))
        rep_table.add_row("Data Breach",         yn(er_breached))
        rep_table.add_row("Disposable Address",  yn(er_disp))
        rep_table.add_row("Deliverable",         yn(er_deliv, warn=False))
        rep_table.add_row("Free Provider",       yn(er_free,  warn=False))
        rep_table.add_row("Spam",                yn(er_spam))
        if er_first: rep_table.add_row("First Seen", er_first)
        if er_last:  rep_table.add_row("Last Seen",  er_last)
        if er_profiles:
            rep_table.add_row("Known Profiles",  ", ".join(er_profiles))

        title_color = "red" if (er_leaked or er_breached or er_susp) else "green"
        console.print(Panel(rep_table, title=f"[bold {title_color}]🛡 EMAIL REPUTATION (EmailRep.io)[/bold {title_color}]", border_style=title_color))

    # ── Gravatar ──
    if gravatar.get("found"):
        g_table = Table(box=box.ROUNDED, show_header=False, border_style="blue", padding=(0, 1))
        g_table.add_column("Key", style="bold blue", no_wrap=True)
        g_table.add_column("Value", style="white")
        g_table.add_row("MD5 Hash", gravatar["hash"])
        g_table.add_row("Profile URL", gravatar.get("url", ""))
        g_table.add_row("Avatar", gravatar.get("avatar", ""))
        console.print(Panel(g_table, title="[bold blue]🖼 GRAVATAR PROFILE[/bold blue]", border_style="blue"))

    # ── GitHub Info ──
    if github.get("found"):
        gh_table = Table(box=box.ROUNDED, show_header=False, border_style="white", padding=(0, 1))
        gh_table.add_column("Key", style="bold white", no_wrap=True)
        gh_table.add_column("Value", style="cyan")
        for k, v in github.items():
            if k != "found" and v:
                gh_table.add_row(k.replace("_", " ").title(), str(v))
        console.print(Panel(gh_table, title="[bold white]🐙 GITHUB PROFILE[/bold white]", border_style="white"))

    # ── Domain Info ──
    if domain_info.get("whois"):
        w = domain_info["whois"]
        w_table = Table(box=box.ROUNDED, show_header=False, border_style="yellow", padding=(0, 1))
        w_table.add_column("Key", style="bold yellow", no_wrap=True)
        w_table.add_column("Value", style="white")
        for k, v in w.items():
            if v and v != "None":
                val = str(v) if not isinstance(v, list) else ", ".join(str(x) for x in v[:5])
                w_table.add_row(k.replace("_", " ").title(), val[:80])
        console.print(Panel(w_table, title=f"[bold yellow]🌐 WHOIS: {domain}[/bold yellow]", border_style="yellow"))

    # ── DNS Records ──
    dns_table = Table(title=f"[bold magenta]DNS Records: {domain}[/bold magenta]", box=box.ROUNDED, border_style="magenta")
    dns_table.add_column("Type", style="bold magenta", width=8)
    dns_table.add_column("Records", style="white")
    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
        records = domain_info.get(f"dns_{rtype}", [])
        if records:
            dns_table.add_row(rtype, "\n".join(records[:5]))
    console.print(dns_table)

    # ── IP Geolocation ──
    if domain_ips:
        for ip in domain_ips[:2]:
            ip_data = await run_ip_osint(ip)
            geo = ip_data.get("geo", {})
            if geo:
                ip_table = Table(box=box.ROUNDED, show_header=False, border_style="green", padding=(0, 1))
                ip_table.add_column("Field", style="bold green", no_wrap=True)
                ip_table.add_column("Value", style="white")
                fields = [
                    ("IP", geo.get("query") or ip),
                    ("Country", f"{geo.get('country', '')} ({geo.get('countryCode', '')})"),
                    ("Region", geo.get("regionName", "")),
                    ("City", geo.get("city", "")),
                    ("ZIP", geo.get("zip", "")),
                    ("Latitude", str(geo.get("lat", ""))),
                    ("Longitude", str(geo.get("lon", ""))),
                    ("Timezone", geo.get("timezone", "")),
                    ("ISP", geo.get("isp", "")),
                    ("Org", geo.get("org", "")),
                    ("ASN", geo.get("as", "")),
                    ("Mobile", "Yes" if geo.get("mobile") else "No"),
                    ("Proxy", "[bold red]YES[/bold red]" if geo.get("proxy") else "No"),
                    ("Hosting", "Yes" if geo.get("hosting") else "No"),
                ]
                for field, value in fields:
                    if value and value != "":
                        ip_table.add_row(field, str(value))
                lat_info = ip_data.get("latency", {})
                if lat_info.get("avg"):
                    ip_table.add_row("Avg Latency", f"{lat_info['avg']} ms")
                console.print(Panel(ip_table, title=f"[bold green]🌍 IP GEOLOCATION: {ip}[/bold green]", border_style="green"))

    # ── Username Service Checks ──
    found_services = [r for r in username_results if r.get("found") is True]
    not_found = [r for r in username_results if r.get("found") is False]
    timeout_count = len([r for r in username_results if r.get("found") is None])

    svc_table = Table(
        title=f"[bold cyan]🔎 USERNAME '{username}' — Service Presence ({len(found_services)}/{len(username_results)} found)[/bold cyan]",
        box=box.ROUNDED, border_style="cyan"
    )
    svc_table.add_column("Status", width=8)
    svc_table.add_column("Service", style="bold white")
    svc_table.add_column("URL", style="dim cyan")

    for r in found_services:
        svc_table.add_row("[bold green]✓ FOUND[/bold green]", r["service"], r["url"])

    console.print(svc_table)

    console.print(f"\n[dim]  ↳ {len(not_found)} services checked — not found | {timeout_count} timed out[/dim]")

    console.print()
    console.print(Rule("[bold green]✓ Email OSINT Complete[/bold green]", style="green"))

# ────────────────── PHONE OSINT (MAIN) ───────────────────────

async def run_phone_osint(phone_input: str):
    console.print()
    console.print(Rule(f"[bold yellow]📱 PHONE OSINT: {phone_input}[/bold yellow]", style="yellow"))
    console.print()

    phone_info = parse_phone_number(phone_input)

    if "error" in phone_info:
        console.print(f"[bold red]✗ Failed to parse phone number: {phone_info['error']}[/bold red]")
        return

    # ── Phone Summary Panel ──
    ph_table = Table(box=box.ROUNDED, show_header=False, border_style="yellow", padding=(0, 1))
    ph_table.add_column("Field", style="bold yellow", no_wrap=True)
    ph_table.add_column("Value", style="white")

    ph_table.add_row("📱 Raw Input", phone_info.get("raw_input", ""))
    ph_table.add_row("🌐 E.164 Format", phone_info.get("e164", ""))
    ph_table.add_row("📞 International", phone_info.get("international", ""))
    ph_table.add_row("📱 National", phone_info.get("national", ""))
    ph_table.add_row("🔗 RFC3966", phone_info.get("rfc3966", ""))
    ph_table.add_row("🌍 Country Code", phone_info.get("country_code", ""))
    ph_table.add_row("🌍 Country", phone_info.get("country", ""))
    ph_table.add_row("🌍 Country ISO", phone_info.get("country_iso", ""))
    ph_table.add_row("📡 Carrier", phone_info.get("carrier", "Unknown") or "[dim]Unknown[/dim]")
    ph_table.add_row("📶 Line Type", phone_info.get("line_type", ""))
    ph_table.add_row("🕐 Timezones", ", ".join(phone_info.get("timezones", [])))
    ph_table.add_row("✅ Valid", "[bold green]YES[/bold green]" if phone_info.get("is_valid") else "[bold red]NO[/bold red]")
    ph_table.add_row("🔍 Possible", "[bold green]YES[/bold green]" if phone_info.get("is_possible") else "[bold red]NO[/bold red]")

    console.print(Panel(ph_table, title="[bold yellow]📱 PHONE NUMBER INTELLIGENCE[/bold yellow]", border_style="yellow"))

    # ── Carrier Latency Test ──
    console.print("\n[bold cyan]🏓 Testing carrier network latency...[/bold cyan]")
    with Progress(
        SpinnerColumn(spinner_name="bouncingBar", style="cyan"),
        TextColumn("[cyan]{task.description}"),
        console=console, transient=True
    ) as prog:
        t = prog.add_task("Measuring latency across carrier endpoints...", total=None)
        latency_results = await test_phone_carrier_latency(phone_info)
        prog.remove_task(t)

    lat_table = Table(title="[bold cyan]🏓 CARRIER LATENCY TESTS[/bold cyan]", box=box.ROUNDED, border_style="cyan")
    lat_table.add_column("Host", style="bold cyan")
    lat_table.add_column("Min (ms)", style="green", justify="right")
    lat_table.add_column("Avg (ms)", style="yellow", justify="right")
    lat_table.add_column("Max (ms)", style="red", justify="right")
    lat_table.add_column("Jitter (ms)", style="magenta", justify="right")
    lat_table.add_column("Status", justify="center")

    for host, data in latency_results.items():
        if data.get("avg") is not None:
            avg = data["avg"]
            status = "[green]Excellent[/green]" if avg < 50 else "[yellow]Good[/yellow]" if avg < 150 else "[red]High[/red]"
            lat_table.add_row(
                host,
                str(data["min"]),
                str(data["avg"]),
                str(data["max"]),
                str(data["jitter"]),
                status
            )
        else:
            lat_table.add_row(host, "—", "—", "—", "—", "[dim]Unreachable[/dim]")

    console.print(lat_table)

    # ── Additional Lookups ──
    console.print("\n[bold cyan]🔍 Running additional lookups...[/bold cyan]")
    async with aiohttp.ClientSession() as session:
        online_info = await lookup_phone_online(phone_info.get("e164", ""), session)

    if online_info:
        ol_table = Table(box=box.ROUNDED, show_header=False, border_style="magenta", padding=(0, 1))
        ol_table.add_column("Key", style="bold magenta")
        ol_table.add_column("Value", style="white")
        for k, v in online_info.items():
            ol_table.add_row(k, str(v)[:120])
        console.print(Panel(ol_table, title="[bold magenta]🔎 ONLINE LOOKUP RESULTS[/bold magenta]", border_style="magenta"))

    # ── Local Time Display ──
    timezones = phone_info.get("timezones", [])
    if timezones:
        tz_table = Table(title="[bold green]🕐 LOCAL TIME IN NUMBER'S TIMEZONE[/bold green]", box=box.ROUNDED, border_style="green")
        tz_table.add_column("Timezone", style="bold green")
        tz_table.add_column("Current Local Time", style="white")
        try:
            import zoneinfo
            for tz in timezones[:3]:
                try:
                    local_time = datetime.now(zoneinfo.ZoneInfo(tz))
                    tz_table.add_row(tz, local_time.strftime("%Y-%m-%d %H:%M:%S %Z"))
                except:
                    tz_table.add_row(tz, "[dim]Could not calculate[/dim]")
        except ImportError:
            tz_table.add_row(timezones[0] if timezones else "—", "[dim]zoneinfo not available[/dim]")
        console.print(tz_table)

    # ── Username check using number as string ──
    number_str = phone_info.get("national_number", "")
    console.print(f"\n[bold cyan]🔎 Checking username '{phone_info.get('e164', phone_input)}' across platforms...[/bold cyan]")

    console.print()
    console.print(Rule("[bold green]✓ Phone OSINT Complete[/bold green]", style="green"))

# ────────────────── IP DIRECT OSINT ──────────────────────────

async def run_ip_direct_osint(ip: str):
    console.print()
    console.print(Rule(f"[bold green]🌍 IP OSINT: {ip}[/bold green]", style="green"))
    console.print()

    with Progress(SpinnerColumn(style="green"), TextColumn("[green]{task.description}"), console=console, transient=True) as prog:
        t = prog.add_task("Gathering IP intelligence...", total=None)
        ip_data = await run_ip_osint(ip)
        prog.remove_task(t)

    geo = ip_data.get("geo", {})
    if geo:
        ip_table = Table(box=box.ROUNDED, show_header=False, border_style="green", padding=(0, 1))
        ip_table.add_column("Field", style="bold green", no_wrap=True)
        ip_table.add_column("Value", style="white")
        fields = [
            ("IP Address", geo.get("query") or ip),
            ("Country", f"{geo.get('country', '')} ({geo.get('countryCode', '')})"),
            ("Continent", f"{geo.get('continent', '')} ({geo.get('continentCode', '')})"),
            ("Region", geo.get("regionName", "")),
            ("City", geo.get("city", "")),
            ("District", geo.get("district", "")),
            ("ZIP Code", geo.get("zip", "")),
            ("Latitude", str(geo.get("lat", ""))),
            ("Longitude", str(geo.get("lon", ""))),
            ("Timezone", geo.get("timezone", "")),
            ("UTC Offset", str(geo.get("offset", ""))),
            ("Currency", geo.get("currency", "")),
            ("ISP", geo.get("isp", "")),
            ("Organization", geo.get("org", "")),
            ("ASN", geo.get("as", "")),
            ("AS Name", geo.get("asname", "")),
            ("Mobile", "Yes" if geo.get("mobile") else "No"),
            ("Proxy/VPN", "[bold red]YES — Proxy/VPN Detected[/bold red]" if geo.get("proxy") else "No"),
            ("Hosting", "Yes" if geo.get("hosting") else "No"),
        ]
        for field, value in fields:
            if value and value.strip():
                ip_table.add_row(field, value)
        console.print(Panel(ip_table, title=f"[bold green]🌍 IP GEOLOCATION & ASN: {ip}[/bold green]", border_style="green"))

    latency = ip_data.get("latency", {})
    if latency.get("avg"):
        lat_table = Table(box=box.ROUNDED, show_header=False, border_style="cyan")
        lat_table.add_column("Metric", style="bold cyan")
        lat_table.add_column("Value", style="white")
        lat_table.add_row("Min Latency", f"{latency['min']} ms")
        lat_table.add_row("Avg Latency", f"{latency['avg']} ms")
        lat_table.add_row("Max Latency", f"{latency['max']} ms")
        lat_table.add_row("Jitter", f"{latency['jitter']} ms")
        console.print(Panel(lat_table, title="[bold cyan]🏓 PING / LATENCY[/bold cyan]", border_style="cyan"))

    console.print()
    console.print(Rule("[bold green]✓ IP OSINT Complete[/bold green]", style="green"))

# ────────────────── DOMAIN OSINT ─────────────────────────────

async def run_domain_direct_osint(domain: str):
    console.print()
    console.print(Rule(f"[bold magenta]🌐 DOMAIN OSINT: {domain}[/bold magenta]", style="magenta"))
    console.print()

    with Progress(SpinnerColumn(style="magenta"), TextColumn("[magenta]{task.description}"), console=console, transient=True) as prog:
        t = prog.add_task("Resolving domain intelligence...", total=None)
        domain_info, domain_ips = await asyncio.gather(
            get_domain_info(domain),
            resolve_host_to_ip(domain)
        )
        prog.remove_task(t)

    if domain_info.get("whois"):
        w = domain_info["whois"]
        w_table = Table(box=box.ROUNDED, show_header=False, border_style="yellow", padding=(0, 1))
        w_table.add_column("Key", style="bold yellow", no_wrap=True)
        w_table.add_column("Value", style="white")
        for k, v in w.items():
            if v and str(v) != "None":
                val = str(v) if not isinstance(v, list) else ", ".join(str(x) for x in v[:5])
                w_table.add_row(k.replace("_", " ").title(), val[:100])
        console.print(Panel(w_table, title=f"[bold yellow]📋 WHOIS: {domain}[/bold yellow]", border_style="yellow"))

    dns_table = Table(title=f"[bold magenta]🔍 DNS Records: {domain}[/bold magenta]", box=box.ROUNDED, border_style="magenta")
    dns_table.add_column("Type", style="bold magenta", width=8)
    dns_table.add_column("Records", style="white")
    for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
        records = domain_info.get(f"dns_{rtype}", [])
        if records:
            dns_table.add_row(rtype, "\n".join(records[:8]))
    console.print(dns_table)

    if domain_ips:
        console.print(f"\n[bold green]Resolved IPs:[/bold green] {', '.join(domain_ips)}")
        for ip in domain_ips[:1]:
            await run_ip_direct_osint(ip)

    console.print()
    console.print(Rule("[bold green]✓ Domain OSINT Complete[/bold green]", style="green"))

# ────────────────── PHONE EXTRACTION ─────────────────────────

PHONE_REGEX = re.compile(
    r'(?:(?:\+|00)[1-9]\d{0,2}[\s\-.]?)?'
    r'(?:\(?\d{2,4}\)?[\s\-.]?)?'
    r'\d{3,4}[\s\-.]?\d{3,4}[\s\-.]?\d{0,4}'
)

def extract_phones_from_text(text: str) -> list:
    raw = PHONE_REGEX.findall(text)
    cleaned = []
    seen = set()
    for p in raw:
        p = p.strip()
        digits = re.sub(r'\D', '', p)
        if len(digits) < 7 or len(digits) > 15:
            continue
        if digits in seen:
            continue
        seen.add(digits)
        cleaned.append(p)
    return cleaned

async def scrape_url_for_phones(session: aiohttp.ClientSession, url: str) -> list:
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8), allow_redirects=True) as resp:
            if resp.status == 200:
                text = await resp.text(errors="ignore")
                return extract_phones_from_text(text)
    except:
        pass
    return []

async def try_find_phones_from_email(email: str, session: aiohttp.ClientSession, github_data: dict, whois_data: dict) -> dict:
    """
    Multi-vector phone hunt:
      1. WHOIS emails → cross-ref with phone patterns in WHOIS raw
      2. GitHub profile page
      3. Personal website from GitHub blog field
      4. Domain homepage + contact page
      5. Common social pages for the username
    """
    username = extract_username(email)
    domain = email.split("@")[1] if "@" in email else ""
    found_phones = {}

    urls_to_scrape = []

    # GitHub profile page
    if github_data.get("found"):
        urls_to_scrape.append((f"https://github.com/{username}", "GitHub Profile"))
        blog = github_data.get("blog")
        if blog:
            if not blog.startswith("http"):
                blog = "https://" + blog
            urls_to_scrape.append((blog, "GitHub Blog/Website"))

    # Domain contact/about pages
    for path in ["", "contact", "contact-us", "about", "about-us", "team"]:
        urls_to_scrape.append((f"https://{domain}/{path}", f"Domain /{path}"))

    # Try common social pages
    for svc, url_tpl in [
        ("LinkedIn",  f"https://www.linkedin.com/in/{username}"),
        ("Twitter",   f"https://twitter.com/{username}"),
        ("About.me",  f"https://about.me/{username}"),
        ("Keybase",   f"https://keybase.io/{username}"),
    ]:
        urls_to_scrape.append((url_tpl, svc))

    # WHOIS stored emails / raw text
    if whois_data:
        raw_whois = str(whois_data)
        phones_in_whois = extract_phones_from_text(raw_whois)
        if phones_in_whois:
            found_phones["WHOIS Record"] = phones_in_whois

    # Scrape all URLs concurrently
    semaphore = asyncio.Semaphore(12)
    async def bounded_scrape(url, label):
        async with semaphore:
            phones = await scrape_url_for_phones(session, url)
            return label, url, phones

    tasks = [bounded_scrape(u, lbl) for u, lbl in urls_to_scrape]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    for label, url, phones in results:
        if phones:
            found_phones[label] = phones

    return found_phones

def validate_extracted_phones(phones_dict: dict) -> dict:
    """Try to parse each extracted phone with phonenumbers for validation."""
    validated = {}
    for source, phone_list in phones_dict.items():
        valid = []
        for p in phone_list:
            for country in ["US", "GB", "IN", "AU", "CA", "DE", "FR", "PK", "BR", "NG"]:
                try:
                    parsed = phonenumbers.parse(p, country)
                    if phonenumbers.is_valid_number(parsed):
                        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
                        intl = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
                        loc = geocoder.description_for_number(parsed, "en")
                        carr = carrier.name_for_number(parsed, "en")
                        valid.append({
                            "raw": p,
                            "e164": e164,
                            "international": intl,
                            "location": loc,
                            "carrier": carr,
                        })
                        break
                except:
                    continue
        if valid:
            validated[source] = valid
    return validated

# ────────────────── ALL-IN-ONE OSINT ─────────────────────────

def detect_input_type(target: str) -> str:
    target = target.strip()
    if is_valid_email(target):
        return "email"
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
        try:
            ipaddress.ip_address(target)
            return "ip"
        except:
            pass
    # IPv6
    try:
        ipaddress.ip_address(target)
        return "ip"
    except:
        pass
    # Phone: starts with + or is all digits (7-15)
    cleaned = re.sub(r'[\s\-\(\)\.]', '', target)
    if cleaned.startswith('+') or (cleaned.lstrip('+').isdigit() and 7 <= len(cleaned.lstrip('+')) <= 15):
        return "phone"
    # Domain-like: has dot, no spaces, no @
    if '.' in target and ' ' not in target and '@' not in target and len(target) > 3:
        return "domain"
    # Fallback: treat as username
    return "username"

async def run_all_in_one(target: str):
    console.print()
    console.print(Panel(
        f"[bold white]🚀 ALL-IN-ONE INTELLIGENCE SCAN[/bold white]\n"
        f"[dim]Target:[/dim] [bold cyan]{target}[/bold cyan]",
        border_style="bold red", padding=(1, 2)
    ))

    input_type = detect_input_type(target)
    console.print(f"[bold green]  ↳ Detected type:[/bold green] [bold yellow]{input_type.upper()}[/bold yellow]\n")

    master_report = {
        "target": target,
        "type": input_type,
        "timestamp": datetime.now().isoformat(),
        "results": {}
    }

    # ── Phase banner helper ──
    def phase(n, label, color="cyan"):
        console.print()
        console.print(Rule(f"[bold {color}]Phase {n}: {label}[/bold {color}]", style=color))

    # ─────────────────────────────────────────────────────────
    # EMAIL path
    # ─────────────────────────────────────────────────────────
    if input_type == "email":
        email = target
        username = extract_username(email)
        domain = email.split("@")[1]

        headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-Tool/3.0; +Og-py3)"}
        connector = aiohttp.TCPConnector(limit=100, ssl=False)

        async with aiohttp.ClientSession(headers=headers, connector=connector) as session:

            phase(1, "Core Email Intelligence", "cyan")
            with Progress(SpinnerColumn(style="cyan"), TextColumn("[cyan]{task.description}"), console=console, transient=True) as prog:
                t = prog.add_task("Running all parallel checks...", total=None)
                emailrep_task  = asyncio.create_task(check_email_reputation(email, session))
                spotify_task   = asyncio.create_task(check_spotify_email(email, session))
                gravatar_task  = asyncio.create_task(get_gravatar_info(email, session))
                github_task    = asyncio.create_task(get_github_info(username, session))
                domain_task    = asyncio.create_task(get_domain_info(domain))
                ip_resolve_task= asyncio.create_task(resolve_host_to_ip(domain))
                username_task  = asyncio.create_task(run_username_checks(username))

                emailrep, spotify, gravatar, github, domain_info, domain_ips, username_results = await asyncio.gather(
                    emailrep_task, spotify_task, gravatar_task, github_task,
                    domain_task, ip_resolve_task, username_task
                )
                prog.remove_task(t)

            # ── Extract EmailRep fields ──
            aio_details  = emailrep.get("details", {})
            aio_leaked   = aio_details.get("credentials_leaked", False)
            aio_breached = aio_details.get("data_breach", False)
            aio_susp     = emailrep.get("suspicious", False)
            aio_rep      = emailrep.get("reputation", "unknown")
            aio_profiles = aio_details.get("profiles", [])

            if aio_leaked or aio_breached:
                breach_label = "[bold red]⚠ Credentials / Breach Detected[/bold red]"
            elif emailrep:
                breach_label = "[bold green]✓ No Known Breaches[/bold green]"
            else:
                breach_label = "[dim]Check unavailable[/dim]"

            # ── Summary ──
            found_svcs = [r for r in username_results if r.get("found") is True]
            s_table = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 1))
            s_table.add_column("Field", style="bold cyan", no_wrap=True)
            s_table.add_column("Value", style="white")
            s_table.add_row("📧 Email",        email)
            s_table.add_row("👤 Username",     username)
            s_table.add_row("🌐 Domain",       domain)
            s_table.add_row("🛡 Reputation",   aio_rep.title() if aio_rep else "[dim]Unknown[/dim]")
            s_table.add_row("🔓 Breach",       breach_label)
            s_table.add_row("🎵 Spotify",      "[bold green]Registered[/bold green]" if spotify.get("registered") else ("[dim]Not registered[/dim]" if spotify.get("registered") is False else "[dim]Check failed[/dim]"))
            s_table.add_row("🖼 Gravatar",     "[green]YES[/green]" if gravatar.get("found") else "[dim]No[/dim]")
            s_table.add_row("🐙 GitHub",       f"[green]{github.get('name') or username}[/green]" if github.get("found") else "[dim]No[/dim]")
            s_table.add_row("📡 Profiles",     f"[bold green]{len(found_svcs)}[/bold green] / {len(username_results)} platforms")
            s_table.add_row("🌍 Domain IPs",   ", ".join(domain_ips) if domain_ips else "[dim]None[/dim]")
            console.print(Panel(s_table, title="[bold white]📊 CORE SUMMARY[/bold white]", border_style="cyan"))

            # EmailRep detail panel
            if emailrep:
                def _yn(val, warn=True):
                    if val is True:  return "[bold red]YES[/bold red]" if warn else "[bold green]YES[/bold green]"
                    if val is False: return "[bold green]No[/bold green]" if warn else "[dim]No[/dim]"
                    return "[dim]Unknown[/dim]"
                rt = Table(box=box.ROUNDED, show_header=False, border_style="red" if (aio_leaked or aio_breached) else "green", padding=(0, 1))
                rt.add_column("Field", style="bold white", no_wrap=True)
                rt.add_column("Value", style="white")
                rt.add_row("Credentials Leaked", _yn(aio_leaked))
                rt.add_row("Data Breach",        _yn(aio_breached))
                rt.add_row("Suspicious",         _yn(aio_susp))
                rt.add_row("Disposable",         _yn(aio_details.get("disposable", False)))
                rt.add_row("Deliverable",        _yn(aio_details.get("deliverable"), warn=False))
                rt.add_row("Spam",               _yn(aio_details.get("spam", False)))
                if aio_profiles: rt.add_row("Known Profiles", ", ".join(aio_profiles))
                color = "red" if (aio_leaked or aio_breached or aio_susp) else "green"
                console.print(Panel(rt, title=f"[bold {color}]🛡 EMAIL REPUTATION[/bold {color}]", border_style=color))

            # Gravatar
            if gravatar.get("found"):
                console.print(f"  [bold blue]🖼 Gravatar:[/bold blue] {gravatar.get('url')}  |  Hash: {gravatar.get('hash')}")

            # GitHub
            if github.get("found"):
                gh = Table(box=box.ROUNDED, show_header=False, border_style="white", padding=(0, 1))
                gh.add_column("Key", style="bold white", no_wrap=True)
                gh.add_column("Value", style="cyan")
                for k, v in github.items():
                    if k != "found" and v:
                        gh.add_row(k.replace("_", " ").title(), str(v))
                console.print(Panel(gh, title="[bold white]🐙 GITHUB[/bold white]", border_style="white"))

            # Platform presence
            if found_svcs:
                pt = Table(title=f"[bold cyan]🔎 Platform Presence — {len(found_svcs)} found[/bold cyan]", box=box.ROUNDED, border_style="cyan")
                pt.add_column("Status", width=10)
                pt.add_column("Platform", style="bold white")
                pt.add_column("URL", style="dim cyan")
                for r in found_svcs:
                    pt.add_row("[bold green]✓[/bold green]", r["service"], r["url"])
                console.print(pt)

            # ── Phase 2: Phone Hunt ──
            phase(2, "Phone Number Hunt (Email → Phone)", "yellow")
            console.print("[dim]  Scanning WHOIS, GitHub, domain pages, and social profiles for linked phone numbers...[/dim]\n")

            with Progress(SpinnerColumn(style="yellow"), TextColumn("[yellow]{task.description}"), console=console, transient=True) as prog:
                t = prog.add_task("Hunting for phone numbers...", total=None)
                raw_phones = await try_find_phones_from_email(email, session, github, domain_info.get("whois", {}))
                prog.remove_task(t)

            validated_phones = validate_extracted_phones(raw_phones)

            if validated_phones:
                for source, phone_list in validated_phones.items():
                    ph_t = Table(title=f"[bold yellow]📱 Phones found via: {source}[/bold yellow]", box=box.ROUNDED, border_style="yellow")
                    ph_t.add_column("Raw", style="dim")
                    ph_t.add_column("E.164", style="bold white")
                    ph_t.add_column("International", style="cyan")
                    ph_t.add_column("Location", style="green")
                    ph_t.add_column("Carrier", style="magenta")
                    for p in phone_list:
                        ph_t.add_row(p["raw"], p["e164"], p["international"], p["location"], p["carrier"] or "—")
                    console.print(ph_t)

                # Deep-dive the first found valid phone
                all_valid = [p for plist in validated_phones.values() for p in plist]
                if all_valid:
                    first_phone = all_valid[0]["e164"]
                    console.print(f"\n[bold yellow]  ↳ Auto-running Phone OSINT on discovered number:[/bold yellow] [bold white]{first_phone}[/bold white]")
                    await run_phone_osint(first_phone)
                    master_report["results"]["discovered_phones"] = [p["e164"] for p in all_valid]
            else:
                console.print(Panel(
                    "[dim]No phone numbers found linked to this email across scanned sources.\n"
                    "Try running Phone OSINT manually if you have a number.[/dim]",
                    border_style="yellow"
                ))

            # ── Phase 3: Domain & IP Deep-dive ──
            phase(3, "Domain & IP Intelligence", "magenta")

            if domain_info.get("whois"):
                w = domain_info["whois"]
                w_t = Table(box=box.ROUNDED, show_header=False, border_style="yellow", padding=(0, 1))
                w_t.add_column("Key", style="bold yellow", no_wrap=True)
                w_t.add_column("Value", style="white")
                for k, v in w.items():
                    if v and str(v) != "None":
                        val = str(v) if not isinstance(v, list) else ", ".join(str(x) for x in v[:5])
                        w_t.add_row(k.replace("_", " ").title(), val[:80])
                console.print(Panel(w_t, title=f"[bold yellow]📋 WHOIS: {domain}[/bold yellow]", border_style="yellow"))

            dns_t = Table(title=f"[bold magenta]🔍 DNS: {domain}[/bold magenta]", box=box.ROUNDED, border_style="magenta")
            dns_t.add_column("Type", style="bold magenta", width=8)
            dns_t.add_column("Records", style="white")
            for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]:
                recs = domain_info.get(f"dns_{rtype}", [])
                if recs:
                    dns_t.add_row(rtype, "\n".join(recs[:5]))
            console.print(dns_t)

            for ip in domain_ips[:2]:
                ip_data = await run_ip_osint(ip)
                geo = ip_data.get("geo", {})
                if geo:
                    ip_t = Table(box=box.ROUNDED, show_header=False, border_style="green", padding=(0, 1))
                    ip_t.add_column("Field", style="bold green", no_wrap=True)
                    ip_t.add_column("Value", style="white")
                    for field, value in [
                        ("IP", geo.get("query") or ip),
                        ("Country", f"{geo.get('country','')} ({geo.get('countryCode','')})"),
                        ("City", geo.get("city", "")),
                        ("ISP", geo.get("isp", "")),
                        ("ASN", geo.get("as", "")),
                        ("Proxy/VPN", "[bold red]YES[/bold red]" if geo.get("proxy") else "No"),
                        ("Hosting", "Yes" if geo.get("hosting") else "No"),
                    ]:
                        if value:
                            ip_t.add_row(field, str(value))
                    console.print(Panel(ip_t, title=f"[bold green]🌍 IP: {ip}[/bold green]", border_style="green"))

        master_report["results"]["emailrep"] = emailrep
        master_report["results"]["gravatar"] = gravatar
        master_report["results"]["github"] = github
        master_report["results"]["platforms_found"] = [r["service"] for r in found_svcs]

    # ─────────────────────────────────────────────────────────
    # PHONE path
    # ─────────────────────────────────────────────────────────
    elif input_type == "phone":
        await run_phone_osint(target)
        # Also run username check using the national number
        info = parse_phone_number(target)
        if not info.get("error"):
            nat = info.get("national_number", "")
            if nat:
                phase(2, "Platform Username Check (Number as Username)", "cyan")
                console.print(f"[dim]  Checking '{nat}' across platforms...[/dim]")
                results = await run_username_checks(nat)
                found = [r for r in results if r.get("found") is True]
                if found:
                    u_t = Table(title=f"[bold cyan]Platforms with '{nat}'[/bold cyan]", box=box.ROUNDED, border_style="cyan")
                    u_t.add_column("Platform", style="bold white")
                    u_t.add_column("URL", style="dim cyan")
                    for r in found:
                        u_t.add_row(r["service"], r["url"])
                    console.print(u_t)
                else:
                    console.print("[dim]  No platform profiles found with this number as username.[/dim]")

    # ─────────────────────────────────────────────────────────
    # IP path
    # ─────────────────────────────────────────────────────────
    elif input_type == "ip":
        await run_ip_direct_osint(target)

    # ─────────────────────────────────────────────────────────
    # DOMAIN path
    # ─────────────────────────────────────────────────────────
    elif input_type == "domain":
        await run_domain_direct_osint(target)

        phase(2, "Phone Hunt on Domain", "yellow")
        headers = {"User-Agent": "Mozilla/5.0 (compatible; OSINT-Tool/3.0)"}
        async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(ssl=False)) as session:
            all_phones = []
            tasks = [
                scrape_url_for_phones(session, f"https://{target}"),
                scrape_url_for_phones(session, f"https://{target}/contact"),
                scrape_url_for_phones(session, f"https://{target}/about"),
                scrape_url_for_phones(session, f"https://{target}/team"),
            ]
            results = await asyncio.gather(*tasks)
            for phones in results:
                all_phones.extend(phones)
            validated = validate_extracted_phones({"Domain Pages": list(set(all_phones))})
            if validated:
                for src, plist in validated.items():
                    ph_t = Table(title=f"[bold yellow]📱 Phones — {src}[/bold yellow]", box=box.ROUNDED, border_style="yellow")
                    ph_t.add_column("E.164", style="bold white")
                    ph_t.add_column("International", style="cyan")
                    ph_t.add_column("Location", style="green")
                    ph_t.add_column("Carrier", style="magenta")
                    for p in plist:
                        ph_t.add_row(p["e164"], p["international"], p["location"], p["carrier"] or "—")
                    console.print(ph_t)
            else:
                console.print("[dim]  No phone numbers found on domain pages.[/dim]")

    # ─────────────────────────────────────────────────────────
    # USERNAME path
    # ─────────────────────────────────────────────────────────
    elif input_type == "username":
        username = target
        phase(1, f"Platform Scan: '{username}'", "cyan")
        with Progress(SpinnerColumn(style="cyan"), TextColumn("[cyan]{task.description}"), console=console, transient=True) as prog:
            t = prog.add_task("Scanning 100+ platforms...", total=None)
            results = await run_username_checks(username)
            prog.remove_task(t)

        found = [r for r in results if r.get("found") is True]
        u_t = Table(title=f"[bold cyan]🔎 '{username}' — {len(found)} profiles found[/bold cyan]", box=box.ROUNDED, border_style="cyan")
        u_t.add_column("Status", width=10)
        u_t.add_column("Platform", style="bold white")
        u_t.add_column("URL", style="dim cyan")
        for r in found:
            u_t.add_row("[bold green]✓ FOUND[/bold green]", r["service"], r["url"])
        console.print(u_t)

        phase(2, "GitHub Deep Lookup", "white")
        async with aiohttp.ClientSession() as session:
            github = await get_github_info(username, session)
            if github.get("found"):
                gh = Table(box=box.ROUNDED, show_header=False, border_style="white", padding=(0, 1))
                gh.add_column("Key", style="bold white", no_wrap=True)
                gh.add_column("Value", style="cyan")
                for k, v in github.items():
                    if k != "found" and v:
                        gh.add_row(k.replace("_", " ").title(), str(v))
                console.print(Panel(gh, title="[bold white]🐙 GITHUB[/bold white]", border_style="white"))

                if github.get("email"):
                    disc_email = github["email"]
                    console.print(f"\n[bold yellow]  ↳ Email discovered from GitHub:[/bold yellow] [bold white]{disc_email}[/bold white]")
                    console.print("[dim]  Running email OSINT on discovered address...[/dim]")
                    await run_email_osint(disc_email)

    # ── Final save prompt ──
    console.print()
    console.print(Rule("[bold red]✓ ALL-IN-ONE SCAN COMPLETE — Made by Og-py3[/bold red]", style="red"))
    try:
        sv = console.input("\n[bold cyan]  💾 Save full report to JSON? (y/n): [/bold cyan]").strip().lower()
        if sv == "y":
            save_results(target, master_report)
    except (KeyboardInterrupt, EOFError):
        pass

# ────────────────── EXPORT RESULTS ───────────────────────────

def save_results(target: str, data: dict):
    filename = f"osint_{target.replace('@', '_at_').replace('+', '').replace(' ', '_')}_{int(time.time())}.json"
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, default=str)
    console.print(f"\n[bold green]💾 Results saved to:[/bold green] [cyan]{filename}[/cyan]")
    return filename

# ────────────────── MAIN MENU ─────────────────────────────────

def print_banner():
    os.system("clear" if os.name != "nt" else "cls")
    console.print(BANNER)
    console.print(Panel(
        f"  {CREDITS}\n  {VERSION}",
        border_style="red",
        padding=(0, 2),
    ))
    console.print()

def print_menu():
    menu = Table(box=box.ROUNDED, show_header=False, border_style="dim white", padding=(0, 2))
    menu.add_column("Option", style="bold yellow", width=6)
    menu.add_column("Description", style="white")
    menu.add_row("[1]", "📧  Email OSINT    — Breaches, services, social profiles, domain info")
    menu.add_row("[2]", "📱  Phone OSINT    — Carrier, location, latency, number intelligence")
    menu.add_row("[3]", "🌍  IP OSINT       — Geolocation, ASN, ISP, proxy detection, latency")
    menu.add_row("[4]", "🌐  Domain OSINT   — WHOIS, DNS, IP resolve, full domain profile")
    menu.add_row("[5]", "🔎  Username       — Check 100+ platforms for profile existence")
    menu.add_row("[6]", "[bold red]🚀  ALL-IN-ONE[/bold red]    — Auto-detect & run ALL checks + Email→Phone hunt")
    menu.add_row("[7]", "🚪  Exit")
    console.print(Panel(menu, title="[bold white]SELECT OSINT MODE[/bold white]", border_style="cyan"))

async def main():
    print_banner()

    while True:
        print_menu()
        try:
            choice = console.input("\n[bold cyan]┌─[Og-py3]─[OSINT]─►[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[bold red]Exiting OSINT Tool. Goodbye.[/bold red]")
            break

        if choice == "1":
            try:
                email = console.input("[bold cyan]  Enter Email: [/bold cyan]").strip()
                if not is_valid_email(email):
                    console.print("[bold red]  ✗ Invalid email format.[/bold red]")
                    continue
                save = console.input("[bold cyan]  Save results to JSON? (y/n): [/bold cyan]").strip().lower()
                await run_email_osint(email)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]  Interrupted. Returning to menu.[/yellow]")

        elif choice == "2":
            try:
                phone = console.input("[bold yellow]  Enter Phone (with country code, e.g. +14155552671): [/bold yellow]").strip()
                await run_phone_osint(phone)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]  Interrupted. Returning to menu.[/yellow]")

        elif choice == "3":
            try:
                ip = console.input("[bold green]  Enter IP Address: [/bold green]").strip()
                try:
                    ipaddress.ip_address(ip)
                except:
                    console.print("[bold red]  ✗ Invalid IP address.[/bold red]")
                    continue
                await run_ip_direct_osint(ip)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]  Interrupted. Returning to menu.[/yellow]")

        elif choice == "4":
            try:
                domain = console.input("[bold magenta]  Enter Domain (e.g. example.com): [/bold magenta]").strip()
                domain = domain.replace("http://", "").replace("https://", "").split("/")[0]
                await run_domain_direct_osint(domain)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]  Interrupted. Returning to menu.[/yellow]")

        elif choice == "5":
            try:
                username = console.input("[bold cyan]  Enter Username: [/bold cyan]").strip()
                console.print(f"\n[bold cyan]🔎 Checking '{username}' across 100+ platforms...[/bold cyan]\n")
                with Progress(SpinnerColumn(style="cyan"), TextColumn("[cyan]{task.description}"), console=console, transient=True) as prog:
                    t = prog.add_task("Scanning platforms...", total=None)
                    results = await run_username_checks(username)
                    prog.remove_task(t)

                found = [r for r in results if r.get("found") is True]
                not_found_c = len([r for r in results if r.get("found") is False])
                timeouts = len([r for r in results if r.get("found") is None])

                u_table = Table(
                    title=f"[bold cyan]🔎 Username: '{username}' — {len(found)} profiles found[/bold cyan]",
                    box=box.ROUNDED, border_style="cyan"
                )
                u_table.add_column("Status", width=10)
                u_table.add_column("Platform", style="bold white")
                u_table.add_column("URL", style="dim cyan")
                for r in found:
                    u_table.add_row("[bold green]✓ FOUND[/bold green]", r["service"], r["url"])
                console.print(u_table)
                console.print(f"\n[dim]  {not_found_c} not found | {timeouts} timed out[/dim]")
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]  Interrupted. Returning to menu.[/yellow]")

        elif choice == "6":
            try:
                console.print()
                console.print(Panel(
                    "[bold white]🚀 ALL-IN-ONE SCANNER[/bold white]\n"
                    "[dim]Enter any target — email, phone, IP, domain, or username.\n"
                    "The tool auto-detects the type and runs every relevant check,\n"
                    "including attempting to extract phone numbers from email targets.[/dim]",
                    border_style="bold red", padding=(1, 2)
                ))
                target = console.input("[bold red]  Enter Target (email / phone / IP / domain / username): [/bold red]").strip()
                if not target:
                    console.print("[bold red]  ✗ No input provided.[/bold red]")
                    continue
                await run_all_in_one(target)
            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]  Interrupted. Returning to menu.[/yellow]")

        elif choice == "7" or choice.lower() in ("exit", "quit", "q"):
            console.print("\n[bold red]  Exiting OSINT Tool. Stay safe. — Og-py3[/bold red]\n")
            break
        else:
            console.print("[bold red]  ✗ Invalid option. Choose 1-7.[/bold red]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        try:
            input()
            print_banner()
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold red]\nInterrupted. Goodbye. — Og-py3[/bold red]\n")
        sys.exit(0)
