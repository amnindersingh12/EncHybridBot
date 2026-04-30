#!/bin/bash
set -e

APP_NAME=$1

if [ -z "$APP_NAME" ]; then
    echo "Usage: ./heroku_setup.sh <your-app-name>"
    echo "Example: ./heroku_setup.sh my-awesome-encbot"
    exit 1
fi

if ! command -v heroku &> /dev/null; then
    echo "Error: Heroku CLI is not installed."
    echo "Install it from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "🚀 Creating Heroku app: $APP_NAME"
heroku create $APP_NAME || true

echo "📦 Setting stack to container (Docker)..."
heroku stack:set container -a $APP_NAME

echo "⚠️ Important: Make sure to set your Environment Variables (APP_ID, API_HASH, etc.) in the Heroku Dashboard!"
echo "Go to: https://dashboard.heroku.com/apps/$APP_NAME/settings"
read -p "Press Enter when you have set the config vars..."

echo "⚙️ Pushing code to Heroku..."
git push heroku main

echo "🔨 Scaling worker dyno..."
heroku ps:scale worker=1 -a $APP_NAME

echo "✅ Deployment complete! Check the logs with:"
echo "heroku logs --tail -a $APP_NAME"
