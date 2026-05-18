# 🧠 QuizMe: AI-Powered Interactive Quiz Generator Telegram Bot

An end-to-end, asynchronous Telegram bot designed to automate educational quiz generation from old exams pdf files. Powered by **Gemini 2.5 Flash Vision API**, the system processes files, extracts multilingual text, and instantly deploys interactive Telegram Native Polls with logical explanations.

---

## 🚀 Key Features

* **Advanced Document Intelligence:** Converts PDF documents into high-resolution images for vision processing.
* **Multilingual Context Preservation:** Automatically detects and retains the source language (Arabic/English), preventing unwanted translations.
* **Native Telegram UX:** Generates actual **Telegram Quiz Polls** with immediate feedback, colored animations, and conceptual explanations.
* **Flow Control (On-Demand Stop):** Includes a dynamic `/stop` command utilizing state management to halt quiz streaming instantly.
* **Production-Grade Security:** Zero hardcoded tokens. Seamlessly manages secrets via environment variables (`.env`) and keeps temporary files isolated.

---

## 🛠️ System Architecture & Tech Stack

The system implements an asynchronous pipeline to ensure smooth concurrency handling without blocking the main event loop:

```text
User PDF ──> PyMuPDF Pipeline ──> Image Extractions ──> Gemini Vision API ──> Structured JSON ──> Telegram Native Quiz Polls
```

* **Backend Framework:** Python with `python-telegram-bot` (Asynchronous I/O)
* **Core AI Engine:** Google GenAI SDK (`gemini-2.5-flash` model)
* **Vision & Document Processing:** `PyMuPDF` (fitz) & `Pillow` (PIL)
* **Deployment & Environment:** Render Cloud Platform & Containerization via Environment Variables (`python-dotenv`)

---

## 📁 Project Structure

```text
├── bot.py             # Main asynchronous bot implementation & logic
├── requirements.txt   # Production dependencies
├── .gitignore         # Prevents sensitive files and caches from being tracked
└── temp/              # Isolated directory for handling temporary runtime files
```

---

## ⚙️ Setup & Local Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Intsaar/QuizMe-Telegram-Bot.git
cd QuizMe-Telegram-Bot
```
### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Run the Bot
```bash
python bot.py
```

---
## ☁️ Deployment (Render)

This project is configured to run smoothly as a *Web Service* on *Render* (Free Tier), using a built-in aiohttp web server to handle port binding efficiently without extra hosting costs.

### How to Deploy:
1. *Create a Web Service* on [Render](https://render.com/).
2. Connect your GitHub repository: QuizMe-Telegram-Bot.
3. Select the *Free Tier ($0/month)*.
4. Set the following commands:
   - *Build Command:* pip install -r requirements.txt
   - *Start Command:* python quizMe.py
5. Add your environment variables under *Advanced*:
   - TELEGRAM_TOKEN: Your Telegram Bot API Token.
   - GEMINI_API_KEY: Your Google Gemini API Key.
6. Click *Create Web Service* and the bot will be live 24/7!

---

## 📄 License
This project is open-source and available under the MIT License.
