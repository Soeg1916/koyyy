# Vercel Deployment Troubleshooting Guide

This guide helps you troubleshoot common issues with the Telegram bot deployment on Vercel.

## Common Issues and Solutions

### 1. Function Invocation Failed (500 Error)

If you see an error like: 
```
500: INTERNAL_SERVER_ERROR
Code: FUNCTION_INVOCATION_FAILED
```

#### Debugging Steps:

1. **Check the Debug Endpoint**:
   Visit `https://your-project-name.vercel.app/api/debug`
   
   This will show information about Python version and available environment variables.

2. **Check Import Compatibility**:
   Visit `https://your-project-name.vercel.app/api/debug/test-import`
   
   This will tell you if any modules are failing to import.

3. **Check Vercel Logs**:
   - Go to your Vercel dashboard
   - Select your project
   - Click "Deployments"
   - Select the latest deployment
   - Click "Functions" to see detailed logs

### 2. Missing Environment Variables

If your bot is deployed but not responding:

1. **Verify Environment Variables**:
   - In your Vercel dashboard, go to Settings > Environment Variables
   - Make sure `TELEGRAM_BOT_TOKEN` is set correctly
   - If it wasn't set before deployment, add it and then redeploy:
     ```
     vercel --prod
     ```

2. **Reset Webhook**:
   Visit `https://your-project-name.vercel.app/api/set-webhook`
   
   This will re-configure Telegram to send updates to your bot.

### 3. Package Installation Issues

If certain imports are failing:

1. Try modifying `requirements-vercel.txt` to include only the essential packages:
   ```
   flask==2.2.5
   gunicorn==21.2.0
   pytelegrambotapi==4.14.1
   python-dotenv==1.0.0
   requests==2.31.0
   werkzeug==2.2.3
   ```

2. Redeploy with:
   ```
   vercel --prod
   ```

### 4. Function Timeout

If your functions are timing out:

1. Update `vercel.json` to increase memory and duration:
   ```json
   "functions": {
     "api/index.py": {
       "memory": 1024,
       "maxDuration": 60
     }
   }
   ```

2. For large media downloads, you might need to modify the bot to handle smaller files only, as Vercel has execution limits.

### 5. Webhook Issues

If the webhook isn't working:

1. **Check Webhook Status**:
   Use the BotFather API to check webhook status:
   ```
   https://api.telegram.org/bot<your-token>/getWebhookInfo
   ```

2. **Delete and Reset Webhook**:
   ```
   https://api.telegram.org/bot<your-token>/deleteWebhook
   ```
   
   Then visit:
   ```
   https://your-project-name.vercel.app/api/set-webhook
   ```

## Advanced Troubleshooting

### Checking Server Logs

To get more detailed logs from your Vercel functions:

1. Install Vercel CLI locally:
   ```
   npm install -g vercel
   ```

2. Pull environment variables:
   ```
   vercel env pull
   ```

3. Run development server locally:
   ```
   vercel dev
   ```

4. Test API endpoints locally:
   ```
   curl http://localhost:3000/api
   ```

### Simplified Deployment

If you're still having issues with the full bot, consider deploying a minimal version first:

1. Create a simplified `api/index.py` with basic functionality
2. Get that working on Vercel
3. Gradually add more features

## Contact Telegram Support

If webhook issues persist, check Telegram's webhook requirements:
- HTTPS only
- Valid SSL certificate
- Correct response format

For webhook testing tools:
- https://webhook.site/
- https://requestbin.com/