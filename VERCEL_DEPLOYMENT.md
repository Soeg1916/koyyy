# Deploying Your Telegram Bot to Vercel

This guide will walk you through the process of deploying your Telegram bot to Vercel.

## Prerequisites

1. A [Vercel account](https://vercel.com/signup)
2. A [Telegram bot token](https://t.me/BotFather)
3. Git installed on your computer

## Deployment Steps

### Step 1: Push Your Code to a Git Repository

1. Create a repository on GitHub, GitLab, or Bitbucket
2. Push your code to the repository

### Step 2: Connect to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" → "Project"
3. Import your Git repository
4. Configure your project:
   - Framework Preset: Other
   - Build Command: Leave empty
   - Output Directory: Leave empty
   - Install Command: `pip install -r requirements-vercel.txt`

### Step 3: Configure Environment Variables

1. Click on "Environment Variables"
2. Add the following variable:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather

### Step 4: Deploy

1. Click "Deploy"
2. Wait for the deployment to complete

### Step 5: Set Up the Webhook

After deployment, visit your Vercel domain with the webhook setup endpoint:

```
https://<your-vercel-domain>/api/set-webhook
```

This will automatically configure your Telegram bot to use the webhook.

## Testing Your Deployment

To make sure everything is working:

1. Visit your Vercel domain in a browser - you should see your bot's information page
2. Send a message to your bot on Telegram - it should respond

## Troubleshooting

If your bot doesn't respond:

1. Check the Vercel function logs in your Vercel dashboard
2. Make sure your webhook is set up correctly
3. Ensure your `TELEGRAM_BOT_TOKEN` is correct
4. Try re-deploying or setting up the webhook again

## Limitations on Vercel

1. **Serverless Function Timeout**: Vercel functions have a maximum execution time (10 seconds in the free tier)
2. **Read-Only File System**: The file system is read-only in production. For persistent storage, you'll need to use a database service.
3. **Cold Starts**: Your functions might experience "cold starts" if they haven't been used recently

## Maintaining Your Bot

To update your bot:

1. Make changes to your code
2. Push to your Git repository
3. Vercel will automatically redeploy your application