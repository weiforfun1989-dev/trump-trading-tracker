# Trump Trading Tracker

🚀 **The first comprehensive Trump social media trading alert system**

Monitor Donald Trump's Truth Social posts and related activity to generate real-time trading signals.

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 📱 Features

- **Truth Social Monitoring** - Track new posts in real-time
- **AI-Powered Analysis** - GPT-powered sentiment and entity extraction
- **Smart Stock Mapping** - 50+ keywords mapped to tickers
- **DJT Stock Alerts** - Price movement notifications
- **Telegram Integration** - Instant mobile notifications

## 🎯 Quick Start

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/trump-trading-tracker.git
cd trump-trading-tracker

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Telegram bot token

# Run once
python3 trump_tracker.py --once

# Run continuously
python3 trump_tracker.py --loop
```

## 📊 How It Works

1. **Monitor** - Checks Truth Social for new Trump posts
2. **Analyze** - AI extracts sentiment and mentioned entities
3. **Map** - Keywords mapped to stocks (e.g., "China" → BABA, JD)
4. **Signal** - Generates buy/sell/watch signals with confidence scores
5. **Alert** - Sends formatted alerts to Telegram

## 🗺️ Keyword Mappings

| Keywords | Stocks | Signal Type |
|----------|--------|-------------|
| China, Tariff | BABA, JD, PDD, KWEB | Watch |
| Apple, Tim Cook | AAPL | Watch |
| Tesla, Elon | TSLA | Watch |
| Bitcoin, Crypto | BTC, COIN, MSTR | Watch |
| Oil, Drill | XOM, CVX, XLE | Buy |
| War, Military | LMT, RTX, NOC | Buy |
| Truth Social | DJT | Buy |

## ⚙️ Configuration

Create `.env` file:
```bash
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
OPENAI_API_KEY=your_openai_key_here  # Optional
```

## 📱 Sample Alert

```
🟢 Trump Trading Signal 🟢

Type: BUY
Confidence: 85/100 ⭐⭐⭐⭐

Triggers: apple, tim cook

Targets:
• AAPL (stock) - $185.50

Analysis: Trump praised Apple and Tim Cook. 
Positive sentiment detected. Consider AAPL long.

⚠️ Disclaimer: AI analysis, not financial advice
```

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. Not financial advice. Trade at your own risk.

## 📄 License

MIT License - See [LICENSE](LICENSE)

## 🙏 Acknowledgments

- Inspired by congressional trading trackers
- Uses OpenAI for sentiment analysis
- Stock data via Yahoo Finance

---

**Star ⭐ this repo if you find it useful!**
