# Deploying Your Telegram Bot to Vercel

This guide will walk you through the process of deploying your Telegram bot to Vercel's free tier.

## Important Notes About Telegram Bots on Vercel

Vercel is primarily designed for serverless functions and static websites, not for long-running processes like a traditional Telegram bot that uses polling. To make our bot work on Vercel, we'll use a webhook-based approach.

**Limitations to be aware of:**
- Vercel functions have a maximum execution time (10 seconds in the free tier)
- The file system is read-only in production, so we can't save files permanently
- We'll need to use a database service if we want to store user data permanently

## Pre-deployment Steps

### Step 1: Prepare Your Project

Before deploying, make sure your project is ready:

1. Rename the required files:
   ```bash
   cp app.py.vercel app.py
   ```

2. Make sure you have all these files:
   - `api/index.py` - Webhook handler for Telegram updates
   - `vercel.json` - Vercel configuration
   - `.gitignore` - Excludes unnecessary files
   - `requirements-vercel.txt` - Dependencies for Vercel

## Deployment Process

### Step 1: Create a GitHub Repository

1. Create a new repository on GitHub
2. Push your code to the repository:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-repository-url>
git push -u origin main
```

### Step 2: Connect to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure your project:
   - Framework Preset: Other
   - Build Command: Leave empty
   - Output Directory: Leave empty
   - Install Command: `pip install -r requirements-vercel.txt`

### Step 3: Configure Environment Variables

1. Click on "Environment Variables"
2. Add the following variables:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token

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

## Maintaining Your Bot

To update your bot:

1. Make changes to your code
2. Push to GitHub
3. Vercel will automatically redeploy

## Advanced: Using a Database

For user data storage in production, consider using:

- Vercel KV (Redis)
- MongoDB Atlas
- Supabase
- Firebase

You'll need to modify the user_storage.py file to use a database instead of the local file system.