#!/usr/bin/env python3
"""
Script to prepare the Telegram bot for Vercel deployment.
This automates the process of updating necessary files for Vercel compatibility.
"""
import os
import shutil
import sys

def main():
    """Main function to handle the Vercel preparation."""
    print("===================================================")
    print("      Preparing Telegram Bot for Vercel Deployment")
    print("===================================================")
    
    # Step 1: Verify files exist
    required_files = [
        "vercel.json",
        "requirements-vercel.txt",
        "api/index.py",
        "api/webhook.py",
        "bot.py",
        "user_storage.py",
        "user_storage_vercel.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ ERROR: The following required files are missing:")
        for file in missing_files:
            print(f"   - {file}")
        print("\nPlease ensure all required files are present before continuing.")
        return False
    
    print("✅ All required files are present.")
    
    # Step 2: Copy user_storage_vercel.py to user_storage.py.vercel
    try:
        shutil.copy2("user_storage_vercel.py", "user_storage.py.vercel")
        print("✅ Created user_storage.py.vercel")
    except Exception as e:
        print(f"❌ ERROR: Failed to copy user_storage_vercel.py: {str(e)}")
        return False
    
    # Step 3: Create directory for temporary storage
    tmp_dir = "/tmp/telegram_bot_temp"
    os.makedirs(tmp_dir, exist_ok=True)
    print(f"✅ Created temporary directory: {tmp_dir}")
    
    # Step 4: Modify prepare_for_vercel.sh to also copy user_storage.py.vercel
    try:
        with open("prepare_for_vercel.sh", "r") as f:
            content = f.read()
        
        # Check if our modification already exists
        if "user_storage.py.vercel" not in content:
            # Find the line with app.py.vercel
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if "app.py.vercel" in line and "cp app.py.vercel app.py" in line:
                    # Insert our line after this
                    indent = line.split("cp")[0]
                    lines.insert(i+1, f"{indent}cp user_storage.py.vercel user_storage.py")
                    lines.insert(i+2, f'{indent}echo "   ✓ Copied user_storage.py.vercel to user_storage.py"')
                    break
            
            # Write the modified content back
            with open("prepare_for_vercel.sh", "w") as f:
                f.write("\n".join(lines))
            
            print("✅ Modified prepare_for_vercel.sh to include user_storage.py")
        else:
            print("✅ prepare_for_vercel.sh already contains user_storage.py handling")
    except Exception as e:
        print(f"❌ ERROR: Failed to modify prepare_for_vercel.sh: {str(e)}")
        return False
    
    # Step 5: Add a note about Vercel environment variables
    print("\n===================================================")
    print("                Important Notes")
    print("===================================================")
    print("1. When deploying to Vercel, make sure to set these environment variables:")
    print("   - TELEGRAM_BOT_TOKEN: Your Telegram bot token")
    print("   - BOT_USERNAME: Your bot's username (without the @ symbol)")
    print("\n2. After deployment, visit these URLs to set up your bot:")
    print("   - https://<your-vercel-domain>/api/set-webhook")
    print("     This will set up the webhook for your bot")
    print("\n3. Test the webhook is working by visiting:")
    print("   - https://<your-vercel-domain>/api")
    print("     You should see a 'Telegram Bot Webhook' status message")
    print("\n4. Important Limitations:")
    print("   - The /save feature will not persist files between function calls")
    print("   - Temporary downloads will work but may be limited by Vercel's function timeout")
    print("===================================================")
    
    print("\nPreparation complete! Run ./prepare_for_vercel.sh to finalize deployment files.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)