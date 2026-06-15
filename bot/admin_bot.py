#!/usr/bin/env python3
"""
AI Playground Telegram Admin Bot
Full admin control panel via Telegram
"""

import os
import asyncio
import httpx
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "0"))
API_URL = os.getenv("API_URL", "http://localhost:8000")
ADMIN_TOKEN = os.getenv("ADMIN_JWT_TOKEN", "")

# Conversation states
WAITING_PROVIDER, WAITING_KEY = range(2)
WAITING_BAN_ID, WAITING_UNBAN_ID = range(2, 4)
WAITING_BROADCAST = 4
WAITING_LIMIT_USER, WAITING_LIMIT_VALUE = range(5, 7)


def admin_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != ADMIN_CHAT_ID:
            await update.message.reply_text("❌ Unauthorized")
            return
        return await func(update, context)
    return wrapper


async def api_get(endpoint: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{API_URL}{endpoint}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        return resp.json()


async def api_post(endpoint: str, data: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{API_URL}{endpoint}",
            json=data,
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        return resp.json()


async def api_delete(endpoint: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.delete(
            f"{API_URL}{endpoint}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"}
        )
        return resp.json()


# ===================== COMMANDS =====================

@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data="stats"),
         InlineKeyboardButton("👥 Users", callback_data="users")],
        [InlineKeyboardButton("🤖 Models", callback_data="models"),
         InlineKeyboardButton("🔑 API Keys", callback_data="apikeys")],
        [InlineKeyboardButton("🚫 Ban User", callback_data="ban"),
         InlineKeyboardButton("✅ Unban User", callback_data="unban")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast"),
         InlineKeyboardButton("⚙️ Set Limit", callback_data="setlimit")],
        [InlineKeyboardButton("❤️ Health Check", callback_data="health"),
         InlineKeyboardButton("💾 Backup DB", callback_data="backup")],
    ]
    await update.message.reply_text(
        "🎮 *AI Playground Admin Panel*\n\nSelect an action:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


@admin_only
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await api_get("/api/admin/stats")
    text = (
        f"📊 *System Statistics*\n\n"
        f"👥 Total Users: `{data.get('total_users', 0)}`\n"
        f"💬 Total Messages: `{data.get('total_messages', 0)}`\n"
        f"📅 Today Messages: `{data.get('today_messages', 0)}`\n"
        f"🤖 Active Models: `{data.get('active_models', 0)}`\n"
        f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


@admin_only
async def models_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    models = await api_get("/api/admin/models")
    if not models:
        await update.message.reply_text("No models found")
        return
    
    keyboard = []
    text = "🤖 *Models List*\n\n"
    for m in models:
        status = "✅" if m["is_enabled"] else "❌"
        text += f"{status} `{m['display_name']}` ({m['provider']})\n"
        action = "disable" if m["is_enabled"] else "enable"
        keyboard.append([InlineKeyboardButton(
            f"{'❌ Disable' if m['is_enabled'] else '✅ Enable'} {m['display_name']}",
            callback_data=f"toggle_{m['id']}_{not m['is_enabled']}"
        )])
    
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


@admin_only
async def apikeys_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keys = await api_get("/api/admin/api-keys")
    text = "🔑 *API Keys*\n\n"
    if not keys:
        text += "No API keys configured"
    for k in keys:
        text += f"• `{k['provider']}` - {k.get('label', 'No label')}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Key", callback_data="addkey")],
        [InlineKeyboardButton("🗑 Delete Key", callback_data="delkey")],
    ]
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


@admin_only  
async def health_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{API_URL}/health")
            data = resp.json()
        text = f"❤️ *Health Check*\n\nStatus: `{data.get('status', 'unknown')}`\n🟢 API is online!"
    except Exception as e:
        text = f"🔴 API is DOWN!\nError: `{str(e)}`"
    
    await update.message.reply_text(text, parse_mode="Markdown")


# ===================== CALLBACK HANDLERS =====================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_CHAT_ID:
        await query.edit_message_text("❌ Unauthorized")
        return
    
    data = query.data
    
    if data == "stats":
        stats = await api_get("/api/admin/stats")
        text = (
            f"📊 *Statistics*\n\n"
            f"👥 Users: `{stats.get('total_users', 0)}`\n"
            f"💬 Total Messages: `{stats.get('total_messages', 0)}`\n"
            f"📅 Today: `{stats.get('today_messages', 0)}`\n"
            f"🤖 Active Models: `{stats.get('active_models', 0)}`"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif data == "health":
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{API_URL}/health")
            await query.edit_message_text("❤️ API Status: 🟢 *Online*", parse_mode="Markdown")
        except:
            await query.edit_message_text("❤️ API Status: 🔴 *Offline*", parse_mode="Markdown")
    
    elif data == "models":
        models = await api_get("/api/admin/models")
        text = "🤖 *Models*\n\n"
        keyboard = []
        for m in models:
            status = "✅" if m["is_enabled"] else "❌"
            text += f"{status} {m['display_name']} ({m['provider']})\n"
            new_state = str(not m["is_enabled"]).lower()
            keyboard.append([InlineKeyboardButton(
                f"{'❌ Disable' if m['is_enabled'] else '✅ Enable'} {m['display_name']}",
                callback_data=f"toggle_{m['id']}_{new_state}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back")])
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("toggle_"):
        parts = data.split("_")
        model_id, enabled_str = parts[1], parts[2]
        enabled = enabled_str == "true"
        result = await api_post("/api/admin/models/toggle", {"model_id": model_id, "enabled": enabled})
        await query.edit_message_text(f"✅ {result.get('message', 'Done')}")
    
    elif data == "users":
        users = await api_get("/api/admin/users")
        text = f"👥 *Users* (last 10)\n\n"
        for u in users[:10]:
            banned = "🚫" if u.get("is_banned") else "✅"
            text += f"{banned} `{u['username']}` - {u['email']}\n"
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif data == "apikeys":
        keys = await api_get("/api/admin/api-keys")
        text = "🔑 *API Keys*\n\n"
        for k in keys:
            text += f"• `{k['provider']}` - {k.get('label', '-')}\n"
        if not keys:
            text += "No keys configured\n"
        text += "\nSend `/addkey provider:your_key` to add"
        await query.edit_message_text(text, parse_mode="Markdown")
    
    elif data == "back":
        keyboard = [
            [InlineKeyboardButton("📊 Stats", callback_data="stats"),
             InlineKeyboardButton("👥 Users", callback_data="users")],
            [InlineKeyboardButton("🤖 Models", callback_data="models"),
             InlineKeyboardButton("🔑 API Keys", callback_data="apikeys")],
            [InlineKeyboardButton("❤️ Health", callback_data="health")],
        ]
        await query.edit_message_text(
            "🎮 *AI Playground Admin Panel*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ===================== CONVERSATION HANDLERS =====================

@admin_only
async def addkey_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /addkey openai:sk-xxxx"""
    text = update.message.text.replace("/addkey", "").strip()
    if ":" not in text:
        await update.message.reply_text("Usage: `/addkey provider:api_key`\nExample: `/addkey openai:sk-xxxx`", parse_mode="Markdown")
        return
    
    provider, key = text.split(":", 1)
    result = await api_post("/api/admin/api-keys", {"provider": provider.strip(), "key_value": key.strip()})
    await update.message.reply_text(f"✅ {result.get('message', 'Done')}")


@admin_only
async def delkey_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /delkey openai"""
    provider = update.message.text.replace("/delkey", "").strip()
    if not provider:
        await update.message.reply_text("Usage: `/delkey provider`\nExample: `/delkey openai`", parse_mode="Markdown")
        return
    result = await api_delete(f"/api/admin/api-keys/{provider}")
    await update.message.reply_text(f"✅ {result.get('message', 'Done')}")


@admin_only
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /ban user_id"""
    user_id = update.message.text.replace("/ban", "").strip()
    if not user_id:
        await update.message.reply_text("Usage: `/ban user_id`", parse_mode="Markdown")
        return
    result = await api_post("/api/admin/users/ban", {"user_id": user_id})
    await update.message.reply_text(f"🚫 {result.get('message', 'Done')}")


@admin_only
async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /unban user_id"""
    user_id = update.message.text.replace("/unban", "").strip()
    if not user_id:
        await update.message.reply_text("Usage: `/unban user_id`", parse_mode="Markdown")
        return
    result = await api_post("/api/admin/users/unban", {"user_id": user_id})
    await update.message.reply_text(f"✅ {result.get('message', 'Done')}")


@admin_only
async def setlimit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Usage: /setlimit user_id:50"""
    text = update.message.text.replace("/setlimit", "").strip()
    if ":" not in text:
        await update.message.reply_text("Usage: `/setlimit user_id:daily_limit`\nExample: `/setlimit abc123:100`", parse_mode="Markdown")
        return
    user_id, limit = text.split(":", 1)
    result = await api_post("/api/admin/limits", {"user_id": user_id.strip(), "daily_message_limit": int(limit.strip())})
    await update.message.reply_text(f"✅ {result.get('message', 'Done')}")


@admin_only
async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = await api_get("/api/admin/users")
    text = "👥 *User List*\n\n"
    for u in users[:20]:
        banned = "🚫" if u.get("is_banned") else "✅"
        text += f"{banned} `{u['id'][:8]}...` {u['username']} ({u['email']})\n"
    await update.message.reply_text(text, parse_mode="Markdown")


def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("models", models_cmd))
    app.add_handler(CommandHandler("apikeys", apikeys_cmd))
    app.add_handler(CommandHandler("health", health_cmd))
    app.add_handler(CommandHandler("addkey", addkey_start))
    app.add_handler(CommandHandler("delkey", delkey_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("setlimit", setlimit_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
