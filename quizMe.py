import json
import os
from dotenv import load_dotenv
import fitz  # PyMuPDF
from PIL import Image
from pathlib import Path
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# prompt

SYSTEM_INSTRUCTION = """
You are an expert exam generator. Your task is to analyze the provided images of exam papers or lecture slides.
Extract all multiple-choice questions (MCQs) and format them into a strict JSON array.

Strict Language Rule:
- You MUST preserve the original language of the questions and options. 
- If the question in the image is in Arabic, the "question", "options", and "explanation" MUST be in Arabic.
- If the question in the image is in English, the "question", "options", and "explanation" MUST be in English.
- NEVER translate the questions or options. Keep them exactly as they appear in the source image.

Strict JSON Output Format:
[
  {
    "question": "The question text here (in its original language)",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,  // Index of the correct answer (0-based)
    "explanation": "Brief explanation of why this answer is correct (in the same language as the question)."
  }
]

Rules:
1. Do not include any markdown, backticks (```json), or conversational text. Output ONLY the raw JSON array.
2. Ignore header/footer noise like phone battery, time, or signal bars from screenshots.
3. Keep the number of options between 2 and 4 (Telegram Poll limits).
4. Ensure text length for questions (<300 chars) and options (<100 chars) complies with Telegram limits.
"""

# The /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧠 أهلاً بك في QuizMe!\n"
        "أرسل لي ملف PDF (تجميعات، صور، أو أسئلة) وسأقوم بتحويله لك إلى كويز تفاعلي فوراً! 🚀"
    )


# the /stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # check if the bot is currently sending quiz
    if context.user_data.get("is_sending_quiz"):
        context.user_data["stop_requested"] = True
        await update.message.reply_text("🛑 جاري إيقاف الكويز... تم إلغاء بقية الأسئلة بنجاح.")
    else:
        await update.message.reply_text("💡تم ايقاف الكويز")

# processing the file
async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

# Define the secure path inside the temp folder
    pdf_path = temp_dir / f"user_{update.effective_user.id}.pdf"    

    status_message = await update.message.reply_text(
        "⏳ جاري تحميل الملف وتحليله بالذكاء الاصطناعي..."
    )

    file = await update.message.document.get_file()
    await file.download_to_drive(str(pdf_path))

    try:
        doc = fitz.open(pdf_path)
        images_to_send = []
        saved_paths = []

        # 
        max_pages = min(len(doc), 10)

        for i in range(max_pages):
            page = doc[i]
            pix = page.get_pixmap(dpi=200)

            # safely join temp directory with the image file
            img_path = temp_dir / f"page_{update.effective_user.id}_{i}.png"

            # convert path to string 
            pix.save(str(img_path))

            # opening the image from new temp path
            img = Image.open(str(img_path))
            images_to_send.append(img)

            saved_paths.append(str(img_path))
        doc.close()

        if not images_to_send:
            await status_message.edit_text(" الملف فارغ أو لا يحتوي على صفحات.")
            return

        await status_message.edit_text(
            "🤖 جاري قراءة الأسئلة وحلها ..."
        )
        # images and the system instructions are added into one list
        contents = images_to_send + [SYSTEM_INSTRUCTION]

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)

        # processing the json
        quiz_data = json.loads(response.text)

        if not quiz_data or not isinstance(quiz_data, list):
            await status_message.edit_text(
                "❌ لم أتمكن من استخراج أسئلة واضحة من هذا الملف. تأكد أنه يحتوي على خيارات."
            )
            return

        await status_message.delete() 

        context.user_data["is_sending_quiz"] = True
        context.user_data["stop_requested"] = False

        # sending the intractive quiz to the user
        for item in quiz_data:
            # checking if the the user sent the stop command
            if context.user_data.get("stop_requested"):
                break 

            # checking 
            question = item.get("question", "")[:299]
            options = [str(opt)[:99] for opt in item.get("options", [])][:4]
            correct_index = int(item.get("correct_index", 0))
            explanation = item.get("explanation", "")[:199]

            if len(options) >= 2:
                await context.bot.send_poll(
                    chat_id=update.effective_chat.id,
                    question=question,
                    options=options,
                    type="quiz",
                    correct_option_id=correct_index,
                    explanation=explanation,
                    is_anonymous=False,
                )
                
                # for preventing spam 
                import asyncio
                await asyncio.sleep(1)

        context.user_data["is_sending_quiz"] = False
        context.user_data["stop_requested"] = False

    except Exception as e:
        print(f"Error occurred: {e}")
        await status_message.edit_text(
            "💥 حدث خطأ أثناء معالجة الملف، تأكد من جودة الصور داخل الـ PDF."
        )
    finally:
        if 'img_path' in locals() and os.path.exists(str(img_path)):
            os.remove(str(img_path))
        if os.path.exists(str(pdf_path)):
            os.remove(str(pdf_path))

# Build the application using the token (Make sure this variable name matches your setup)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Add handlers to the application
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))


if __name__ == '__main__':
    from aiohttp import web
    from telegram import Update

    # 1. Define the webhook handler to receive updates from Telegram
    async def telegram_webhook(request):
        global application  # Access the global application variable
        
        # Read the incoming JSON data from Telegram
        data = await request.json()
        # Convert JSON to a Telegram Update object and push it to the application queue
        update = Update.de_json(data, application.bot)
        await application.update_queue.put(update)
        return web.Response(text="OK")

    # Simple health check endpoint for browser access and Render pings
    async def hello(request):
        return web.Response(text="Bot Webhook is running smoothly!")

    # 2. Initialize the aiohttp web application
    web_app = web.Application()
    web_app.router.add_post("/webhook", telegram_webhook)  # Endpoint for Telegram updates
    web_app.router.add_get("/", hello)                      # Root endpoint for Render port scan

    port = int(os.environ.get("PORT", 10000))
    
    # 3. Startup hook to initialize the bot and set the webhook URL with Telegram
    async def start_bot_webhook(app_arg):
        global application  # Access the global application variable
        
        await application.initialize()
        await application.start()
        # Register the webhook URL and secret token with Telegram
        await application.bot.set_webhook(
            url="https://quizme-telegram-bot-1.onrender.com/webhook",
            secret_token="quizme_secret_2025"
        )
        print("Webhook has been set successfully with Telegram!")

    # Attach the startup hook to the web application
    web_app.on_startup.append(start_bot_webhook)
    
    # 4. Start the aiohttp web server (This successfully passes Render's port binding check)
    web.run_app(web_app, host="0.0.0.0", port=port)