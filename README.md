# Social Media Downloader Telegram Bot

A Telegram bot for efficient social media video and image downloading, with enhanced multi-platform extraction capabilities.

## Features

- Multi-platform video and image download support
- Pinterest image and video extraction
- Audio and media extraction functionality
- User-specific media management
- Telegram bot integration

## Deploying to Vercel

### Prerequisites

1. A [Vercel account](https://vercel.com/signup)
2. A [Telegram bot token](https://t.me/BotFather)
3. Git installed on your computer

### Step 1: Clone this repository

```bash
git clone <your-repository-url>
cd <repository-folder>
```

### Step 2: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 3: Login to Vercel

```bash
vercel login
```

### Step 4: Deploy to Vercel

```bash
vercel
```

During deployment, you'll be asked a few questions:
- Set up and deploy?: Yes
- Which scope?: (Select your account)
- Link to existing project?: No
- What's your project's name?: (Enter a name)
- In which directory is your code located?: ./
- Want to override settings?: No

### Step 5: Set environment variables

After deployment, go to the Vercel dashboard, select your project, and add the following environment variables:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token obtained from BotFather

### Step 6: Set up the webhook

After deployment, you need to set up the webhook for your Telegram bot. Visit:

```
https://<your-vercel-domain>/api/set-webhook
```

This will automatically configure your bot to receive updates through Vercel's serverless functions.

## Running Locally

### Prerequisites

- Python 3.9 or higher
- Telegram bot token

### Installation

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements-vercel.txt
```

3. Create a `.env` file with:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

4. Run the bot:

```bash
python main.py
```

## Usage

1. Start a chat with your bot on Telegram
2. Send a link to a supported platform (Instagram, TikTok, Pinterest, YouTube)
3. The bot will download the media and send it back
4. Use `/help` to see all available commands