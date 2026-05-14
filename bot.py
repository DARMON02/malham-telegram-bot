import os
import requests
from dotenv import load_dotenv

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
APPS_SCRIPT_URL = os.getenv("APPS_SCRIPT_URL")
API_SECRET = os.getenv("API_SECRET")

users = {}


def api(payload: dict) -> dict:
    payload["secret"] = API_SECRET

    r = requests.post(
        APPS_SCRIPT_URL,
        json=payload,
        timeout=20,
    )

    return r.json()


def contact_keyboard():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
    )


def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📡 Davomat linkim"],
            ["📊 Bugungi hisobim"],
            ["📅 Oylik hisobotim"],
        ],
        resize_keyboard=True,
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id in users:
        await update.message.reply_text(
            "✅ Siz tizimga ulangansiz.",
            reply_markup=main_keyboard(),
        )
        return

    await update.message.reply_text(
        "Assalomu alaykum.\n\nTelefon raqamingizni yuboring.",
        reply_markup=contact_keyboard(),
    )


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    contact = update.message.contact

    if not contact:
        return

    phone = str(contact.phone_number).replace("+", "").replace(" ", "").replace("-", "")

    print("TELEGRAM PHONE:", phone)

    res = api({
        "action": "find_employee_by_phone",
        "phone": phone
    })

    print("APPS SCRIPT JAVOB:", res)

    if not res.get("ok"):

        await update.message.reply_text(
            "❌ Telefon raqam Xodimlar bazasidan topilmadi.",
            reply_markup=contact_keyboard(),
        )

        return

    employee = res["employee"]

    users[update.effective_chat.id] = employee

    await update.message.reply_text(
        f"✅ Tizim ulandi\n\nXodim: {employee['ism']}",
        reply_markup=main_keyboard(),
    )

    await send_attendance_link(update, employee)


async def send_attendance_link(update: Update, employee: dict):
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 Davomatni ochish",
                url=employee["davomat_link"],
            )
        ]
    ])

    await update.message.reply_text(
        "📡 Davomat uchun pastdagi tugmani bosing:",
        reply_markup=keyboard,
    )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in users:
        await update.message.reply_text(
            "❌ Avval /start bosing va telefon raqamingizni yuboring.",
            reply_markup=contact_keyboard(),
        )
        return

    employee = users[chat_id]

    if text == "📡 Davomat linkim":
        await send_attendance_link(update, employee)
        return

    if text == "📊 Bugungi hisobim":
        res = api({
            "action": "today_report",
            "id": employee["id"],
        })

        await update.message.reply_text(
            res.get("text", "❌ Hisobot olinmadi.")
        )
        return

    if text == "📅 Oylik hisobotim":
        res = api({
            "action": "monthly_report",
            "id": employee["id"],
        })

        await update.message.reply_text(
            res.get("text", "❌ Hisobot olinmadi.")
        )
        return

    await update.message.reply_text(
        "Kerakli bo‘limni tanlang.",
        reply_markup=main_keyboard(),
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env ichida yo‘q")

    if not APPS_SCRIPT_URL:
        raise RuntimeError("APPS_SCRIPT_URL .env ichida yo‘q")

    if not API_SECRET:
        raise RuntimeError("API_SECRET .env ichida yo‘q")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("BOT ISHGA TUSHDI")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
