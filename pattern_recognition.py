"""
Candlestick Pattern Recognition Engine for CryptoScanner Pro.

Detects 15+ candlestick patterns with confidence scoring.
Patterns classified as: Bullish, Bearish, Reversal/Continuation.

Reference: Common candlestick pattern analysis, TradingView implementations.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from indicators_engine import TechnicalIndicators

logger = logging.getLogger(__name__)


class InsufficientDataError(Exception):
    """Raised when insufficient data points are available for pattern detection."""
    pass


class PatternRecognition:
    """
    Candlestick pattern recognition engine for cryptocurrency trading.

    Detects 15+ patterns including:
    - Bullish: Morning Star, Three White Soldiers, Hammer, Bullish Engulfing, Piercing Line, Three Inside Up
    - Bearish: Evening Star, Three Black Crows, Hanging Man, Bearish Engulfing, Dark Cloud Cover, Three Inside Down
    - Reversal/Continuation: Doji, Spinning Top, Marubozu

    Example:
        >>> ohlcv_data = [[1634567890000, 42000, 43000, 41000, 42500, 1000000], ...]
        >>> patterns = PatternRecognition(ohlcv_data)
        >>> result = patterns.detect_all_patterns()
        >>> print(result["patterns"])
    """

    def __init__(self, ohlcv_data: list[list[float]]) -> None:
        """
        Initialize pattern recognition engine with OHLCV data.

        Args:
            ohlcv_data: List of [timestamp, open, high, low, close, volume]

        Raises:
            ValueError: If ohlcv_data is empty or malformed
        """
        if not ohlcv_data:
            raise ValueError("OHLCV data cannot be empty")

        # Extract OHLCV components as numpy arrays
        ohlcv_array = np.array(ohlcv_data, dtype=np.float64)
        if ohlcv_array.shape[1] < 6:
            raise ValueError("OHLCV data must have 6 columns: timestamp, O, H, L, C, V")

        self.timestamps = ohlcv_array[:, 0]
        self.open = ohlcv_array[:, 1]
        self.high = ohlcv_array[:, 2]
        self.low = ohlcv_array[:, 3]
        self.close = ohlcv_array[:, 4]
        self.volume = ohlcv_array[:, 5]
        self.length = len(self.close)

        self.indicators = TechnicalIndicators(ohlcv_data)

        logger.debug(f"Initialized PatternRecognition with {self.length} candles")

    def _get_body_size(self, idx: int) -> float:
        """Calculate candle body size (absolute value of close - open)."""
        return abs(self.close[idx] - self.open[idx])

    def _get_range(self, idx: int) -> float:
        """Calculate candle range (high - low)."""
        return self.high[idx] - self.low[idx]

    def _is_bullish(self, idx: int) -> bool:
        """Check if candle is bullish (close > open)."""
        return self.close[idx] > self.open[idx]

    def _is_bearish(self, idx: int) -> bool:
        """Check if candle is bearish (close < open)."""
        return self.close[idx] < self.open[idx]

    def _calculate_confidence(
        self, base_score: float, adjustments: list[float] = None
    ) -> int:
        """Calculate final confidence percentage (0-100)."""
        confidence = base_score
        if adjustments:
            for adj in adjustments:
                confidence += adj
        return min(100, max(0, int(confidence)))

    # ==================== BULLISH PATTERNS ====================

    def _detect_morning_star(self) -> Optional[dict]:
        """
        Detect Morning Star pattern (3 candles - strong reversal).

        Pattern:
        - Candle 1: Bearish with large body
        - Candle 2: Small body (doji-like), gap down from candle 1
        - Candle 3: Bullish with large body, closes > midpoint of candle 1

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 3:
            return None

        idx = self.length - 1  # Latest candle (position 0 = now, -1 = yesterday, -2 = 2 days ago)
        c1_idx, c2_idx, c3_idx = idx - 2, idx - 1, idx

        # Candle 1: Bearish with large body
        if not self._is_bearish(c1_idx):
            return None
        body1 = self._get_body_size(c1_idx)
        range1 = self._get_range(c1_idx)
        if body1 < range1 * 0.5:  # Body should be substantial
            return None

        # Candle 2: Small body (doji-like)
        body2 = self._get_body_size(c2_idx)
        range2 = self._get_range(c2_idx)
        if range2 == 0:
            return None
        if body2 / range2 > 0.3:  # Body should be very small
            return None

        # Candle 2 should gap down below candle 1's close
        if self.high[c2_idx] >= self.close[c1_idx]:
            return None

        # Candle 3: Bullish with large body
        if not self._is_bullish(c3_idx):
            return None
        body3 = self._get_body_size(c3_idx)
        if body3 < range1 * 0.4:
            return None

        # Candle 3 closes above midpoint of candle 1
        midpoint1 = (self.open[c1_idx] + self.close[c1_idx]) / 2.0
        if self.close[c3_idx] < midpoint1:
            return None

        # Calculate confidence
        base_confidence = 75.0
        gap_adj = min(10.0, abs(self.low[c2_idx] - self.close[c1_idx]) / range1 * 10)
        close_strength = min(10.0, (self.close[c3_idx] - midpoint1) / body1 * 10)
        confidence = self._calculate_confidence(
            base_confidence, [gap_adj * 0.5, close_strength * 0.5]
        )

        return {
            "name": "Morning Star",
            "type": "bullish",
            "confidence": confidence,
            "position": -2,
        }

    def _detect_evening_star(self) -> Optional[dict]:
        """
        Detect Evening Star pattern (3 candles - bearish reversal).

        Pattern:
        - Candle 1: Bullish with large body
        - Candle 2: Small body (doji-like), gap up from candle 1
        - Candle 3: Bearish with large body, closes < midpoint of candle 1

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 3:
            return None

        idx = self.length - 1
        c1_idx, c2_idx, c3_idx = idx - 2, idx - 1, idx

        # Candle 1: Bullish with large body
        if not self._is_bullish(c1_idx):
            return None
        body1 = self._get_body_size(c1_idx)
        range1 = self._get_range(c1_idx)
        if body1 < range1 * 0.5:
            return None

        # Candle 2: Small body (doji-like)
        body2 = self._get_body_size(c2_idx)
        range2 = self._get_range(c2_idx)
        if range2 == 0:
            return None
        if body2 / range2 > 0.3:
            return None

        # Candle 2 should gap up above candle 1's close
        if self.low[c2_idx] <= self.close[c1_idx]:
            return None

        # Candle 3: Bearish with large body
        if not self._is_bearish(c3_idx):
            return None
        body3 = self._get_body_size(c3_idx)
        if body3 < range1 * 0.4:
            return None

        # Candle 3 closes below midpoint of candle 1
        midpoint1 = (self.open[c1_idx] + self.close[c1_idx]) / 2.0
        if self.close[c3_idx] > midpoint1:
            return None

        # Calculate confidence
        base_confidence = 75.0
        gap_adj = min(10.0, abs(self.high[c2_idx] - self.close[c1_idx]) / range1 * 10)
        close_strength = min(10.0, (midpoint1 - self.close[c3_idx]) / body1 * 10)
        confidence = self._calculate_confidence(
            base_confidence, [gap_adj * 0.5, close_strength * 0.5]
        )

        return {
            "name": "Evening Star",
            "type": "bearish",
            "confidence": confidence,
            "position": -2,
        }

    def _detect_three_white_soldiers(self) -> Optional[dict]:
        """
        Detect Three White Soldiers pattern (3 bullish candles in a row).

        Pattern:
        - All 3 candles are bullish
        - Each candle opens within previous candle's body
        - Each candle closes higher than previous

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 3:
            return None

        idx = self.length - 1
        c1_idx, c2_idx, c3_idx = idx - 2, idx - 1, idx

        # All must be bullish
        if not (self._is_bullish(c1_idx) and self._is_bullish(c2_idx) and self._is_bullish(c3_idx)):
            return None

        # Each opens within previous body and closes higher
        # C2 opens within C1 body: open >= C1 open and open <= C1 close
        if not (self.open[c2_idx] >= self.open[c1_idx] and self.open[c2_idx] <= self.close[c1_idx]):
            return None
        if self.close[c2_idx] <= self.close[c1_idx]:
            return None

        # C3 opens within C2 body: open >= C2 open and open <= C2 close
        if not (self.open[c3_idx] >= self.open[c2_idx] and self.open[c3_idx] <= self.close[c2_idx]):
            return None
        if self.close[c3_idx] <= self.close[c2_idx]:
            return None

        # Calculate confidence
        base_confidence = 80.0
        body1 = self._get_body_size(c1_idx)
        body2 = self._get_body_size(c2_idx)
        body3 = self._get_body_size(c3_idx)

        # Bonus for consistent body sizes
        if body1 > 0 and body2 > 0 and body3 > 0:
            consistency = min(10.0, abs(body1 - body2) / body1 * 5)
            base_confidence += consistency

        confidence = self._calculate_confidence(base_confidence)

        return {
            "name": "Three White Soldiers",
            "type": "bullish",
            "confidence": confidence,
            "position": -2,
        }

    def _detect_three_black_crows(self) -> Optional[dict]:
        """
        Detect Three Black Crows pattern (3 bearish candles in a row).

        Pattern:
        - All 3 candles are bearish
        - Each candle opens within previous candle's body
        - Each candle closes lower than previous

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 3:
            return None

        idx = self.length - 1
        c1_idx, c2_idx, c3_idx = idx - 2, idx - 1, idx

        # All must be bearish
        if not (self._is_bearish(c1_idx) and self._is_bearish(c2_idx) and self._is_bearish(c3_idx)):
            return None

        # Each opens within previous body and closes lower
        # C2 opens within C1 body: open >= C1 close and open <= C1 open (bearish candle)
        if not (self.open[c2_idx] >= self.close[c1_idx] and self.open[c2_idx] <= self.open[c1_idx]):
            return None
        if self.close[c2_idx] >= self.close[c1_idx]:
            return None

        # C3 opens within C2 body: open >= C2 close and open <= C2 open (bearish candle)
        if not (self.open[c3_idx] >= self.close[c2_idx] and self.open[c3_idx] <= self.open[c2_idx]):
            return None
        if self.close[c3_idx] >= self.close[c2_idx]:
            return None

        # Calculate confidence
        base_confidence = 80.0
        body1 = self._get_body_size(c1_idx)
        body2 = self._get_body_size(c2_idx)
        body3 = self._get_body_size(c3_idx)

        # Bonus for consistent body sizes
        if body1 > 0 and body2 > 0 and body3 > 0:
            consistency = min(10.0, abs(body1 - body2) / body1 * 5)
            base_confidence += consistency

        confidence = self._calculate_confidence(base_confidence)

        return {
            "name": "Three Black Crows",
            "type": "bearish",
            "confidence": confidence,
            "position": -2,
        }

    def _detect_hammer(self) -> Optional[dict]:
        """
        Detect Hammer pattern (single bullish candle with long lower wick).

        Pattern:
        - Small body (usually bullish)
        - Long lower wick (2x+ of body)
        - Little or no upper wick

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 1:
            return None

        idx = self.length - 1
        body = self._get_body_size(idx)
        range_val = self._get_range(idx)

        if range_val == 0:
            return None

        lower_wick = self.open[idx] - self.low[idx] if self.close[idx] > self.open[idx] else self.close[idx] - self.low[idx]
        upper_wick = self.high[idx] - self.close[idx] if self.close[idx] > self.open[idx] else self.high[idx] - self.open[idx]

        # Body must be in upper half, lower wick much longer
        if body / range_val > 0.3:
            return None
        if lower_wick < body * 2:
            return None
        if upper_wick > lower_wick * 0.3:
            return None

        # Calculate confidence
        base_confidence = 70.0
        wick_ratio = min(15.0, (lower_wick / body - 2.0) * 2)
        confidence = self._calculate_confidence(base_confidence, [wick_ratio])

        return {
            "name": "Hammer",
            "type": "bullish",
            "confidence": confidence,
            "position": 0,
        }

    def _detect_hanging_man(self) -> Optional[dict]:
        """
        Detect Hanging Man pattern (single bearish candle with long lower wick).

        Pattern:
        - Small body (usually bearish)
        - Long lower wick (2x+ of body)
        - Little or no upper wick

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 1:
            return None

        idx = self.length - 1
        body = self._get_body_size(idx)
        range_val = self._get_range(idx)

        if range_val == 0:
            return None

        lower_wick = self.open[idx] - self.low[idx] if self.close[idx] < self.open[idx] else self.close[idx] - self.low[idx]
        upper_wick = self.high[idx] - self.close[idx] if self.close[idx] < self.open[idx] else self.high[idx] - self.open[idx]

        # Body must be in upper half, lower wick much longer
        if body / range_val > 0.3:
            return None
        if lower_wick < body * 2:
            return None
        if upper_wick > lower_wick * 0.3:
            return None

        # Calculate confidence
        base_confidence = 70.0
        wick_ratio = min(15.0, (lower_wick / body - 2.0) * 2)
        confidence = self._calculate_confidence(base_confidence, [wick_ratio])

        return {
            "name": "Hanging Man",
            "type": "bearish",
            "confidence": confidence,
            "position": 0,
        }

    def _detect_bullish_engulfing(self) -> Optional[dict]:
        """
        Detect Bullish Engulfing pattern (2 candles).

        Pattern:
        - Candle 1: Bearish
        - Candle 2: Bullish, opens below candle 1's close, closes above candle 1's open

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 2:
            return None

        idx = self.length - 1
        c1_idx, c2_idx = idx - 1, idx

        # Candle 1 bearish, Candle 2 bullish
        if not self._is_bearish(c1_idx) or not self._is_bullish(c2_idx):
            return None

        # Candle 2 opens below candle 1 close
        if self.open[c2_idx] >= self.close[c1_idx]:
            return None

        # Candle 2 closes above candle 1 open
        if self.close[c2_idx] <= self.open[c1_idx]:
            return None

        # Calculate confidence
        body1 = self._get_body_size(c1_idx)
        body2 = self._get_body_size(c2_idx)

        base_confidence = 75.0
        engulfing_ratio = min(15.0, (body2 / body1 - 1.0) * 10) if body1 > 0 else 5.0
        confidence = self._calculate_confidence(base_confidence, [engulfing_ratio])

        return {
            "name": "Bullish Engulfing",
            "type": "bullish",
            "confidence": confidence,
            "position": -1,
        }

    def _detect_bearish_engulfing(self) -> Optional[dict]:
        """
        Detect Bearish Engulfing pattern (2 candles).

        Pattern:
        - Candle 1: Bullish
        - Candle 2: Bearish, opens above candle 1's close, closes below candle 1's open

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 2:
            return None

        idx = self.length - 1
        c1_idx, c2_idx = idx - 1, idx

        # Candle 1 bullish, Candle 2 bearish
        if not self._is_bullish(c1_idx) or not self._is_bearish(c2_idx):
            return None

        # Candle 2 opens above candle 1 close
        if self.open[c2_idx] <= self.close[c1_idx]:
            return None

        # Candle 2 closes below candle 1 open
        if self.close[c2_idx] >= self.open[c1_idx]:
            return None

        # Calculate confidence
        body1 = self._get_body_size(c1_idx)
        body2 = self._get_body_size(c2_idx)

        base_confidence = 75.0
        engulfing_ratio = min(15.0, (body2 / body1 - 1.0) * 10) if body1 > 0 else 5.0
        confidence = self._calculate_confidence(base_confidence, [engulfing_ratio])

        return {
            "name": "Bearish Engulfing",
            "type": "bearish",
            "confidence": confidence,
            "position": -1,
        }

    def _detect_piercing_line(self) -> Optional[dict]:
        """
        Detect Piercing Line pattern (2 candles - bullish).

        Pattern:
        - Candle 1: Bearish with large body
        - Candle 2: Bullish, opens below candle 1's low, closes > 50% into candle 1's body

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 2:
            return None

        idx = self.length - 1
        c1_idx, c2_idx = idx - 1, idx

        # Candle 1 bearish, Candle 2 bullish
        if not self._is_bearish(c1_idx) or not self._is_bullish(c2_idx):
            return None

        body1 = self._get_body_size(c1_idx)
        if body1 < self._get_range(c1_idx) * 0.4:
            return None

        # Candle 2 opens below candle 1's low
        if self.open[c2_idx] >= self.low[c1_idx]:
            return None

        # Candle 2 closes > 50% into candle 1's body
        midpoint1 = (self.open[c1_idx] + self.close[c1_idx]) / 2.0
        if self.close[c2_idx] <= midpoint1:
            return None

        # Calculate confidence
        base_confidence = 70.0
        penetration = min(10.0, (self.close[c2_idx] - midpoint1) / body1 * 10)
        confidence = self._calculate_confidence(base_confidence, [penetration])

        return {
            "name": "Piercing Line",
            "type": "bullish",
            "confidence": confidence,
            "position": -1,
        }

    def _detect_dark_cloud_cover(self) -> Optional[dict]:
        """
        Detect Dark Cloud Cover pattern (2 candles - bearish).

        Pattern:
        - Candle 1: Bullish with large body
        - Candle 2: Bearish, opens above candle 1's high, closes < 50% into candle 1's body

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 2:
            return None

        idx = self.length - 1
        c1_idx, c2_idx = idx - 1, idx

        # Candle 1 bullish, Candle 2 bearish
        if not self._is_bullish(c1_idx) or not self._is_bearish(c2_idx):
            return None

        body1 = self._get_body_size(c1_idx)
        if body1 < self._get_range(c1_idx) * 0.4:
            return None

        # Candle 2 opens above candle 1's high
        if self.open[c2_idx] <= self.high[c1_idx]:
            return None

        # Candle 2 closes < 50% into candle 1's body
        midpoint1 = (self.open[c1_idx] + self.close[c1_idx]) / 2.0
        if self.close[c2_idx] >= midpoint1:
            return None

        # Calculate confidence
        base_confidence = 70.0
        penetration = min(10.0, (midpoint1 - self.close[c2_idx]) / body1 * 10)
        confidence = self._calculate_confidence(base_confidence, [penetration])

        return {
            "name": "Dark Cloud Cover",
            "type": "bearish",
            "confidence": confidence,
            "position": -1,
        }

    def _detect_doji(self) -> Optional[dict]:
        """
        Detect Doji pattern (single candle with very small body).

        Pattern:
        - Open and close are nearly equal (body < 5% of range)
        - Can have long wicks

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 1:
            return None

        idx = self.length - 1
        body = self._get_body_size(idx)
        range_val = self._get_range(idx)

        if range_val == 0:
            return None

        # Body must be very small
        if body / range_val > 0.05:
            return None

        # Calculate confidence
        base_confidence = 80.0
        body_ratio = (0.05 - body / range_val) / 0.05 * 10
        confidence = self._calculate_confidence(base_confidence, [body_ratio])

        return {
            "name": "Doji",
            "type": "neutral",
            "confidence": confidence,
            "position": 0,
        }

    def _detect_spinning_top(self) -> Optional[dict]:
        """
        Detect Spinning Top pattern (single candle with small body and wicks).

        Pattern:
        - Small body (5-30% of range)
        - Upper and lower wicks of similar length
        - Indecision pattern

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 1:
            return None

        idx = self.length - 1
        body = self._get_body_size(idx)
        range_val = self._get_range(idx)

        if range_val == 0:
            return None

        body_ratio = body / range_val

        # Body between 5-30% of range
        if body_ratio < 0.05 or body_ratio > 0.3:
            return None

        # Similar upper and lower wicks
        midpoint = (self.open[idx] + self.close[idx]) / 2.0
        upper_wick = self.high[idx] - midpoint
        lower_wick = midpoint - self.low[idx]

        if upper_wick == 0 or lower_wick == 0:
            return None

        wick_ratio = min(upper_wick, lower_wick) / max(upper_wick, lower_wick)
        if wick_ratio < 0.5:
            return None

        # Calculate confidence
        base_confidence = 75.0
        balance = min(10.0, (1.0 - abs(upper_wick - lower_wick) / max(upper_wick, lower_wick)) * 10)
        confidence = self._calculate_confidence(base_confidence, [balance])

        return {
            "name": "Spinning Top",
            "type": "neutral",
            "confidence": confidence,
            "position": 0,
        }

    def _detect_marubozu(self) -> Optional[dict]:
        """
        Detect Marubozu pattern (single candle with little or no wicks).

        Pattern:
        - Large body (80%+ of range)
        - Very small or no upper and lower wicks
        - Strong conviction

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 1:
            return None

        idx = self.length - 1
        body = self._get_body_size(idx)
        range_val = self._get_range(idx)

        if range_val == 0:
            return None

        body_ratio = body / range_val

        # Body must be 80%+ of range
        if body_ratio < 0.8:
            return None

        # Determine direction
        is_bullish = self._is_bullish(idx)

        # Upper wick should be small
        if is_bullish:
            upper_wick = self.high[idx] - self.close[idx]
            lower_wick = self.open[idx] - self.low[idx]
        else:
            upper_wick = self.high[idx] - self.open[idx]
            lower_wick = self.close[idx] - self.low[idx]

        max_wick = max(upper_wick, lower_wick)
        if max_wick > body * 0.1:
            return None

        # Calculate confidence
        base_confidence = 85.0
        body_strength = min(10.0, (body_ratio - 0.8) / 0.2 * 10)
        confidence = self._calculate_confidence(base_confidence, [body_strength])

        pattern_type = "bullish" if is_bullish else "bearish"

        return {
            "name": "Marubozu",
            "type": pattern_type,
            "confidence": confidence,
            "position": 0,
        }

    def _detect_three_inside_up(self) -> Optional[dict]:
        """
        Detect Three Inside Up pattern (3 bullish candles).

        Pattern:
        - Candle 1: Bearish with large body
        - Candle 2: Bullish, inside candle 1
        - Candle 3: Bullish, closes above candle 1's close

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 3:
            return None

        idx = self.length - 1
        c1_idx, c2_idx, c3_idx = idx - 2, idx - 1, idx

        # Candle 1: Bearish
        if not self._is_bearish(c1_idx):
            return None

        # Candle 2: Bullish and inside candle 1
        if not self._is_bullish(c2_idx):
            return None
        if self.open[c2_idx] < self.low[c1_idx] or self.close[c2_idx] > self.high[c1_idx]:
            return None

        # Candle 3: Bullish and closes above candle 1's close
        if not self._is_bullish(c3_idx):
            return None
        if self.close[c3_idx] <= self.close[c1_idx]:
            return None

        # Calculate confidence
        base_confidence = 75.0
        confidence = self._calculate_confidence(base_confidence)

        return {
            "name": "Three Inside Up",
            "type": "bullish",
            "confidence": confidence,
            "position": -2,
        }

    def _detect_three_inside_down(self) -> Optional[dict]:
        """
        Detect Three Inside Down pattern (3 bearish candles).

        Pattern:
        - Candle 1: Bullish with large body
        - Candle 2: Bearish, inside candle 1
        - Candle 3: Bearish, closes below candle 1's close

        Returns:
            Dict with name, confidence, position if found, else None
        """
        if self.length < 3:
            return None

        idx = self.length - 1
        c1_idx, c2_idx, c3_idx = idx - 2, idx - 1, idx

        # Candle 1: Bullish
        if not self._is_bullish(c1_idx):
            return None

        # Candle 2: Bearish and inside candle 1
        if not self._is_bearish(c2_idx):
            return None
        if self.open[c2_idx] < self.low[c1_idx] or self.close[c2_idx] > self.high[c1_idx]:
            return None

        # Candle 3: Bearish and closes below candle 1's close
        if not self._is_bearish(c3_idx):
            return None
        if self.close[c3_idx] >= self.close[c1_idx]:
            return None

        # Calculate confidence
        base_confidence = 75.0
        confidence = self._calculate_confidence(base_confidence)

        return {
            "name": "Three Inside Down",
            "type": "bearish",
            "confidence": confidence,
            "position": -2,
        }

    def detect_all_patterns(self) -> dict:
        """
        Detect all patterns in the OHLCV data.

        Returns:
            Dict with:
            - "patterns": List of detected patterns with name, type, confidence, position
            - "last_candle": Dict with latest OHLCV values
            - "detection_count": Total patterns detected

        Example:
            >>> result = patterns.detect_all_patterns()
            >>> print(f"Found {result['detection_count']} patterns")
            >>> for p in result['patterns']:
            ...     print(f"{p['name']}: {p['confidence']}% confidence")
        """
        if self.length == 0:
            raise InsufficientDataError("No OHLCV data available")

        patterns = []

        # Detect all patterns
        pattern_detectors = [
            # Bullish patterns
            self._detect_morning_star,
            self._detect_three_white_soldiers,
            self._detect_hammer,
            self._detect_bullish_engulfing,
            self._detect_piercing_line,
            self._detect_three_inside_up,
            # Bearish patterns
            self._detect_evening_star,
            self._detect_three_black_crows,
            self._detect_hanging_man,
            self._detect_bearish_engulfing,
            self._detect_dark_cloud_cover,
            self._detect_three_inside_down,
            # Neutral/Reversal patterns
            self._detect_doji,
            self._detect_spinning_top,
            self._detect_marubozu,
        ]

        for detector in pattern_detectors:
            try:
                result = detector()
                if result:
                    patterns.append(result)
            except Exception as e:
                logger.warning(f"Error detecting {detector.__name__}: {e}")

        # Sort by confidence descending
        patterns = sorted(patterns, key=lambda x: x["confidence"], reverse=True)

        # Get last candle data
        idx = self.length - 1
        last_candle = {
            "timestamp": int(self.timestamps[idx]),
            "open": float(self.open[idx]),
            "high": float(self.high[idx]),
            "low": float(self.low[idx]),
            "close": float(self.close[idx]),
            "volume": float(self.volume[idx]),
        }

        return {
            "patterns": patterns,
            "last_candle": last_candle,
            "detection_count": len(patterns),
            "timestamp": int(self.timestamps[idx]),
        }
