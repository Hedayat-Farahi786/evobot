"""
Signal parser for extracting trading signals from Telegram messages.
Uses regex + structured parsing + fallback checks for reliability.
"""
import re
from typing import Optional, List, Tuple
from datetime import datetime
import logging

from models.trade import Signal, SignalType, TradeDirection
from config.settings import config

logger = logging.getLogger("evobot.parser")


class SignalParser:
    """
    Parser for trading signals from Telegram messages.
    Handles various formats, emojis, and formatting differences.
    """
    
    # Supported symbols with aliases
    SYMBOL_ALIASES = {
        "GOLD": "XAUUSD",
        "XAUUSD": "XAUUSD",
        "XAU/USD": "XAUUSD",
        "XAU": "XAUUSD",
        "GBPUSD": "GBPUSD",
        "GBP/USD": "GBPUSD",
        "CABLE": "GBPUSD",
        "EURUSD": "EURUSD",
        "EUR/USD": "EURUSD",
        "FIBER": "EURUSD",
        "USDJPY": "USDJPY",
        "USD/JPY": "USDJPY",
        "USDCAD": "USDCAD",
        "USD/CAD": "USDCAD",
        "LOONIE": "USDCAD",
        "AUDUSD": "AUDUSD",
        "AUD/USD": "AUDUSD",
        "AUSSIE": "AUDUSD",
        "NZDUSD": "NZDUSD",
        "NZD/USD": "NZDUSD",
        "KIWI": "NZDUSD",
        "USDCHF": "USDCHF",
        "USD/CHF": "USDCHF",
        "SWISSY": "USDCHF",
        "GBPJPY": "GBPJPY",
        "GBP/JPY": "GBPJPY",
        "GUPPY": "GBPJPY",
        "EURJPY": "EURJPY",
        "EUR/JPY": "EURJPY",
        "EURGBP": "EURGBP",
        "EUR/GBP": "EURGBP",
        "SILVER": "XAGUSD",
        "XAGUSD": "XAGUSD",
        "XAG/USD": "XAGUSD",
    }
    
    # Regex patterns for parsing
    PATTERNS = {
        # Symbol patterns
        "symbol": re.compile(
            r"\b(XAUUSD|XAU/?USD|GOLD|GBPUSD|GBP/?USD|EURUSD|EUR/?USD|"
            r"USDJPY|USD/?JPY|USDCAD|USD/?CAD|AUDUSD|AUD/?USD|NZDUSD|NZD/?USD|"
            r"USDCHF|USD/?CHF|GBPJPY|GBP/?JPY|EURJPY|EUR/?JPY|EURGBP|EUR/?GBP|"
            r"XAGUSD|XAG/?USD|SILVER|CABLE|FIBER|LOONIE|AUSSIE|KIWI|SWISSY|GUPPY|"
            r"BTCUSD|BTC/?USD|ETHUSD|ETH/?USD|US30|NAS100|USTEC)\b",
            re.IGNORECASE
        ),
        
        # Direction patterns - Updated for "buy now", "SELL NOW" formats
        "buy": re.compile(
            r"\b(BUY|LONG|BULLISH|📈|🟢|🔼|⬆️|COMPRA)\b",
            re.IGNORECASE
        ),
        "sell": re.compile(
            r"\b(SELL|SHORT|BEARISH|📉|🔴|🔽|⬇️|VENDA)\b",
            re.IGNORECASE
        ),
        
        # Entry patterns - Updated for multiple formats:
        # "Entry Zone: X-Y", "🎯5569-- 5568🎯", "Gold buy now 5094 - 5091"
        "entry_single": re.compile(
            r"(?:ENTRY|ENTER|PRICE|@|EP)\s*[:=]?\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        "entry_zone": re.compile(
            r"(?:ENTRY|ENTER)\s*(?:ZONE)?\s*[:=]?\s*(\d+\.?\d*)\s*[-–—]+\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        # Format: 🎯5569-- 5568🎯 or 🎯5569--5568🎯
        "entry_emoji_zone": re.compile(
            r"🎯\s*(\d+\.?\d*)\s*[-–—]+\s*(\d+\.?\d*)\s*🎯",
            re.IGNORECASE
        ),
        # Format: "Gold buy now 5094 - 5091" - price range after direction
        "entry_after_direction": re.compile(
            r"(?:buy|sell)\s+now\s+(\d+\.?\d*)\s*[-–—]\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        "entry_now": re.compile(
            r"\b(NOW|MARKET|INSTANT|CMP|CURRENT)\b",
            re.IGNORECASE
        ),
        
        # Stop Loss patterns - Updated for "Stop loss: X", "SL 5550", "SL: 5088"
        "sl": re.compile(
            r"(?:SL|STOP\s*LOSS|STOPLOSS|S\.L\.?)\s*[:=]?\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        
        # Take Profit patterns - Updated for multiple formats:
        # "TP1: 5572", "Take Profit 1: X", "TP: 5096" (multiple TPs)
        "tp1": re.compile(
            r"(?:TP\s*1|TP1|TAKE\s*PROFIT\s*1|T\.P\.?\s*1)\s*[:=]?\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        "tp2": re.compile(
            r"(?:TP\s*2|TP2|TAKE\s*PROFIT\s*2|T\.P\.?\s*2)\s*[:=]?\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        "tp3": re.compile(
            r"(?:TP\s*3|TP3|TAKE\s*PROFIT\s*3|T\.P\.?\s*3)\s*[:=]?\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        "tp_generic": re.compile(
            r"(?:TP|TAKE\s*PROFIT|TARGET|T\.P\.?)\s*[:=]?\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        # Multiple "TP:" lines format (Channel 1)
        "tp_line": re.compile(
            r"^TP\s*[:=]?\s*(\d+\.?\d*)\s*$",
            re.IGNORECASE | re.MULTILINE
        ),
        
        # Lot size patterns - Updated for "use 0.01 lot size" format
        "lot": re.compile(
            r"(?:LOT|LOTS|SIZE|VOLUME|use)\s*(?:size)?\s*[:=]?\s*(\d+\.?\d*)",
            re.IGNORECASE
        ),
        
        # Update patterns - TP hit messages
        # "All 3 TakeProfits hit", "TP1 hit", "reaches TP1", "TP 1,2,3 hit"
        "tp_hit": re.compile(
            r"(?:TP\s*(\d)?(?:\s*,\s*\d)*\s*(?:HIT|REACHED|DONE|✅)|TARGET\s*(\d)?\s*(?:HIT|REACHED)|"
            r"ALL\s*\d?\s*(?:TAKE\s*PROFITS?|TPS?)\s*(?:HIT|REACHED|DONE)|"
            r"reaches\s*(?:🔥)?TP(\d)?(?:️⃣)?(?:🔥)?)",
            re.IGNORECASE
        ),
        "tp_multi_hit": re.compile(
            r"TP\s*(\d)(?:\s*,\s*(\d))*\s*(?:HIT|✅)",
            re.IGNORECASE
        ),
        # "All 3 TPs have been achieved" format
        "all_tp_hit": re.compile(
            r"ALL\s*(\d)?\s*(?:TPS?|TAKE\s*PROFITS?)\s*(?:HAVE\s*BEEN\s*)?(?:ACHIEVED|HIT|REACHED|DONE)",
            re.IGNORECASE
        ),
        
        "sl_hit": re.compile(
            r"(?:SL\s*(?:HIT|REACHED|TRIGGERED|❌)|STOP\s*LOSS\s*(?:HIT|REACHED)|^SL\s*❌)",
            re.IGNORECASE
        ),
        "breakeven": re.compile(
            r"(?:BREAKEVEN|BE|MOVE\s*SL\s*TO\s*(?:ENTRY|BE|HOLD)|SL\s*TO\s*(?:ENTRY|BE|HOLD)|"
            r"SET\s*BREAKEVEN|MOVE\s*SL\s*TO\s*ENTRY)",
            re.IGNORECASE
        ),
        "close": re.compile(
            r"(?:^CLOSED$|TRADE\s*CLOSED|CLOSE\s*(?:ALL\s*)?TRADES?|EXIT|EXITED|CANCEL|CANCELLED|INVALIDATED|"
            r"CLOSE\s*MANUALLY|CLOSE\s*(?:PART|PARTIAL))",
            re.IGNORECASE | re.MULTILINE
        ),
        
        # New signal indicator - "🔔🔔🔔 NEW SIGNAL 🔔🔔🔔", "🔔Ready Signal"
        "new_signal": re.compile(
            r"(?:🔔+\s*)?(?:NEW\s*SIGNAL|READY\s*SIGNAL)(?:\s*🔔+)?",
            re.IGNORECASE
        ),
        
        # Price number extraction (fallback)
        "price": re.compile(r"(\d{1,5}\.?\d{0,5})"),
    }
    
    def __init__(self):
        self.logger = logging.getLogger("evobot.parser")
        
        # Phrases that indicate non-signal messages (announcements, chat, promotions, etc.)
        self.IGNORE_PHRASES = [
            "will start",
            "session soon",
            "signals will be paused",
            "read pinned",
            "connect the bot",
            "today james goal",
            "make sure lot size",
            "recommended minimum balance",
            "calibrating the bot",
            "please do not spam",
            "scalping strategy",
            "automatic trader",
            "recovering all losses",
            "send me last",
            "working perfectly",
            "answering you all",
            "people messaged",
            "example of james",
            "copybot is working",
            "give it 1-3 days",
            "last scalped trades",
            "new user - connect",
            "scroll down",
            "triple check",
            "expect delays",
            "dm me",
            "critical/risky",
            "top up",
            "buffer in case",
            "don't be scared",
            "don't be afraid",
            "extremely happy",
            "private account",
            "automatically copy",
            # Channel 2 promotional messages
            "new year bonanza",
            "premium signals for just",
            "win rate to lock",
            "limited-time offer",
            "dm me to secure",
            "chief analyst",
            "chief tutor",
            "super signal group",
            "unlock",
            "privilege previously",
            "account balance",
            # Channel 3/4 promotional/chat messages
            "screenshot of your wins",
            "day in a life",
            "hundreds of profits",
            "small break and later",
            "were liquidated",
            "people made around",
            "you are in the 1-3%",
            "never use stop loss on scalping",
            "i wanna share something",
            "basically gambled",
            "single mistake",
            "more scalping",
            "please everybody top up",
            "quick night scalping",
            "good night",
            # General promotional
            "trading signal statistics",
            "total profits",
            "total losses",
            "results:",
            "lot = $",
        ]
        
        # Phrases that indicate it IS a signal (override ignore)
        self.SIGNAL_INDICATORS = [
            "buy now",
            "sell now",
            "new signal",
            "ready signal",
            "entry zone",
            "stop loss",
            "take profit",
            "sl:",
            "tp:",
            "tp1:",
            "tp2:",
            "tp3:",
        ]
    
    def is_ignorable_message(self, message: str) -> bool:
        """Check if message should be ignored (announcements, chat, etc.)"""
        msg_lower = message.lower()
        
        # First check if it has strong signal indicators - never ignore these
        for indicator in self.SIGNAL_INDICATORS:
            if indicator in msg_lower:
                return False
        
        # Check for TP/SL hit messages - these are important updates
        if "hit" in msg_lower and ("tp" in msg_lower or "takeprofit" in msg_lower.replace(" ", "")):
            return False
        if "reached" in msg_lower and "tp" in msg_lower:
            return False
        if "achieved" in msg_lower and "tp" in msg_lower:
            return False
        if "breakeven" in msg_lower or "break even" in msg_lower:
            return False
        if "sl" in msg_lower and ("hit" in msg_lower or "❌" in message):
            return False
        
        # Check for ignore phrases
        for phrase in self.IGNORE_PHRASES:
            if phrase in msg_lower:
                return True
        
        # Ignore very short messages (less than 20 chars) unless they have key indicators
        if len(message) < 20:
            # Short messages are OK if they're TP/SL updates
            if "tp" in msg_lower or "sl" in msg_lower or "hit" in msg_lower:
                return False
            return True
        
        # Ignore if no trading-related keywords at all
        trading_keywords = ["buy", "sell", "entry", "stop loss", "sl:", "sl ", "tp", "take profit", 
                          "new signal", "ready signal", "🔔", "hit", "closed", "breakeven", "🎯",
                          "achieved", "reached", "pips"]
        has_trading_keyword = any(kw in msg_lower for kw in trading_keywords)
        
        if not has_trading_keyword:
            return True
        
        return False
    
    def parse(self, message: str, channel_id: str = "", message_id: int = 0) -> Signal:
        """
        Parse a Telegram message and extract trading signal.
        
        Args:
            message: Raw message text
            channel_id: Source channel ID
            message_id: Message ID
            
        Returns:
            Signal object with parsed data
        """
        signal = Signal(
            raw_message=message,
            channel_id=channel_id,
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
        
        # Check if message should be ignored (announcements, chat, etc.)
        if self.is_ignorable_message(message):
            signal.signal_type = SignalType.UNKNOWN
            signal.parse_errors.append("Non-signal message (announcement/chat)")
            signal.parsed_successfully = False
            return signal
        
        # Clean message
        clean_msg = self._clean_message(message)
        
        # Determine signal type
        signal.signal_type = self._detect_signal_type(clean_msg)
        
        # Parse based on signal type
        if signal.signal_type == SignalType.NEW_TRADE:
            self._parse_new_trade(clean_msg, signal)
        elif signal.signal_type in [SignalType.TP1_HIT, SignalType.TP2_HIT, SignalType.TP3_HIT]:
            self._parse_tp_hit(clean_msg, signal)
        elif signal.signal_type == SignalType.SL_HIT:
            self._parse_sl_hit(clean_msg, signal)
        elif signal.signal_type == SignalType.BREAKEVEN:
            self._parse_breakeven(clean_msg, signal)
        elif signal.signal_type == SignalType.CLOSE_TRADE:
            self._parse_close(clean_msg, signal)
        elif signal.signal_type == SignalType.UPDATE_SL:
            self._parse_sl_update(clean_msg, signal)
        elif signal.signal_type == SignalType.UPDATE_TP:
            self._parse_tp_update(clean_msg, signal)
        
        # Validate signal
        signal.parsed_successfully = self._validate_signal(signal)
        
        return signal
    
    def _clean_message(self, message: str) -> str:
        """Clean and normalize message text"""
        # Remove Telegram markdown formatting (**, __, ~~, `, etc.)
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', message)  # Bold **text**
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)      # Italic *text*
        cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)      # Underline __text__
        cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)        # Italic _text_
        cleaned = re.sub(r'~~([^~]+)~~', r'\1', cleaned)      # Strikethrough ~~text~~
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)        # Code `text`
        cleaned = re.sub(r'```[^`]*```', '', cleaned)         # Code blocks
        # Remove common Unicode characters that look like spaces
        cleaned = cleaned.replace('\u200b', '').replace('\u200c', '').replace('\u200d', '')
        # Replace multiple spaces with single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Replace various dash types with standard dash
        cleaned = re.sub(r'[–—−]', '-', cleaned)
        return cleaned.strip()
    
    def _detect_signal_type(self, message: str) -> SignalType:
        """Detect the type of signal from message content"""
        msg_lower = message.lower()
        
        # Check for SL hit first (before TP checks) - "SL ❌" format
        if self.PATTERNS["sl_hit"].search(message) or "sl ❌" in msg_lower or "sl❌" in msg_lower:
            return SignalType.SL_HIT
        
        # Check for "All TPs achieved/hit" format (Channel 2) - before NEW SIGNAL check
        if self.PATTERNS["all_tp_hit"].search(message) or "all 3 tps" in msg_lower or "all 3️⃣ tps" in msg_lower:
            return SignalType.TP3_HIT
        
        # Check for "All TakeProfits hit" format (Channel 1)
        if "all" in msg_lower and "takeprofit" in msg_lower.replace(" ", "") and "hit" in msg_lower:
            return SignalType.TP3_HIT
        
        # Check for TP hit with "reaches" format BEFORE checking for new signal
        # "reaches TP1", "reaches TP2", "reaches TP3"
        if "reaches" in msg_lower and "tp" in msg_lower:
            if "tp3" in msg_lower or "tp 3" in msg_lower or "tp3️⃣" in message:
                return SignalType.TP3_HIT
            if "tp2" in msg_lower or "tp 2" in msg_lower or "tp2️⃣" in message:
                return SignalType.TP2_HIT
            if "tp1" in msg_lower or "tp 1" in msg_lower or "tp1️⃣" in message:
                return SignalType.TP1_HIT
            return SignalType.TP1_HIT  # Default to TP1 if just "reaches TP"
        
        # Check for "NEW SIGNAL" or "Ready Signal" indicator
        if self.PATTERNS["new_signal"].search(message):
            return SignalType.NEW_TRADE
        
        # Check for CLOSED signal
        if re.search(r'^CLOSED$', message, re.MULTILINE | re.IGNORECASE) or "trade closed" in msg_lower:
            # But if there's entry/SL/TP info, it's a new signal with status
            if "entry" in msg_lower and ("stop loss" in msg_lower or "sl:" in msg_lower or "sl " in msg_lower):
                return SignalType.NEW_TRADE
            return SignalType.CLOSE_TRADE
        
        # Check for TP hit - "TP 1 hit", "TP 1,2 hit" formats
        tp_match = self.PATTERNS["tp_hit"].search(message)
        if tp_match or "tp 1 hit" in msg_lower or "tp1 hit" in msg_lower:
            # But if there's entry/SL/TP info, it's a new signal with status note
            if "entry" in msg_lower and ("stop loss" in msg_lower or "sl:" in msg_lower or "sl " in msg_lower):
                return SignalType.NEW_TRADE
            
            # Check for multi-TP hit like "TP 1,2 hit"
            if "tp 1,2" in msg_lower or "tp1,2" in msg_lower:
                return SignalType.TP2_HIT
            if "tp 1,2,3" in msg_lower or "tp1,2,3" in msg_lower:
                return SignalType.TP3_HIT
            
            # Check for specific TP number
            if "tp3" in msg_lower or "tp 3" in msg_lower or "tp3️⃣" in message:
                return SignalType.TP3_HIT
            if "tp2" in msg_lower or "tp 2" in msg_lower or "tp2️⃣" in message:
                return SignalType.TP2_HIT
            
            return SignalType.TP1_HIT
        
        # Check for breakeven - "Move SL to entry", "Set breakeven", "move SL to Hold"
        if self.PATTERNS["breakeven"].search(message) or "move sl to entry" in msg_lower or "set breakeven" in msg_lower:
            return SignalType.BREAKEVEN
        
        # Check for close/cancel - "Close all trades", "close manually"
        if self.PATTERNS["close"].search(message):
            return SignalType.CLOSE_TRADE
        
        # Check for SL update
        if "update" in msg_lower and "sl" in msg_lower:
            return SignalType.UPDATE_SL
        
        # Check for TP update
        if "update" in msg_lower and "tp" in msg_lower:
            return SignalType.UPDATE_TP
        
        # Default to new trade if has direction indicator
        if self.PATTERNS["buy"].search(message) or self.PATTERNS["sell"].search(message):
            return SignalType.NEW_TRADE
        
        return SignalType.NEW_TRADE
    
    def _parse_new_trade(self, message: str, signal: Signal):
        """Parse a new trade signal"""
        # Extract symbol
        symbol_match = self.PATTERNS["symbol"].search(message)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper().replace("/", "")
            signal.symbol = self.SYMBOL_ALIASES.get(raw_symbol, raw_symbol)
        else:
            signal.parse_errors.append("Symbol not found")
        
        # Extract direction
        if self.PATTERNS["buy"].search(message):
            signal.direction = TradeDirection.BUY
        elif self.PATTERNS["sell"].search(message):
            signal.direction = TradeDirection.SELL
        else:
            signal.parse_errors.append("Direction not found")
        
        # Extract entry zone or single entry - try multiple formats
        entry_found = False
        
        # Format 1: "Entry Zone: X-Y"
        entry_zone_match = self.PATTERNS["entry_zone"].search(message)
        if entry_zone_match:
            entry1 = float(entry_zone_match.group(1))
            entry2 = float(entry_zone_match.group(2))
            signal.entry_min = min(entry1, entry2)
            signal.entry_max = max(entry1, entry2)
            entry_found = True
        
        # Format 2: "🎯5569-- 5568🎯"
        if not entry_found:
            emoji_zone_match = self.PATTERNS["entry_emoji_zone"].search(message)
            if emoji_zone_match:
                entry1 = float(emoji_zone_match.group(1))
                entry2 = float(emoji_zone_match.group(2))
                signal.entry_min = min(entry1, entry2)
                signal.entry_max = max(entry1, entry2)
                entry_found = True
        
        # Format 3: "Gold buy now 5094 - 5091"
        if not entry_found:
            after_dir_match = self.PATTERNS["entry_after_direction"].search(message)
            if after_dir_match:
                entry1 = float(after_dir_match.group(1))
                entry2 = float(after_dir_match.group(2))
                signal.entry_min = min(entry1, entry2)
                signal.entry_max = max(entry1, entry2)
                entry_found = True
        
        # Format 4: Single entry "Entry: X" or "@X"
        if not entry_found:
            entry_single_match = self.PATTERNS["entry_single"].search(message)
            if entry_single_match:
                entry = float(entry_single_match.group(1))
                signal.entry_min = entry
                signal.entry_max = entry
                entry_found = True
        
        # Format 5: Market order - "NOW"
        if not entry_found and self.PATTERNS["entry_now"].search(message):
            # Market order - entry will be determined at execution
            signal.entry_min = None
            signal.entry_max = None
            entry_found = True
        
        # Fallback extraction
        if not entry_found:
            entries = self._extract_prices_fallback(message, "entry")
            if entries:
                signal.entry_min = entries[0]
                signal.entry_max = entries[-1] if len(entries) > 1 else entries[0]
            else:
                signal.parse_errors.append("Entry price not found")
        
        # Extract Stop Loss
        sl_match = self.PATTERNS["sl"].search(message)
        if sl_match:
            signal.stop_loss = float(sl_match.group(1))
        else:
            signal.parse_errors.append("Stop loss not found")
        
        # Extract Take Profits - try numbered TPs first
        tp1_match = self.PATTERNS["tp1"].search(message)
        tp2_match = self.PATTERNS["tp2"].search(message)
        tp3_match = self.PATTERNS["tp3"].search(message)
        
        if tp1_match:
            signal.take_profit_1 = float(tp1_match.group(1))
        if tp2_match:
            signal.take_profit_2 = float(tp2_match.group(1))
        if tp3_match:
            signal.take_profit_3 = float(tp3_match.group(1))
        
        # If no numbered TPs, try multiple "TP:" lines format (Channel 1)
        if not signal.take_profit_1:
            tp_lines = self.PATTERNS["tp_line"].findall(message)
            if tp_lines:
                tps = [float(tp) for tp in tp_lines]
                # Sort TPs based on direction
                if signal.direction == TradeDirection.BUY:
                    tps.sort()  # Ascending for BUY (lowest TP first)
                else:
                    tps.sort(reverse=True)  # Descending for SELL (highest TP first)
                
                if len(tps) >= 1:
                    signal.take_profit_1 = tps[0]
                if len(tps) >= 2:
                    signal.take_profit_2 = tps[1]
                if len(tps) >= 3:
                    signal.take_profit_3 = tps[2]
        
        # If still no TPs, try generic TP pattern
        if not signal.take_profit_1:
            generic_tps = self.PATTERNS["tp_generic"].findall(message)
            if generic_tps:
                # Filter out any TP that matches SL (avoid false positives)
                tps = []
                for tp in generic_tps:
                    tp_val = float(tp)
                    if signal.stop_loss and abs(tp_val - signal.stop_loss) < 0.1:
                        continue  # Skip if too close to SL
                    tps.append(tp_val)
                
                # Sort TPs based on direction
                if signal.direction == TradeDirection.BUY:
                    tps.sort()
                else:
                    tps.sort(reverse=True)
                
                if len(tps) >= 1:
                    signal.take_profit_1 = tps[0]
                if len(tps) >= 2:
                    signal.take_profit_2 = tps[1]
                if len(tps) >= 3:
                    signal.take_profit_3 = tps[2]
        
        if not signal.take_profit_1:
            signal.parse_errors.append("Take profit not found")
        
        # Extract lot size (optional)
        lot_match = self.PATTERNS["lot"].search(message)
        if lot_match:
            signal.lot_size = float(lot_match.group(1))
    
    def _parse_tp_hit(self, message: str, signal: Signal):
        """Parse TP hit update"""
        symbol_match = self.PATTERNS["symbol"].search(message)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper().replace("/", "")
            signal.symbol = self.SYMBOL_ALIASES.get(raw_symbol, raw_symbol)
    
    def _parse_sl_hit(self, message: str, signal: Signal):
        """Parse SL hit update"""
        symbol_match = self.PATTERNS["symbol"].search(message)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper().replace("/", "")
            signal.symbol = self.SYMBOL_ALIASES.get(raw_symbol, raw_symbol)
    
    def _parse_breakeven(self, message: str, signal: Signal):
        """Parse breakeven update"""
        symbol_match = self.PATTERNS["symbol"].search(message)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper().replace("/", "")
            signal.symbol = self.SYMBOL_ALIASES.get(raw_symbol, raw_symbol)
    
    def _parse_close(self, message: str, signal: Signal):
        """Parse close/cancel update"""
        symbol_match = self.PATTERNS["symbol"].search(message)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper().replace("/", "")
            signal.symbol = self.SYMBOL_ALIASES.get(raw_symbol, raw_symbol)
    
    def _parse_sl_update(self, message: str, signal: Signal):
        """Parse SL update"""
        symbol_match = self.PATTERNS["symbol"].search(message)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper().replace("/", "")
            signal.symbol = self.SYMBOL_ALIASES.get(raw_symbol, raw_symbol)
        
        sl_match = self.PATTERNS["sl"].search(message)
        if sl_match:
            signal.stop_loss = float(sl_match.group(1))
    
    def _parse_tp_update(self, message: str, signal: Signal):
        """Parse TP update"""
        symbol_match = self.PATTERNS["symbol"].search(message)
        if symbol_match:
            raw_symbol = symbol_match.group(1).upper().replace("/", "")
            signal.symbol = self.SYMBOL_ALIASES.get(raw_symbol, raw_symbol)
        
        tp1_match = self.PATTERNS["tp1"].search(message)
        tp2_match = self.PATTERNS["tp2"].search(message)
        tp3_match = self.PATTERNS["tp3"].search(message)
        
        if tp1_match:
            signal.take_profit_1 = float(tp1_match.group(1))
        if tp2_match:
            signal.take_profit_2 = float(tp2_match.group(1))
        if tp3_match:
            signal.take_profit_3 = float(tp3_match.group(1))
    
    def _extract_prices_fallback(self, message: str, context: str) -> List[float]:
        """
        Fallback price extraction based on context.
        Looks for numbers that could be prices near context keywords.
        """
        prices = []
        
        # Find all numbers in message
        all_numbers = self.PATTERNS["price"].findall(message)
        
        # Filter for plausible prices based on symbol context
        for num_str in all_numbers:
            try:
                num = float(num_str)
                # Gold prices typically 1000-3000
                # Forex pairs typically 0.5-2.0 or 100-200 for JPY pairs
                if 0.1 < num < 10000:
                    prices.append(num)
            except ValueError:
                continue
        
        return prices
    
    def _validate_signal(self, signal: Signal) -> bool:
        """Validate that signal has minimum required data"""
        if signal.signal_type == SignalType.NEW_TRADE:
            # New trade needs symbol, direction, and at least SL or TP
            if not signal.symbol:
                return False
            if not signal.direction:
                return False
            if not signal.stop_loss and not signal.take_profit_1:
                return False
            
            # Validate price consistency
            if signal.direction == TradeDirection.BUY:
                # For BUY: SL < Entry < TP
                if signal.stop_loss and signal.entry_min:
                    if signal.stop_loss >= signal.entry_min:
                        signal.parse_errors.append("SL >= Entry for BUY")
                        return False
                if signal.take_profit_1 and signal.entry_max:
                    if signal.take_profit_1 <= signal.entry_max:
                        signal.parse_errors.append("TP1 <= Entry for BUY")
                        return False
            else:  # SELL
                # For SELL: SL > Entry > TP
                if signal.stop_loss and signal.entry_max:
                    if signal.stop_loss <= signal.entry_max:
                        signal.parse_errors.append("SL <= Entry for SELL")
                        return False
                if signal.take_profit_1 and signal.entry_min:
                    if signal.take_profit_1 >= signal.entry_min:
                        signal.parse_errors.append("TP1 >= Entry for SELL")
                        return False
            
            return True
        
        # For update signals (TP hit, SL hit, breakeven, close), symbol is optional
        # These messages often don't include the symbol - they refer to the most recent trade
        if signal.signal_type in [SignalType.TP1_HIT, SignalType.TP2_HIT, SignalType.TP3_HIT,
                                   SignalType.SL_HIT, SignalType.BREAKEVEN, SignalType.CLOSE_TRADE]:
            # Valid even without symbol - the trade manager will apply to active trades
            return True
        
        # Other updates need symbol
        return bool(signal.symbol)
    
    def parse_multiple_signals(self, message: str, channel_id: str = "", message_id: int = 0) -> List[Signal]:
        """
        Parse message that might contain multiple signals.
        Split by common separators and parse each.
        """
        signals = []
        
        # Try to split by common separators
        separators = ["\n\n", "---", "===", "***"]
        parts = [message]
        
        for sep in separators:
            if sep in message:
                parts = message.split(sep)
                break
        
        for i, part in enumerate(parts):
            part = part.strip()
            if part and len(part) > 10:  # Minimum length for a signal
                signal = self.parse(part, channel_id, message_id)
                if signal.parsed_successfully:
                    signals.append(signal)
        
        # If no signals found from splitting, try the whole message
        if not signals:
            signal = self.parse(message, channel_id, message_id)
            if signal.parsed_successfully:
                signals.append(signal)
        
        return signals


# Singleton instance
signal_parser = SignalParser()
