import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram bot token and affiliate tag
bot_token = "7807178711:AAGoL1uZVx_X6BQH34z7nIL7f6hUNvz8I5Y"  # Replace with your bot token
affiliate_tag = "junodeals-21"
channel_id = "@junodeals"  # Replace with your channel ID or username

# Function to convert Amazon URL to affiliate link and fetch details via scraping
def fetch_amazon_details(amazon_url):
    # Convert the Amazon URL to an affiliate link
    affiliate_link = f"{amazon_url}?tag={affiliate_tag}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }
    
    # Fetch the Amazon page
    response = requests.get(amazon_url, headers=headers)
    
    if response.status_code != 200:
        return {"error": "Failed to fetch the Amazon page."}

    soup = BeautifulSoup(response.content, 'html.parser')
    
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
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    if "amazon" in user_message:
        # If an Amazon link is found
        amazon_details = fetch_amazon_details(user_message)

        if "error" in amazon_details:
            await update.message.reply_text(amazon_details["error"])
            return
        
        response_message = (
            f"**Grab 🔥**: {amazon_details['product_name']}\n"
            f"**MRP ❌**: {amazon_details['mrp']}  "
            f"**Current Price ✔️**: {amazon_details['current_price']}\n"
            f"**Discount**: {amazon_details['discount']}\n"
            f"**Best Buy**: [Buy Now]({amazon_details['affiliate_link']})"
        )
        
        # Send the response back to the user
        await update.message.reply_text(response_message, parse_mode='Markdown')
        
        # Forward the original message to the channel
        await context.bot.send_message(channel_id, response_message, parse_mode='Markdown')

# Main function to set up handlers
def main():
    # Create an application
    application = Application.builder().token(bot_token).build()

    # Handle text messages
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
