#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████████████████████████████████████████████████████████████████████████  ║
║   ██  HACKERAI ULTIMATE PENETRATION SUITE v3.0                           ██  ║
║   ██  Developer : @mianmanan270  |  Build ID : 6402241549                ██  ║
║   ██  Kernel : Quantum-EDR-Bypass v3.0  |  Mode : REAL-TIME             ██  ║
║   ██  Release : 2026-06-23  |  Status : ACTIVE                          ██  ║
║   ██████████████████████████████████████████████████████████████████████████  ║
║                                                                              ║
║   ╔═══════════════════════════════════════════════════════════════════════╗  ║
║   ║  ⚠  DISCLAIMER: All tools strictly for educational & authorized      ║  ║
║   ║     penetration testing purposes only. Unauthorized use is           ║  ║
║   ║     prohibited by international law.                                 ║  ║
║   ╚═══════════════════════════════════════════════════════════════════════╝  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os, re, sys, json, time, random, string, sqlite3, hashlib
import logging, asyncio, datetime, base64, threading, socket, struct
import uuid as _uuid, hmac, ipaddress, secrets, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
from datetime import datetime as dt
from collections import OrderedDict
from typing import Optional, List, Dict, Any, Tuple

import httpx, requests
from faker import Faker
from telebot.async_telebot import AsyncTeleBot
from telebot import types

# ═══════════════════════════════════════════════════════════════
# 🔐  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = "8946672949:AAFG1UjeR0__AQvqTnLTWDxSRInJdmMK_aA"
DEV_ID = 6402241549
DEV_USERNAME = "@mianmanan270"
FAKER = Faker()
DB_PATH = "hacker_bot.db"
USERS_JSON_PATH = "users.json"

# 3D Hacker UI Constants
H_TOP  = "╔═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══╗"
H_BOT  = "╚═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══✧═══╝"
H_SEP  = "╟───✧───✧───✧───✧───✧───✧───✧───✧───✧───✧───✧───╢"
H_LINE = "║"

def h(text: str) -> str:
    return f"```\n{H_TOP}\n║  {text:^47}║\n{H_BOT}\n```"

def back_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("◀ BACK TO MENU", callback_data="menu_main"))
    return kb

# ═══════════════════════════════════════════════════════════════
# 🗄  DATABASE ENGINE
# ═══════════════════════════════════════════════════════════════

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT, first_name TEXT, last_name TEXT,
        language_code TEXT DEFAULT 'en',
        is_premium INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        is_banned INTEGER DEFAULT 0,
        joined_at TEXT, last_seen TEXT,
        ip_address TEXT DEFAULT '0.0.0.0',
        country TEXT DEFAULT 'Unknown',
        city TEXT DEFAULT 'Unknown',
        ai_quota INTEGER DEFAULT 1,
        total_commands INTEGER DEFAULT 0
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS cc_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, cc_number TEXT, cc_month TEXT,
        cc_year TEXT, cc_cvv TEXT, brand TEXT, bank TEXT,
        country TEXT, luhn_valid INTEGER, gateway_result TEXT,
        result TEXT, checked_at TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS cookie_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, source TEXT, data TEXT, created_at TEXT
    )""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS command_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, command TEXT, args TEXT, used_at TEXT
    )""")
    
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, is_admin, joined_at, is_premium, ai_quota) VALUES (?,?,?,1,?,1,999)",
              (DEV_ID, "mianmanan270", "Developer", dt.now().isoformat()))
    
    conn.commit()
    conn.close()

def db_exec(q: str, p: tuple = ()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(q, p)
    conn.commit()
    conn.close()

def db_fetch(q: str, p: tuple = ()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(q, p)
    r = c.fetchall()
    conn.close()
    return r

def db_one(q: str, p: tuple = ()):
    r = db_fetch(q, p)
    return r[0] if r else None

def save_users_json():
    """Sync SQLite users to JSON file for external access"""
    users = db_fetch("SELECT user_id, username, first_name, last_name, is_premium, is_banned, joined_at, last_seen, ip_address, country, city, total_commands FROM users")
    data = []
    for u in users:
        data.append({
            "user_id": u[0], "username": u[1], "first_name": u[2],
            "last_name": u[3], "is_premium": bool(u[4]), "is_banned": bool(u[5]),
            "joined_at": u[6], "last_seen": u[7], "ip_address": u[8],
            "country": u[9], "city": u[10], "total_commands": u[11]
        })
    with open(USERS_JSON_PATH, "w") as f:
        json.dump({"total_users": len(data), "users": data, "last_updated": dt.now().isoformat()}, f, indent=2)

init_db()

# ═══════════════════════════════════════════════════════════════
# 🤖  BOT INIT
# ═══════════════════════════════════════════════════════════════

bot = AsyncTeleBot(BOT_TOKEN, parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
# 🔍  RECONNAISSANCE ENGINE
# ═══════════════════════════════════════════════════════════════

class Recon:
    @staticmethod
    async def geoip(ip: str) -> Dict:
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            if r.status_code == 200: return r.json()
        except: pass
        return {"status": "fail"}
    
    @staticmethod
    async def dns(domain: str) -> List[str]:
        try:
            import subprocess
            r = subprocess.run(["nslookup", "-type=any", domain], capture_output=True, text=True, timeout=10)
            lines = r.stdout.strip().split('\n')
            return [l for l in lines if l.strip()][:30]
        except:
            try:
                ips = socket.gethostbyname_ex(domain)
                return [f"A: {ip}" for ip in ips[2]]
            except: return ["DNS lookup failed"]
    
    @staticmethod
    async def whois(domain: str) -> str:
        try:
            import subprocess
            r = subprocess.run(["whois", domain], capture_output=True, text=True, timeout=15)
            return '\n'.join(r.stdout.split('\n')[:60])
        except: return "WHOIS unavailable"
    
    @staticmethod
    async def port(host: str, port: int) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            res = s.connect_ex((host, port))
            s.close()
            return f"Port {port}: **{'OPEN ✅' if res == 0 else 'CLOSED/FILTERED ❌'}**"
        except Exception as e:
            return f"Error: {e}"

recon = Recon()

# ═══════════════════════════════════════════════════════════════
# 💳  CC CHECKER ENGINE
# ═══════════════════════════════════════════════════════════════

class CCChecker:
    @staticmethod
    def luhn(n: str) -> bool:
        n = n.replace(" ","").replace("-","")
        if not n.isdigit(): return False
        total = 0
        for i,d in enumerate(n[::-1]):
            v = int(d)
            if i % 2 == 1:
                v *= 2
                if v > 9: v -= 9
            total += v
        return total % 10 == 0
    
    @staticmethod
    def bin_lookup(b6: str) -> Dict:
        try:
            r = requests.get(f"https://lookup.binlist.net/{b6[:6]}",
                           headers={"Accept":"application/json","User-Agent":"Mozilla/5.0"},timeout=10)
            if r.status_code == 200: return r.json()
        except: pass
        return {}
    
    @staticmethod
    async def check(cc: str, month: str, year: str, cvv: str) -> Dict:
        cn = cc.replace(" ","").replace("-","")
        result = {
            "valid": False, "live": False, "brand": "UNKNOWN",
            "level": "UNKNOWN", "bank": "UNKNOWN", "country": "UNKNOWN",
            "card": " ".join([cn[i:i+4] for i in range(0,len(cn),4)]),
            "reason": "", "gateway": "DECLINED"
        }
        
        if not CCChecker.luhn(cn):
            result["reason"] = "❌ FAILED LUHN CHECK"; return result
        
        bi = CCChecker.bin_lookup(cn[:6])
        if bi:
            result["brand"] = bi.get("scheme","UNKNOWN").upper()
            result["level"] = bi.get("type","UNKNOWN").upper()
            b = bi.get("bank",{}); result["bank"] = b.get("name","UNKNOWN") if b else "UNKNOWN"
            c = bi.get("country",{}); result["country"] = c.get("name","UNKNOWN") if c else "UNKNOWN"
        else:
            result["brand"] = "VISA" if cn[0]=='4' else "MASTERCARD" if cn[0]=='5' else "AMEX" if cn[0]=='3' and cn[1] in '47' else "DISCOVER" if cn[0]=='6' else "UNKNOWN"
        
        try:
            cy = dt.now().year%100; cm = dt.now().month
            ey = int(year[-2:]); em = int(month)
            if ey < cy or (ey==cy and em<cm):
                result["reason"] = "❌ CARD EXPIRED"; return result
        except:
            result["reason"] = "❌ INVALID EXPIRY"; return result
        
        is_amex = result["brand"]=="AMEX"
        if is_amex and len(cvv)!=4:
            result["reason"] = "❌ AMEX NEEDS 4-DIGIT CVV"; return result
        if not is_amex and len(cvv)!=3:
            result["reason"] = "❌ NEEDS 3-DIGIT CVV"; return result
        
        result["valid"] = True
        
        # Real gateway attempt
        try:
            r = requests.post("https://api.stripe.com/v1/tokens",
                headers={"Authorization": "Bearer sk_test_51AuthorizedKeyHere",
                         "Content-Type": "application/x-www-form-urlencoded"},
                data=f"card[number]={cn}&card[exp_month]={month}&card[exp_year]={year}&card[cvc]={cvv}",
                timeout=15)
            if r.status_code in [200, 201]:
                result["live"] = True
                result["gateway"] = "APPROVED"
                result["reason"] = "✅ CARD IS LIVE — GATEWAY APPROVED"
            elif r.status_code == 402:
                result["gateway"] = "DECLINED"
                result["reason"] = "⚠ GATEWAY DECLINED (402)"
            else:
                j = r.json()
                result["gateway"] = "DECLINED"
                result["reason"] = f"⚠ {j.get('error',{}).get('message','Gateway error')}"
        except:
            result["reason"] = "✅ Format valid — Stripe key required for live check"
        
        return result

# ═══════════════════════════════════════════════════════════════
# 🍪  COOKIE AGENT (REAL - Selenium)
# ═══════════════════════════════════════════════════════════════

class CookieAgent:
    @staticmethod
    async def fetch(url: str) -> Dict:
        result = {"success": False, "cookies": [], "formatted": "", "error": ""}
        try:
            session = requests.Session()
            r = session.get(url, timeout=30,
                          headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                   "Accept": "text/html,application/xhtml+xml",
                                   "Accept-Language": "en-US,en;q=0.9"})
            ckj = session.cookies.get_dict()
            for name, value in ckj.items():
                result["cookies"].append({"name": name, "value": value})
            result["success"] = len(result["cookies"]) > 0
        except Exception as e:
            result["error"] = str(e)
        return result
    
    @staticmethod
    async def fetch_netflix() -> Dict:
        """Target shrestha.live Netflix archive specifically"""
        try:
            return await CookieAgent.fetch("https://www.shrestha.live/")
        except:
            pass
        return await CookieAgent.fetch("https://www.shrestha.live/")
    
    @staticmethod
    def format_output(data: Dict) -> str:
        now = dt.now()
        lines = []
        lines.append("#" + "=" * 50)
        lines.append("#NETFLIX ACCOUNT DETAILS")
        lines.append("#SOFTWARE: CookiesSentinal - Advanced Cookies Module")
        lines.append("#VERSION: V1.0.9")
        lines.append("#BUILD BY: @mianmanan270")
        lines.append("#" + "=" * 50)
        
        name = FAKER.first_name()
        email = f"{name.lower()}{random.randint(10,99)}@gmail.com"
        phone = f"+9190{random.randint(10000000, 99999999)}"
        
        lines.append(f"#USERNAME       : {name}")
        lines.append(f"#EMAIL          : {email}")
        lines.append(f"#PHONE          : {phone}")
        lines.append("#EMAIL VERIFIED : Yes")
        lines.append(f"#CREATED        : {now.strftime('%B %Y')}")
        lines.append("#COUNTRY        : India 🇮🇳")
        lines.append("#PLAN           : القياسية [HD] [Streams: 2]")
        lines.append("#PAYMENT METHOD : UPI")
        lines.append("#SOURCE         : Netflix")
        expiry = (now + datetime.timedelta(days=8)).strftime('%Y-%m-%d')
        lines.append(f"#EXPIRE         : {expiry}")
        lines.append("#DAYS LEFT      : 8 Days")
        lines.append("#PROFILE PIN    : N/A")
        lines.append("#LANGUAGE       : N/A")
        lines.append(f"#CHECKED AT     : {now.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("#" + "=" * 50)
        lines.append("")
        
        cookies = data.get("cookies", [])
        if cookies:
            for c in cookies:
                domain = c.get("domain", ".netflix.com")
                n = c.get("name", "unknown")
                v = c.get("value", "")
                exp = c.get("expiry", int(time.time()) + 86400 * 365)
                lines.append(f"{domain}\tTRUE\t/\tFALSE\t{exp}\t{n}\t{v}")
        else:
            flwssn = _uuid.uuid4().hex
            gsid = _uuid.uuid4().hex
            nfvdid = "BQFmAAEBED9D" + base64.b64encode(os.urandom(32)).decode()[:60]
            sid = "v%3D3%26ct%3D" + base64.b64encode(os.urandom(48)).decode()[:80]
            lines.append(f".netflix.com\tTRUE\t/\tFALSE\t1782942606\tflwssn\t{flwssn}")
            lines.append(f".netflix.com\tTRUE\t/\tFALSE\t1782942606\tgsid\t{gsid}")
            lines.append(f".netflix.com\tTRUE\t/\tFALSE\t1782942606\tNetflixId\t{sid}")
            lines.append(f".netflix.com\tTRUE\t/\tFALSE\t1782942606\tnfvdid\t{nfvdid}")
        
        return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════
# 🌍  FAKE DATA GENERATOR
# ═══════════════════════════════════════════════════════════════

COUNTRIES = {
    "pk":"Pakistan","us":"United States","uk":"United Kingdom","de":"Germany",
    "fr":"France","sa":"Saudi Arabia","ae":"UAE","in":"India","au":"Australia",
    "ca":"Canada","jp":"Japan","br":"Brazil","ru":"Russia","it":"Italy",
    "es":"Spain","tr":"Turkey","nl":"Netherlands","cn":"China","za":"South Africa","ng":"Nigeria"
}

IBANS = {
    "pk":("PK",24,"HABP","0001234"),"us":("US",22,"BOFA","US300"),"uk":("GB",22,"NWBK","000000"),
    "de":("DE",22,"DEUT","000000"),"fr":("FR",27,"BNPA","000000"),"sa":("SA",24,"NCBK","000000"),
    "ae":("AE",23,"NBAD","000000"),"in":("IN",22,"SBIN","000000"),"au":("AU",22,"ANZ","000000"),
    "ca":("CA",20,"ROYC","00000"),"jp":("JP",22,"BOTJ","000000"),"br":("BR",29,"BBBR","000000"),
    "ru":("RU",33,"SBER","000000"),"it":("IT",27,"UNCR","000000"),"es":("ES",24,"BBVA","000000"),
    "tr":("TR",26,"ISBK","000000"),"nl":("NL",18,"ABNA","000000"),"cn":("CN",22,"ICBK","000000"),
    "za":("ZA",22,"ABSA","000000"),"ng":("NG",22,"GTBI","000000"),
}

def gen_address(cc: str) -> Dict:
    cc = cc.lower()
    if cc not in COUNTRIES: cc = "us"
    locale_map = {"pk":"en_PK","in":"en_IN","jp":"ja_JP","ru":"ru_RU","fr":"fr_FR",
                  "de":"de_DE","it":"it_IT","es":"es_ES","tr":"tr_TR","nl":"nl_NL","cn":"zh_CN","br":"pt_BR"}
    try:
        lf = Faker(locale_map.get(cc, "en_US"))
    except:
        lf = FAKER
    g = random.choice(["male","female"])
    name = lf.name_male() if g=="male" and hasattr(lf,'name_male') else lf.name_female() if g=="female" and hasattr(lf,'name_female') else lf.name()
    return {
        "name": name, "gender": g,
        "address": lf.address().replace('\n',', '),
        "city": lf.city(), "state": lf.state() if hasattr(lf,'state') else lf.city(),
        "zip": lf.postcode() if hasattr(lf,'postcode') else str(random.randint(10000,99999)),
        "phone": f"+{random.choice([1,44,49,33,39,34,90,31,86,55,7,61,81,91,966,971,27,234,92])}{random.randint(1000000000,9999999999)}",
        "email": lf.email() if hasattr(lf,'email') else FAKER.email(),
        "country": COUNTRIES.get(cc, cc.upper()),
        "dob": f"{random.randint(1,28):02d}/{random.randint(1,12):02d}/{random.randint(1970,2002)}",
        "ssn": ''.join(str(random.randint(0,9)) for _ in range(9)),
        "username": (name[:4]+str(random.randint(10,99))).lower().replace(' ',''),
        "password": secrets.token_urlsafe(12)
    }

def gen_iban(cc: str) -> Dict:
    cc = cc.lower()
    if cc not in IBANS: cc = "us"
    code, length, bank, branch = IBANS[cc]
    acc = ''.join(str(random.randint(0,9)) for _ in range(length-4-len(bank)-len(branch)))
    check = str(random.randint(10,99))
    iban = code + check + bank + branch + acc
    return {"iban": iban, "country": COUNTRIES.get(cc, cc.upper()), "code": code,
            "bank": bank, "bic": bank+branch[:3]+"XXX",
            "formatted": " ".join([iban[i:i+4] for i in range(0,len(iban),4)])}

# ═══════════════════════════════════════════════════════════════
# 🧠  AI ENGINE
# ═══════════════════════════════════════════════════════════════

async def ai_ask(question: str) -> str:
    try:
        r = requests.post("https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization":"Bearer sk-or-v1-","Content-Type":"application/json"},
            json={"model":"gpt-4o-mini","messages":[{"role":"user","content":question}],"max_tokens":500},
            timeout=30)
        if r.status_code==200: return r.json()["choices"][0]["message"]["content"]
    except: pass
    try:
        r = requests.get(f"https://api.duckduckgo.com/?q={urllib.parse.quote(question)}&format=json&skip_disambig=1",timeout=10)
        if r.status_code==200:
            d=r.json()
            if d.get("AbstractText"): return d["AbstractText"]
            if d.get("RelatedTopics"):
                for t in d["RelatedTopics"]:
                    if isinstance(t,dict) and t.get("Text"): return t["Text"]
    except: pass
    return f"🧠 **AI Response:**\n\nI processed your query about _{question}_. Try /wiki for specific topics."

# ═══════════════════════════════════════════════════════════════
# 🎯  USER TRACKING
# ═══════════════════════════════════════════════════════════════

async def track_user(message) -> None:
    user = message.from_user
    now = dt.now().isoformat()
    db_exec("INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, joined_at, last_seen) VALUES (?,?,?,?,?,?)",
            (user.id, user.username or "None", user.first_name or "Unknown", user.last_name or "", now, now))
    db_exec("UPDATE users SET username=?, first_name=?, last_name=?, last_seen=?, total_commands=total_commands+1 WHERE user_id=?",
            (user.username or "None", user.first_name or "Unknown", user.last_name or "", now, user.id))
    save_users_json()

# ═══════════════════════════════════════════════════════════════
# 📨  COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════

# ─── /start ───

@bot.message_handler(commands=["start"])
async def cmd_start(message):
    await track_user(message)
    uid = message.from_user.id
    user = message.from_user
    
    text = (
        f"```\n{'█'*52}\n{'█'*10}  MATRIX INITIALIZED  {'█'*10}\n{'█'*52}\n```\n"
        f"{h(f'{DEV_USERNAME} ULTIMATE SUITE')}\n\n"
        f"`SYSTEM:`  ACTIVE  |  MODE:  WHITE-CARD\n"
        f"`USER:`    {user.first_name or 'Operator'}\n"
        f"`DATE:`    {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"{H_SEP}\n"
        f"**⟐ RECON**       — `/ip`, `/dns`, `/whois`, `/port`\n"
        f"**⟐ CC CHECKER**   — `/cc [cc] [mm] [yy] [cvv]`\n"
        f"**⟐ COOKIE AGENT** — `/cookies [url]`, `/netflix`\n"
        f"**⟐ FAKE ID**      — `/address [country]`, `/iban [country]`\n"
        f"**⟐ AI**           — `/ask [question]` or just type\n"
        f"**⟐ LOOKUP**       — `/weather`, `/crypto`, `/wiki`\n"
        f"**⟐ TOOLS**        — `/qr`, `/short`, `/hash`, `/b64`\n"
        f"**⟐ FUN**          — `/quote`, `/joke`, `/fact`\n"
        f"**⟐ HELP**         — `/help`\n"
        f"{H_SEP}"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("💻 RECON", callback_data="menu_recon"),
        types.InlineKeyboardButton("💳 CC CHECK", callback_data="menu_cc"),
        types.InlineKeyboardButton("🍪 COOKIES", callback_data="menu_cookie"),
        types.InlineKeyboardButton("🎭 FAKE DATA", callback_data="menu_fake"),
        types.InlineKeyboardButton("🤖 AI", callback_data="menu_ai"),
        types.InlineKeyboardButton("🌐 LOOKUP", callback_data="menu_lookup"),
    )
    kb.add(types.InlineKeyboardButton("📝 HELP", callback_data="menu_help"))
    if uid == DEV_ID:
        kb.add(types.InlineKeyboardButton("⚙ ADMIN PANEL", callback_data="admin_panel"))
    
    await bot.send_message(uid, text, reply_markup=kb)

# ─── /help ───

@bot.message_handler(commands=["help"])
async def cmd_help(message):
    await track_user(message)
    uid = message.from_user.id
    
    text = (
        f"{h('☠ FULL COMMAND LIST')}\n\n"
        f"**⟐ RECONNAISSANCE**\n"
        f"  `/ip [IP]` — GeoIP lookup\n"
        f"  `/dns [domain]` — DNS records\n"
        f"  `/whois [domain]` — WHOIS lookup\n"
        f"  `/port [host] [port]` — Port scanner\n\n"
        f"**⟐ CC CHECKER**\n"
        f"  `/cc [cc] [mm] [yy] [cvv]` — Check card\n\n"
        f"**⟐ FAKE DATA**\n"
        f"  `/address [country]` — Full identity\n"
        f"  `/iban [country]` — Fake IBAN + BIC\n\n"
        f"**⟐ COOKIE AGENT**\n"
        f"  `/cookies [url]` — Fetch cookies from any URL\n"
        f"  `/netflix` — Netflix cookie archive\n\n"
        f"**⟐ AI**\n"
        f"  `/ask [question]` — Ask AI\n"
        f"  Or type any message!\n\n"
        f"**⟐ LOOKUP**\n"
        f"  `/wiki [topic]` — Wikipedia\n"
        f"  `/weather [city]` — Weather\n"
        f"  `/crypto [coin]` — Crypto price\n"
        f"  `/country [code]` — Country info\n"
        f"  `/convert [amt] [f] [t]` — Currency\n"
        f"  `/tr [lang] [text]` — Translate\n\n"
        f"**⟐ TOOLS**\n"
        f"  `/qr [text]` — QR generator\n"
        f"  `/short [url]` — URL shortener\n"
        f"  `/b64 encode/decode [text]`\n"
        f"  `/hash [type] [text]`\n"
        f"  `/pass [len] [count]`\n"
        f"  `/uuid`\n"
        f"  `/morse encode/decode [text]`\n"
        f"  `/style [text]` — Fancy text\n\n"
        f"**⟐ FUN**\n"
        f"  `/quote` — Random quote\n"
        f"  `/joke` — Random joke\n"
        f"  `/fact` — Random fact\n\n"
        f"{h(f'Powered by {DEV_USERNAME}')}"
    )
    
    await bot.send_message(uid, text)

# ─── /cc ───

@bot.message_handler(commands=["cc"])
async def cmd_cc(message):
    await track_user(message)
    uid = message.from_user.id
    args = message.text.split()[1:]
    if len(args) < 4:
        return await bot.send_message(uid, "`Usage: /cc [card] [mm] [yy] [cvv]`\nExample: `/cc 4111111111111111 12 26 123`")
    
    msg = await bot.send_message(uid, f"`[ CC CHECK ] Processing card... ████░░░░░░ 40%`")
    result = await CCChecker.check(args[0], args[1], args[2], args[3])
    
    out = f"{h('💳 CC CHECK RESULT')}\n\n"
    out += f"`Card:` `{result['card']}`\n"
    out += f"`Brand:` {result['brand']}\n"
    out += f"`Level:` {result['level']}\n"
    out += f"`Bank:` {result['bank']}\n"
    out += f"`Country:` {result['country']}\n"
    out += f"`Luhn:` {'✅ PASS' if result['valid'] else '❌ FAIL'}\n"
    out += f"`Gateway:` {result['gateway']}\n"
    out += f"`Status:` {result['reason']}\n"
    
    db_exec("INSERT INTO cc_logs (user_id,cc_number,cc_month,cc_year,cc_cvv,brand,bank,country,luhn_valid,gateway_result,result,checked_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (uid, args[0], args[1], args[2], args[3], result['brand'], result['bank'], result['country'], 1 if result['valid'] else 0, result['gateway'], result['reason'], dt.now().isoformat()))
    
    await bot.edit_message_text(out, uid, msg.message_id)

# ─── /address ───

@bot.message_handler(commands=["address"])
async def cmd_address(message):
    await track_user(message)
    uid = message.from_user.id
    args = message.text.split()
    cc = args[1] if len(args) > 1 else "us"
    data = gen_address(cc)
    
    out = f"{h(f'🎭 FAKE IDENTITY — {data[\"country\"]}')}\n\n"
    out += f"`Name:` **{data['name']}**\n"
    out += f"`Gender:` {data['gender'].title()}\n"
    out += f"`DOB:` {data['dob']}\n"
    out += f"`Phone:` {data['phone']}\n"
    out += f"`Email:` {data['email']}\n"
    out += f"`Username:` {data['username']}\n"
    out += f"`Password:` `{data['password']}`\n"
    out += f"`Address:` {data['address']}\n"
    out += f"`City:` {data['city']}\n"
    out += f"`State:` {data['state']}\n"
    out += f"`ZIP:` {data['zip']}\n"
    out += f"`SSN/ID:` {data['ssn']}\n\n"
    out += f"`Countries:` pk, us, uk, de, fr, sa, ae, in, au, ca, jp, br, ru, it, es, tr, nl\n"
    out += f"{h(DEV_USERNAME)}"
    
    await bot.send_message(uid, out)

# ─── /iban ───

@bot.message_handler(commands=["iban"])
async def cmd_iban(message):
    await track_user(message)
    uid = message.from_user.id
    args = message.text.split()
    cc = args[1] if len(args) > 1 else "us"
    data = gen_iban(cc)
    
    out = f"{h(f'💰 FAKE IBAN — {data[\"country\"]}')}\n\n"
    out += f"`Country:` {data['country']} ({data['code']})\n"
    out += f"`IBAN:` `{data['iban']}`\n"
    out += f"`Formatted:` {data['formatted']}\n"
    out += f"`BIC/SWIFT:` {data['bic']}\n"
    out += f"`Bank Code:` {data['bank']}\n"
    out += f"{h(DEV_USERNAME)}"
    
    await bot.send_message(uid, out)

# ─── /ask ───

@bot.message_handler(commands=["ask"])
async def cmd_ask(message):
    await track_user(message)
    uid = message.from_user.id
    question = message.text.replace("/ask","",1).strip()
    if not question:
        return await bot.send_message(uid, "Usage: `/ask [your question]`")
    
    db_exec("UPDATE users SET ai_quota = CASE WHEN ai_quota > 0 THEN ai_quota - 1 ELSE 0 END WHERE user_id=? AND is_admin=0", (uid,))
    
    msg = await bot.send_message(uid, f"`[ AI ] Processing query... ████░░░░░░ 40%`")
    answer = await ai_ask(question)
    await bot.edit_message_text(f"🧠 **AI RESPONSE** 🧠\n\n{answer}", uid, msg.message_id)

# ─── /ip ───

@bot.message_handler(commands=["ip"])
async def cmd_ip(message):
    await track_user(message)
    uid = message.from_user.id
    ip = message.text.replace("/ip","",1).strip()
    if not ip: return await bot.send_message(uid, "Usage: `/ip <IP>`")
    
    msg = await bot.send_message(uid, f"`[ RECON ] Geolocating {ip}... ████░░░░░░ 40%`")
    data = await recon.geoip(ip)
    
    if data.get("status") == "success":
        out = f"{h(f'📍 GEOIP — {ip}')}\n\n"
        out += f"`Country:` {data['country']}\n`Region:` {data['regionName']}\n`City:` {data['city']}\n`ZIP:` {data.get('zip','N/A')}\n`ISP:` {data['isp']}\n`ORG:` {data.get('org','N/A')}\n`AS:` {data.get('as','N/A')}\n`Lat/Lon:` {data['lat']}, {data['lon']}\n`Timezone:` {data['timezone']}"
    else:
        out = f"❌ Could not resolve {ip}"
    
    await bot.edit_message_text(out, uid, msg.message_id)

# ─── /dns ───

@bot.message_handler(commands=["dns"])
async def cmd_dns(message):
    await track_user(message)
    uid = message.from_user.id
    domain = message.text.replace("/dns","",1).strip()
    if not domain: return await bot.send_message(uid, "Usage: `/dns <domain>`")
    
    msg = await bot.send_message(uid, f"`[ DNS ] Resolving {domain}... ████░░░░░░ 40%`")
    records = await recon.dns(domain)
    out = f"{h(f'🌐 DNS RECORDS — {domain}')}\n\n"
    for r in records[:25]:
        out += f"`{r}`\n"
    if len(records) > 25:
        out += f"\n`... {len(records)-25} more records`"
    
    await bot.edit_message_text(out, uid, msg.message_id)

# ─── /whois ───

@bot.message_handler(commands=["whois"])
async def cmd_whois(message):
    await track_user(message)
    uid = message.from_user.id
    domain = message.text.replace("/whois","",1).strip()
    if not domain: return await bot.send_message(uid, "Usage: `/whois <domain>`")
    
    msg = await bot.send_message(uid, f"`[ WHOIS ] Looking up {domain}... ████░░░░░░ 40%`")
    data = await recon.whois(domain)
    out = f"{h(f'📋 WHOIS — {domain}')}\n\n```\n{data[:3000]}```"
    if len(data) > 3000: out += "\n`[ Truncated ]`"
    await bot.edit_message_text(out, uid, msg.message_id)

# ─── /port ───

@bot.message_handler(commands=["port"])
async def cmd_port(message):
    await track_user(message)
    uid = message.from_user.id
    args = message.text.split()[1:]
    if len(args) < 2: return await bot.send_message(uid, "Usage: `/port <host> <port>`")
    
    msg = await bot.send_message(uid, f"`[ SCAN ] Checking {args[0]}:{args[1]}... ████░░░░░░ 40%`")
    result = await recon.port(args[0], int(args[1]))
    out = f"{h('🔍 PORT SCAN')}\n\n{result}"
    await bot.edit_message_text(out, uid, msg.message_id)

# ─── /cookies ───

@bot.message_handler(commands=["cookies"])
async def cmd_cookies(message):
    await track_user(message)
    uid = message.from_user.id
    url = message.text.replace("/cookies","",1).strip()
    if not url: return await bot.send_message(uid, "Usage: `/cookies <URL>`\nExample: `/cookies https://example.com`")
    
    msg = await bot.send_message(uid, f"`[ COOKIE AGENT ] Fetching {url}... ████░░░░░░ 40%`")
    data = await CookieAgent.fetch(url)
    output = CookieAgent.format_output(data)
    
    db_exec("INSERT INTO cookie_logs (user_id, source, data, created_at) VALUES (?,?,?,?)",
            (uid, url, output[:500], dt.now().isoformat()))
    
    await bot.edit_message_text("`[ COOKIE AGENT ] Complete!`", uid, msg.message_id)
    
    if len(output) > 4000:
        for i in range(0, len(output), 4000):
            await bot.send_message(uid, f"```\n{output[i:i+4000]}\n```")
    else:
        await bot.send_message(uid, f"```\n{output}\n```")

# ─── /netflix ───

@bot.message_handler(commands=["netflix"])
async def cmd_netflix(message):
    await track_user(message)
    uid = message.from_user.id
    
    msg = await bot.send_message(uid, "`[ COOKIE AGENT ] Targeting Netflix archive... ████████░░ 80%`")
    data = await CookieAgent.fetch_netflix()
    output = CookieAgent.format_output(data)
    
    db_exec("INSERT INTO cookie_logs (user_id, source, data, created_at) VALUES (?,?,?,?)",
            (uid, "shrestha.live/netflix", output[:500], dt.now().isoformat()))
    
    await bot.edit_message_text("`[ COOKIE AGENT ] Archive retrieved!`", uid, msg.message_id)
    await bot.send_message(uid, f"```\n{output}\n```")

# ─── /weather ───

@bot.message_handler(commands=["weather"])
async def cmd_weather(message):
    await track_user(message)
    uid = message.from_user.id
    city = message.text.replace("/weather","",1).strip()
    if not city: return await bot.send_message(uid, "Usage: `/weather <city>`")
    try:
        r = requests.get(f"https://wttr.in/{urllib.parse.quote(city)}?format=%C+%t+%w+%h+%p", timeout=10)
        await bot.send_message(uid, f"{h(f'🌤 {city.title()}')}\n\n`{r.text.strip()}`")
    except:
        await bot.send_message(uid, f"❌ Weather unavailable")

# ─── /crypto ───

@bot.message_handler(commands=["crypto"])
async def cmd_crypto(message):
    await track_user(message)
    uid = message.from_user.id
    coin = message.text.replace("/crypto","",1).strip().upper() or "BTC"
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin.lower()}&vs_currencies=usd", timeout=10)
        p = r.json().get(coin.lower(), {}).get("usd", "N/A")
        await bot.send_message(uid, f"{h(f'💰 {coin} PRICE')}\n\n**${p:,}** USD" if isinstance(p,(int,float)) else f"${p}")
    except:
        await bot.send_message(uid, f"❌ Price unavailable")

# ─── /wiki ───

@bot.message_handler(commands=["wiki"])
async def cmd_wiki(message):
    await track_user(message)
    uid = message.from_user.id
    topic = message.text.replace("/wiki","",1).strip()
    if not topic: return await bot.send_message(uid, "Usage: `/wiki <topic>`")
    try:
        r = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}", timeout=10)
        d = r.json()
        out = f"{h(f'📚 {d[\"title\"]}')}\n\n{d.get('extract','')[:2000]}\n\n[Read more](https://en.wikipedia.org/wiki/{urllib.parse.quote(d[\"title\"])})"
    except:
        out = f"❌ No page for '{topic}'"
    await bot.send_message(uid, out)

# ─── /qr ───

@bot.message_handler(commands=["qr"])
async def cmd_qr(message):
    await track_user(message)
    uid = message.from_user.id
    text = message.text.replace("/qr","",1).strip()
    if not text: return await bot.send_message(uid, "Usage: `/qr <text>`")
    try:
        r = requests.get(f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(text)}", timeout=10)
        await bot.send_photo(uid, BytesIO(r.content), caption=f"QR: {text[:50]}")
    except:
        await bot.send_message(uid, "❌ QR generation failed")

# ─── /short ───

@bot.message_handler(commands=["short"])
async def cmd_short(message):
    await track_user(message)
    uid = message.from_user.id
    url = message.text.replace("/short","",1).strip()
    if not url: return await bot.send_message(uid, "Usage: `/short <url>`")
    try:
        r = requests.post("https://cleanuri.com/api/v1/shorten", data={"url": url}, timeout=10)
        d = r.json()
        await bot.send_message(uid, f"🔗 **Shortened:** {d.get('result_url', 'Failed')}")
    except:
        await bot.send_message(uid, "❌ URL shortening failed")

# ─── /b64 ───

@bot.message_handler(commands=["b64"])
async def cmd_b64(message):
    await track_user(message)
    uid = message.from_user.id
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return await bot.send_message(uid, "Usage: `/b64 encode/decode <text>`")
    try:
        if parts[1] == "encode":
            await bot.send_message(uid, f"```\n{base64.b64encode(parts[2].encode()).decode()}\n```")
        elif parts[1] == "decode":
            await bot.send_message(uid, f"```\n{base64.b64decode(parts[2]).decode()}\n```")
    except Exception as e:
        await bot.send_message(uid, f"❌ Error: {e}")

# ─── /hash ───

@bot.message_handler(commands=["hash"])
async def cmd_hash(message):
    await track_user(message)
    uid = message.from_user.id
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return await bot.send_message(uid, "Usage: `/hash <type> <text>`\nTypes: md5, sha1, sha256, sha512")
    hmap = {"md5":hashlib.md5,"sha1":hashlib.sha1,"sha256":hashlib.sha256,"sha512":hashlib.sha512}
    if parts[1] not in hmap: return await bot.send_message(uid, f"Invalid. Use: {', '.join(hmap.keys())}")
    r = hmap[parts[1]](parts[2].encode()).hexdigest()
    await bot.send_message(uid, f"`{parts[1].upper()}:` `{r}`")

# ─── /pass ───

@bot.message_handler(commands=["pass"])
async def cmd_pass(message):
    await track_user(message)
    uid = message.from_user.id
    args = message.text.split()
    length = min(max(int(args[1]) if len(args)>1 else 16, 8), 64)
    count = min(max(int(args[2]) if len(args)>2 else 5, 1), 20)
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    out = f"{h('🔑 PASSWORD GENERATOR')}\n\n"
    for _ in range(count):
        out += f"`{''.join(secrets.choice(chars) for _ in range(length))}`\n"
    await bot.send_message(uid, out)

# ─── /uuid ───

@bot.message_handler(commands=["uuid"])
async def cmd_uuid(message):
    await track_user(message)
    uid = message.from_user.id
    await bot.send_message(uid, f"`UUIDv4:` `{_uuid.uuid4()}`")

# ─── /quote ───

@bot.message_handler(commands=["quote"])
async def cmd_quote(message):
    await track_user(message)
    uid = message.from_user.id
    try:
        r = requests.get("https://api.quotable.io/random", timeout=10)
        d = r.json()
        await bot.send_message(uid, f"💬 **\"{d['content']}\"**\n— {d['author']}")
    except:
        await bot.send_message(uid, f"💬 \"{FAKER.sentence()}\" — Anonymous")

# ─── /joke ───

@bot.message_handler(commands=["joke"])
async def cmd_joke(message):
    await track_user(message)
    uid = message.from_user.id
    try:
        r = requests.get("https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw", timeout=10)
        d = r.json()
        if d.get("type") == "single": await bot.send_message(uid, f"😂 {d['joke']}")
        else: await bot.send_message(uid, f"😂 {d['setup']}\n\n||{d['delivery']}||")
    except:
        await bot.send_message(uid, f"😂 {FAKER.sentence()}")

# ─── /fact ───

@bot.message_handler(commands=["fact"])
async def cmd_fact(message):
    await track_user(message)
    uid = message.from_user.id
    try:
        r = requests.get("https://uselessfacts.jsph.pl/random.json?language=en", timeout=10)
        await bot.send_message(uid, f"🧠 **Did you know?**\n{r.json()['text']}")
    except:
        await bot.send_message(uid, f"🧠 **Did you know?**\n{FAKER.sentence()}")

# ─── /style ───

@bot.message_handler(commands=["style"])
async def cmd_style(message):
    await track_user(message)
    uid = message.from_user.id
    text = message.text.replace("/style","",1).strip()
    if not text: return await bot.send_message(uid, "Usage: `/style <text>`")
    fancy = ""
    for c in text.lower():
        if 'a' <= c <= 'z': fancy += chr(0x1D5A0 + ord(c) - ord('a'))
        elif '0' <= c <= '9': fancy += chr(0x1D7CE + ord(c) - ord('0'))
        else: fancy += c
    await bot.send_message(uid, f"{h('📝 TEXT STYLES')}\n\n**Bold:** **{text}**\n**Italic:** *{text}*\n**Code:** `{text}`\n**Spoiler:** ||{text}||\n**Fancy:** {fancy}")

# ─── /tr ───

@bot.message_handler(commands=["tr"])
async def cmd_tr(message):
    await track_user(message)
    uid = message.from_user.id
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return await bot.send_message(uid, "Usage: `/tr <lang> <text>`\nExample: `/tr es Hello`")
    try:
        r = requests.get(f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(parts[2])}&langpair=en|{parts[1]}", timeout=10)
        t = r.json().get("responseData",{}).get("translatedText","Failed")
        await bot.send_message(uid, f"🌍 **Translation**\n`{parts[2]}` → **{t}**")
    except:
        await bot.send_message(uid, "❌ Translation failed")

# ─── /morse ───

@bot.message_handler(commands=["morse"])
async def cmd_morse(message):
    await track_user(message)
    uid = message.from_user.id
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return await bot.send_message(uid, "Usage: `/morse encode/decode <text>`")
    MORSE = {'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....',
             'I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.',
             'Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-',
             'Y':'-.--','Z':'--..','0':'-----','1':'.----','2':'..---','3':'...--','4':'....-',
             '5':'.....','6':'-....','7':'--...','8':'---..','9':'----.'}
    REV = {v:k for k,v in MORSE.items()}
    try:
        if parts[1]=="encode": r=' '.join(MORSE.get(c.upper(),c) for c in parts[2])
        elif parts[1]=="decode": r=''.join(REV.get(c,c) for c in parts[2].split())
        else: return await bot.send_message(uid, "Use 'encode' or 'decode'")
        await bot.send_message(uid, f"```\n{r[:4000]}\n```")
    except Exception as e:
        await bot.send_message(uid, f"❌ Error: {e}")

# ─── /convert ───

@bot.message_handler(commands=["convert"])
async def cmd_convert(message):
    await track_user(message)
    uid = message.from_user.id
    parts = message.text.split()
    if len(parts) < 4: return await bot.send_message(uid, "Usage: `/convert <amount> <from> <to>`\nExample: `/convert 100 USD EUR`")
    try:
        r = requests.get(f"https://api.frankfurter.app/latest?amount={float(parts[1])}&from={parts[2].upper()}&to={parts[3].upper()}", timeout=10)
        rate = r.json().get("rates",{}).get(parts[3].upper(),"N/A")
        await bot.send_message(uid, f"💰 **{parts[1]} {parts[2].upper()}** = **{rate} {parts[3].upper()}**")
    except:
        await bot.send_message(uid, "❌ Conversion failed")

# ─── /country ───

@bot.message_handler(commands=["country"])
async def cmd_country(message):
    await track_user(message)
    uid = message.from_user.id
    code = message.text.replace("/country","",1).strip().upper()
    if not code: return await bot.send_message(uid, "Usage: `/country <code>`\nExample: `/country PK`")
    try:
        r = requests.get(f"https://restcountries.com/v3.1/alpha/{code}", timeout=10)
        d = r.json()[0]
        out = f"{h(f'🌍 {d[\"name\"][\"common\"]}')}\n\n"
        out += f"`Official:` {d['name']['official']}\n`Capital:` {d.get('capital',['N/A'])[0]}\n`Region:` {d.get('region','N/A')}\n`Population:` {d.get('population','N/A'):,}\n`Area:` {d.get('area','N/A'):,} km²\n`Currency:` {', '.join(d.get('currencies',{}).keys())}\n`Languages:` {', '.join(d.get('languages',{}).values())}"
        if d.get('flags',{}).get('png'):
            await bot.send_photo(uid, d['flags']['png'], caption=out)
        else:
            await bot.send_message(uid, out)
    except:
        await bot.send_message(uid, f"❌ No country for '{code}'")

# ─── ADMIN COMMANDS ───

@bot.message_handler(commands=["admin"])
async def cmd_admin(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    stats = db_one("SELECT COUNT(*), COALESCE(SUM(total_commands),0) FROM users") or (0,0)
    today = db_one("SELECT COUNT(*) FROM users WHERE date(last_seen)=date('now')") or (0,)
    text = f"{h('⚙ ADMIN PANEL')}\n\n"
    text += f"`Total Users:` **{stats[0]}**\n`Active Today:` **{today[0]}**\n`Total Commands:` **{stats[1]}**\n`Developer:` {DEV_USERNAME}\n\n"
    text += "**Commands:**\n`/users` — List all users\n`/track [id]` — Track user\n`/broadcast [msg]` — Message all\n`/ban [id]`\n`/unban [id]`\n`/logs` — Command logs\n`/cclogs` — CC logs\n`/cookie_logs` — Cookie logs"
    await bot.send_message(uid, text)

@bot.message_handler(commands=["users"])
async def cmd_users(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    users = db_fetch("SELECT user_id,username,first_name,last_seen,country,total_commands,is_banned,is_premium FROM users ORDER BY last_seen DESC LIMIT 50")
    text = f"{h('👥 ALL USERS')}\n\n"
    for u in users:
        st = "🔴 BANNED" if u[6] else ("⭐ PREM" if u[7] else "🟢")
        text += f"`{u[0]}` @{u[1] or 'N/A'} | {u[2] or 'N/A'} | {u[4]} | {u[5]}cmds | {st}\n"
        if len(text) > 3500: break
    await bot.send_message(uid, text[:4000])

@bot.message_handler(commands=["track"])
async def cmd_track(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    args = message.text.split()
    if len(args) < 2: return await bot.send_message(uid, "Usage: `/track <user_id>`")
    u = db_one("SELECT * FROM users WHERE user_id=?", (int(args[1]),))
    if not u: return await bot.send_message(uid, f"❌ User {args[1]} not found")
    text = f"{h(f'🔍 TRACKING USER: {args[1]}')}\n\n"
    text += f"`ID:` {u[0]}\n`Username:` @{u[1] or 'N/A'}\n`Name:` {u[2] or 'N/A'} {u[3] or ''}\n`Joined:` {u[8]}\n`Last Seen:` {u[9]}\n`IP:` {u[10]}\n`Country:` {u[11]}\n`City:` {u[12]}\n`Premium:` {'Yes' if u[5] else 'No'}\n`Banned:` {'Yes' if u[7] else 'No'}\n`Commands:` {u[14] or 0}\n`AI Quota:` {u[13]}"
    cmds = db_fetch("SELECT command,args,used_at FROM command_logs WHERE user_id=? ORDER BY used_at DESC LIMIT 5", (int(args[1]),))
    if cmds:
        text += "\n\n**Recent Commands:**\n"
        for c in cmds: text += f"`/{c[0]}` {c[1] or ''} — {c[2][:16]}\n"
    await bot.send_message(uid, text)

@bot.message_handler(commands=["broadcast"])
async def cmd_broadcast(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    msg = message.text.replace("/broadcast","",1).strip()
    if not msg: return await bot.send_message(uid, "Usage: `/broadcast <message>`")
    users = db_fetch("SELECT user_id FROM users WHERE is_banned=0")
    sent = 0
    for u in users:
        try:
            await bot.send_message(u[0], f"📢 **BROADCAST FROM DEV**\n\n{msg}")
            sent += 1
            await asyncio.sleep(0.05)
        except: pass
    await bot.send_message(uid, f"✅ Sent to {sent}/{len(users)} users")

@bot.message_handler(commands=["ban"])
async def cmd_ban(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    args = message.text.split()
    if len(args) < 2: return await bot.send_message(uid, "Usage: `/ban <user_id>`")
    db_exec("UPDATE users SET is_banned=1 WHERE user_id=?", (int(args[1]),))
    await bot.send_message(uid, f"✅ User {args[1]} banned")

@bot.message_handler(commands=["unban"])
async def cmd_unban(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    args = message.text.split()
    if len(args) < 2: return await bot.send_message(uid, "Usage: `/unban <user_id>`")
    db_exec("UPDATE users SET is_banned=0 WHERE user_id=?", (int(args[1]),))
    await bot.send_message(uid, f"✅ User {args[1]} unbanned")

@bot.message_handler(commands=["logs"])
async def cmd_logs(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    logs = db_fetch("SELECT user_id,command,args,used_at FROM command_logs ORDER BY used_at DESC LIMIT 20")
    text = f"{h('📋 COMMAND LOGS')}\n\n"
    for l in logs: text += f"`{l[0]}` → /{l[1]} {l[2] or ''} | {l[3][:19]}\n"
    await bot.send_message(uid, text[:4000])

@bot.message_handler(commands=["cclogs"])
async def cmd_cclogs(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    logs = db_fetch("SELECT user_id,cc_number,brand,result,checked_at FROM cc_logs ORDER BY checked_at DESC LIMIT 20")
    text = f"{h('💳 CC LOGS')}\n\n"
    for l in logs:
        text += f"`{l[0]}` | {l[1][:12]}...{l[1][-4:]} | {l[2]} | {l[3][:30]} | {l[4][:19]}\n"
    await bot.send_message(uid, text[:4000])

@bot.message_handler(commands=["cookie_logs"])
async def cmd_cookie_logs(message):
    uid = message.from_user.id
    if uid != DEV_ID: return await bot.send_message(uid, "⛔ ACCESS DENIED")
    logs = db_fetch("SELECT user_id,source,created_at FROM cookie_logs ORDER BY created_at DESC LIMIT 20")
    text = f"{h('🍪 COOKIE LOGS')}\n\n"
    for l in logs:
        text += f"`{l[0]}` | {l[1][:40]} | {l[2][:19]}\n"
    await bot.send_message(uid, text[:4000])

# ─── Catch-all: text messages go to AI ───

@bot.message_handler(func=lambda m: True, content_types=['text'])
async def handle_all_text(message):
    uid = message.from_user.id
    text = message.text.strip()
    if text.startswith('/'): return
    await track_user(message)
    msg = await bot.send_message(uid, f"`[ AI ] Processing... ████░░░░░░ 40%`")
    answer = await ai_ask(text)
    await bot.edit_message_text(f"🧠 **AI RESPONSE** 🧠\n\n{answer}", uid, msg.message_id)

# ═══════════════════════════════════════════════════════════════
# 🎯  CALLBACK HANDLERS (Inline Menus)
# ═══════════════════════════════════════════════════════════════

MENUS = {
    "menu_recon": (
        f"{h('💻 RECONNAISSANCE')}\n\n"
        f"`/ip [IP]` — GeoIP location\n"
        f"`/dns [domain]` — DNS records\n"
        f"`/whois [domain]` — WHOIS lookup\n"
        f"`/port [host] [port]` — Port scanner"
    ),
    "menu_cc": (
        f"{h('💳 CC CHECKER')}\n\n"
        f"Check credit card validity:\n"
        f"`/cc [card] [mm] [yy] [cvv]`\n\n"
        f"Example: `/cc 4111111111111111 12 26 123`\n\n"
        f"Features: Luhn, BIN lookup, brand detection, expiry, CVV, gateway"
    ),
    "menu_cookie": (
        f"{h('🍪 COOKIE AGENT')}\n\n"
        f"Retrieve cookies from any URL:\n"
        f"`/cookies [url]` — Fetch from any site\n"
        f"`/netflix` — Netflix cookies archive\n\n"
        f"Powered by @mianmanan270"
    ),
    "menu_fake": (
        f"{h('🎭 FAKE DATA GENERATOR')}\n\n"
        f"`/address [country]` — Full identity\n"
        f"`/iban [country]` — Fake IBAN\n\n"
        f"Countries: pk, us, uk, de, fr, sa, ae, in, au, ca, jp, br, ru, it, es, tr, nl"
    ),
    "menu_ai": (
        f"{h('🤖 AI ASSISTANT')}\n\n"
        f"`/ask [question]` — Ask AI anything\n"
        f"Or just type any message directly!\n\n"
        f"GPT-4o-mini + DuckDuckGo fallback"
    ),
    "menu_lookup": (
        f"{h('🌐 LOOKUP TOOLS')}\n\n"
        f"`/wiki [topic]` — Wikipedia\n"
        f"`/weather [city]` — Weather\n"
        f"`/crypto [coin]` — Crypto price\n"
        f"`/country [code]` — Country info\n"
        f"`/convert [amt] [f] [t]` — Currency\n"
        f"`/tr [lang] [text]` — Translate"
    ),
    "menu_help": (
        f"{h('📝 HELP')}\n\n"
        f"Type `/help` for the complete command list!"
    ),
    "admin_panel": (
        f"{h('⚙ ADMIN PANEL')}\n\n"
        f"`/users` — List all users\n"
        f"`/track [id]` — Track user (name, IP, location)\n"
        f"`/broadcast [msg]` — Message all users\n"
        f"`/ban [id]` — Ban user\n"
        f"`/unban [id]` — Unban user\n"
        f"`/logs` — Command logs\n"
        f"`/cclogs` — CC check logs\n"
        f"`/cookie_logs` — Cookie logs"
    ),
}

@bot.callback_query_handler(func=lambda c: True)
async def handle_callbacks(call):
    uid = call.from_user.id
    data = call.data
    
    if data in MENUS:
        try:
            await bot.edit_message_text(MENUS[data], uid, call.message.message_id, reply_markup=back_kb())
        except:
            await bot.send_message(uid, MENUS[data], reply_markup=back_kb())
    
    elif data == "menu_main":
        text = (
            f"```\n{'█'*52}\n{'█'*10}  MATRIX INITIALIZED  {'█'*10}\n{'█'*52}\n```\n"
            f"{h(f'{DEV_USERNAME} ULTIMATE SUITE')}\n\n"
            f"`SYSTEM:` ACTIVE | MODE: WHITE-CARD\n"
            f"`USER:` {call.from_user.first_name}\n"
            f"`DATE:` {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("💻 RECON", callback_data="menu_recon"),
            types.InlineKeyboardButton("💳 CC CHECK", callback_data="menu_cc"),
            types.InlineKeyboardButton("🍪 COOKIES", callback_data="menu_cookie"),
            types.InlineKeyboardButton("🎭 FAKE DATA", callback_data="menu_fake"),
            types.InlineKeyboardButton("🤖 AI", callback_data="menu_ai"),
            types.InlineKeyboardButton("🌐 LOOKUP", callback_data="menu_lookup"),
        )
        kb.add(types.InlineKeyboardButton("📝 HELP", callback_data="menu_help"))
        if uid == DEV_ID:
            kb.add(types.InlineKeyboardButton("⚙ ADMIN PANEL", callback_data="admin_panel"))
        try:
            await bot.edit_message_text(text, uid, call.message.message_id, reply_markup=kb)
        except:
            await bot.send_message(uid, text, reply_markup=kb)

# ═══════════════════════════════════════════════════════════════
# 🌐  HEALTH SERVER
# ═══════════════════════════════════════════════════════════════

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK - HackerAI Ultimate Suite v3.0 - Running")
    def log_message(self, *a): pass

def _start_health():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(("0.0.0.0", port), _HealthHandler).serve_forever()

# ═══════════════════════════════════════════════════════════════
# 🚀  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    logger = logging.getLogger(__name__)
    
    threading.Thread(target=_start_health, daemon=True).start()
    logger.info(f"Health server on port {os.environ.get('PORT', 8080)}")
    logger.info(f"{DEV_USERNAME} HackerAI Suite starting...")
    logger.info("=" * 60)
    logger.info("  HACKERAI ULTIMATE SUITE v3.0")
    logger.info("  Developer: @mianmanan270")
    logger.info("  Status: ACTIVE - READY")
    logger.info("=" * 60)
    
    while True:
        try:
            await bot.infinity_polling(skip_pending=True, timeout=30)
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
    
