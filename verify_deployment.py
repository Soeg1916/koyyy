#!/usr/bin/env python3
"""
Script to verify deployment of the Telegram bot webhook.
This script tests the connection to the webhook endpoint.
"""
import sys
import requests
import argparse

def check_webhook_endpoint(url):
    """Check if the webhook endpoint is responding."""
    try:
        # Check the base URL
        response = requests.get(url)
        if response.status_code == 200:
            print(f"✅ Base URL is responding: {url} (Status: {response.status_code})")
        else:
            print(f"❌ Base URL returned status code {response.status_code}: {url}")
            return False
        
        # Check webhook setup endpoint
        webhook_url = f"{url.rstrip('/')}/api/set-webhook"
        response = requests.get(webhook_url)
        if response.status_code == 200:
            print(f"✅ Webhook setup endpoint is working: {webhook_url}")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Webhook setup endpoint returned status code {response.status_code}: {webhook_url}")
            print(f"Response: {response.text}")
            return False
            
        print("\n✅ Deployment verification passed!")
        return True
        
    except requests.RequestException as e:
        print(f"❌ Error connecting to {url}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Verify deployment of Telegram bot webhook")
    parser.add_argument("url", help="URL of the deployed application")
    args = parser.parse_args()
    
    print("\n🔍 Verifying deployment...\n")
    
    if not args.url.startswith(('http://', 'https://')):
        args.url = 'https://' + args.url
    
    success = check_webhook_endpoint(args.url)
    
    if success:
        print("\n🎉 Your Telegram bot webhook appears to be working correctly!")
        print("Send a message to your bot on Telegram to verify it's responding.")
    else:
        print("\n❌ Verification failed. Please check the logs and deployment settings.")
        sys.exit(1)

if __name__ == "__main__":
    main()