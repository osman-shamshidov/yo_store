#!/bin/bash

echo "🚀 Yo Store - Quick Deploy Script"
echo "=================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit - Yo Store"
    echo "✅ Git repository initialized"
else
    echo "📁 Git repository already exists"
fi

echo ""
echo "📋 Next steps:"
echo "1. Create a GitHub repository:"
echo "   - Go to https://github.com/new"
echo "   - Name: yo-store"
echo "   - Make it public"
echo ""
echo "2. Push your code:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/yo-store.git"
echo "   git push -u origin main"
echo ""
echo "3. Deploy on Render.com:"
echo "   - Go to https://render.com"
echo "   - Login with GitHub"
echo "   - New + → Web Service"
echo "   - Connect GitHub repo: osman-shamshidov/yo_store"
echo ""
echo "4. Configure environment variables in Render:"
echo "   - TELEGRAM_BOT_TOKEN=your_bot_token"
echo "   - SECRET_KEY=your_secret_key"
echo "   - DEBUG=False"
echo "   - HOST=0.0.0.0"
echo "   - PORT=\$PORT"
echo ""
echo "5. Add PostgreSQL database in Render"
echo ""
echo "6. Get your app URL and configure Telegram bot"
echo ""
echo "📖 Full instructions: RENDER_DEPLOY.md"
echo "🎉 Happy deploying on Render!"
