Here is a project description for GitHub based on the provided code, duplicated in English and Russian.

---

# 🇬🇧 English Version

# 💱 Crypto & Fiat Rate Telegram Bot

A powerful asynchronous Telegram bot built with **aiogram** for tracking cryptocurrency and fiat currency exchange rates in real-time. It features an inline mode, user database management, and an administrative panel for monitoring and moderation.

## ✨ Features

-   **Real-time Rates:** Get current prices for popular cryptocurrencies (BTC, ETH, USDT, etc.) and fiat currencies (USD, EUR, RUB, etc.).
-   **Multiple Sources:** Uses CoinGecko API for crypto and ExchangeRate API for fiat.
-   **Inline Mode:** Check rates directly in any chat by typing `@bot_name BTC`.
-   **Database Storage:** Uses **SQLite** (`aiosqlite`) to store user data, request logs, and ban lists.
-   **Admin Panel:**
    -   View statistics (total users, active today, banned, total requests).
    -   View user list.
    -   Download user database as `.txt`.
    -   Ban/Unban users by ID.
-   **User Commands:**
    -   `/start` - Main menu.
    -   `/help` - Instructions and supported currencies.
    -   `/rate <symbol>` - Quick rate check (e.g., `/rate BTC`).
-   **Interactive Keyboards:** Convenient inline buttons for navigating currencies.

## 🛠 Tech Stack

-   **Language:** Python 3.7+
-   **Framework:** `aiogram` (Async Telegram Bot API)
-   **Database:** `aiosqlite` (Async SQLite)
-   **HTTP Client:** `aiohttp`
-   **APIs:** CoinGecko, ExchangeRate-API

## 🚀 Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

2.  **Install dependencies:**
    ```bash
    pip install aiogram aiohttp aiosqlite
    ```

3.  **Configure the bot:**
    Open `cr.py` and edit the configuration section:
    ```python
    BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
    ADMIN_IDS = [123456789]  # Your Telegram User ID
    ```

4.  **Run the bot:**
    ```bash
    python cr.py
    ```

## ⚙️ Configuration

-   **BOT_TOKEN:** Get this from [@BotFather](https://t.me/BotFather).
-   **ADMIN_IDS:** Add your Telegram numeric ID to access admin commands (`/admin`, `/ban`, etc.).
-   **DB_PATH:** Default is `crypto.db`. The database is created automatically on first run.

## 📖 Usage

### User Commands
-   **Menu:** Click `/start` to see the main keyboard.
-   **Quick Check:** Send a currency symbol directly (e.g., `BTC`, `USD`).
-   **Inline:** Type `@your_bot_name ETH` in any chat.

### Admin Commands
-   `/admin` - Open admin control panel.
-   `/ban <user_id>` - Ban a user.
-   `/unban <user_id>` - Unban a user.

## ⚠️ Disclaimer
-   Ensure your `BOT_TOKEN` is kept private. Do not commit it to public repositories.
-   Free API tiers (CoinGecko, ExchangeRate) have rate limits. For high-load projects, consider using paid API keys or caching mechanisms.

---

# 🇷🇺 Русская версия

# 💱 Telegram Бот Курсов Валют и Крипты

Мощный асинхронный Telegram бот на базе **aiogram** для отслеживания курсов криптовалют и фиатных валют в реальном времени.Includes inline-режим, управление базой данных пользователей и админ-панель для мониторинга и модерации.

## ✨ Возможности

-   **Актуальные курсы:** Получение текущих цен на популярные криптовалюты (BTC, ETH, USDT и др.) и фиатные валюты (USD, EUR, RUB и др.).
-   **Несколько источников:** Использует CoinGecko API для крипты и ExchangeRate API для фиата.
-   **Inline Режим:** Проверка курса прямо в любом чате через `@имя_бота BTC`.
-   **База данных:** Использует **SQLite** (`aiosqlite`) для хранения данных пользователей, логов запросов и черного списка.
-   **Админ-панель:**
    -   Просмотр статистики (всего юзеров, активные за сегодня, забанены, всего запросов).
    -   Просмотр списка пользователей.
    -   Скачивание базы пользователей в формате `.txt`.
    -   Бан/Разбан пользователей по ID.
-   **Команды пользователя:**
    -   `/start` - Главное меню.
    -   `/help` - Инструкция и список поддерживаемых валют.
    -   `/rate <символ>` - Быстрая проверка курса (например, `/rate BTC`).
-   **Интерактивные клавиатуры:** Удобные inline-кнопки для навигации по валютам.

## 🛠 Технологии

-   **Язык:** Python 3.7+
-   **Фреймворк:** `aiogram` (Async Telegram Bot API)
-   **База данных:** `aiosqlite` (Async SQLite)
-   **HTTP Клиент:** `aiohttp`
-   **API:** CoinGecko, ExchangeRate-API

## 🚀 Установка

1.  **Склонируйте репозиторий:**
    ```bash
    git clone <ссылка-на-репозиторий>
    cd <папка-проекта>
    ```

2.  **Установите зависимости:**
    ```bash
    pip install aiogram aiohttp aiosqlite
    ```

3.  **Настройте бота:**
    Откройте `cr.py` и отредактируйте секцию конфигурации:
    ```python
    BOT_TOKEN = "ВАШ_ТОКЕН_ТЕЛЕГРАМ_БОТА"
    ADMIN_IDS = [123456789]  # Ваш числовой ID в Telegram
    ```

4.  **Запустите бота:**
    ```bash
    python cr.py
    ```

## ⚙️ Конфигурация

-   **BOT_TOKEN:** Получите у [@BotFather](https://t.me/BotFather).
-   **ADMIN_IDS:** Добавьте свой числовой ID Telegram для доступа к админ-командам (`/admin`, `/ban` и т.д.).
-   **DB_PATH:** По умолчанию `crypto.db`. База данных создается автоматически при первом запуске.

## 📖 Использование

### Команды пользователя
-   **Меню:** Нажмите `/start`, чтобы увидеть главную клавиатуру.
-   **Быстрая проверка:** Отправьте символ валюты прямо в чат (например, `BTC`, `USD`).
-   **Inline:** Введите `@ваш_бот ETH` в любом чате.

### Команды администратора
-   `/admin` - Открыть панель управления.
-   `/ban <user_id>` - Забанить пользователя.
-   `/unban <user_id>` - Разбанить пользователя.

## ⚠️ Предупреждение
-   Убедитесь, что ваш `BOT_TOKEN` хранится в секрете. Не коммитьте его в публичные репозитории.
-   Бесплатные тарифы API (CoinGecko, ExchangeRate) имеют ограничения по количеству запросов. Для проектов с высокой нагрузкой рекомендуется использовать платные ключи API или механизмы кэширования.
