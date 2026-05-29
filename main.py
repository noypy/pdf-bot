import os, zipfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ HANDLE PDF (FIXED)
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    name = update.message.document.file_name
    await file.download_to_drive(name)

    # merge mode එකේ නම් collect කරන්න
    if context.user_data.get("merge"):
        context.user_data.setdefault("files", []).append(name)
    else:
        context.user_data["pdf"] = name
        await update.message.reply_text("✅ PDF Saved")

# ✅ MERGE MODE START
async def merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["merge"] = True
    context.user_data["files"] = []
    await update.message.reply_text("📂 Send PDFs then /done")

# ✅ MERGE DONE
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = context.user_data.get("files")

    if not files:
        await update.message.reply_text("❌ No files to merge")
        return

    merger = PdfMerger()
    for f in files:
        merger.append(f)

    merger.write("merged.pdf")
    merger.close()

    await update.message.reply_document(open("merged.pdf", "rb"))

# ✅ SPLIT ALL
async def split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")
    if not pdf:
        await update.message.reply_text("❌ Send a PDF first")
        return

    reader = PdfReader(pdf)
    files = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        name = f"p{i+1}.pdf"
        with open(name, "wb") as f:
            writer.write(f)
        files.append(name)

    with zipfile.ZipFile("split.zip", "w") as z:
        for f in files:
            z.write(f)

    await update.message.reply_document(open("split.zip", "rb"))

# ✅ RANGE SPLIT
async def range_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send a PDF first")
        return

    try:
        args = context.args[0]
        start, end = map(int, args.split("-"))
    except:
        await update.message.reply_text("❌ Use like: /range 1-5")
        return

    reader = PdfReader(pdf)
    files = []

    for i in range(start - 1, end):
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        name = f"r{i+1}.pdf"
        with open(name, "wb") as f:
            writer.write(f)
        files.append(name)

    with zipfile.ZipFile("range.zip", "w") as z:
        for f in files:
            z.write(f)

    await update.message.reply_document(open("range.zip", "rb"))

# ✅ COMPRESS (basic)
async def compress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    reader = PdfReader(pdf)
    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    with open("compressed.pdf", "wb") as f:
        writer.write(f)

    await update.message.reply_document(open("compressed.pdf", "rb"))

# ✅ PASSWORD PROTECT
async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    try:
        password = context.args[0]
    except:
        await update.message.reply_text("❌ Use: /protect 1234")
        return

    reader = PdfReader(pdf)
    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    writer.encrypt(password)

    with open("protected.pdf", "wb") as f:
        writer.write(f)

    await update.message.reply_document(open("protected.pdf", "rb"))

# ✅ UNLOCK
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    try:
        password = context.args[0]
    except:
        await update.message.reply_text("❌ Use: /unlock 1234")
        return

    reader = PdfReader(pdf)

    if reader.is_encrypted:
        reader.decrypt(password)

    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    with open("unlocked.pdf", "wb") as f:
        writer.write(f)

    await update.message.reply_document(open("unlocked.pdf", "rb"))

# ✅ APP START
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("merge", merge))
app.add_handler(CommandHandler("done", done))
app.add_handler(CommandHandler("split", split))
app.add_handler(CommandHandler("range", range_split))
app.add_handler(CommandHandler("compress", compress))
app.add_handler(CommandHandler("protect", protect))
app.add_handler(CommandHandler("unlock", unlock))

# ✅ SINGLE PDF HANDLER (FIXED)
app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

print("🔥 FULL PRO BOT RUNNING...")
app.run_polling()
