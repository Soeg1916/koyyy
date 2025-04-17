# Deploying Your Telegram Media Bot on Koyeb

This guide provides step-by-step instructions to deploy your Telegram bot on Koyeb.

## What is Koyeb?

Koyeb is a developer-friendly serverless platform that lets you run applications globally with simple Git deployments. Unlike Vercel, Koyeb is more suitable for long-running processes like a Telegram bot.

## Advantages of Koyeb for Your Bot

1. **Persistent File System** - Your bot can actually save files (unlike Vercel's read-only filesystem)
2. **Long-running Processes** - No serverless function timeouts
3. **Simple Deployment** - Connect your GitHub repository for automatic deployments
4. **Reasonable Free Tier** - Includes enough resources for your bot

## Deployment Steps

### 1. Create a Koyeb Account

1. Sign up at [koyeb.com](https://koyeb.com)
2. Complete the verification process

### 2. Prepare Your Repository

1. Push your code to GitHub if you haven't already:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
   git push -u origin main
   ```

2. Make sure your repository contains:
   - All your bot code
   - The `Procfile` (created above)
   - The `koyeb.yml` configuration file (created above)

### 3. Create a New Koyeb App

1. In the Koyeb dashboard, click "Create App"
2. Select "GitHub" as your deployment method
3. Connect your GitHub account if not already connected
4. Select your bot repository
5. For deployment settings:
   - **Name**: Choose a name for your app
   - **Region**: Select a region close to your target users
   - **Instance Type**: Choose the "Free" instance
   - **Environment Variables**: Add your `TELEGRAM_BOT_TOKEN`

6. Click "Deploy"

### 4. Set Up Webhook

After your bot is deployed:

1. Get your app's public URL from the Koyeb dashboard (looks like `https://your-app-name-yourusername.koyeb.app`)

2. Set up the webhook by visiting:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://your-app-name-yourusername.koyeb.app/webhook
   ```

3. You should get a response saying `{"ok":true,"result":true,"description":"Webhook was set"}`

### 5. Verify Deployment

1. Start a chat with your bot on Telegram
2. Send `/start` to check if it responds
3. Try sending a URL to test the media download functionality
4. Try the `/save` command - it should work properly on Koyeb since it has a persistent filesystem

## Troubleshooting

If your bot doesn't respond:

1. Check the Koyeb logs in your dashboard
2. Verify the webhook is set correctly by visiting:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
   ```
3. Make sure your `TELEGRAM_BOT_TOKEN` environment variable is set correctly

## Updating Your Bot

To update your bot after code changes:

1. Push changes to your GitHub repository
2. Koyeb will automatically redeploy your app

## Cost Considerations

The free tier includes:
- 2 instances with 256MB RAM and shared CPU
- 100GB outbound data transfer

This should be sufficient for your bot with moderate usage. If you need more resources, Koyeb has affordable paid plans.