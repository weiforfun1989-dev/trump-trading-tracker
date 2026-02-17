#!/usr/bin/env python3
"""
Trump Trading Tracker (特朗普交易追踪器)
监控特朗普的社交媒体和相关信息，生成交易信号

功能：
1. Truth Social 帖子监听
2. AI 内容分析 (情绪 + 实体识别)
3. 股票/加密货币映射
4. Telegram 实时通知
5. DJT 股票监控
6. 关税政策关键词追踪
"""

import requests
import json
import time
import os
import re
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import threading

# 尝试导入可选依赖
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


@dataclass
class TrumpPost:
    """Trump 帖子数据结构"""
    id: str
    content: str
    created_at: datetime
    source: str  # 'truth_social', 'twitter', 'news'
    sentiment: str = ""  # 'positive', 'negative', 'neutral'
    entities: List[str] = None  # 提到的公司/关键词
    trading_signal: str = ""  # 'buy', 'sell', 'watch', 'none'
    target_stocks: List[str] = None
    ai_analysis: str = ""


@dataclass
class TradingSignal:
    """交易信号"""
    source: str  # 来源帖子ID
    signal_type: str  # 'buy', 'sell', 'watch'
    confidence: int  # 0-100
    target_assets: List[Dict]  # [{"symbol": "AAPL", "type": "stock", "reason": "..."}]
    trigger_keywords: List[str]
    analysis: str
    timestamp: datetime


class TrumpTracker:
    """Trump 交易追踪器主类"""
    
    # 关键词映射表
    KEYWORD_MAPPINGS = {
        # 关税/贸易
        "tariff": {"signal": "watch", "targets": ["SPY", "QQQ", "AAPL", "TSLA"], "sector": "trade"},
        "china": {"signal": "watch", "targets": ["BABA", "JD", "PDD", "NIO", "KWEB"], "sector": "china"},
        "trade war": {"signal": "sell", "targets": ["SPY", "QQQ"], "sector": "trade"},
        
        # 特定公司
        "apple": {"signal": "watch", "targets": ["AAPL"], "sector": "tech"},
        "tim cook": {"signal": "watch", "targets": ["AAPL"], "sector": "tech"},
        "tesla": {"signal": "watch", "targets": ["TSLA"], "sector": "ev"},
        "elon": {"signal": "watch", "targets": ["TSLA", "X"], "sector": "tech"},
        "amazon": {"signal": "watch", "targets": ["AMZN"], "sector": "tech"},
        "jeff bezos": {"signal": "watch", "targets": ["AMZN"], "sector": "tech"},
        "microsoft": {"signal": "watch", "targets": ["MSFT"], "sector": "tech"},
        "google": {"signal": "watch", "targets": ["GOOGL"], "sector": "tech"},
        "meta": {"signal": "watch", "targets": ["META"], "sector": "tech"},
        "nvidia": {"signal": "watch", "targets": ["NVDA"], "sector": "tech"},
        "bitcoin": {"signal": "watch", "targets": ["BTC", "MSTR", "COIN"], "sector": "crypto"},
        "crypto": {"signal": "watch", "targets": ["BTC", "ETH", "COIN", "MSTR"], "sector": "crypto"},
        
        # 能源
        "oil": {"signal": "watch", "targets": ["XOM", "CVX", "USO"], "sector": "energy"},
        "gas": {"signal": "watch", "targets": ["XOM", "CVX"], "sector": "energy"},
        "drill": {"signal": "buy", "targets": ["XLE", "XOM", "CVX"], "sector": "energy"},
        
        # 金融
        "fed": {"signal": "watch", "targets": ["SPY", "QQQ", "TLT", "GLD"], "sector": "macro"},
        "interest rate": {"signal": "watch", "targets": ["TLT", "TBT", "SPY"], "sector": "macro"},
        "dollar": {"signal": "watch", "targets": ["UUP", "GLD"], "sector": "forex"},
        
        # 军事/国防
        "war": {"signal": "buy", "targets": ["LMT", "RTX", "NOC", "GD"], "sector": "defense"},
        "military": {"signal": "buy", "targets": ["LMT", "RTX", "NOC"], "sector": "defense"},
        "defense": {"signal": "buy", "targets": ["LMT", "RTX", "NOC"], "sector": "defense"},
        
        # DJT 相关
        "truth social": {"signal": "buy", "targets": ["DJT"], "sector": "trump"},
        "media": {"signal": "watch", "targets": ["DJT"], "sector": "trump"},
    }
    
    def __init__(self, telegram_token: str = None, telegram_chat_id: str = None, openai_key: str = None):
        self.posts: List[TrumpPost] = []
        self.signals: List[TradingSignal] = []
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.openai_key = openai_key
        
        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if OPENAI_AVAILABLE and openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
        else:
            self.openai_client = None
            
        self.last_check_time = datetime.now() - timedelta(hours=1)
        
    def fetch_truth_social(self) -> List[TrumpPost]:
        """获取 Truth Social 帖子 (使用 CNN 实时存档)"""
        print("📡 从 CNN 存档获取 Truth Social 新帖子...")
        
        try:
            # CNN 维护的实时 Trump 帖子存档 (每5分钟更新)
            url = "https://ix.cnn.io/data/truth-social/truth_archive.json"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            # CNN 格式: 通常是对象列表，每个对象有 content, created_at 等字段
            for item in data:
                # 处理不同可能的格式
                content = item.get("content") or item.get("text") or item.get("body", "")
                post_id = item.get("id") or item.get("post_id") or f"ts_{hash(content) % 10000}"
                created_str = item.get("created_at") or item.get("date") or item.get("timestamp")
                
                if not content:
                    continue
                
                # 解析时间
                try:
                    # 尝试多种时间格式
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
                        try:
                            created_at = datetime.strptime(created_str, fmt)
                            break
                        except:
                            continue
                    else:
                        # 如果是时间戳
                        try:
                            created_at = datetime.fromtimestamp(int(created_str))
                        except:
                            created_at = datetime.now() - timedelta(hours=1)
                except:
                    created_at = datetime.now() - timedelta(hours=1)
                
                # 只获取最近的新帖子
                if created_at > self.last_check_time:
                    posts.append(TrumpPost(
                        id=str(post_id),
                        content=content,
                        created_at=created_at,
                        source="truth_social"
                    ))
            
            print(f"   找到 {len(posts)} 条新帖子")
            return posts
            
        except Exception as e:
            print(f"   ⚠️  获取 CNN 数据失败: {e}")
            print("   使用备用模拟数据...")
            return self._fetch_mock_data()
    
    def _fetch_mock_data(self) -> List[TrumpPost]:
        """备用模拟数据"""
        mock_posts = [
            {
                "id": "ts_001",
                "content": "Apple is making great products in America! Tim Cook is a friend of mine. MAGA!",
                "created_at": datetime.now() - timedelta(minutes=30),
            },
            {
                "id": "ts_002", 
                "content": "China trade deal is going to be HUGE. Tariffs working better than expected!",
                "created_at": datetime.now() - timedelta(hours=2),
            },
            {
                "id": "ts_003",
                "content": "Bitcoin is the future. The US will be the crypto capital of the world!",
                "created_at": datetime.now() - timedelta(hours=5),
            },
        ]
        
        posts = []
        for p in mock_posts:
            if p["created_at"] > self.last_check_time:
                posts.append(TrumpPost(
                    id=p["id"],
                    content=p["content"],
                    created_at=p["created_at"],
                    source="truth_social"
                ))
        return posts
    
    def analyze_with_ai(self, post: TrumpPost) -> TrumpPost:
        """使用 AI 分析帖子内容"""
        if not self.openai_client:
            # 回退到关键词匹配
            return self._analyze_with_keywords(post)
        
        try:
            prompt = f"""
            Analyze this Trump social media post for trading signals:
            
            Post: "{post.content}"
            
            1. Sentiment (positive/negative/neutral toward market/stocks)
            2. Entities mentioned (companies, sectors, assets)
            3. Trading signal (buy/sell/watch/none)
            4. Target stocks/crypto if any
            5. Brief analysis (1-2 sentences)
            
            Return JSON format:
            {{
                "sentiment": "positive",
                "entities": ["Apple", "Tech"],
                "signal": "watch",
                "targets": ["AAPL"],
                "analysis": "Positive mention of Apple suggests potential upside"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            post.sentiment = result.get("sentiment", "neutral")
            post.entities = result.get("entities", [])
            post.trading_signal = result.get("signal", "none")
            post.target_stocks = result.get("targets", [])
            post.ai_analysis = result.get("analysis", "")
            
        except Exception as e:
            print(f"   AI分析失败，回退到关键词: {e}")
            return self._analyze_with_keywords(post)
        
        return post
    
    def _analyze_with_keywords(self, post: TrumpPost) -> TrumpPost:
        """使用关键词匹配分析"""
        content_lower = post.content.lower()
        
        matched_keywords = []
        target_stocks = set()
        signal_strength = "none"
        
        for keyword, mapping in self.KEYWORD_MAPPINGS.items():
            if keyword in content_lower:
                matched_keywords.append(keyword)
                target_stocks.update(mapping["targets"])
                if mapping["signal"] in ["buy", "sell"]:
                    signal_strength = mapping["signal"]
                elif signal_strength == "none":
                    signal_strength = mapping["signal"]
        
        post.entities = list(matched_keywords)
        post.target_stocks = list(target_stocks)
        post.trading_signal = signal_strength if matched_keywords else "none"
        post.ai_analysis = f"关键词匹配: {', '.join(matched_keywords)}" if matched_keywords else "无交易信号"
        
        # 简单情绪分析
        positive_words = ["great", "good", "best", "incredible", "huge", "love", "friend"]
        negative_words = ["bad", "terrible", "worst", "hate", "enemy", "disaster"]
        
        pos_count = sum(1 for w in positive_words if w in content_lower)
        neg_count = sum(1 for w in negative_words if w in content_lower)
        
        if pos_count > neg_count:
            post.sentiment = "positive"
        elif neg_count > pos_count:
            post.sentiment = "negative"
        else:
            post.sentiment = "neutral"
        
        return post
    
    def generate_signal(self, post: TrumpPost) -> Optional[TradingSignal]:
        """从帖子生成交易信号"""
        if post.trading_signal == "none" or not post.target_stocks:
            return None
        
        # 获取当前股价
        assets = []
        for symbol in post.target_stocks[:5]:  # 最多5个标的
            price = self._get_stock_price(symbol) if YFINANCE_AVAILABLE else 0
            assets.append({
                "symbol": symbol,
                "type": "crypto" if symbol in ["BTC", "ETH"] else "stock",
                "current_price": price,
                "reason": f"Trump mentioned in post: '{post.content[:50]}...'"
            })
        
        # 计算置信度
        confidence = 50  # 基础分
        if post.sentiment == "positive" and post.trading_signal == "buy":
            confidence += 20
        if len(post.entities) >= 2:
            confidence += 10
        if "great" in post.content.lower() or "best" in post.content.lower():
            confidence += 10
        
        return TradingSignal(
            source=post.id,
            signal_type=post.trading_signal,
            confidence=min(confidence, 95),
            target_assets=assets,
            trigger_keywords=post.entities,
            analysis=post.ai_analysis,
            timestamp=post.created_at
        )
    
    def _get_stock_price(self, symbol: str) -> float:
        """获取股票当前价格"""
        if not YFINANCE_AVAILABLE:
            return 0.0
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        return 0.0
    
    def get_recent_posts_summary(self, limit: int = 5) -> str:
        """获取最近Trump帖子的摘要"""
        try:
            url = "https://ix.cnn.io/data/truth-social/truth_archive.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            summary = []
            for i, item in enumerate(data[:limit]):
                content = item.get("content", "")[:150]  # 截取前150字符
                if len(item.get("content", "")) > 150:
                    content += "..."
                
                created_str = item.get("created_at", "")
                try:
                    # 解析ISO格式时间
                    created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    time_ago = (datetime.now() - created.replace(tzinfo=None)).total_seconds() / 3600
                    if time_ago < 1:
                        time_str = f"{int(time_ago * 60)}分钟前"
                    else:
                        time_str = f"{int(time_ago)}小时前"
                except:
                    time_str = "未知时间"
                
                # 提取关键词
                content_lower = content.lower()
                keywords_found = []
                for kw in self.KEYWORD_MAPPINGS.keys():
                    if kw in content_lower:
                        keywords_found.append(kw)
                
                # 获取帖子URL
                post_url = item.get("url", "")
                
                summary.append({
                    "content": content,
                    "time": time_str,
                    "keywords": keywords_found[:3],  # 最多3个关键词
                    "url": post_url
                })
            
            return summary
        except Exception as e:
            print(f"   获取摘要失败: {e}")
            return []
    
    def send_telegram_alert(self, signal: TradingSignal, include_summary: bool = True):
        """发送 Telegram 通知"""
        if not self.telegram_token or not self.telegram_chat_id:
            print("   ⚠️  Telegram 未配置，跳过通知")
            return
        
        # 获取最近帖子摘要
        recent_summary = []
        if include_summary:
            recent_summary = self.get_recent_posts_summary(5)
        
        # 构建消息
        emoji = "🟢" if signal.signal_type == "buy" else "🔴" if signal.signal_type == "sell" else "🟡"
        confidence_stars = "⭐" * (signal.confidence // 20)
        
        message = f"""
{emoji} **Trump 交易信号** {emoji}

**信号类型**: {signal.signal_type.upper()}
**置信度**: {signal.confidence}/100 {confidence_stars}
**时间**: {signal.timestamp.strftime('%Y-%m-%d %H:%M')}

**触发关键词**: {', '.join(signal.trigger_keywords)}

**目标标的**:
"""
        
        for asset in signal.target_assets:
            price_str = f"${asset['current_price']:.2f}" if asset['current_price'] > 0 else "N/A"
            message += f"\n• {asset['symbol']} ({asset['type']}) - {price_str}"
        
        message += f"""

**AI分析**:
{signal.analysis}
"""
        
        # 添加Trump最新动态摘要
        if recent_summary:
            message += """
———————————————————
📰 **Trump 最新动态摘要**
"""
            for i, post in enumerate(recent_summary[:3], 1):
                keywords_str = f" | 关键词: {', '.join(post['keywords'])}" if post['keywords'] else ""
                url_str = f"\n   🔗 [查看原文]({post['url']})" if post.get('url') else ""
                message += f"""
{i}. [{post['time']}] {post['content'][:100]}{keywords_str}{url_str}
"""
        
        message += """
———————————————————
⚠️ **免责声明**: 此为AI自动分析，不构成投资建议。请自行判断风险。
"""
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("   ✅ Telegram 通知已发送")
            else:
                print(f"   ❌ Telegram 发送失败: {response.text}")
        except Exception as e:
            print(f"   ❌ Telegram 错误: {e}")
    
    def check_djt_stock(self):
        """检查 DJT (Trump Media) 股票异动"""
        if not YFINANCE_AVAILABLE:
            return
        
        print("📈 检查 DJT 股票...")
        try:
            djt = yf.Ticker("DJT")
            hist = djt.history(period="5d")
            
            if len(hist) >= 2:
                latest_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change_pct = ((latest_price - prev_price) / prev_price) * 100
                
                print(f"   DJT 当前价格: ${latest_price:.2f} ({change_pct:+.2f}%)")
                
                # 如果波动超过5%，生成信号
                if abs(change_pct) > 5:
                    signal_type = "buy" if change_pct > 0 else "sell"
                    signal = TradingSignal(
                        source="DJT_PRICE_ALERT",
                        signal_type=signal_type,
                        confidence=70,
                        target_assets=[{"symbol": "DJT", "type": "stock", "current_price": latest_price, "reason": f"Price moved {change_pct:.1f}%"}],
                        trigger_keywords=["DJT", "Trump Media"],
                        analysis=f"DJT stock price moved {change_pct:+.1f}% today",
                        timestamp=datetime.now()
                    )
                    self.send_telegram_alert(signal)
                    
        except Exception as e:
            print(f"   获取DJT价格失败: {e}")
    
    def send_no_signal_report(self, posts_analyzed: int, latest_posts: list):
        """发送无信号报告"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        message = f"""
⚪ **Trump Tracker 4小时报告** ⚪

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**分析帖子数**: {posts_analyzed}
**交易信号**: ❌ 无

最近4小时内 Trump 未提及任何与交易相关的关键词。

"""
        
        # 添加最新动态摘要（即使无信号也显示）
        if latest_posts:
            message += """📰 **Trump 最新动态摘要**\n"""
            for i, post in enumerate(latest_posts[:3], 1):
                url_str = f"\n   🔗 [查看原文]({post.get('url', '')})" if post.get('url') else ""
                content = post.get('content', '')[:100]
                time_str = post.get('time', '未知时间')
                message += f"""
{i}. [{time_str}] {content}...{url_str}
"""
        
        message += """
———————————————————
💡 提示: 当 Trump 提及股票、加密货币、关税等关键词时，将发送交易信号。
"""
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print("   ✅ 无信号报告已发送")
        except Exception as e:
            print(f"   ❌ 发送失败: {e}")
    
    def run_once(self):
        """运行一次检查"""
        print(f"\n{'='*60}")
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Trump Tracker")
        print(f"{'='*60}\n")
        
        signals_generated = []
        posts_analyzed = []
        
        # 1. 获取新帖子
        new_posts = self.fetch_truth_social()
        
        # 2. 分析每个帖子
        for post in new_posts:
            print(f"\n📝 新帖子 [{post.id}]: {post.content[:60]}...")
            
            # AI分析
            analyzed_post = self.analyze_with_ai(post)
            print(f"   情绪: {analyzed_post.sentiment}")
            print(f"   实体: {', '.join(analyzed_post.entities) if analyzed_post.entities else 'None'}")
            print(f"   信号: {analyzed_post.trading_signal}")
            
            posts_analyzed.append(post)
            
            # 生成交易信号
            signal = self.generate_signal(analyzed_post)
            if signal:
                print(f"   🚨 生成交易信号！置信度: {signal.confidence}%")
                self.send_telegram_alert(signal)
                signals_generated.append(signal)
            else:
                print(f"   ℹ️  无交易信号")
        
        # 3. 检查 DJT 股票
        self.check_djt_stock()
        
        # 4. 如果没有交易信号，发送无信号报告
        if not signals_generated and posts_analyzed:
            print("\n📤 无交易信号，发送定期报告...")
            recent_summary = self.get_recent_posts_summary(5)
            self.send_no_signal_report(len(posts_analyzed), recent_summary)
        
        # 更新时间
        self.last_check_time = datetime.now()
        
        print(f"\n✅ 检查完成，等待下次运行...\n")
    
    def run_continuous(self, interval_minutes: int = 15):
        """持续运行"""
        print(f"🚀 Trump Tracker 启动 - 每{interval_minutes}分钟检查一次")
        
        while True:
            try:
                self.run_once()
            except Exception as e:
                print(f"❌ 运行时错误: {e}")
            
            print(f"⏳ 等待 {interval_minutes} 分钟...")
            time.sleep(interval_minutes * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Trump 交易追踪器 - 监控特朗普社交媒体生成交易信号',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 trump_tracker.py --once                    # 运行一次
  python3 trump_tracker.py --loop --interval 30      # 每30分钟循环运行
  python3 trump_tracker.py --test-alert              # 测试 Telegram 通知
        """
    )
    
    parser.add_argument('--once', action='store_true', help='运行一次')
    parser.add_argument('--loop', action='store_true', help='持续循环运行')
    parser.add_argument('--interval', type=int, default=15, help='检查间隔(分钟)，默认15')
    parser.add_argument('--test-alert', action='store_true', help='发送测试通知')
    
    args = parser.parse_args()
    
    # 从环境变量获取配置
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    openai_key = os.getenv('OPENAI_API_KEY', '')
    
    # 创建追踪器
    tracker = TrumpTracker(
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
        openai_key=openai_key
    )
    
    if args.test_alert:
        # 发送测试信号
        test_signal = TradingSignal(
            source="TEST",
            signal_type="buy",
            confidence=85,
            target_assets=[
                {"symbol": "AAPL", "type": "stock", "current_price": 185.50, "reason": "Trump mentioned Apple positively"},
                {"symbol": "TSLA", "type": "stock", "current_price": 240.30, "reason": "Elon relationship"}
            ],
            trigger_keywords=["apple", "tesla"],
            analysis="这是一个测试信号。Trump在Truth Social上称赞了Apple和Tesla。",
            timestamp=datetime.now()
        )
        tracker.send_telegram_alert(test_signal)
        
    elif args.loop:
        tracker.run_continuous(args.interval)
    else:
        # 默认运行一次
        tracker.run_once()


if __name__ == "__main__":
    main()
