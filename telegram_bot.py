import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import Config
import requests
import json

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class ElectronicsStoreBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.api_url = f"http://{Config.HOST}:{Config.PORT}"
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""
🛍️ Добро пожаловать в Yo Store, {user.first_name}!

Здесь вы найдете:
📱 Смартфоны
💻 Ноутбуки  
🎮 Игровые приставки
🎧 Наушники
📱 Планшеты
🔊 Умные колонки

Цены обновляются каждые 10 минут!
        """
        
        keyboard = [
            [InlineKeyboardButton("🛍️ Открыть магазин", web_app=WebAppInfo(url=f"{self.api_url}/webapp"))],
            [InlineKeyboardButton("📱 Смартфоны", callback_data="category_1")],
            [InlineKeyboardButton("💻 Ноутбуки", callback_data="category_2")],
            [InlineKeyboardButton("🎮 Игровые приставки", callback_data="category_3")],
            [InlineKeyboardButton("🎧 Наушники", callback_data="category_4")],
            [InlineKeyboardButton("📱 Планшеты", callback_data="category_5")],
            [InlineKeyboardButton("🔊 Умные колонки", callback_data="category_6")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🆘 Помощь по использованию бота:

/start - Главное меню
/help - Эта справка
/categories - Показать все категории
/search <запрос> - Поиск товаров

💡 Используйте кнопки для навигации по магазину
💡 Цены обновляются автоматически каждые 10 минут
💡 Нажмите "Открыть магазин" для полного интерфейса
        """
        await update.message.reply_text(help_text)
    
    async def categories_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /categories command"""
        try:
            response = requests.get(f"{self.api_url}/categories")
            if response.status_code == 200:
                categories = response.json()
                
                text = "📂 Категории товаров:\n\n"
                keyboard = []
                
                for category in categories:
                    text += f"{category['icon']} {category['name']} ({category['product_count']} товаров)\n"
                    text += f"   {category['description']}\n\n"
                    
                    keyboard.append([InlineKeyboardButton(
                        f"{category['icon']} {category['name']}",
                        callback_data=f"category_{category['id']}"
                    )])
                
                keyboard.append([InlineKeyboardButton("🛍️ Открыть магазин", web_app=WebAppInfo(url=f"{self.api_url}/webapp"))])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text("❌ Ошибка загрузки категорий")
                
        except Exception as e:
            logger.error(f"Error fetching categories: {e}")
            await update.message.reply_text("❌ Ошибка подключения к серверу")
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        if not context.args:
            await update.message.reply_text("❌ Укажите поисковый запрос: /search iPhone")
            return
        
        query = " ".join(context.args)
        try:
            response = requests.get(f"{self.api_url}/search", params={"q": query, "limit": 10})
            if response.status_code == 200:
                products = response.json()
                
                if not products:
                    await update.message.reply_text(f"🔍 По запросу '{query}' ничего не найдено")
                    return
                
                text = f"🔍 Результаты поиска по запросу '{query}':\n\n"
                
                for product in products:
                    discount_text = f" (скидка {product['discount_percentage']:.0f}%)" if product['discount_percentage'] > 0 else ""
                    text += f"📱 {product['name']}\n"
                    text += f"💰 {product['price']:,.0f} ₽{discount_text}\n"
                    text += f"🏷️ {product['brand']} {product['model']}\n"
                    text += f"📂 {product['category_name']}\n\n"
                
                keyboard = [[InlineKeyboardButton("🛍️ Открыть магазин", web_app=WebAppInfo(url=f"{self.api_url}/webapp"))]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_text(text, reply_markup=reply_markup)
            else:
                await update.message.reply_text("❌ Ошибка поиска")
                
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            await update.message.reply_text("❌ Ошибка подключения к серверу")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("category_"):
            category_id = int(query.data.split("_")[1])
            await self.show_category_products(query, category_id)
    
    async def show_category_products(self, query, category_id: int):
        """Show products in a specific category"""
        try:
            response = requests.get(f"{self.api_url}/products", params={"category_id": category_id, "limit": 10})
            if response.status_code == 200:
                products = response.json()
                
                if not products:
                    await query.edit_message_text("❌ В этой категории пока нет товаров")
                    return
                
                # Get category name
                category_response = requests.get(f"{self.api_url}/categories")
                category_name = "Товары"
                if category_response.status_code == 200:
                    categories = category_response.json()
                    for cat in categories:
                        if cat['id'] == category_id:
                            category_name = cat['name']
                            break
                
                text = f"📂 {category_name}:\n\n"
                
                for product in products:
                    discount_text = f" (скидка {product['discount_percentage']:.0f}%)" if product['discount_percentage'] > 0 else ""
                    text += f"📱 {product['name']}\n"
                    text += f"💰 {product['price']:,.0f} ₽{discount_text}\n"
                    text += f"🏷️ {product['brand']} {product['model']}\n\n"
                
                keyboard = [
                    [InlineKeyboardButton("🛍️ Открыть магазин", web_app=WebAppInfo(url=f"{self.api_url}/webapp"))],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(text, reply_markup=reply_markup)
            else:
                await query.edit_message_text("❌ Ошибка загрузки товаров")
                
        except Exception as e:
            logger.error(f"Error fetching category products: {e}")
            await query.edit_message_text("❌ Ошибка подключения к серверу")
    
    def run(self):
        """Run the bot"""
        if not self.token:
            logger.error("TELEGRAM_BOT_TOKEN not set!")
            return
        
        application = Application.builder().token(self.token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("categories", self.categories_command))
        application.add_handler(CommandHandler("search", self.search_command))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        logger.info("Starting bot...")
        application.run_polling()

if __name__ == "__main__":
    bot = ElectronicsStoreBot()
    bot.run()

