import sqlite3
import random
import os
import re
import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ========== تنظیمات ==========
BOT_TOKEN = "636975564:mjAvpfwy7qT5wR24o8WLEdHAqLtXq6Tw9Ok"
ADMIN_ID = 1621801431
ADMIN_USERNAME = "@alonewolfinworld"
CHANNEL_USERNAME = "@channelofworldwar"
GROUP_USERNAME = "@groupofworldwar"
CARD_NUMBER = "6221-0612-2285-1588"
CARD_OWNER = "نام مالک کارت ، محمد جعفری"
BOT_USERNAME = "@asnoasnbot"
DB_NAME = "war_bot_data_new.db"
# ============================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.path.exists(DB_NAME):
    print("🆕 اولین اجرا - دیتابیس جدید ساخته میشه")
else:
    print("📂 دیتابیس قبلی پیدا شد - اطلاعات حفظ میشه")

conn = sqlite3.connect(DB_NAME, check_same_thread=False)
cursor = conn.cursor()

cursor.executescript('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, username TEXT UNIQUE, first_name TEXT,
    money INTEGER DEFAULT 1000, diamond INTEGER DEFAULT 10,
    bank_money INTEGER DEFAULT 0, bank_level INTEGER DEFAULT 0, bank_interest REAL DEFAULT 0.05,
    wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0,
    last_daily TEXT, clan TEXT DEFAULT 'بدون کلن',
    power INTEGER DEFAULT 100, defense INTEGER DEFAULT 50,
    soldier INTEGER DEFAULT 10, tank INTEGER DEFAULT 0, plane INTEGER DEFAULT 0,
    missile INTEGER DEFAULT 0, robot INTEGER DEFAULT 0,
    soldier_elite INTEGER DEFAULT 0, tank_advanced INTEGER DEFAULT 0, plane_stealth INTEGER DEFAULT 0,
    mine_coin_level INTEGER DEFAULT 0, mine_diamond_level INTEGER DEFAULT 0,
    mine_oil_level INTEGER DEFAULT 0, mine_gold_level INTEGER DEFAULT 0, mine_uranium_level INTEGER DEFAULT 0,
    mine_accumulated INTEGER DEFAULT 0,
    atomic_bomb INTEGER DEFAULT 0, shield_item INTEGER DEFAULT 0, power_potion INTEGER DEFAULT 0,
    weekly_wins INTEGER DEFAULT 0,
    has_username INTEGER DEFAULT 0, registered_date TEXT,
    vip_level INTEGER DEFAULT 0, vip_expire TEXT, username_color TEXT DEFAULT 'white',
    name_change_count INTEGER DEFAULT 0,
    league TEXT DEFAULT 'برنز',
    referral_code TEXT, referred_by INTEGER, referral_count INTEGER DEFAULT 0,
    citizens INTEGER DEFAULT 50, houses INTEGER DEFAULT 0, apartments INTEGER DEFAULT 0,
    towers INTEGER DEFAULT 0, skyscrapers INTEGER DEFAULT 0,
    spin_free_used INTEGER DEFAULT 0, spin_paid_remaining INTEGER DEFAULT 0, last_spin_date TEXT,
    revenge_list TEXT DEFAULT '', shield_until TEXT,
    last_active TEXT, power_history TEXT DEFAULT '',
    consecutive_wins INTEGER DEFAULT 0, last_win_time TEXT,
    poison_until TEXT, cursed_until TEXT,
    badges TEXT DEFAULT '', riddles_solved INTEGER DEFAULT 0,
    last_riddle_date TEXT,
    loan_amount INTEGER DEFAULT 0, loan_due TEXT
);

CREATE TABLE IF NOT EXISTS clans (
    clan_name TEXT PRIMARY KEY, owner_id INTEGER,
    total_power INTEGER DEFAULT 0, members_count INTEGER DEFAULT 1,
    wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, level INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS clan_members (user_id INTEGER PRIMARY KEY, clan_name TEXT, join_date TEXT);
CREATE TABLE IF NOT EXISTS attacks (id INTEGER PRIMARY KEY AUTOINCREMENT, attacker_id INTEGER, defender_id INTEGER, attacker_name TEXT, defender_name TEXT, attacker_won INTEGER, loot INTEGER, attack_date TEXT);
CREATE TABLE IF NOT EXISTS black_market (id INTEGER PRIMARY KEY AUTOINCREMENT, seller_id INTEGER, seller_name TEXT, item_name TEXT, price INTEGER, amount INTEGER, listed_date TEXT);
CREATE TABLE IF NOT EXISTS market_prices (asset_name TEXT PRIMARY KEY, price INTEGER, last_update TEXT);
CREATE TABLE IF NOT EXISTS price_history (id INTEGER PRIMARY KEY AUTOINCREMENT, asset_name TEXT, price INTEGER, recorded_date TEXT);
CREATE TABLE IF NOT EXISTS user_assets (user_id INTEGER, asset_name TEXT, amount REAL, avg_buy_price INTEGER, PRIMARY KEY (user_id, asset_name));
CREATE TABLE IF NOT EXISTS riddles (id INTEGER PRIMARY KEY AUTOINCREMENT, question TEXT, answer TEXT, used_date TEXT);
CREATE TABLE IF NOT EXISTS wanted_list (user_id INTEGER PRIMARY KEY, username TEXT, power INTEGER, listed_date TEXT, expires TEXT);
''')
conn.commit()

try: cursor.execute("ALTER TABLE users ADD COLUMN last_riddle_date TEXT"); conn.commit()
except: pass
try: cursor.execute("ALTER TABLE users ADD COLUMN loan_amount INTEGER DEFAULT 0"); conn.commit()
except: pass
try: cursor.execute("ALTER TABLE users ADD COLUMN loan_due TEXT"); conn.commit()
except: pass

# ====================== تنظیمات ======================
MINE_TYPES = {
    "coin": {"cost": 500, "income": 50, "emoji": "🪙", "name": "سکه", "key": "mine_coin_level"},
    "diamond": {"cost": 2000, "income": 200, "emoji": "💎", "name": "الماس", "key": "mine_diamond_level"},
    "oil": {"cost": 5000, "income": 500, "emoji": "🛢️", "name": "نفت", "key": "mine_oil_level"},
    "gold": {"cost": 10000, "income": 1000, "emoji": "🥇", "name": "طلا", "key": "mine_gold_level"},
    "uranium": {"cost": 25000, "income": 2500, "emoji": "☢️", "name": "اورانیوم", "key": "mine_uranium_level"},
}

SPECIAL_ITEMS_RIAL = {
    "بمب اتم": {"price": 50000, "power": 500, "emoji": "💣", "desc": "قدرت حمله ۵۰۰+"},
    "سپر نامرئی": {"price": 30000, "defense": 400, "emoji": "🛡️", "desc": "دفاع ۴۰۰+"},
    "معجون قدرت": {"price": 20000, "power": 200, "defense": 100, "emoji": "🧪", "desc": "۲۰۰ قدرت + ۱۰۰ دفاع"},
    "موشک قاره‌پیما": {"price": 80000, "power": 800, "emoji": "🚀", "desc": "حمله ویرانگر ۸۰۰+"},
    "گنبد پلاسمایی": {"price": 100000, "defense": 1200, "emoji": "🔮", "desc": "دفاع مطلق ۱۲۰۰+"},
    "لشکر اجاره‌ای": {"price": 40000, "soldier": 50, "emoji": "👥", "desc": "۵۰ سرباز"},
    "زهر": {"price": 100000, "poison": 24, "emoji": "🧪", "desc": "قدرت دشمن ۱۰٪ کم"},
}

VIP_LEVELS = {
    1: {"name": "🥉 برنزی", "price": 30000, "duration_days": 30, "power_bonus": 50, "daily_bonus": 500},
    2: {"name": "🥈 نقره‌ای", "price": 70000, "duration_days": 30, "power_bonus": 150, "daily_bonus": 1500},
    3: {"name": "🥇 طلایی", "price": 150000, "duration_days": 30, "power_bonus": 400, "daily_bonus": 4000},
    4: {"name": "💎 الماسی", "price": 300000, "duration_days": 30, "power_bonus": 1000, "daily_bonus": 10000},
    5: {"name": "👑 افسانه‌ای", "price": 600000, "duration_days": 60, "power_bonus": 2500, "daily_bonus": 25000},
}

LEAGUES = {
    "برنز": {"min_power": 0, "max_power": 500, "emoji": "🥉", "citizen_bonus": 0},
    "نقره": {"min_power": 500, "max_power": 2000, "emoji": "🥈", "citizen_bonus": 25},
    "طلا": {"min_power": 2000, "max_power": 5000, "emoji": "🥇", "citizen_bonus": 50},
    "الماس": {"min_power": 5000, "max_power": 15000, "emoji": "💎", "citizen_bonus": 100},
    "افسانه‌ای": {"min_power": 15000, "max_power": 999999, "emoji": "👑", "citizen_bonus": 200},
}

MARKET_ASSETS = {
    "نقره": {"price": 100, "emoji": "🥈"}, "طلا": {"price": 500, "emoji": "🥇"},
    "الماس_بازار": {"price": 2000, "emoji": "💎"}, "نفت": {"price": 1000, "emoji": "🛢️"},
    "بیت_کوین": {"price": 5000, "emoji": "₿"}, "اتریوم": {"price": 3000, "emoji": "🪙"},
    "دوج_کوین": {"price": 50, "emoji": "🐕"}, "کاردانو": {"price": 200, "emoji": "⚡"},
    "ریپل": {"price": 150, "emoji": "🌐"}, "سولانا": {"price": 800, "emoji": "🔗"},
    "پولکادات": {"price": 400, "emoji": "🟣"}, "بایننس": {"price": 2500, "emoji": "🔶"},
    "سوشی": {"price": 100, "emoji": "🍣"}, "متیک": {"price": 300, "emoji": "🌽"},
    "شیبا": {"price": 10, "emoji": "🦊"},
}

BUILDINGS = {"home": {"cost": 500, "citizens": 10, "emoji": "🏠", "name": "خانه"}, "apartment": {"cost": 2000, "citizens": 30, "emoji": "🏘️", "name": "آپارتمان"}, "tower": {"cost": 8000, "citizens": 100, "emoji": "🏢", "name": "برج"}, "skyscraper": {"cost": 30000, "citizens": 500, "emoji": "🏙️", "name": "آسمان‌خراش"}}
UNITS = {"soldier": {"cost": 200, "power": 25, "emoji": "💂", "name": "سرباز"}, "tank": {"cost": 1000, "power": 100, "emoji": "🪖", "name": "تانک"}, "plane": {"cost": 5000, "power": 300, "emoji": "✈️", "name": "هواپیما"}, "missile": {"cost": 10000, "power": 700, "emoji": "🚀", "name": "موشک"}, "robot": {"cost": 25000, "power": 1500, "emoji": "🤖", "name": "ربات"}}
DEFENSE_ITEMS = {"wall": {"cost": 500, "defense": 30, "emoji": "🧱", "name": "دیوار"}, "tower": {"cost": 2000, "defense": 100, "emoji": "🗼", "name": "برج"}, "dome": {"cost": 8000, "defense": 350, "emoji": "🛡️", "name": "گنبد"}, "fortress": {"cost": 20000, "defense": 800, "emoji": "🏰", "name": "قلعه"}}
ELITE_ITEMS = {"elite_soldier": {"cost": 500, "power": 50, "from": "soldier", "to": "soldier_elite", "emoji": "💂‍♂️", "name": "سرباز نخبه"}, "elite_tank": {"cost": 2000, "power": 200, "from": "tank", "to": "tank_advanced", "emoji": "🪖", "name": "تانک پیشرفته"}, "elite_plane": {"cost": 8000, "power": 600, "from": "plane", "to": "plane_stealth", "emoji": "✈️", "name": "رادارگریز"}}
SPIN_PRIZES = [{"name": "۱۰۰ سکه", "type": "money", "amount": 100, "emoji": "💰", "chance": 30}, {"name": "۵۰۰ سکه", "type": "money", "amount": 500, "emoji": "💵", "chance": 20}, {"name": "۱۰۰۰ سکه", "type": "money", "amount": 1000, "emoji": "💎", "chance": 15}, {"name": "۵ الماس", "type": "diamond", "amount": 5, "emoji": "💠", "chance": 12}, {"name": "۲۰ الماس", "type": "diamond", "amount": 20, "emoji": "💠", "chance": 8}, {"name": "بمب اتم", "type": "item", "item_key": "atomic_bomb", "amount": 1, "emoji": "💣", "chance": 7}, {"name": "جکپات ۵۰۰۰", "type": "money", "amount": 5000, "emoji": "🎰", "chance": 3}]
NATURAL_DISASTERS = [{"name": "آتشفشان", "damage": 0.1, "emoji": "🌋"}, {"name": "سونامی", "damage": 0.15, "emoji": "🌊"}, {"name": "طوفان", "damage": 0.05, "emoji": "🌪️"}, {"name": "زلزله", "damage": 0.12, "emoji": "💥"}]
RIDDLES_LIST = [{"q": "آن چیست که هرچه بیشتر برداریم بزرگتر می‌شود؟", "a": "چاله"}, {"q": "کدام ماه ۲۸ روز دارد؟", "a": "همه"}, {"q": "آن چیست که یک چشم دارد اما نمی‌بیند؟", "a": "سوزن"}, {"q": "چه چیزی پر از سوراخ است اما آب را نگه می‌دارد؟", "a": "اسفنج"}, {"q": "آن چیست که مال توست ولی دیگران بیشتر استفاده می‌کنند؟", "a": "اسم"}, {"q": "آن چیست که هرچه بیشتر باشد کمتر می‌بینی؟", "a": "تاریکی"}, {"q": "آن چیست که می‌تواند دور دنیا سفر کند بدون اینکه گوشه‌ای تکان بخورد؟", "a": "تمبر"}, {"q": "آن چیست که بالای سرت است ولی سایه ندارد؟", "a": "آسمان"}]
BANK_LEVELS = {1: {"cost": 1000, "interest": 0.05}, 2: {"cost": 5000, "interest": 0.08}, 3: {"cost": 15000, "interest": 0.12}, 4: {"cost": 50000, "interest": 0.18}, 5: {"cost": 150000, "interest": 0.25}}
OTHER_SERVICES = {"تغییر اسم": {"price": 10000}, "اسم رنگی": {"price": 100000}, "شارژ سکه ۱۰۰۰": {"price": 20000, "money": 1000}, "شارژ سکه ۵۰۰۰": {"price": 80000, "money": 5000}, "شارژ سکه ۱۰۰۰۰": {"price": 150000, "money": 10000}, "پک طلایی": {"price": 120000, "items": {"بمب اتم": 3, "سپر نامرئی": 2}}, "پک الماس": {"price": 250000, "items": {"بمب اتم": 5, "معجون قدرت": 3}}}

def get_user(user_id=None, username=None):
    if username: cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    elif user_id: cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    else: return None
    row = cursor.fetchone()
    return dict(zip([d[0] for d in cursor.description], row)) if row else None

def create_user(user_id, first_name):
    ref = f"REF{user_id}{random.randint(100,999)}"
    cursor.execute("INSERT INTO users (user_id, first_name, registered_date, referral_code, last_active) VALUES (?, ?, ?, ?, ?)", (user_id, first_name, datetime.now().isoformat(), ref, datetime.now().isoformat()))
    conn.commit()
    return get_user(user_id=user_id)

def update_user(user_id, **kwargs):
    for k, v in kwargs.items(): cursor.execute(f"UPDATE users SET {k} = ? WHERE user_id = ?", (v, user_id))
    conn.commit()

def set_username(user_id, username):
    cursor.execute("UPDATE users SET username = ?, has_username = 1 WHERE user_id = ?", (username, user_id)); conn.commit()

def username_exists(u): return cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (u,)).fetchone()[0] > 0
def search_users(q): cursor.execute("SELECT user_id, username, power, defense FROM users WHERE username LIKE ? AND is_banned = 0 AND has_username = 1", (f"%{q}%",)); return cursor.fetchall()
def get_all_usernames(): cursor.execute("SELECT user_id, username, power, defense FROM users WHERE is_banned = 0 AND has_username = 1"); return cursor.fetchall()
def add_revenge(uid, aid):
    u = get_user(user_id=uid); lst = [x for x in (u["revenge_list"] or "").split(",") if x]
    if str(aid) not in lst: lst.append(str(aid))
    update_user(uid, revenge_list=",".join(lst))
def remove_revenge(uid, aid):
    u = get_user(user_id=uid); lst = [x for x in (u["revenge_list"] or "").split(",") if x]
    lst = [x for x in lst if x != str(aid)]; update_user(uid, revenge_list=",".join(lst) if lst else "")
def get_revenge_list(uid):
    u = get_user(user_id=uid); return [int(x) for x in u["revenge_list"].split(",") if x] if u and u["revenge_list"] else []
def get_leaderboard(limit=10):
    cursor.execute("SELECT user_id, username, wins, money, power, vip_level, username_color, league FROM users WHERE is_banned = 0 AND has_username = 1 ORDER BY power DESC LIMIT ?", (limit,)); return cursor.fetchall()
def get_mine_income(ud): return sum(ud.get(d["key"], 0) * d["income"] for d in MINE_TYPES.values())
async def announce_to_channel(context, text):
    try: await context.bot.send_message(CHANNEL_USERNAME, text)
    except: pass
async def notify_admin(context, ud, pt, item, amt, price):
    try: await context.bot.send_message(ADMIN_ID, f"🛒 **خرید**\n👤 {ud['username']}\n📦 {pt}\n🎁 {item}\n💰 {price:,} ریال\n✅ `/confirm {ud['user_id']} {item} {amt}`")
    except: pass

def get_main_keyboard(user_id=None):
    k = [
        [KeyboardButton("⚔️ حمله"), KeyboardButton("💀 انتقام‌ها")],
        [KeyboardButton("💰 موجودی"), KeyboardButton("🏆 لیدربورد")],
        [KeyboardButton("🛒 فروشگاه"), KeyboardButton("💎 فروشگاه ویژه")],
        [KeyboardButton("👑 VIP"), KeyboardButton("🏭 معدن‌ها")],
        [KeyboardButton("🏦 بانک"), KeyboardButton("🏪 بازار سیاه")],
        [KeyboardButton("🎰 کازینو"), KeyboardButton("🏰 کلن من")],
        [KeyboardButton("👥 شهروندان"), KeyboardButton("🏗️ ساختمان‌ها")],
        [KeyboardButton("🎰 چرخ شانس"), KeyboardButton("🔗 رفرال")],
        [KeyboardButton("🎁 هدیه دادن"), KeyboardButton("🎁 جایزه روزانه")],
        [KeyboardButton("📜 بیانیه"), KeyboardButton("ℹ️ اطلاعات من")],
        [KeyboardButton("📊 نمودار قدرت"), KeyboardButton("📚 آموزش")],
        [KeyboardButton("📞 پشتیبانی"), KeyboardButton("👑 پادشاه هفته")],
        [KeyboardButton("📈 بازار سرمایه"), KeyboardButton("🧠 معما")],
        [KeyboardButton("🌟 نشان‌ها"), KeyboardButton("🏦 وام")],
        [KeyboardButton(f"📢 کانال"), KeyboardButton(f"👥 گروه")],
    ]
    if user_id == ADMIN_ID:
        k.append([KeyboardButton("👥 کاربران")])
        k.append([KeyboardButton("🚫 بن"), KeyboardButton("✅ آنبن")])
        k.append([KeyboardButton("💸 سکه دادن"), KeyboardButton("💎 الماس دادن")])
        k.append([KeyboardButton("🎁 دادن آیتم"), KeyboardButton("✅ تایید خرید")])
    return ReplyKeyboardMarkup(k, resize_keyboard=True)

async def auto_disaster(context):
    d = random.choice(NATURAL_DISASTERS)
    cursor.execute("SELECT user_id, money FROM users WHERE is_banned = 0 AND has_username = 1")
    users = cursor.fetchall()
    if not users: return
    aff = random.sample(users, min(10, len(users)))
    lst = []
    for uid, money in aff:
        dmg = int(money * d["damage"])
        if dmg > 0: update_user(uid, money=max(0, money - dmg)); lst.append(f"{get_user(user_id=uid)['username']}: -{dmg:,}")
    if lst: await announce_to_channel(context, f"{d['emoji']} **{d['name']}**!\n" + "\n".join(lst[:5]))

async def accumulate_mines(context):
    cursor.execute("SELECT user_id FROM users WHERE has_username = 1 AND is_banned = 0")
    for (uid,) in cursor.fetchall():
        ud = get_user(user_id=uid); income = get_mine_income(ud)
        if income > 0: update_user(uid, mine_accumulated=ud["mine_accumulated"] + income)

async def bank_interest_auto(context):
    cursor.execute("SELECT user_id, bank_money, bank_interest FROM users WHERE bank_money > 0 AND has_username = 1 AND is_banned = 0")
    for uid, bm, bi in cursor.fetchall():
        interest = int(bm * bi)
        if interest > 0: update_user(uid, bank_money=bm + interest)

async def update_market(context):
    now = datetime.now()
    for an, d in MARKET_ASSETS.items():
        cur = d["price"]; ch = random.uniform(-0.3, 0.3); np = max(1, int(cur * (1 + ch)))
        cursor.execute("INSERT OR REPLACE INTO market_prices VALUES (?, ?, ?)", (an, np, now.isoformat()))
        MARKET_ASSETS[an]["price"] = np
        cursor.execute("INSERT INTO price_history (asset_name, price, recorded_date) VALUES (?, ?, ?)", (an, np, now.isoformat()))
    cursor.execute("DELETE FROM price_history WHERE recorded_date < ?", ((now - timedelta(hours=4)).isoformat(),)); conn.commit()

async def update_wanted(context):
    cursor.execute("DELETE FROM wanted_list")
    cursor.execute("SELECT user_id, username, power FROM users WHERE is_banned = 0 AND has_username = 1 ORDER BY RANDOM() LIMIT 3")
    for uid, un, p in cursor.fetchall(): cursor.execute("INSERT INTO wanted_list VALUES (?, ?, ?, ?, ?)", (uid, un, p, datetime.now().isoformat(), (datetime.now() + timedelta(hours=2)).isoformat()))
    conn.commit()
    cursor.execute("SELECT username, power FROM wanted_list"); wanted = cursor.fetchall()
    if wanted:
        txt = "🔴 **تحت تعقیب‌های جدید!**\n\n"
        for un, p in wanted: txt += f"👤 {un} | ⚡{p}\n"
        txt += "\n💰 جایزه: ۲ برابر غارت!\n⏰ فرصت: ۲ ساعت"; await announce_to_channel(context, txt)

async def daily_riddle(context):
    r = random.choice(RIDDLES_LIST)
    cursor.execute("INSERT INTO riddles (question, answer, used_date) VALUES (?, ?, ?)", (r["q"], r["a"], datetime.now().strftime("%Y-%m-%d"))); conn.commit()
    await announce_to_channel(context, f"🧠 **معمای امروز:**\n\n{r['q']}\n\n💰 اول: ۱۰,۰۰۰ سکه + ۱۰ الماس\n🥈 دوم: ۵,۰۰۰ + ۵\n🥉 سوم: ۲,۰۰۰ + ۲\n📝 جواب رو به ربات پیام بده!")

async def fireworks(context):
    now = datetime.now()
    if now.hour == 21 and now.minute == 0:
        cursor.execute("SELECT user_id FROM users WHERE has_username = 1 AND is_banned = 0 AND last_active > ?", ((now - timedelta(hours=1)).isoformat(),))
        for (uid,) in cursor.fetchall(): update_user(uid, money=get_user(user_id=uid)["money"] + 5000, diamond=get_user(user_id=uid)["diamond"] + 5)
        await announce_to_channel(context, f"🎆🎆🎆\n🎆 آتش‌بازی شبانه! 🎆\n🎆🎆🎆\n\n💰 ۵,۰۰۰ سکه + 💎 ۵ الماس\n✨ به همه آنلاین‌ها!")

async def weekly_king(context):
    if datetime.now().weekday() == 5:
        cursor.execute("SELECT user_id, username, weekly_wins FROM users ORDER BY weekly_wins DESC LIMIT 1"); king = cursor.fetchone()
        if king: update_user(king[0], diamond=get_user(user_id=king[0])["diamond"] + 100); await announce_to_channel(context, f"👑 **پادشاه هفته!**\n🏆 {king[1]}\n⚔️ {king[2]} برد\n🎁 ۱۰۰ الماس!")
        cursor.execute("UPDATE users SET weekly_wins = 0"); conn.commit()

async def collect_taxes(context):
    cursor.execute("SELECT user_id, citizens FROM users WHERE has_username = 1 AND is_banned = 0")
    for uid, c in cursor.fetchall():
        tax = int(c * 0.5)
        if tax > 0: update_user(uid, money=get_user(user_id=uid)["money"] + tax)

async def remind_inactive(context):
    threshold = (datetime.now() - timedelta(hours=24)).isoformat()
    cursor.execute("SELECT user_id, username FROM users WHERE has_username = 1 AND is_banned = 0 AND last_active < ?", (threshold,))
    for uid, un in cursor.fetchall():
        try: await context.bot.send_message(uid, f"🔔 {un} جان!\n۲۴ ساعته به بازی سر نزدی!\nبرگرد ⚔️")
        except: pass

async def publish_newspaper(context):
    cursor.execute("SELECT attacker_name, defender_name, loot, attacker_won FROM attacks ORDER BY attack_date DESC LIMIT 5"); recent = cursor.fetchall()
    top = get_leaderboard(5)
    txt = f"📰 **روزنامه**\n⏰ {datetime.now().strftime('%H:%M')}\n\n⚔️ **نبردها:**\n"
    if recent:
        for a, d, l, w in recent: txt += f"{'✅' if w else '❌'} {a} ← {d}\n"
    else: txt += "هنوز نبردی نیست\n"
    txt += "\n🏆 **برترین‌ها:**\n"
    for i, (_, u, _, _, p, _, _, _) in enumerate(top): txt += f"{['🥇','🥈','🥉'][i] if i < 3 else f'{i+1}.'} {u} | ⚡{p}\n"
    if datetime.now().weekday() == 4: txt += "\n🎪 **جمعه! ۳۰٪ تخفیف فروشگاه!**"
    await announce_to_channel(context, txt)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; user_id = user.id
    user_data = get_user(user_id=user_id)
    if not user_data: user_data = create_user(user_id, user.first_name)
    update_user(user_id, last_active=datetime.now().isoformat())
    if user_data["is_banned"]: await update.message.reply_text("⛔ بن شدی!"); return
    if not user_data["has_username"]:
        await update.message.reply_text("📝 یه اسم انتخاب کن (حداقل ۲ حرف):")
        context.user_data["waiting_for_username"] = True; return
    if context.args and user_data["referred_by"] is None:
        ref_code = context.args[0]
        cursor.execute("SELECT user_id FROM users WHERE referral_code = ?", (ref_code,)); ref_user = cursor.fetchone()
        if ref_user and ref_user[0] != user_id:
            update_user(user_id, referred_by=ref_user[0])
            update_user(ref_user[0], referral_count=get_user(user_id=ref_user[0])["referral_count"] + 1)
            update_user(ref_user[0], money=get_user(user_id=ref_user[0])["money"] + 500, atomic_bomb=get_user(user_id=ref_user[0])["atomic_bomb"] + 1)
            update_user(user_id, money=user_data["money"] + 300)
    await update_league(user_id); user_data = get_user(user_id=user_id)
    vb = VIP_LEVELS.get(user_data["vip_level"], {}).get("power_bonus", 0)
    await update.message.reply_text(f"⚔️ **بازوی جنگی**\n\n👤 {user_data['username']}\n🏅 {LEAGUES[user_data['league']]['emoji']} {user_data['league']}\n💰 {user_data['money']:,} | 💎 {user_data['diamond']}\n⚡ {user_data['power']} (+{vb}) | 🛡️ {user_data['defense']}", reply_markup=get_main_keyboard(user_id))

async def update_league(uid):
    ud = get_user(user_id=uid)
    for ln, ld in LEAGUES.items():
        if ld["min_power"] <= ud["power"] < ld["max_power"] and ud["league"] != ln: update_user(uid, league=ln, citizens=ud["citizens"] + ld["citizen_bonus"])

async def set_username_handler(update, context):
    uid = update.effective_user.id; un = update.message.text.strip()
    if len(un) < 2: await update.message.reply_text("❌ حداقل ۲ حرف!"); return
    if username_exists(un): await update.message.reply_text("❌ تکراریه!"); return
    set_username(uid, un); context.user_data["waiting_for_username"] = False
    update_user(uid, money=get_user(user_id=uid)["money"] + 500)
    await update.message.reply_text(f"✅ **{un}**!\n🎁 ۵۰۰ سکه!", reply_markup=get_main_keyboard(uid))
    await announce_to_channel(context, f"🎉 {un} به بازی پیوست!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user; uid = user.id; text = update.message.text
    ud = get_user(user_id=uid)
    if not ud: return
    update_user(uid, last_active=datetime.now().isoformat())
    if ud["is_banned"]: await update.message.reply_text("⛔ بن هستی!"); return
    if context.user_data.get("waiting_for_username"): await set_username_handler(update, context); return
    if context.user_data.get("waiting_for_riddle"): await check_riddle(update, context); return
    if context.user_data.get("waiting_for_curse"): await curse_user(update, context); return
    if context.user_data.get("buying_asset"): await buy_asset(update, context); return
    if context.user_data.get("selling_asset"): await sell_asset(update, context); return
    
    if text == "⚔️ حمله": await update.message.reply_text("⚔️ **نوع حمله:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚡ سریع (۵ دقیقه)", callback_data="attack_fast")], [InlineKeyboardButton("💪 سنگین (۲۰ دقیقه تا ۱۰ ساعت)", callback_data="attack_heavy")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "💀 انتقام‌ها":
        rev = get_revenge_list(uid)
        if not rev: await update.message.reply_text("🎉 کسی حمله نکرده!"); return
        kb = [[InlineKeyboardButton(f"💀 {get_user(user_id=t)['username']}", callback_data=f"revenge_{t}")] for t in rev[:10] if get_user(user_id=t)]
        kb.append([InlineKeyboardButton("⚡ انتقام فوری (۵۰ الماس + ۱۵٪)", callback_data="revenge_fast")]); kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")])
        await update.message.reply_text("💀 **انتقام‌ها:**", reply_markup=InlineKeyboardMarkup(kb))
    elif text == "💰 موجودی":
        vb = VIP_LEVELS.get(ud["vip_level"], {}).get("power_bonus", 0); lt = f"\n🏦 وام: {ud['loan_amount']:,}" if ud.get("loan_amount", 0) > 0 else ""
        await update.message.reply_text(f"💰 {ud['money']:,} | 💎 {ud['diamond']}\n🏦 {ud['bank_money']:,}\n⚡ {ud['power']} (+{vb}){lt}")
    elif text == "🏆 لیدربورد":
        top = get_leaderboard(10)
        if not top: await update.message.reply_text("🏆 خالیه!"); return
        txt = "🏆 **لیدربورد:**\n\n"
        for i, (_, u, _, _, p, _, _, l) in enumerate(top): txt += f"{['🥇','🥈','🥉'][i] if i < 3 else f'{i+1}.'} {LEAGUES.get(l,{}).get('emoji','')} **{u}** | ⚡{p}\n"
        await update.message.reply_text(txt)
    elif text == "🛒 فروشگاه":
        d = 0.7 if datetime.now().weekday() == 4 else 1.0
        await update.message.reply_text(f"🛒 **فروشگاه**{' 🎪 ۳۰٪ تخفیف!' if d==0.7 else ''}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"💂 سرباز ({int(200*d)})", callback_data="buy_soldier")], [InlineKeyboardButton(f"🪖 تانک ({int(1000*d)})", callback_data="buy_tank")], [InlineKeyboardButton(f"✈️ هواپیما ({int(5000*d)})", callback_data="buy_plane")], [InlineKeyboardButton(f"🚀 موشک ({int(10000*d)})", callback_data="buy_missile")], [InlineKeyboardButton(f"🤖 ربات ({int(25000*d)})", callback_data="buy_robot")], [InlineKeyboardButton("⬆️ ارتقای نخبه", callback_data="elite_menu")], [InlineKeyboardButton("🛡️ تقویت دفاع", callback_data="defense_menu")], [InlineKeyboardButton("🛡️ گارد ویژه (۱۰۰ الماس)", callback_data="special_guard")], [InlineKeyboardButton("🧙 نفرین (۱۰۰ الماس)", callback_data="buy_curse")], [InlineKeyboardButton("🕯️ حرز (۱۰۰ الماس)", callback_data="buy_antidote")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "💎 فروشگاه ویژه":
        kb = [[InlineKeyboardButton(f"{v['emoji']} {k} ({v['price']:,} ریال)", callback_data=f"buy_real_{k}")] for k, v in SPECIAL_ITEMS_RIAL.items()]
        kb += [[InlineKeyboardButton("🎁 پک‌ها", callback_data="real_packs")], [InlineKeyboardButton("⚡ شارژ سکه", callback_data="real_charge")], [InlineKeyboardButton("✏️ تغییر اسم", callback_data="real_name_change")], [InlineKeyboardButton("🎨 اسم رنگی", callback_data="real_name_color")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]
        await update.message.reply_text("💎 **فروشگاه ویژه:**", reply_markup=InlineKeyboardMarkup(kb))
    elif text == "👑 VIP":
        kb = [[InlineKeyboardButton(f"{v['name']} - {v['price']:,} ریال", callback_data=f"vip_{l}")] for l, v in VIP_LEVELS.items()]
        kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]); await update.message.reply_text("👑 **VIP:**", reply_markup=InlineKeyboardMarkup(kb))
    elif text == "🏭 معدن‌ها":
        acc = ud.get("mine_accumulated", 0); income = get_mine_income(ud)
        txt = f"🏭 **معدن‌ها**\n💰 ذخیره: {acc:,}\n📈 درآمد: {income:,}/ساعت\n\n"
        for mt, d in MINE_TYPES.items(): txt += f"{d['emoji']} {d['name']}: سطح {ud.get(d['key'], 0)}\n"
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🪙 سکه (۵۰۰)", callback_data="mine_coin")], [InlineKeyboardButton("💎 الماس (۲۰۰۰)", callback_data="mine_diamond")], [InlineKeyboardButton("🛢️ نفت (۵۰۰۰)", callback_data="mine_oil")], [InlineKeyboardButton("🥇 طلا (۱۰۰۰۰)", callback_data="mine_gold")], [InlineKeyboardButton("☢️ اورانیوم (۲۵۰۰۰)", callback_data="mine_uranium")], [InlineKeyboardButton(f"💰 برداشت ({acc:,})", callback_data="collect_mines")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🏦 بانک": await update.message.reply_text(f"🏦 **بانک**\n💰 {ud['bank_money']:,}\n📈 {ud['bank_interest']*100}%\n⏰ سود خودکار هر ۱۲ ساعت", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 واریز", callback_data="bank_deposit")], [InlineKeyboardButton("💸 برداشت", callback_data="bank_withdraw")], [InlineKeyboardButton("⬆️ ارتقا", callback_data="bank_upgrade")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🏪 بازار سیاه": await update.message.reply_text("🏪 **بازار سیاه:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 لیست فروش", callback_data="bm_list")], [InlineKeyboardButton("📦 فروش آیتم", callback_data="bm_sell")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🎰 کازینو": await update.message.reply_text(f"🎰 **کازینو**\n💰 {ud['money']:,}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 ۱۰۰ (۲x)", callback_data="casino_100")], [InlineKeyboardButton("🎰 ۵۰۰ (۳x)", callback_data="casino_500")], [InlineKeyboardButton("🎰 ۱۰۰۰ (۵x)", callback_data="casino_1000")], [InlineKeyboardButton("🎲 جکپات ۵۰۰۰ (۱۰x)", callback_data="casino_jackpot")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🏰 کلن من":
        if ud["clan"] == "بدون کلن": await update.message.reply_text("🏰 کلنی نداری!\nایجاد: `ایجاد کلن [اسم]`")
        else:
            cursor.execute("SELECT * FROM clans WHERE clan_name = ?", (ud["clan"],)); c = cursor.fetchone()
            if c: await update.message.reply_text(f"🏰 **{c[0]}**\n⚡ {c[2]} | 👥 {c[3]}")
    elif text == "👥 شهروندان": await update.message.reply_text(f"👥 **شهروندان**\n👥 {ud['citizens']}\n🏠 {ud['houses']} | 🏘️ {ud['apartments']} | 🏢 {ud['towers']} | 🏙️ {ud['skyscrapers']}")
    elif text == "🏗️ ساختمان‌ها": await update.message.reply_text("🏗️ **ساختمان‌ها:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 خانه (۵۰۰)", callback_data="build_home")], [InlineKeyboardButton("🏘️ آپارتمان (۲۰۰۰)", callback_data="build_apartment")], [InlineKeyboardButton("🏢 برج (۸۰۰۰)", callback_data="build_tower")], [InlineKeyboardButton("🏙️ آسمان‌خراش (۳۰۰۰۰)", callback_data="build_skyscraper")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🎰 چرخ شانس":
        paid = ud.get("spin_paid_remaining", 0)
        await update.message.reply_text(f"🎰 **چرخ شانس**\n🎫 رایگان: ۱ بار در روز\n💎 ویژه: {paid} بار", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 رایگان", callback_data="spin_free")], [InlineKeyboardButton(f"💎 ویژه ({paid} بار)", callback_data="spin_paid")], [InlineKeyboardButton("🛒 خرید ویژه (۱۵۰ هزار ریال)", callback_data="buy_spin_paid")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🔗 رفرال": await update.message.reply_text(f"🔗 **رفرال**\n👥 {ud['referral_count']} نفر\n🎁 دعوت‌کننده: ۵۰۰ سکه + بمب\n🎁 جدید: ۳۰۰ سکه", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 دریافت لینک", callback_data="show_ref_link")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🎁 هدیه دادن": await update.message.reply_text("🎁 **هدیه:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💰 سکه", callback_data="gift_money")], [InlineKeyboardButton("💎 الماس", callback_data="gift_diamond")], [InlineKeyboardButton("🎁 آیتم", callback_data="gift_item")], [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]))
    elif text == "🎁 جایزه روزانه":
        today = datetime.now().strftime("%Y-%m-%d")
        if ud["last_daily"] == today: await update.message.reply_text("❌ امروز گرفتی!"); return
        vb = VIP_LEVELS.get(ud["vip_level"], {}).get("daily_bonus", 0); reward = random.randint(1000, 5000) + vb
        update_user(uid, money=ud["money"] + reward, last_daily=today); await update.message.reply_text(f"🎁 **{reward:,}** سکه (+{vb} VIP)")
    elif text == "📜 بیانیه": await update.message.reply_text("📝 متن:"); context.user_data["waiting_for_bayan"] = True
    elif text == "ℹ️ اطلاعات من":
        total = ud['wins'] + ud['losses']; rate = (ud['wins'] / total * 100) if total > 0 else 0
        await update.message.reply_text(f"🎖️ **{ud['username']}**\n🏅 {LEAGUES[ud['league']]['emoji']} {ud['league']}\n⚡ {ud['power']} | 🛡️ {ud['defense']}\n💰 {ud['money']:,}\n⚔️ {ud['wins']} برد | 💀 {ud['losses']} باخت\n📊 {rate:.1f}%")
    elif text == "📊 نمودار قدرت":
        hist = [int(x) for x in (ud.get("power_history") or "").split(",") if x]
        if len(hist) < 2: await update.message.reply_text("📊 حداقل ۲ روز داده لازمه!"); return
        await update.message.reply_text(f"📊 **نمودار**\nاول: {hist[0]}\nالان: {hist[-1]}\n📈 {hist[-1]-hist[0]:+d}")
    elif text == "📚 آموزش": await update.message.reply_text(f"📚 **آموزش**\n⚔️ حمله | 🛒 فروشگاه | 🏭 معدن\n🏦 بانک | 🎰 کازینو | 🎰 چرخ شانس\n📞 {ADMIN_USERNAME}")
    elif text in ["📞 پشتیبانی", "📢 کانال", "👥 گروه"]:
        if "پشتیبانی" in text: await update.message.reply_text(f"📞 {ADMIN_USERNAME}\n🆔 `{ADMIN_ID}`")
        elif "کانال" in text: await update.message.reply_text(CHANNEL_USERNAME)
        else: await update.message.reply_text(GROUP_USERNAME)
    elif text == "👑 پادشاه هفته":
        cursor.execute("SELECT username, weekly_wins FROM users ORDER BY weekly_wins DESC LIMIT 1"); k = cursor.fetchone()
        await update.message.reply_text(f"👑 **{k[0]}**\n⚔️ {k[1]} برد" if k and k[1] > 0 else "👑 هنوز کسی نیست!")
    elif text == "📈 بازار سرمایه":
        txt = "📈 **بازار سرمایه**\n\n"; kb = []
        for an, d in MARKET_ASSETS.items():
            dn = an.replace("_", " "); txt += f"{d['emoji']} {dn}: {d['price']:,} سکه\n"
            kb.append([InlineKeyboardButton(f"{d['emoji']} خرید {dn}", callback_data=f"buy_asset_{an}")])
            kb.append([InlineKeyboardButton(f"{d['emoji']} فروش {dn}", callback_data=f"sell_asset_{an}")])
        kb.append([InlineKeyboardButton("📜 تاریخچه قیمت‌ها", callback_data="price_history")]); kb.append([InlineKeyboardButton("📊 پرتفوی من", callback_data="portfolio")]); kb.append([InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")])
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    elif text == "🧠 معما":
        today = datetime.now().strftime("%Y-%m-%d")
        if ud.get("last_riddle_date") == today: await update.message.reply_text("❌ امروز قبلاً جواب دادی!"); return
        cursor.execute("SELECT * FROM riddles WHERE used_date = ? ORDER BY id DESC LIMIT 1", (today,)); r = cursor.fetchone()
        if r: await update.message.reply_text(f"🧠 **معمای امروز:**\n\n{r[1]}\n\n📝 جوابت رو بفرست:"); context.user_data["waiting_for_riddle"] = True
        else: await update.message.reply_text("🧠 امروز هنوز معمایی مطرح نشده!")
    elif text == "🌟 نشان‌ها":
        badges = (ud.get("badges") or "").split(","); txt = "🌟 **نشان‌های تو:**\n\n"
        for bk, bd in {"first_win": "🎖️ اولین برد", "10_wins": "🏅 ۱۰ برد", "100_wins": "👑 ۱۰۰ برد"}.items(): txt += f"{'✅' if bk in badges else '🔒'} {bd}\n"
        await update.message.reply_text(txt)
    elif text == "🏦 وام":
        if ud.get("loan_amount", 0) > 0: await update.message.reply_text(f"🏦 **وام فعال**\n💰 بدهی: {ud['loan_amount']:,}\n📈 سود: ۷۵٪\n⏰ مهلت: {ud.get('loan_due', '---')}\n\nبرای پرداخت: `پرداخت وام`")
        else:
            ml = min(100000, int(ud["power"] * 0.5)); await update.message.reply_text(f"🏦 **درخواست وام**\n💰 سقف: {ml:,}\n📈 سود: ۷۵٪\n⏰ مهلت: ۴۸ ساعت\n\nبرای درخواست: `وام [مبلغ]`")
    elif text.startswith("وام "):
        if ud.get("loan_amount", 0) > 0: await update.message.reply_text("❌ اول وام قبلی رو بده!"); return
        try: amt = int(text.replace("وام ", ""))
        except: await update.message.reply_text("❌ عدد!"); return
        ml = min(100000, int(ud["power"] * 0.5))
        if amt > ml: await update.message.reply_text(f"❌ حداکثر {ml:,}"); return
        update_user(uid, money=ud["money"] + amt, loan_amount=int(amt * 1.75), loan_due=(datetime.now() + timedelta(hours=48)).isoformat())
        await update.message.reply_text(f"✅ {amt:,} وام!\n📈 برگردوندن: {int(amt*1.75):,}")
    elif text == "پرداخت وام":
        if ud.get("loan_amount", 0) == 0: await update.message.reply_text("❌ وامی نداری!"); return
        if ud["money"] < ud["loan_amount"]: await update.message.reply_text(f"❌ {ud['loan_amount']:,} سکه نیاز داری!"); return
        update_user(uid, money=ud["money"] - ud["loan_amount"], loan_amount=0, loan_due=None); await update.message.reply_text("✅ وام پرداخت شد!")
    elif text == "💰 خرید الماس": await update.message.reply_text("📝 چندتا الماس؟ (هر ۱۰,۰۰۰ سکه = ۱ الماس)\n\n`خرید_الماس [تعداد]`")
    elif text.startswith("خرید_الماس "):
        try: amt = int(text.replace("خرید_الماس ", ""))
        except: await update.message.reply_text("❌ عدد!"); return
        cost = amt * 10000
        if ud["money"] < cost: await update.message.reply_text(f"❌ {cost:,} سکه نیاز داری!"); return
        update_user(uid, money=ud["money"] - cost, diamond=ud["diamond"] + amt); await update.message.reply_text(f"✅ {amt} الماس 💎")
    
    elif text == "👥 کاربران" and uid == ADMIN_ID:
        cursor.execute("SELECT first_name, username, user_id, league, power, money FROM users WHERE has_username = 1 AND is_banned = 0 ORDER BY power DESC")
        users = cursor.fetchall()
        if not users:
            await update.message.reply_text("❌ هیچ کاربری نیست!")
            return
        txt = f"👥 **لیست کاربران ({len(users)} نفر):**\n\n"
        for i, (fn, un, u_id, l, p, m) in enumerate(users[:50], 1):
            txt += f"{i}. 📝 {fn} | 👤 @{un} | 🔗 @{un} | 🆔 `{u_id}` | 🏅 {l} | ⚡ {p} | 💰 {m:,}\n"
        if len(users) > 50:
            txt += f"\n... و {len(users)-50} نفر دیگه"
        await update.message.reply_text(txt)
    
    elif text == "🚫 بن" and uid == ADMIN_ID: context.user_data["waiting_for_ban"] = True; await update.message.reply_text("📝 اسم:")
    elif text == "✅ آنبن" and uid == ADMIN_ID: context.user_data["waiting_for_unban"] = True; await update.message.reply_text("📝 اسم:")
    elif text == "💸 سکه دادن" and uid == ADMIN_ID: context.user_data["waiting_for_give_money"] = True; await update.message.reply_text("📝 اسم و مبلغ:")
    elif text == "💎 الماس دادن" and uid == ADMIN_ID: context.user_data["waiting_for_give_diamond"] = True; await update.message.reply_text("📝 اسم و تعداد:")
    elif text == "🎁 دادن آیتم" and uid == ADMIN_ID: context.user_data["waiting_for_give_special"] = True; await update.message.reply_text("📝 اسم، آیتم، تعداد:")
    elif text == "✅ تایید خرید" and uid == ADMIN_ID: await update.message.reply_text("📝 /confirm [آی‌دی] [آیتم] [تعداد]")
    
    elif context.user_data.get("waiting_for_bayan"):
        context.user_data["waiting_for_bayan"] = False
        try: await context.bot.send_message(CHANNEL_USERNAME, f"📜 **{ud['username']}:**\n{update.message.text}"); await update.message.reply_text("✅ ثبت شد!")
        except: await update.message.reply_text("❌ خطا!")
    elif context.user_data.get("waiting_for_ban"): await ban_user(update, context)
    elif context.user_data.get("waiting_for_unban"): await unban_user(update, context)
    elif context.user_data.get("waiting_for_give_money"): await give_res(update, context, "money")
    elif context.user_data.get("waiting_for_give_diamond"): await give_res(update, context, "diamond")
    elif context.user_data.get("waiting_for_give_special"): await give_special(update, context)
    elif context.user_data.get("waiting_for_bank_deposit"): await bank_action(update, context, "deposit")
    elif context.user_data.get("waiting_for_bank_withdraw"): await bank_action(update, context, "withdraw")
    elif context.user_data.get("waiting_for_gift_money"): await gift_action(update, context, "money")
    elif context.user_data.get("waiting_for_gift_diamond"): await gift_action(update, context, "diamond")
    elif context.user_data.get("waiting_for_gift_item"): await gift_action(update, context, "item")
    elif context.user_data.get("waiting_for_bm_sell"): await bm_sell(update, context)
    elif context.user_data.get("waiting_for_atomic"): await atomic_attack(update, context)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; data = query.data; uid = query.from_user.id; ud = get_user(user_id=uid)
    if data == "main_menu": await query.message.delete(); await context.bot.send_message(uid, "🏠 منوی اصلی:", reply_markup=get_main_keyboard(uid)); return
    elif data == "show_ref_link":
        ref = f"https://ble.ir/{BOT_USERNAME.replace('@', '')}?start={ud['referral_code']}"
        await query.answer("✅ لینک آماده!"); await query.message.edit_text(f"🔗 **لینک دعوت:**\n\n`{ref}`"); return
    elif data == "price_history": await query.message.edit_text("📜 انتخاب کن:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"{v['emoji']} {k.replace('_',' ')}", callback_data=f"history_{k}")] for k, v in MARKET_ASSETS.items()] + [[InlineKeyboardButton("🔙", callback_data="main_menu")]])); return
    elif data.startswith("history_"):
        an = data.replace("history_", ""); em = MARKET_ASSETS[an]["emoji"]; cp = MARKET_ASSETS[an]["price"]
        cursor.execute("SELECT price, recorded_date FROM price_history WHERE asset_name = ? ORDER BY recorded_date DESC LIMIT 24", (an,)); hist = cursor.fetchall()
        if not hist: await query.answer("❌ تاریخچه‌ای نیست!", show_alert=True); return
        prices = [p[0] for p in hist]; avg = sum(prices) // len(prices)
        txt = f"📜 **{em} {an.replace('_',' ')}**\n💰 الان: {cp:,}\n📊 میانگین: {avg:,}\n\n"
        for price, date in reversed(hist[-12:]): txt += f"⏰ {datetime.fromisoformat(date).strftime('%H:%M')} → {price:,} {'📈' if price > avg else '📉'}\n"
        await query.message.edit_text(txt); return
    elif data == "portfolio":
        cursor.execute("SELECT asset_name, amount, avg_buy_price FROM user_assets WHERE user_id = ?", (uid,)); assets = cursor.fetchall()
        if not assets: await query.answer("❌ پرتفوی خالیه!", show_alert=True); return
        txt = "📊 **پرتفوی:**\n\n"; tp = 0
        for an, amt, ap in assets:
            cp = MARKET_ASSETS.get(an, {}).get("price", 0); pf = int((cp - ap) * amt); tp += pf
            txt += f"{MARKET_ASSETS.get(an,{}).get('emoji','')} {an.replace('_',' ')}: {amt} عدد | {pf:+,}\n"
        txt += f"\n📈 کل: {tp:+,} سکه"; await query.message.edit_text(txt); return
    elif data == "spin_free":
        today = datetime.now().strftime("%Y-%m-%d")
        if ud["last_spin_date"] == today and ud["spin_free_used"] >= 1: await query.answer("❌ امروز استفاده کردی!", show_alert=True); return
        update_user(uid, spin_free_used=ud["spin_free_used"] + 1, last_spin_date=today)
        prize = random.choices(SPIN_PRIZES, weights=[p["chance"] for p in SPIN_PRIZES])[0]
        if prize["type"] == "money": update_user(uid, money=ud["money"] + prize["amount"])
        elif prize["type"] == "diamond": update_user(uid, diamond=ud["diamond"] + prize["amount"])
        elif prize["type"] == "item": update_user(uid, **{prize["item_key"]: ud[prize["item_key"]] + prize["amount"]})
        await query.message.edit_text(f"🎰 **چرخ شانس**\n\n🎉 {prize['emoji']} **{prize['name']}**!"); await query.answer(f"{prize['emoji']} {prize['name']}!", show_alert=True); return
    elif data == "spin_paid":
        if ud.get("spin_paid_remaining", 0) <= 0: await query.answer("❌ اعتبار نداری!", show_alert=True); return
        update_user(uid, spin_paid_remaining=ud["spin_paid_remaining"] - 1)
        prize = random.choices(SPIN_PRIZES, weights=[p["chance"] for p in SPIN_PRIZES])[0]
        if prize["type"] == "money": update_user(uid, money=ud["money"] + prize["amount"])
        elif prize["type"] == "diamond": update_user(uid, diamond=ud["diamond"] + prize["amount"])
        elif prize["type"] == "item": update_user(uid, **{prize["item_key"]: ud[prize["item_key"]] + prize["amount"]})
        rem = ud["spin_paid_remaining"] - 1
        await query.message.edit_text(f"💎 **چرخ ویژه**\n\n🎉 {prize['emoji']} **{prize['name']}**!\n🎫 باقی: {rem}"); await query.answer(f"{prize['emoji']} {prize['name']}!", show_alert=True); return
    elif data == "buy_spin_paid": await query.message.edit_text(f"💎 **۵ بار چرخ ویژه**\n💰 ۱۵۰,۰۰۰ ریال\n\n💳 `{CARD_NUMBER}`\n👤 {CARD_OWNER}"); await notify_admin(context, ud, "چرخ ویژه", "۵ بار", 5, 150000); return
    elif data == "collect_mines":
        acc = ud.get("mine_accumulated", 0)
        if acc <= 0: await query.answer("❌ چیزی جمع نشده!", show_alert=True); return
        update_user(uid, money=ud["money"] + acc, mine_accumulated=0); await query.answer(f"💰 {acc:,} سکه برداشت شد!", show_alert=True); return
    elif data.startswith("build_"):
        bt = data.replace("build_", ""); b = BUILDINGS.get(bt)
        if not b: return
        if ud["money"] < b["cost"]: await query.answer(f"❌ {b['cost']} سکه!", show_alert=True); return
        km = {"home": "houses", "apartment": "apartments", "tower": "towers", "skyscraper": "skyscrapers"}
        update_user(uid, money=ud["money"] - b["cost"], citizens=ud["citizens"] + b["citizens"]); update_user(uid, **{km[bt]: ud[km[bt]] + 1})
        await query.answer(f"✅ {b['name']}! +{b['citizens']}", show_alert=True); return
    elif data in ["buy_soldier", "buy_tank", "buy_plane", "buy_missile", "buy_robot"]:
        ut = data.replace("buy_", ""); u = UNITS.get(ut)
        if not u: return
        cost = int(u["cost"] * (0.7 if datetime.now().weekday() == 4 else 1.0))
        if ud["money"] < cost: await query.answer(f"❌ {cost} سکه!", show_alert=True); return
        update_user(uid, money=ud["money"] - cost, power=ud["power"] + u["power"]); update_user(uid, **{ut: ud[ut] + 1})
        await query.answer(f"✅ {u['name']}!", show_alert=True); return
    elif data == "elite_menu": await query.message.edit_text("⬆️ **ارتقا:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💂‍♂️ سرباز نخبه (۵۰۰)", callback_data="elite_soldier")], [InlineKeyboardButton("🪖 تانک پیشرفته (۲۰۰۰)", callback_data="elite_tank")], [InlineKeyboardButton("✈️ رادارگریز (۸۰۰۰)", callback_data="elite_plane")], [InlineKeyboardButton("🔙", callback_data="main_menu")]])); return
    elif data in ["elite_soldier", "elite_tank", "elite_plane"]:
        e = ELITE_ITEMS.get(data)
        if not e: return
        if ud[e["from"]] < 1: await query.answer(f"❌ {e['name']} نیاز داری!", show_alert=True); return
        if ud["money"] < e["cost"]: await query.answer(f"❌ {e['cost']} سکه!", show_alert=True); return
        update_user(uid, money=ud["money"] - e["cost"], power=ud["power"] + e["power"]); update_user(uid, **{e["from"]: ud[e["from"]] - 1, e["to"]: ud[e["to"]] + 1})
        await query.answer(f"✅ {e['name']}!", show_alert=True); return
    elif data == "defense_menu": await query.message.edit_text("🛡️ **دفاع:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🧱 دیوار (۵۰۰)", callback_data="defense_wall")], [InlineKeyboardButton("🗼 برج (۲۰۰۰)", callback_data="defense_tower")], [InlineKeyboardButton("🛡️ گنبد (۸۰۰۰)", callback_data="defense_dome")], [InlineKeyboardButton("🏰 قلعه (۲۰۰۰۰)", callback_data="defense_fortress")], [InlineKeyboardButton("🔙", callback_data="main_menu")]])); return
    elif data in ["defense_wall", "defense_tower", "defense_dome", "defense_fortress"]:
        d = DEFENSE_ITEMS.get(data.replace("defense_", ""))
        if not d: return
        if ud["money"] < d["cost"]: await query.answer(f"❌ {d['cost']} سکه!", show_alert=True); return
        update_user(uid, money=ud["money"] - d["cost"], defense=ud["defense"] + d["defense"]); await query.answer(f"✅ {d['name']}!", show_alert=True); return
    elif data == "special_guard":
        if ud["diamond"] < 100: await query.answer("❌ ۱۰۰ الماس!", show_alert=True); return
        update_user(uid, diamond=ud["diamond"] - 100, shield_until=(datetime.now() + timedelta(hours=1)).isoformat()); await query.answer("🛡️ گارد ویژه! ۱ ساعت", show_alert=True); return
    elif data == "buy_curse": await query.message.delete(); await context.bot.send_message(uid, "📝 اسم طرف:"); context.user_data["waiting_for_curse"] = True; return
    elif data == "buy_antidote":
        if ud["diamond"] < 100: await query.answer("❌ ۱۰۰ الماس!", show_alert=True); return
        update_user(uid, diamond=ud["diamond"] - 100, cursed_until=None); await query.answer("🕯️ حرز استفاده شد!", show_alert=True); return
    elif data.startswith("mine_"):
        mt = data.replace("mine_", ""); m = MINE_TYPES.get(mt)
        if not m: return
        if ud["money"] < m["cost"]: await query.answer(f"❌ {m['cost']} سکه!", show_alert=True); return
        cl = ud[m["key"]]; update_user(uid, money=ud["money"] - m["cost"]); update_user(uid, **{m["key"]: cl + 1})
        await query.answer(f"✅ معدن {m['name']} سطح {cl+1}!", show_alert=True); return
    elif data in ["casino_100", "casino_500", "casino_1000", "casino_jackpot"]:
        bets = {"casino_100": (100, 2), "casino_500": (500, 3), "casino_1000": (1000, 5), "casino_jackpot": (5000, 10)}; bet, mult = bets[data]
        if ud["money"] < bet: await query.answer("❌ سکه کافی نیست!", show_alert=True); return
        if random.random() < 0.4: win = bet * mult; update_user(uid, money=ud["money"] + win); await query.answer(f"🎉 {win:,}!", show_alert=True)
        else: update_user(uid, money=ud["money"] - bet); await query.answer(f"💀 -{bet}!", show_alert=True); return
    elif data.startswith("attack_user_"): await execute_attack(update, context, uid, int(data.replace("attack_user_", ""))); return
    elif data.startswith("revenge_"): await execute_attack(update, context, uid, int(data.replace("revenge_", "")), is_revenge=True); return
    elif data == "attack_fast" or data == "attack_heavy": await query.message.delete(); await context.bot.send_message(uid, "📝 آی‌دی یا اسم هدف:"); context.user_data["attack_type"] = "fast" if data == "attack_fast" else "heavy"; return
    elif data == "revenge_fast":
        if ud["diamond"] < 50: await query.answer("❌ ۵۰ الماس!", show_alert=True); return
        update_user(uid, diamond=ud["diamond"] - 50); await query.message.delete(); await context.bot.send_message(uid, "📝 آی‌دی هدف:"); context.user_data["revenge_fast"] = True; return
    elif data == "attack_search": await query.message.delete(); await context.bot.send_message(uid, "🔍 حداقل ۲ حرف:"); context.user_data["waiting_for_attack_search"] = True; return
    elif data == "attack_list":
        players = [(id, u, p, d) for id, u, p, d in get_all_usernames() if id != uid]
        if not players: await query.answer("هیچ بازیکنی نیست!", show_alert=True); return
        targets = random.sample(players, min(20, len(players)))
        kb = [[InlineKeyboardButton(f"👤 {u} | ⚡{p}", callback_data=f"attack_user_{id}")] for id, u, p, d in targets]; kb.append([InlineKeyboardButton("🔙", callback_data="main_menu")])
        await query.message.delete(); await context.bot.send_message(uid, "📋 انتخاب کن:", reply_markup=InlineKeyboardMarkup(kb)); return
    elif data == "attack_atomic":
        if ud["atomic_bomb"] < 1: await query.answer("❌ بمب اتم نداری!", show_alert=True); return
        await query.message.delete(); await context.bot.send_message(uid, "💣 آی‌دی هدف:"); context.user_data["waiting_for_atomic"] = True; return
    elif data == "bank_deposit": await query.message.delete(); await context.bot.send_message(uid, "📝 چقدر واریز کنم؟"); context.user_data["waiting_for_bank_deposit"] = True; return
    elif data == "bank_withdraw": await query.message.delete(); await context.bot.send_message(uid, f"📝 چقدر برداشت کنم؟ (بانک: {ud['bank_money']:,})"); context.user_data["waiting_for_bank_withdraw"] = True; return
    elif data == "bank_upgrade":
        lv = ud["bank_level"]; nb = BANK_LEVELS.get(lv + 1)
        if not nb: await query.answer("حداکثر سطح!", show_alert=True); return
        if ud["money"] < nb["cost"]: await query.answer(f"❌ {nb['cost']} سکه!", show_alert=True); return
        update_user(uid, money=ud["money"] - nb["cost"], bank_level=lv + 1, bank_interest=nb["interest"]); await query.answer(f"✅ سود {nb['interest']*100}%!", show_alert=True); return
    elif data in ["gift_money", "gift_diamond", "gift_item"]:
        gt = {"gift_money": "money", "gift_diamond": "diamond", "gift_item": "item"}[data]; await query.message.delete()
        await context.bot.send_message(uid, "📝 اسم و مبلغ:" if gt != "item" else "📝 اسم، آیتم، تعداد:"); context.user_data[f"waiting_for_gift_{gt}"] = True; return
    elif data == "bm_list":
        cursor.execute("SELECT * FROM black_market ORDER BY listed_date DESC LIMIT 10"); items = cursor.fetchall()
        if not items: await query.answer("بازار خالیه!", show_alert=True); return
        txt = "🏪 **بازار سیاه:**\n\n"; kb = []
        for item in items:
            txt += f"🆔{item[0]} | {item[2]} x{item[5]} | {item[4]} سکه\n"; kb.append([InlineKeyboardButton(f"خرید {item[2]}", callback_data=f"bm_buy_{item[0]}")])
        kb.append([InlineKeyboardButton("🔙", callback_data="main_menu")]); await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb)); return
    elif data == "bm_sell": await query.message.delete(); await context.bot.send_message(uid, "📝 آیتم، قیمت، تعداد: بمب اتم 3000 1"); context.user_data["waiting_for_bm_sell"] = True; return
    elif data.startswith("bm_buy_"):
        iid = int(data.replace("bm_buy_", "")); cursor.execute("SELECT * FROM black_market WHERE id = ?", (iid,)); item = cursor.fetchone()
        if not item: await query.answer("❌ فروخته شد!", show_alert=True); return
        if ud["money"] < item[4]: await query.answer("❌ سکه کافی نیست!", show_alert=True); return
        update_user(uid, money=ud["money"] - item[4]); update_user(item[1], money=get_user(user_id=item[1])["money"] + item[4])
        ik = {"بمب اتم": "atomic_bomb", "سپر نامرئی": "shield_item", "معجون قدرت": "power_potion"}.get(item[2])
        if ik: update_user(uid, **{ik: ud[ik] + item[5]})
        cursor.execute("DELETE FROM black_market WHERE id = ?", (iid,)); conn.commit(); await query.answer("✅ خرید موفق!", show_alert=True); return
    elif data.startswith("vip_"):
        lv = int(data.replace("vip_", "")); vd = VIP_LEVELS[lv]
        await query.message.edit_text(f"{vd['name']}\n⏱ {vd['duration_days']} روز\n💰 {vd['price']:,} ریال\n\n💳 `{CARD_NUMBER}`\n👤 {CARD_OWNER}"); await notify_admin(context, ud, "VIP", vd["name"], 1, vd["price"]); return
    elif data.startswith("buy_real_"):
        iname = data.replace("buy_real_", "")
        if iname in SPECIAL_ITEMS_RIAL:
            item = SPECIAL_ITEMS_RIAL[iname]; await query.message.edit_text(f"{item['emoji']} **{iname}**\n{item.get('desc','')}\n💰 {item['price']:,} ریال\n\n💳 `{CARD_NUMBER}`\n👤 {CARD_OWNER}"); await notify_admin(context, ud, "آیتم", iname, 1, item["price"])
        elif iname in OTHER_SERVICES:
            item = OTHER_SERVICES[iname]; await query.message.edit_text(f"**{iname}**\n💰 {item['price']:,} ریال\n\n💳 `{CARD_NUMBER}`\n👤 {CARD_OWNER}"); await notify_admin(context, ud, "خدمت", iname, 1, item["price"]); return
    elif data == "real_packs": await query.message.edit_text("🎁 **پک‌ها:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎁 پک طلایی (۱۲۰,۰۰۰)", callback_data="buy_real_پک طلایی")], [InlineKeyboardButton("💎 پک الماس (۲۵۰,۰۰۰)", callback_data="buy_real_پک الماس")], [InlineKeyboardButton("🔙", callback_data="main_menu")]])); return
    elif data == "real_charge": await query.message.edit_text("⚡ **شارژ:**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚡ ۱۰۰۰ (۲۰,۰۰۰)", callback_data="buy_real_شارژ سکه ۱۰۰۰")], [InlineKeyboardButton("⚡ ۵۰۰۰ (۸۰,۰۰۰)", callback_data="buy_real_شارژ سکه ۵۰۰۰")], [InlineKeyboardButton("⚡ ۱۰۰۰۰ (۱۵۰,۰۰۰)", callback_data="buy_real_شارژ سکه ۱۰۰۰۰")], [InlineKeyboardButton("🔙", callback_data="main_menu")]])); return
    elif data in ["real_name_change", "real_name_color"]:
        sm = {"real_name_change": "تغییر اسم", "real_name_color": "اسم رنگی"}; item = OTHER_SERVICES[sm[data]]
        await query.message.edit_text(f"**{sm[data]}**\n💰 {item['price']:,} ریال\n\n💳 `{CARD_NUMBER}`\n👤 {CARD_OWNER}"); await notify_admin(context, ud, sm[data], sm[data], 1, item["price"]); return
    elif data.startswith("buy_asset_"):
        an = data.replace("buy_asset_", ""); await query.message.delete(); await context.bot.send_message(uid, f"📝 چندتا {an.replace('_',' ')} می‌خوای؟ (قیمت: {MARKET_ASSETS[an]['price']:,})"); context.user_data["buying_asset"] = an; return
    elif data.startswith("sell_asset_"):
        an = data.replace("sell_asset_", ""); cursor.execute("SELECT amount FROM user_assets WHERE user_id = ? AND asset_name = ?", (uid, an)); row = cursor.fetchone()
        if not row or row[0] <= 0: await query.answer("❌ نداری!", show_alert=True); return
        await query.message.delete(); await context.bot.send_message(uid, f"📝 چندتا {an.replace('_',' ')} می‌فروشی؟ (موجودی: {row[0]}, قیمت: {MARKET_ASSETS[an]['price']:,})"); context.user_data["selling_asset"] = an; return

async def execute_attack(update, context, aid, tid, is_revenge=False):
    query = update.callback_query; a = get_user(user_id=aid); d = get_user(user_id=tid)
    if not d: await query.answer("پیدا نشد!", show_alert=True); return
    if d.get("shield_until") and datetime.now() < datetime.fromisoformat(d["shield_until"]): await query.answer("🛡️ سپر داره!", show_alert=True); return
    ap = a["power"] * (2 if is_revenge else 1); dp = d["defense"]; nb = 1.15 if datetime.now().hour >= 18 or datetime.now().hour < 6 else 1.0
    now = datetime.now()
    if ap > dp:
        loot = int(d["money"] * random.uniform(0.2, 0.3) * nb)
        if a.get("last_win_time") and (now - datetime.fromisoformat(a["last_win_time"])).seconds < 1800:
            cons = a.get("consecutive_wins", 0) + 1
            if cons >= 3: loot = int(loot * 1.5)
            update_user(aid, consecutive_wins=cons)
        else: update_user(aid, consecutive_wins=1)
        update_user(aid, last_win_time=now.isoformat(), money=a["money"] + loot, wins=a["wins"] + 1, weekly_wins=a["weekly_wins"] + 1)
        update_user(tid, money=d["money"] - loot, losses=d["losses"] + 1, shield_until=(now + timedelta(hours=1)).isoformat())
        add_revenge(tid, aid)
        if is_revenge: remove_revenge(aid, tid)
        if a["power"] < 1000: pl = random.randint(10, 100)
        elif a["power"] < 100000: pl = random.randint(100, 1500)
        elif a["power"] < 1000000: pl = random.randint(500, 10000)
        else: pl = random.randint(1000, 50000)
        update_user(aid, power=max(50, a["power"] - pl))
        cursor.execute("INSERT INTO attacks VALUES (NULL, ?, ?, ?, ?, 1, ?, ?)", (aid, tid, a["username"], d["username"], loot, now.isoformat())); conn.commit()
        await announce_to_channel(context, f"⚔️ {a['username']} ← {d['username']} | +{loot:,} سکه")
        try: await context.bot.send_message(tid, f"⚠️ {a['username']} بهت حمله کرد!\n💰 -{loot:,}\n🛡️ سپر ۱h")
        except: pass
        await query.answer(f"🎉 {loot:,} سکه!", show_alert=True)
    else:
        loss = int(a["money"] * 0.05); update_user(aid, money=a["money"] - loss, losses=a["losses"] + 1)
        cursor.execute("INSERT INTO attacks VALUES (NULL, ?, ?, ?, ?, 0, ?, ?)", (aid, tid, a["username"], d["username"], loss, now.isoformat())); conn.commit()
        await query.answer(f"💀 -{loss:,} سکه!", show_alert=True)
    hist = [x for x in (a.get("power_history") or "").split(",") if x]; hist.append(str(a["power"])); update_user(aid, power_history=",".join(hist[-30:]))
    await query.message.delete(); await context.bot.send_message(aid, "🏠 منوی اصلی:", reply_markup=get_main_keyboard(aid)); await update_league(aid)

async def check_riddle(update, context):
    uid = update.effective_user.id; ans = update.message.text.strip().replace(" ", "").replace("‌", "")
    u = get_user(user_id=uid); today = datetime.now().strftime("%Y-%m-%d")
    if u.get("last_riddle_date") == today: context.user_data["waiting_for_riddle"] = False; await update.message.reply_text("❌ امروز قبلاً جواب دادی!"); return
    cursor.execute("SELECT * FROM riddles WHERE used_date = ? ORDER BY id DESC LIMIT 1", (today,)); r = cursor.fetchone()
    if not r: context.user_data["waiting_for_riddle"] = False; await update.message.reply_text("❌ معمایی فعال نیست!"); return
    correct = r[2].strip().replace(" ", "").replace("‌", "")
    if ans == correct:
        cursor.execute("SELECT COUNT(*) FROM users WHERE riddles_solved > 0 AND last_active > ?", ((datetime.now() - timedelta(hours=24)).isoformat(),)); solvers = cursor.fetchone()[0]
        if solvers == 0: rm, rd = 10000, 10
        elif solvers == 1: rm, rd = 5000, 5
        elif solvers == 2: rm, rd = 2000, 2
        else: context.user_data["waiting_for_riddle"] = False; await update.message.reply_text("❌ ۳ نفر زودتر جواب دادن!"); return
        update_user(uid, money=u["money"] + rm, diamond=u["diamond"] + rd, riddles_solved=u["riddles_solved"] + 1, last_riddle_date=today)
        context.user_data["waiting_for_riddle"] = False; await update.message.reply_text(f"✅ آفرین!\n💰 {rm:,} سکه + 💎 {rd} الماس")
    else: context.user_data["waiting_for_riddle"] = False; await update.message.reply_text(f"❌ اشتباه! جواب درست رو جا زدی.\nبرای دیدن دوباره معما: /start")

async def curse_user(update, context):
    uid = update.effective_user.id; tn = update.message.text.strip(); t = get_user(username=tn)
    if not t: await update.message.reply_text("❌ پیدا نشد!"); return
    u = get_user(user_id=uid)
    if u["diamond"] < 100: await update.message.reply_text("❌ ۱۰۰ الماس!"); return
    update_user(uid, diamond=u["diamond"] - 100); update_user(t["user_id"], cursed_until=(datetime.now() + timedelta(hours=6)).isoformat())
    context.user_data["waiting_for_curse"] = False; await update.message.reply_text(f"🧙 {tn} نفرین شد! ۶ ساعت")

async def buy_asset(update, context):
    uid = update.effective_user.id; an = context.user_data["buying_asset"]; context.user_data["buying_asset"] = None
    try: amt = float(update.message.text)
    except: await update.message.reply_text("❌ عدد!"); return
    price = MARKET_ASSETS[an]["price"]; total = int(price * amt)
    if get_user(user_id=uid)["money"] < total: await update.message.reply_text(f"❌ {total:,} سکه!"); return
    update_user(uid, money=get_user(user_id=uid)["money"] - total)
    cursor.execute("SELECT amount FROM user_assets WHERE user_id = ? AND asset_name = ?", (uid, an)); row = cursor.fetchone()
    if row: cursor.execute("UPDATE user_assets SET amount = amount + ?, avg_buy_price = (avg_buy_price + ?) / 2 WHERE user_id = ? AND asset_name = ?", (amt, price, uid, an))
    else: cursor.execute("INSERT INTO user_assets VALUES (?, ?, ?, ?)", (uid, an, amt, price))
    conn.commit(); await update.message.reply_text(f"✅ {amt} {an.replace('_',' ')} ({total:,} سکه)")

async def sell_asset(update, context):
    uid = update.effective_user.id; an = context.user_data["selling_asset"]; context.user_data["selling_asset"] = None
    try: amt = float(update.message.text)
    except: await update.message.reply_text("❌ عدد!"); return
    cursor.execute("SELECT amount FROM user_assets WHERE user_id = ? AND asset_name = ?", (uid, an)); row = cursor.fetchone()
    if not row or row[0] < amt: await update.message.reply_text("❌ موجودی کافی نیست!"); return
    price = MARKET_ASSETS[an]["price"]; total = int(price * amt); update_user(uid, money=get_user(user_id=uid)["money"] + total)
    if row[0] == amt: cursor.execute("DELETE FROM user_assets WHERE user_id = ? AND asset_name = ?", (uid, an))
    else: cursor.execute("UPDATE user_assets SET amount = amount - ? WHERE user_id = ? AND asset_name = ?", (amt, uid, an))
    conn.commit(); await update.message.reply_text(f"✅ {amt} {an.replace('_',' ')} ({total:,} سکه)")

async def ban_user(update, context):
    u = get_user(username=update.message.text.strip())
    if not u: await update.message.reply_text("❌ نیست!"); return
    update_user(u["user_id"], is_banned=1); context.user_data["waiting_for_ban"] = False; await update.message.reply_text(f"🚫 {u['username']} بن شد.")

async def unban_user(update, context):
    u = get_user(username=update.message.text.strip())
    if not u: await update.message.reply_text("❌ نیست!"); return
    update_user(u["user_id"], is_banned=0); context.user_data["waiting_for_unban"] = False; await update.message.reply_text(f"✅ {u['username']} آنبن شد.")

async def give_res(update, context, res):
    p = update.message.text.split()
    if len(p) < 2: await update.message.reply_text("❌ فرمت: اسم مقدار"); return
    u = get_user(username=p[0])
    if not u: await update.message.reply_text("❌ نیست!"); return
    try: amt = int(p[1])
    except: await update.message.reply_text("❌ عدد!"); return
    if res == "money": update_user(u["user_id"], money=u["money"] + amt)
    else: update_user(u["user_id"], diamond=u["diamond"] + amt)
    context.user_data[f"waiting_for_give_{res}"] = False; await update.message.reply_text(f"✅ {amt} {res} به {p[0]}")

async def give_special(update, context):
    p = update.message.text.split(maxsplit=2)
    if len(p) < 3: await update.message.reply_text("❌ فرمت: اسم آیتم تعداد"); return
    u = get_user(username=p[0])
    if not u: await update.message.reply_text("❌ نیست!"); return
    try: amt = int(p[2])
    except: await update.message.reply_text("❌ عدد!"); return
    ik = {"بمب اتم": "atomic_bomb", "سپر نامرئی": "shield_item", "معجون قدرت": "power_potion"}.get(p[1])
    if ik: update_user(u["user_id"], **{ik: u[ik] + amt})
    context.user_data["waiting_for_give_special"] = False; await update.message.reply_text(f"✅ {amt}x {p[1]} به {p[0]}")

async def bank_action(update, context, action):
    uid = update.effective_user.id; ud = get_user(user_id=uid); context.user_data[f"waiting_for_bank_{action}"] = False
    try: amt = int(update.message.text)
    except: await update.message.reply_text("❌ عدد!"); return
    if action == "deposit":
        if amt > ud["money"]: await update.message.reply_text("❌ سکه کافی نیست!"); return
        update_user(uid, money=ud["money"] - amt, bank_money=ud["bank_money"] + amt)
    else:
        if amt > ud["bank_money"]: await update.message.reply_text("❌ موجودی بانک کافی نیست!"); return
        update_user(uid, money=ud["money"] + amt, bank_money=ud["bank_money"] - amt)
    await update.message.reply_text(f"✅ {amt:,} سکه!")

async def gift_action(update, context, gt):
    uid = update.effective_user.id; context.user_data[f"waiting_for_gift_{gt}"] = False; p = update.message.text.split()
    if gt in ["money", "diamond"]:
        if len(p) != 2: await update.message.reply_text("❌ فرمت: اسم مقدار"); return
        un, amt = p[0], p[1]
    else:
        if len(p) < 3: await update.message.reply_text("❌ فرمت: اسم آیتم تعداد"); return
        un, inn, amt = p[0], p[1], p[2]
    try: amt = int(amt)
    except: await update.message.reply_text("❌ عدد!"); return
    s = get_user(user_id=uid); r = get_user(username=un)
    if not r: await update.message.reply_text("❌ کاربر نیست!"); return
    if gt == "money":
        if uid != ADMIN_ID and s["money"] < amt: await update.message.reply_text("❌ سکه کافی نیست!"); return
        update_user(uid, money=s["money"] - amt); update_user(r["user_id"], money=r["money"] + amt)
    elif gt == "diamond":
        if uid != ADMIN_ID and s["diamond"] < amt: await update.message.reply_text("❌ الماس کافی نیست!"); return
        update_user(uid, diamond=s["diamond"] - amt); update_user(r["user_id"], diamond=r["diamond"] + amt)
    else:
        ik = {"بمب اتم": "atomic_bomb", "سپر نامرئی": "shield_item", "معجون قدرت": "power_potion"}.get(inn)
        if not ik: await update.message.reply_text("❌ آیتم نامعتبر!"); return
        if uid != ADMIN_ID and s[ik] < amt: await update.message.reply_text(f"❌ {inn} کافی نیست!"); return
        update_user(uid, **{ik: s[ik] - amt}); update_user(r["user_id"], **{ik: r[ik] + amt})
    await update.message.reply_text(f"✅ به {un} هدیه دادی!")

async def bm_sell(update, context):
    uid = update.effective_user.id; ud = get_user(user_id=uid); context.user_data["waiting_for_bm_sell"] = False; p = update.message.text.split()
    if len(p) < 3: await update.message.reply_text("❌ فرمت: بمب اتم 3000 1"); return
    try: price = int(p[1]); amt = int(p[2])
    except: await update.message.reply_text("❌ عدد!"); return
    ik = {"بمب اتم": "atomic_bomb", "سپر نامرئی": "shield_item", "معجون قدرت": "power_potion"}.get(p[0])
    if not ik: await update.message.reply_text("❌ آیتم نامعتبر!"); return
    if ud[ik] < amt: await update.message.reply_text("❌ کافی نداری!"); return
    update_user(uid, **{ik: ud[ik] - amt}); cursor.execute("INSERT INTO black_market VALUES (NULL, ?, ?, ?, ?, ?, ?)", (uid, ud["username"], p[0], price, amt, datetime.now().isoformat())); conn.commit()
    await update.message.reply_text(f"✅ {amt}x {p[0]} به قیمت {price}")

async def atomic_attack(update, context):
    uid = update.effective_user.id; context.user_data["waiting_for_atomic"] = False; txt = update.message.text.strip()
    t = get_user(username=txt) or (get_user(user_id=int(txt)) if txt.isdigit() else None)
    if not t: await update.message.reply_text("❌ پیدا نشد!"); return
    a = get_user(user_id=uid); update_user(uid, atomic_bomb=a["atomic_bomb"] - 1)
    loot = int(t["money"] * 0.5); update_user(uid, money=a["money"] + loot, wins=a["wins"] + 1); update_user(t["user_id"], money=t["money"] - loot, losses=t["losses"] + 1)
    await announce_to_channel(context, f"💣 {a['username']} ← {t['username']} | +{loot:,}")
    await update.message.reply_text(f"💣 **حمله اتمی!**\n💰 {loot:,} سکه!")

async def confirm_purchase(update, context):
    if update.effective_user.id != ADMIN_ID: return
    p = update.message.text.split()
    if len(p) < 4: await update.message.reply_text("❌ /confirm [آی‌دی] [آیتم] [تعداد]"); return
    try: tid = int(p[1]); amt = int(p[-1]); iname = " ".join(p[2:-1])
    except: await update.message.reply_text("❌ فرمت!"); return
    t = get_user(user_id=tid)
    if not t: await update.message.reply_text("❌ کاربر نیست!"); return
    im = {"بمب اتم": "atomic_bomb", "سپر نامرئی": "shield_item", "معجون قدرت": "power_potion", "زهر": "poison_item"}
    if iname in im: update_user(tid, **{im[iname]: t[im[iname]] + amt})
    elif "شارژ سکه" in iname: update_user(tid, money=t["money"] + 1000 * amt)
    elif "پک" in iname:
        for i_n, i_a in OTHER_SERVICES.get(iname, {}).get("items", {}).items():
            if i_n in im: update_user(tid, **{im[i_n]: t[im[i_n]] + i_a * amt})
    elif "VIP" in iname or "اشتراک" in iname:
        for lv, d in VIP_LEVELS.items():
            if d["name"] == iname: update_user(tid, vip_level=lv, power=t["power"] + d["power_bonus"])
    elif iname == "تغییر اسم": update_user(tid, name_change_count=t["name_change_count"] + amt)
    elif iname == "اسم رنگی": update_user(tid, username_color="gold")
    elif "چرخ" in iname: update_user(tid, spin_paid_remaining=t.get("spin_paid_remaining", 0) + 5)
    await update.message.reply_text(f"✅ {t['username']} | {amt}x {iname}")

def main():
    for an, d in MARKET_ASSETS.items(): cursor.execute("INSERT OR IGNORE INTO market_prices VALUES (?, ?, ?)", (an, d["price"], datetime.now().isoformat()))
    conn.commit()
    app = Application.builder().token(BOT_TOKEN).base_url("https://tapi.bale.ai/bot").base_file_url("https://tapi.bale.ai/file/bot").build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CommandHandler("confirm", confirm_purchase))
    app.add_handler(CallbackQueryHandler(handle_callback)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    try:
        app.job_queue.run_repeating(auto_disaster, interval=3600, first=30)
        app.job_queue.run_repeating(accumulate_mines, interval=3600, first=60)
        app.job_queue.run_repeating(bank_interest_auto, interval=43200, first=120)
        app.job_queue.run_repeating(publish_newspaper, interval=14400, first=180)
        app.job_queue.run_repeating(collect_taxes, interval=3600, first=240)
        app.job_queue.run_repeating(remind_inactive, interval=3600, first=300)
        app.job_queue.run_repeating(update_market, interval=600, first=10)
        app.job_queue.run_repeating(update_wanted, interval=7200, first=20)
        app.job_queue.run_repeating(daily_riddle, interval=86400, first=30)
        app.job_queue.run_repeating(fireworks, interval=3600, first=40)
        app.job_queue.run_repeating(weekly_king, interval=86400, first=50)
        print("✅ همه زمان‌بندی‌ها فعال شد")
    except Exception as e: print(f"⚠️ {e}")
    print("🎮 بازوی جنگی - دکمه 👥 کاربران با ۷ اطلاعات")
    print(f"👑 {ADMIN_USERNAME}")
    app.run_polling()

if __name__ == "__main__":
    main()
