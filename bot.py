import os
import httpx
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import asyncio

# Telegram bot token and affiliate tag
bot_token = "7807178711:AAHYiDVJmJd__w8kd_3XSa2tcf2-h-nh-xY"  # Replace with your bot token
affiliate_tag = "junodeals-21"
channel_id = "@junodeals"  # Replace with your channel ID or username

# Function to convert Amazon URL to affiliate link and fetch details via scraping
async def fetch_amazon_details(amazon_url):
    # Convert the Amazon URL to an affiliate link
    affiliate_link = f"{amazon_url}?tag={affiliate_tag}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    try:
        # Fetch the Amazon page asynchronously
        async with httpx.AsyncClient() as client:
            response = await client.get(amazon_url, headers=headers)
            response.raise_for_status()  # Raise an error for bad responses
            soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        return {
            "product_name": "Error fetching product details",
            "mrp": "N/A",
            "current_price": "N/A",
            "offer": "N/A",
            "discount": "N/A",
            "affiliate_link": affiliate_link
        }

    # Scrape the product details
    try:
        product_name = soup.find(id="productTitle").get_text(strip=True)
    except AttributeError:
        product_name = "N/A"

    try:
        mrp = soup.find("span", class_="a-size-small aok-offscreen").get_text(strip=True).replace('M.R.P.: ', '')
    except AttributeError:
        mrp = "N/A"

    try:
        current_price = soup.find("span", class_="aok-offscreen").get_text(strip=True).split(' ')[0]  # Taking only the price part
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

# Function to handle messages
async def handle_message(update: Update, context):
    user_message = update.message.text
    if "amazon" in user_message.lower():  # Check if the message contains "amazon"
        amazon_details = await fetch_amazon_details(user_message)  # Await the fetch function

        response_message = (
            f"**Product Name**: {amazon_details['product_name']}\n"
            f"**MRP**: {amazon_details['mrp']}\n"
            f"**Current Price**: {amazon_details['current_price']}\n"
            f"**Discount**: {amazon_details['discount']}\n"
            f"**Offers**: {amazon_details['offer']}\n"
            f"**Best Buy**: [Buy Now]({amazon_details['affiliate_link']})"
        )

        # Send the response back to the user
        await update.message.reply_text(response_message, parse_mode='Markdown')

        # Forward the original message to the channel
        await context.bot.send_message(channel_id, response_message, parse_mode='Markdown')

# Main function to set up handlers and run the application
async def main():
    # Create an application
    application = Application.builder().token(bot_token).build()

    # Handle text messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Start the bot
    await application.initialize()  # Await the initialization
    await application.run_polling()  # Use the default settings for run_polling
    await application.shutdown()  # Await the shutdown

# Check if the script is executed directly
if __name__ == "__main__":
    # Use asyncio.run() but in a way compatible with the existing loop
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e) == "This event loop is already running":
            # Run the main function directly without asyncio.run
            loop = asyncio.get_event_loop()
            loop.create_task(main())
