#!/bin/bash

# Script to prepare the project for Vercel deployment

# Print header
echo "========================================="
echo "  Preparing Telegram Bot for Vercel      "
echo "========================================="

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "Vercel CLI is not installed. Please install it with:"
    echo "npm install -g vercel"
    exit 1
fi

echo "1. Preparing deployment files..."

# Copy the Vercel-compatible app.py
if [ -f "app.py.vercel" ]; then
    cp app.py.vercel app.py
    echo "   ✓ Copied app.py.vercel to app.py"
else
    echo "   ! Warning: app.py.vercel not found, skipping"
fi

# Copy the Vercel-compatible user_storage.py
if [ -f "user_storage_vercel.py" ]; then
    cp user_storage_vercel.py user_storage.py
    echo "   ✓ Copied user_storage_vercel.py to user_storage.py"
else
    echo "   ! Warning: user_storage_vercel.py not found, skipping"
fi

# Copy the Vercel-compatible api/index.py
if [ -f "api/index.py.vercel" ]; then
    cp api/index.py.vercel api/index.py
    echo "   ✓ Copied api/index.py.vercel to api/index.py"
else
    echo "   ! Warning: api/index.py.vercel not found, skipping"
fi

# Ensure we have the requirements-vercel.txt file
if [ -f "requirements-vercel.txt" ]; then
    echo "   ✓ requirements-vercel.txt found"
else
    echo "   ! Error: requirements-vercel.txt not found"
    exit 1
fi

# Check for vercel.json
if [ -f "vercel.json" ]; then
    echo "   ✓ vercel.json found"
else
    echo "   ! Error: vercel.json not found"
    exit 1
fi

# Check for API directory and files
if [ -d "api" ] && [ -f "api/index.py" ]; then
    echo "   ✓ API directory and webhook handler found"
else
    echo "   ! Error: API directory or webhook handler missing"
    exit 1
fi

echo "2. Setting up Git repository..."

# Initialize Git repository if not already exists
if [ ! -d ".git" ]; then
    git init
    echo "   ✓ Git repository initialized"
else
    echo "   ✓ Git repository already exists"
fi

# Check if .gitignore exists
if [ -f ".gitignore" ]; then
    echo "   ✓ .gitignore found"
else
    echo "   ! Warning: .gitignore not found, creating minimal version"
    echo "__pycache__/" > .gitignore
    echo "*.py[cod]" >> .gitignore
    echo ".env" >> .gitignore
    echo ".social_media_bot/" >> .gitignore
    echo "/tmp/" >> .gitignore
fi

# Add files to Git
echo "3. Adding files to Git..."
git add .
echo "   ✓ Files added to Git"

# Commit changes
echo "4. Committing changes..."
git commit -m "Prepare for Vercel deployment"
echo "   ✓ Changes committed"

echo
echo "5. Next steps:"
echo "   1. Create a GitHub repository (if you haven't already)"
echo "   2. Link your local repository with the command:"
echo "      git remote add origin <your-github-repo-url>"
echo "   3. Push your code to GitHub:"
echo "      git push -u origin main"
echo "   4. Deploy to Vercel with the command:"
echo "      vercel"
echo
echo "During Vercel deployment, make sure to:"
echo "   - Set TELEGRAM_BOT_TOKEN as an environment variable"
echo "   - Use requirements-vercel.txt for dependencies"
echo
echo "After deployment, set up the webhook by visiting:"
echo "https://<your-vercel-domain>/api/set-webhook"
echo
echo "For more detailed instructions, see DEPLOYING_TO_VERCEL.md"
echo "========================================="