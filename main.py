import os, zipfile
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ CLEAN FILES
def clean(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)

# ✅ START MENU (BUTTON UI)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✂️ Split", callback_data="split")],
        [InlineKeyboardButton("📚 Merge", callback_data="merge")],
        [InlineKeyboardButton("🔐 Protect", callback_data="protect")],
        [InlineKeyboardButton("📦 Compress", callback_data="compress")]
    ]

    await update.message.reply_text(
        "🤖 PDF BOT READY\nSelect option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ✅ BUTTON HANDLER
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data

    if action == "merge":
        context.user_data["merge"] = True
        context.user_data["files"] = []
        await query.message.reply_text("📂 Send PDFs then /done")

    elif action == "split":
        await query.message.reply_text("📤 Send PDF to split")

    elif action == "protect":
        await query.message.reply_text("📤 Send PDF then use /protect 1234")

    elif action == "compress":
        await query.message.reply_text("📤 Send PDF then use /compress")

# ✅ HANDLE PDF
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    name = update.message.document.file_name
    await file.download_to_drive(name)

    if context.user_data.get("merge"):
        context.user_data.setdefault("files", []).append(name)
        await update.message.reply_text("✅ Added")
    else:
        context.user_data["pdf"] = name
        await update.message.reply_text("✅ Saved")

# ✅ MERGE DONE
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = context.user_data.get("files", [])

    if not files:
        await update.message.reply_text("❌ No files")
        return

    msg = await update.message.reply_text("⏳ Processing...")

    merger = PdfMerger()
    for f in files:
        merger.append(f)

    merger.write("merged.pdf")
    merger.close()

    await update.message.reply_document(open("merged.pdf", "rb"))

    clean(files + ["merged.pdf"])
    context.user_data["merge"] = False

    await msg.delete()

# ✅ SPLIT
async def split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    msg = await update.message.reply_text("⏳ Processing...")

    reader = PdfReader(pdf)
    files = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        name = f"page_{i}.pdf"

        with open(name, "wb") as f:
            writer.write(f)

        files.append(name)

    with zipfile.ZipFile("split.zip", "w") as z:
        for f in files:
            z.write(f)

    await update.message.reply_document(open("split.zip", "rb"))

    clean(files + ["split.zip", pdf])
    await msg.delete()

# ✅ COMPRESS
async def compress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    msg = await update.message.reply_text("⏳ Processing...")

    reader = PdfReader(pdf)
    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    with open("compressed.pdf", "wb") as f:
        writer.write(f)

    await update.message.reply_document(open("compressed.pdf", "rb"))

    clean(["compressed.pdf", pdf])
    await msg.delete()

# ✅ PROTECT
async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    if not context.args:
        await update.message.reply_text("❌ Use: /protect 1234")
        return

    msg = await update.message.reply_text("⏳ Processing...")

    password = context.args[0]
    reader = PdfReader(pdf)
    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    writer.encrypt(password)

    with open("protected.pdf", "wb") as f:
        writer.write(f)

    await update.message.reply_document(open("protected.pdf", "rb"))

    clean(["protected.pdf", pdf])
    await msg.delete()

# ✅ MAIN
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("split", split))
    app.add_handler(CommandHandler("compress", compress))
    app.add_handler(CommandHandler("protect", protect))

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    print("🔥 NEXT LEVEL BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
