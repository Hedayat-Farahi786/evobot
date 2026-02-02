"""
AI Fallback Parser - Uses local Ollama for failed regex parses
Only activates when regex parser fails, maintaining speed priority
"""
import json
import logging
from typing import Optional
import httpx
from models.trade import Signal, SignalType, TradeDirection

logger = logging.getLogger("evobot.ai_parser")


class AIFallbackParser:
    """Fast local AI parser using Ollama (completely free, runs locally)"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.model = "phi3:mini"  # 2.3GB, very fast, good for structured extraction
        self.enabled = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if Ollama is running"""
        try:
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            self.enabled = response.status_code == 200
            if self.enabled:
                logger.info("✅ AI fallback parser enabled (Ollama detected)")
        except:
            logger.debug("Ollama not available - AI fallback disabled")
    
    async def is_trading_signal(self, message: str) -> bool:
        """Quick check if message is a trading signal (200-400ms)"""
        if not self.enabled:
            return False
        
        try:
            prompt = f"""Is this a trading signal? Answer ONLY 'yes' or 'no'.

Trading signals contain: symbol (XAUUSD/EURUSD/etc), direction (BUY/SELL), entry price, stop loss, take profit.

Message: {message[:300]}

Answer:"""
            
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                
                if response.status_code != 200:
                    return False
                
                result = response.json()
                answer = result.get("response", "").strip().lower()
                return "yes" in answer[:10]
                
        except Exception as e:
            logger.debug(f"AI signal check failed: {e}")
            return False
    
    async def parse_signal(self, message: str, channel_id: str = "") -> Optional[Signal]:
        """Parse signal using AI - ONLY called when regex fails (500-800ms)"""
        if not self.enabled:
            return None
        
        try:
            prompt = f"""Extract trading signal. Return ONLY valid JSON, no explanation.

Example message: "EURUSD BUY Entry: 1.1800-1.1805 SL: 1.1795 TP1: 1.1820"
Example output: {{"symbol":"EURUSD","direction":"BUY","entry_min":1.1800,"entry_max":1.1805,"stop_loss":1.1795,"tp1":1.1820,"tp2":null,"tp3":null}}

RULES:
- Direction: LONG/BUY/BULL=BUY, SHORT/SELL/BEAR=SELL
- Entry: lowest and highest entry prices
- SL: MUST be BELOW entry for BUY, ABOVE entry for SELL
- TP: MUST be ABOVE entry for BUY, BELOW entry for SELL

Message: {message[:500]}

JSON:"""
            
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                
                if response.status_code != 200:
                    return None
                
                result = response.json()
                text = result.get("response", "")
                
                # Extract JSON from response
                start = text.find("{")
                end = text.rfind("}") + 1
                if start == -1 or end == 0:
                    return None
                
                data = json.loads(text[start:end])
                
                # Build Signal object
                signal = Signal(raw_message=message, channel_id=channel_id)
                signal.symbol = data.get("symbol")
                signal.direction = TradeDirection.BUY if data.get("direction") == "BUY" else TradeDirection.SELL
                signal.entry_min = data.get("entry_min")
                signal.entry_max = data.get("entry_max")
                signal.stop_loss = data.get("stop_loss")
                signal.take_profit_1 = data.get("tp1")
                signal.take_profit_2 = data.get("tp2")
                signal.take_profit_3 = data.get("tp3")
                signal.signal_type = SignalType.NEW_TRADE
                
                # Basic validation only
                if signal.symbol and signal.direction and signal.stop_loss and signal.take_profit_1:
                    signal.parsed_successfully = True
                    return signal
                
                return None
                
        except Exception as e:
            logger.debug(f"AI parse failed: {e}")
            return None


# Singleton
ai_parser = AIFallbackParser()
