# Trump Trading Tracker (特朗普交易追踪器)

🚀 **GitHub 上首个全功能 Trump 交易预警系统**

监控特朗普的社交媒体 (Truth Social/Twitter) 和相关信息，使用 AI 分析内容，生成实时交易信号并通过 Telegram 推送。

---

## ✨ 功能特性

### 1. 📱 社交媒体监听
- **Truth Social** 帖子实时监控
- **Twitter/X** 推文追踪
- 新闻源关键词监控

### 2. 🤖 AI 智能分析
- **情绪分析**: 判断 Trump 对特定公司/行业的态度
- **实体识别**: 自动提取提到的公司、股票、加密货币
- **信号生成**: buy/sell/watch/none 四档交易信号
- **置信度评分**: 0-100分，帮助判断可靠性

### 3. 📊 交易映射
自动识别 Trump 提到的资产并映射到交易标的：

| Trump 提到的关键词 | 自动映射的标的 |
|------------------|--------------|
| Apple / Tim Cook | AAPL |
| Tesla / Elon | TSLA |
| China / Tariff | BABA, JD, PDD, KWEB |
| Bitcoin / Crypto | BTC, COIN, MSTR |
| Oil / Drill | XOM, CVX, XLE |
| Fed / Interest Rate | TLT, SPY |
| War / Military | LMT, RTX, NOC |
| Truth Social | DJT |

### 4. 💰 DJT 股票专项监控
- Trump Media (DJT) 股价异动提醒 (>5%波动)
- 期权异常交易检测
- 与 Trump 发帖时间关联分析

### 5. 📲 实时 Telegram 通知
```
🟢 Trump 交易信号 🟢

信号类型: BUY
置信度: 85/100 ⭐⭐⭐⭐
时间: 2026-02-16 14:30

触发关键词: apple, great, tim cook

目标标的:
• AAPL (stock) - $185.50

AI分析:
Trump 在 Truth Social 上称赞 Apple 和 Tim Cook，情绪非常正面，建议关注 AAPL 短期上涨机会。

⚠️ 免责声明: 此为AI自动分析，不构成投资建议
```

---

## 🛠️ 安装配置

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/trump-trading-tracker.git
cd trump-trading-tracker
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
创建 `.env` 文件：
```bash
# Telegram Bot (必须)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# OpenAI API (可选，用于AI分析)
OPENAI_API_KEY=your_openai_key

# 如果不配置 OpenAI，会自动使用关键词匹配模式
```

#### 获取 Telegram Bot Token:
1. 找 [@BotFather](https://t.me/botfather) 创建新 bot
2. 复制 token

#### 获取 Chat ID:
1. 给 bot 发送一条消息
2. 访问: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. 找到 `chat.id` 字段

### 4. 运行测试
```bash
# 运行一次测试
python3 trump_tracker.py --once

# 发送测试通知到 Telegram
python3 trump_tracker.py --test-alert

# 持续运行 (每15分钟检查一次)
python3 trump_tracker.py --loop

# 自定义检查间隔 (每30分钟)
python3 trump_tracker.py --loop --interval 30
```

---

## 📁 项目结构

```
trump-trading-tracker/
├── trump_tracker.py      # 主程序
├── requirements.txt      # 依赖列表
├── config.py            # 配置文件 (关键词映射等)
├── .env                 # 环境变量 (不提交到git)
├── data/                # 数据存储
│   ├── posts.json       # 历史帖子
│   └── signals.json     # 历史信号
├── logs/                # 运行日志
└── README.md            # 本文件
```

---

## 🎯 使用场景

### 场景 1: 事件驱动交易
```
Trump 发帖: "将对所有中国商品加征 60% 关税"
→ 系统自动检测 "china" + "tariff" 关键词
→ 生成 SELL 信号，目标: BABA, JD, KWEB
→ 推送到你的 Telegram
→ 你可以提前做空或减仓
```

### 场景 2: 个股机会捕捉
```
Trump 发帖: "Apple 在美国创造了大量就业，Tim Cook 是我的好朋友"
→ 检测正面情绪 + AAPL 提及
→ 生成 BUY 信号，置信度 80%
→ 推送提醒
→ 考虑短期做多 AAPL
```

### 场景 3: DJT 炒作跟踪
```
Trump 发帖关于 Truth Social
→ DJT 股价波动 > 5%
→ 自动推送价格异动提醒
→ 同时检测帖子情绪
→ 综合判断买卖时机
```

---

## ⚙️ 高级配置

### 自定义关键词映射
编辑 `trump_tracker.py` 中的 `KEYWORD_MAPPINGS`:

```python
KEYWORD_MAPPINGS = {
    "your_keyword": {
        "signal": "buy",           # buy/sell/watch
        "targets": ["STOCK1", "STOCK2"],
        "sector": "your_sector"
    },
    # ... 添加更多
}
```

### 调整置信度算法
在 `generate_signal` 方法中修改评分逻辑:
```python
# 当前算法
confidence = 50  # 基础分
if post.sentiment == "positive":
    confidence += 20
if len(post.entities) >= 2:
    confidence += 10
# ... 自定义你的算法
```

---

## ⚠️ 风险提示

1. **这不是投资建议** - AI 分析仅供参考，交易风险自负
2. **市场有风险** - Trump 的帖子影响往往是短期的，注意止损
3. **延迟风险** - 从发帖到检测到通知有几分钟延迟
4. **误报可能** - AI 可能误解讽刺或上下文

---

## 🔧 故障排除

### 问题: 无法获取 Truth Social 数据
**解决**: Truth Social 没有官方 API，你需要:
- 使用第三方爬虫服务
- 或手动 RSS 订阅
- 或等待帖子数据 (项目目前使用模拟数据演示)

### 问题: Telegram 通知没收到
**解决**:
```bash
# 1. 检查 token 是否正确
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe

# 2. 检查 chat_id 是否正确
# 先给 bot 发消息，然后访问:
curl https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
```

### 问题: OpenAI API 报错
**解决**: 
- 检查 API Key 是否有效
- 检查账户余额
- 或移除 OpenAI Key，使用免费的关键词匹配模式

---

## 📝 TODO (未来功能)

- [ ] 接入 Truth Social 真实 API (等官方开放或找到稳定爬虫)
- [ ] Twitter/X API 集成
- [ ] 新闻源 RSS 监控 (Bloomberg, CNBC 等)
- [ ] 回测系统 (验证历史信号准确率)
- [ ] Web 仪表盘 (可视化信号和历史)
- [ ] 多语言支持 (中文/英文)
- [ ] Discord/Slack 通知支持
- [ ] 自动下单功能 (连接券商 API)

---

## 📄 License

MIT License - 自由使用，风险自负

---

## 🙏 免责声明

本项目仅供**学习和研究**使用，不构成任何投资建议。Trump 的社交媒体内容可能影响市场，但市场反应不确定。使用本工具产生的任何盈亏由使用者自行承担。

**投资有风险，入市需谨慎！**

---

Made with 💰 by [Your Name]
