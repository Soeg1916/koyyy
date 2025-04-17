# Vercel Deployment Guide

This guide provides step-by-step instructions to deploy your Telegram bot on Vercel. The deployment process is designed to work with Vercel's serverless architecture while maintaining as much functionality as possible.

## Prerequisites

- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- A [Vercel](https://vercel.com) account
- [Node.js](https://nodejs.org/) installed locally (for Vercel CLI)
- [Git](https://git-scm.com/) installed locally

## Important Limitations

When running on Vercel, the bot has some important limitations:

1. **No Persistent File Storage**: Vercel's serverless functions run in a read-only filesystem. The `/save` command will store references to files but actual files are temporary.
2. **Function Timeout**: Vercel functions have a maximum execution time of 10-60 seconds. Very large downloads may timeout.
3. **Polling Not Available**: The bot must use webhooks instead of polling.
4. **Cold Starts**: The first request after a period of inactivity might take a little longer to respond.

## Deployment Steps

### 1. Preparing Files

1. Run the provided preparation script:

```bash
# Make the script executable
chmod +x prepare_vercel_deployment.py

# Run the preparation script
python prepare_vercel_deployment.py
```

2. Then run the shell script to finalize the changes:

```bash
# Make the script executable
chmod +x prepare_for_vercel.sh

# Run the script
./prepare_for_vercel.sh
```

### 2. Install Vercel CLI

```bash
# Install Vercel CLI globally
npm install -g vercel
```

### 3. Deploy to Vercel

1. Login to your Vercel account:

```bash
vercel login
```

2. Deploy the project:

```bash
vercel
```

3. During deployment, you will be asked a series of questions:
   - Set up and deploy?: `Y`
   - Select scope: Choose your account or team
   - Link to existing project?: `N` if it's a new project
   - Project name: Enter a name for your project
   - Directory: Press Enter to use current directory
   - Override settings?: `N` if there's no need to change the default settings

4. **Important**: When prompted to customize build settings, update:
   - Build Command: Leave empty
   - Install Command: `pip install -r requirements-vercel.txt`
   - Development Command: Leave empty

5. **Crucial Step**: After deployment, add environment variables in the Vercel project dashboard:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
   - `BOT_USERNAME`: Your bot's username (without the @ symbol)

### 4. Setting Up the Webhook

After deployment, set up the webhook by visiting:

```
https://<your-vercel-domain>/api/set-webhook
```

This will automatically configure Telegram to send updates to your bot via the deployed webhook URL.

### 5. Verify Deployment

Check if your deployment is working by visiting:

```
https://<your-vercel-domain>/api
```

You should see: `{"status":"alive","service":"Telegram Bot Webhook"}`

## Troubleshooting

1. **Webhook not working**: 
   - Ensure your `TELEGRAM_BOT_TOKEN` is set correctly in Vercel environment variables
   - Visit `/api/set-webhook` again to reset the webhook
   - Check Vercel logs for any errors

2. **Function timeouts**:
   - Very large video downloads might time out. Vercel functions have execution limits.
   - Suggest users try shorter videos or specific platforms that have more direct download options.

3. **File storage issues**:
   - Explain to users that file storage is temporary. The `/save` command will appear to work, but saved files won't persist.

## Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [Flask on Vercel](https://vercel.com/guides/using-flask-with-vercel)

---

Remember that after making changes, you need to redeploy using:

```bash
vercel --prod
```

This ensures your production deployment gets updated.