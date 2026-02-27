import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery, InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
import aiohttp
import aiosqlite

# ============== КОНФИГ ==============
BOT_TOKEN = ""
ADMIN_IDS = []  # ID админов

# API URLs
CRYPTO_API = "https://api.coingecko.com/api/v3"
FIAT_API = "https://api.exchangerate-api.com/v4/latest/USD"

# Популярные криптовалюты
CRYPTO_IDS = {
    "btc": "bitcoin",
    "eth": "ethereum", 
    "usdt": "tether",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "sol": "solana",
    "doge": "dogecoin",
    "ton": "the-open-network",
    "ltc": "litecoin",
    "trx": "tron"
}

# Популярные фиатные валюты
FIAT_CURRENCIES = ["USD", "EUR", "RUB", "UAH", "GBP", "CNY", "JPY", "KZT", "BYN", "PLN"]

# ============== ИНИЦИАЛИЗАЦИЯ ==============
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

DB_PATH = "crypto.db"

# ============== DATABASE ==============
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_banned INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                request_type TEXT,
                query TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_user(user_id: int, username: str, first_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

async def is_banned(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT is_banned FROM users WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] == 1 if row else False

async def ban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def unban_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id, username, first_name, is_banned, created_at FROM users")
        return await cursor.fetchall()

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE is_banned = 1")
        banned = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM requests")
        requests = (await cursor.fetchone())[0]
        
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-1 day')"
        )
        today = (await cursor.fetchone())[0]
        
        return {"total": total, "banned": banned, "requests": requests, "today": today}

async def log_request(user_id: int, request_type: str, query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO requests (user_id, request_type, query) VALUES (?, ?, ?)",
            (user_id, request_type, query)
        )
        await db.commit()

# ============== API ФУНКЦИИ ==============
async def get_crypto_prices(symbols: list[str]) -> dict:
    """Получить цены криптовалют"""
    ids = [CRYPTO_IDS.get(s.lower(), s.lower()) for s in symbols]
    ids_str = ",".join(ids)
    
    async with aiohttp.ClientSession() as session:
        url = f"{CRYPTO_API}/simple/price?ids={ids_str}&vs_currencies=usd,rub,eur&include_24hr_change=true"
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.json()
    return {}

async def get_fiat_rates() -> dict:
    """Получить курсы фиатных валют"""
    async with aiohttp.ClientSession() as session:
        async with session.get(FIAT_API) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("rates", {})
    return {}

def format_crypto_price(data: dict, symbol: str) -> str:
    """Форматировать цену крипты"""
    coin_id = CRYPTO_IDS.get(symbol.lower(), symbol.lower())
    if coin_id not in data:
        return f"❌ {symbol.upper()} не найден"
    
    info = data[coin_id]
    usd = info.get("usd", 0)
    rub = info.get("rub", 0)
    eur = info.get("eur", 0)
    change = info.get("usd_24h_change", 0)
    
    emoji = "🟢" if change >= 0 else "🔴"
    
    return (
        f"💎 <b>{symbol.upper()}</b>\n"
        f"├ USD: <code>${usd:,.2f}</code>\n"
        f"├ RUB: <code>₽{rub:,.2f}</code>\n"
        f"├ EUR: <code>€{eur:,.2f}</code>\n"
        f"└ 24h: {emoji} <code>{change:+.2f}%</code>"
    )

def format_fiat_rate(rates: dict, currency: str) -> str:
    """Форматировать курс фиата"""
    currency = currency.upper()
    if currency not in rates:
        return f"❌ {currency} не найден"
    
    rate = rates[currency]
    
    # Кросс-курсы
    rub_rate = rates.get("RUB", 0)
    eur_rate = rates.get("EUR", 0)
    
    if currency == "USD":
        return (
            f"💵 <b>USD (Доллар США)</b>\n"
            f"├ RUB: <code>₽{rub_rate:,.2f}</code>\n"
            f"└ EUR: <code>€{eur_rate:,.4f}</code>"
        )
    
    usd_value = 1 / rate if rate else 0
    rub_value = rub_rate / rate if rate else 0
    
    return (
        f"💵 <b>{currency}</b>\n"
        f"├ USD: <code>${usd_value:,.4f}</code>\n"
        f"└ RUB: <code>₽{rub_value:,.2f}</code>"
    )

# ============== КЛАВИАТУРЫ ==============
def get_main_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="💎 Крипта", callback_data="menu_crypto"),
            InlineKeyboardButton(text="💵 Валюты", callback_data="menu_fiat")
        ],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_crypto_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, symbol in enumerate(CRYPTO_IDS.keys()):
        row.append(InlineKeyboardButton(text=symbol.upper(), callback_data=f"crypto_{symbol}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_fiat_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, currency in enumerate(FIAT_CURRENCIES):
        row.append(InlineKeyboardButton(text=currency, callback_data=f"fiat_{currency}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Список юзеров", callback_data="admin_users")],
        [InlineKeyboardButton(text="📥 Скачать .txt", callback_data="admin_download")],
        [InlineKeyboardButton(text="🚫 Забанить", callback_data="admin_ban"),
         InlineKeyboardButton(text="✅ Разбанить", callback_data="admin_unban")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ============== ХЕНДЛЕРЫ ==============
@router.message(CommandStart())
async def cmd_start(message: Message):
    if await is_banned(message.from_user.id):
        return await message.answer("🚫 Вы заблокированы")
    
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Я бот для проверки курсов валют и криптовалют.\n\n"
        "📌 <b>Возможности:</b>\n"
        "• Проверка курсов криптовалют\n"
        "• Проверка курсов фиатных валют\n"
        "• Инлайн режим в любом чате\n\n"
        "💡 Используй кнопки ниже или напиши символ валюты (BTC, USD и т.д.)"
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("⛔ Нет доступа")
    
    await message.answer("🔐 <b>Админ-панель</b>", reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)

@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 <b>Справка по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта справка\n"
        "/rate BTC - Курс криптовалюты\n"
        "/rate USD - Курс фиатной валюты\n\n"
        "<b>Инлайн режим:</b>\n"
        f"Напиши <code>@{(await bot.me()).username} BTC</code> в любом чате\n\n"
        "<b>Поддерживаемые крипты:</b>\n"
        f"{', '.join(s.upper() for s in CRYPTO_IDS.keys())}\n\n"
        "<b>Поддерживаемые валюты:</b>\n"
        f"{', '.join(FIAT_CURRENCIES)}"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)

@router.message(Command("rate"))
async def cmd_rate(message: Message):
    if await is_banned(message.from_user.id):
        return
    
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("❌ Укажи валюту: /rate BTC или /rate USD")
    
    symbol = args[1].strip().upper()
    await log_request(message.from_user.id, "command", symbol)
    
    # Проверяем крипта или фиат
    if symbol.lower() in CRYPTO_IDS:
        data = await get_crypto_prices([symbol])
        text = format_crypto_price(data, symbol)
    else:
        rates = await get_fiat_rates()
        text = format_fiat_rate(rates, symbol)
    
    await message.answer(text, parse_mode=ParseMode.HTML)

@router.message(F.text)
async def handle_text(message: Message):
    if await is_banned(message.from_user.id):
        return
    
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    symbol = message.text.strip().upper()
    
    # Проверяем это запрос курса или нет
    if symbol.lower() in CRYPTO_IDS:
        await log_request(message.from_user.id, "text", symbol)
        data = await get_crypto_prices([symbol])
        text = format_crypto_price(data, symbol)
        await message.answer(text, parse_mode=ParseMode.HTML)
    elif symbol in FIAT_CURRENCIES:
        await log_request(message.from_user.id, "text", symbol)
        rates = await get_fiat_rates()
        text = format_fiat_rate(rates, symbol)
        await message.answer(text, parse_mode=ParseMode.HTML)

# ============== CALLBACK HANDLERS ==============
@router.callback_query(F.data == "menu_main")
async def cb_menu_main(callback: CallbackQuery):
    text = (
        "📊 <b>Главное меню</b>\n\n"
        "Выбери категорию:"
    )
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(), parse_mode=ParseMode.HTML)

@router.callback_query(F.data == "menu_crypto")
async def cb_menu_crypto(callback: CallbackQuery):
    await callback.message.edit_text(
        "💎 <b>Криптовалюты</b>\n\nВыбери монету:",
        reply_markup=get_crypto_keyboard(),
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data == "menu_fiat")
async def cb_menu_fiat(callback: CallbackQuery):
    await callback.message.edit_text(
        "💵 <b>Фиатные валюты</b>\n\nВыбери валюту:",
        reply_markup=get_fiat_keyboard(),
        parse_mode=ParseMode.HTML
    )

@router.callback_query(F.data == "menu_help")
async def cb_menu_help(callback: CallbackQuery):
    bot_info = await bot.me()
    text = (
        "📖 <b>Как пользоваться</b>\n\n"
        "1️⃣ Выбери категорию (Крипта/Валюты)\n"
        "2️⃣ Нажми на нужную валюту\n"
        "3️⃣ Или напиши символ в чат (BTC, USD)\n\n"
        f"💡 <b>Инлайн:</b> @{bot_info.username} BTC"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("crypto_"))
async def cb_crypto(callback: CallbackQuery):
    symbol = callback.data.replace("crypto_", "")
    await log_request(callback.from_user.id, "button", symbol)
    
    data = await get_crypto_prices([symbol])
    text = format_crypto_price(data, symbol)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"crypto_{symbol}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_crypto")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@router.callback_query(F.data.startswith("fiat_"))
async def cb_fiat(callback: CallbackQuery):
    currency = callback.data.replace("fiat_", "")
    await log_request(callback.from_user.id, "button", currency)
    
    rates = await get_fiat_rates()
    text = format_fiat_rate(rates, currency)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"fiat_{currency}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu_fiat")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

# ============== ADMIN CALLBACKS ==============
@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)
    
    stats = await get_stats()
    text = (
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего юзеров: <code>{stats['total']}</code>\n"
        f"🆕 За сегодня: <code>{stats['today']}</code>\n"
        f"🚫 Забанено: <code>{stats['banned']}</code>\n"
        f"📨 Запросов: <code>{stats['requests']}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@router.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)
    
    users = await get_all_users()
    text = "👥 <b>Пользователи</b>\n\n"
    
    for user in users[:20]:  # Первые 20
        user_id, username, first_name, is_banned, created = user
        status = "🚫" if is_banned else "✅"
        username_str = f"@{username}" if username else "без юзернейма"
        text += f"{status} <code>{user_id}</code> | {username_str}\n"
    
    if len(users) > 20:
        text += f"\n... и ещё {len(users) - 20} юзеров"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@router.callback_query(F.data == "admin_download")
async def cb_admin_download(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)
    
    users = await get_all_users()
    
    # Формируем txt
    lines = ["user_id\tusername\tfirst_name\tis_banned\tcreated_at"]
    for user in users:
        user_id, username, first_name, is_banned, created = user
        lines.append(f"{user_id}\t{username or '-'}\t{first_name or '-'}\t{is_banned}\t{created}")
    
    content = "\n".join(lines)
    
    file = BufferedInputFile(
        content.encode("utf-8"),
        filename=f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    
    await callback.message.answer_document(file, caption=f"📄 Список юзеров: {len(users)} шт.")
    await callback.answer()

@router.callback_query(F.data == "admin_ban")
async def cb_admin_ban(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)
    
    await callback.message.edit_text(
        "🚫 <b>Бан пользователя</b>\n\n"
        "Отправь ID юзера для бана:",
        parse_mode=ParseMode.HTML
    )
    # Ставим состояние ожидания ID для бана
    await callback.answer()

@router.callback_query(F.data == "admin_unban")
async def cb_admin_unban(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return await callback.answer("⛔ Нет доступа", show_alert=True)
    
    await callback.message.edit_text(
        "✅ <b>Разбан пользователя</b>\n\n"
        "Отправь ID юзера для разбана:",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def cb_admin_back(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        return
    await callback.message.edit_text("🔐 <b>Админ-панель</b>", reply_markup=get_admin_keyboard(), parse_mode=ParseMode.HTML)

# ============== INLINE MODE ==============
@router.inline_query()
async def inline_handler(query: InlineQuery):
    if await is_banned(query.from_user.id):
        return
    
    await add_user(query.from_user.id, query.from_user.username, query.from_user.first_name)
    
    text = query.query.strip().upper()
    results = []
    
    if not text:
        # Показываем популярные
        results.append(
            InlineQueryResultArticle(
                id="help",
                title="💡 Введи символ валюты",
                description="Например: BTC, ETH, USD, EUR",
                input_message_content=InputTextMessageContent(
                    message_text="💡 Напиши символ валюты после @бота\nНапример: BTC, ETH, USD"
                )
            )
        )
    else:
        await log_request(query.from_user.id, "inline", text)
        
        # Ищем в крипте
        if text.lower() in CRYPTO_IDS:
            data = await get_crypto_prices([text])
            formatted = format_crypto_price(data, text)
            results.append(
                InlineQueryResultArticle(
                    id=f"crypto_{text}",
                    title=f"💎 {text}",
                    description="Нажми чтобы отправить курс",
                    input_message_content=InputTextMessageContent(
                        message_text=formatted,
                        parse_mode=ParseMode.HTML
                    )
                )
            )
        
        # Ищем в фиате
        if text in FIAT_CURRENCIES:
            rates = await get_fiat_rates()
            formatted = format_fiat_rate(rates, text)
            results.append(
                InlineQueryResultArticle(
                    id=f"fiat_{text}",
                    title=f"💵 {text}",
                    description="Нажми чтобы отправить курс",
                    input_message_content=InputTextMessageContent(
                        message_text=formatted,
                        parse_mode=ParseMode.HTML
                    )
                )
            )
        
        # Если ничего не нашли
        if not results:
            results.append(
                InlineQueryResultArticle(
                    id="not_found",
                    title=f"❌ {text} не найден",
                    description="Попробуй: BTC, ETH, USD, EUR",
                    input_message_content=InputTextMessageContent(
                        message_text=f"❌ Валюта {text} не найдена"
                    )
                )
            )
    
    await query.answer(results, cache_time=60)

# ============== ADMIN COMMANDS (text) ==============
@router.message(F.text.regexp(r"^/ban\s+(\d+)$"))
async def cmd_ban(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_id = int(message.text.split()[1])
    await ban_user(user_id)
    await message.answer(f"🚫 Пользователь <code>{user_id}</code> забанен", parse_mode=ParseMode.HTML)

@router.message(F.text.regexp(r"^/unban\s+(\d+)$"))
async def cmd_unban(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    user_id = int(message.text.split()[1])
    await unban_user(user_id)
    await message.answer(f"✅ Пользователь <code>{user_id}</code> разбанен", parse_mode=ParseMode.HTML)

# ============== ЗАПУСК ==============
async def main():
    await init_db()
    logging.info("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
