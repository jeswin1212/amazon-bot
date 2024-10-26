import os
import httpx
from bs4 import BeautifulSoup
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from flask import Flask, request
import logging
import re
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram bot token and affiliate tag
bot_token = "7807178711:AAGHXP7iHfj7WIQl5gQZvFyCjsGb3k8hNXc"  # Replace with your bot token
affiliate_tag = "junodeals-21"
channel_id = "@junodeals"  # Replace with your channel ID or username

app = Flask(__name__)
bot = Bot(token=bot_token)

# Function to validate Amazon URLs
def is_valid_amazon_url(url):
    amazon_url_pattern = r'https?://(www\.)?(amazon\.(com|in|co\.uk|ca|de|fr|it|es|jp|com\.br)/.+|amazon\..+\.com/.+)'
    return re.match(amazon_url_pattern, url) is not None

# Function to convert Amazon URL to affiliate link and fetch details via scraping
async def fetch_amazon_details(amazon_url):
    affiliate_link = f"{amazon_url}?tag={affiliate_tag}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(amazon_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        logger.error(f"Error fetching product details: {e}")
        return {
            "product_name": "Error fetching product details",
            "mrp": "N/A",
            "current_price": "N/A",
            "offer": "N/A",
            "discount": "N/A",
            "affiliate_link": affiliate_link
        }

    # Scrape product details
    try:
        product_name = soup.find(id="productTitle").get_text(strip=True)
    except AttributeError:
        product_name = "N/A"

    try:
        mrp = soup.find("span", class_="a-size-small aok-offscreen").get_text(strip=True).replace('M.R.P.: ', '')
    except AttributeError:
        mrp = "N/A"

    try:
        current_price = soup.find("span", class_="aok-offscreen").get_text(strip=True).split(' ')[0]
    except AttributeError:
        current_price = "N/A"

    try:
        offer = soup.find("span", class_="a-truncate-full a-offscreen").get_text(strip=True)
        if not offer:
            offer = "No offers available"
    except AttributeError:
        offer = "No offers available"

    try:
        discount = soup.find("span", class_="savingsPercentage").get_text(strip=True)
    except AttributeError:
        discount = "No discount available"

    return {
        "product_name": product_name,
        "mrp": mrp,
        "current_price": current_price,
        "offer": offer,
        "discount": discount,
        "affiliate_link": affiliate_link
    }

@app.route(f"/{bot_token}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot)

    user_message = update.message.text
    logger.info(f"Received message: {user_message}")

    # Check for valid Amazon URLs in the message
    if is_valid_amazon_url(user_message):
        amazon_details = await fetch_amazon_details(user_message)  # Await the fetch function
        logger.info(f"Fetched Amazon details: {amazon_details}")

        response_message = (
            f"**Product Name**: {amazon_details['product_name']}\n"
            f"**MRP**: {amazon_details['mrp']}\n"
            f"**Current Price**: {amazon_details['current_price']}\n"
            f"**Discount**: {amazon_details['discount']}\n"
            f"**Offers**: {amazon_details['offer']}\n"
            f"**Best Buy**: [Buy Now]({amazon_details['affiliate_link']})"
        )

        bot.send_message(chat_id=update.message.chat.id, text=response_message, parse_mode='Markdown')
        bot.send_message(channel_id, response_message, parse_mode='Markdown')
    else:
        logger.info("No valid Amazon link found in the message.")
        bot.send_message(chat_id=update.message.chat.id, text="Please send a valid Amazon link.")

    return "ok", 200

if __name__ == "__main__":
    # Set your webhook
    webhook_url = f"https://amazon-bot-g2rm.onrender.com/{bot_token}"  # Replace with your Render URL
    httpx.get(f"https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
