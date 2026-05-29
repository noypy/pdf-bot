import os, zipfile
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from PyPDF2 import PdfReader, PdfWriter, PdfMerger

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ HANDLE PDF
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    name = update.message.document.file_name
    await file.download_to_drive(name)

    if context.user_data.get("merge"):
        context.user_data.setdefault("files", []).append(name)
        await update.message.reply_text("📄 Added to merge list")
    else:
        context.user_data["pdf"] = name
        await update.message.reply_text("✅ PDF Saved")

# ✅ MERGE
async def merge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["merge"] = True
    context.user_data["files"] = []
    await update.message.reply_text("📂 Send PDFs then /done")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = context.user_data.get("files", [])

    if len(files) == 0:
        await update.message.reply_text("❌ No files sent")
        return

    merger = PdfMerger()
    for f in files:
        merger.append(f)

    merger.write("merged.pdf")
    merger.close()

    await update.message.reply_document(open("merged.pdf", "rb"))

    # reset
    context.user_data["merge"] = False

# ✅ SPLIT
async def split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    reader = PdfReader(pdf)
    files = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        name = f"page_{i+1}.pdf"

        with open(name, "wb") as f:
            writer.write(f)

        files.append(name)

    with zipfile.ZipFile("split.zip", "w") as z:
        for f in files:
            z.write(f)

    await update.message.reply_document(open("split.zip", "rb"))

# ✅ PROTECT
async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf = context.user_data.get("pdf")

    if not pdf:
        await update.message.reply_text("❌ Send PDF first")
        return

    if not context.args:
        await update.message.reply_text("❌ Use: /protect 1234")
        return

    password = context.args[0]

    reader = PdfReader(pdf)
    writer = PdfWriter()

    for p in reader.pages:
        writer.add_page(p)

    writer.encrypt(password)

    with open("protected.pdf", "wb") as f:
        writer.write(f)

    await update.message.reply_document(open("protected.pdf", "rb"))

# ✅ APP START
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("merge", merge))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("split", split))
    app.add_handler(CommandHandler("protect", protect))

    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

    print("🔥 BOT RUNNING...")
    app.run_polling()

if __name__ == "__main__":
    main()
