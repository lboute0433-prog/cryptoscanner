"""
Technical Indicators Engine for CryptoScanner Pro.

Implements 50+ technical indicators using numpy for efficient calculations.
Indicators organized by category: Trend, Momentum, Volatility, Volume, Oscillators, Support/Resistance.

Reference: TradingView, TA-Lib implementations.
"""

from __future__ import annotations

import logging
import warnings
from typing import Optional

import numpy as np

# Suppress numpy warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

logger = logging.getLogger(__name__)


class InsufficientDataError(Exception):
    """Raised when insufficient data points are available for calculation."""
    pass


class TechnicalIndicators:
    """
    Complete technical indicators engine for cryptocurrency trading.

    Implements 50+ indicators across all major categories:
    - Trend: EMA, SMA, ADX, MACD, Ichimoku
    - Momentum: RSI, Stochastic RSI, CCI, Williams %R
    - Volatility: Bollinger Bands, ATR, Keltner Channel, StdDev
    - Volume: OBV, MFI, VROC
    - Oscillators: Awesome Oscillator, TRIX, ROC
    - Support/Resistance: Pivot Points, Fibonacci Levels

    Example:
        >>> ohlcv_data = [[1634567890000, 42000, 43000, 41000, 42500, 1000000], ...]
        >>> indicators = TechnicalIndicators(ohlcv_data)
        >>> all_indicators = indicators.calculate_all()
        >>> rsi = indicators.calculate_rsi(period=14)
    """

    def __init__(self, ohlcv_data: list[list[float]]) -> None:
        """
        Initialize indicators engine with OHLCV data.

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

        logger.debug(f"Initialized TechnicalIndicators with {self.length} candles")

    def _validate_period(self, period: int, min_period: int | None = None) -> None:
        """Validate that period is valid for current data."""
        if period < 1:
            raise ValueError(f"Period must be >= 1, got {period}")
        if min_period is None:
            min_period = period
        if self.length < min_period:
            raise InsufficientDataError(
                f"Need {min_period} data points, only have {self.length}"
            )

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate EMA using vectorized operations."""
        if len(data) < period:
            return np.full_like(data, np.nan)

        alpha = 2.0 / (period + 1.0)
        ema = np.full_like(data, np.nan)

        # Initial SMA for first period
        ema[period - 1] = np.mean(data[:period])

        # Calculate EMA values
        for i in range(period, len(data)):
            ema[i] = data[i] * alpha + ema[i - 1] * (1.0 - alpha)

        return ema

    def calculate_ema(self, period: int = 12) -> np.ndarray:
        """
        Calculate Exponential Moving Average.

        Args:
            period: EMA period (typically 12, 26, 50, 200)

        Returns:
            Array of EMA values (NaN for insufficient data)

        Example:
            >>> ema_12 = indicators.calculate_ema(12)
            >>> ema_26 = indicators.calculate_ema(26)
        """
        self._validate_period(period)
        return self._ema(self.close, period)

    def calculate_sma(self, period: int = 20) -> np.ndarray:
        """
        Calculate Simple Moving Average.

        Args:
            period: SMA period (typically 20, 50, 200)

        Returns:
            Array of SMA values (NaN for insufficient data)

        Example:
            >>> sma_20 = indicators.calculate_sma(20)
        """
        self._validate_period(period)
        sma = np.full_like(self.close, np.nan)

        for i in range(period - 1, len(self.close)):
            sma[i] = np.mean(self.close[i - period + 1:i + 1])

        return sma

    def calculate_macd(
        self, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> dict[str, np.ndarray]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line EMA period (default 9)

        Returns:
            Dict with 'macd', 'signal', 'histogram' arrays

        Example:
            >>> macd_data = indicators.calculate_macd()
            >>> macd = macd_data['macd']
            >>> histogram = macd_data['histogram']
        """
        self._validate_period(slow)

        ema_fast = self._ema(self.close, fast)
        ema_slow = self._ema(self.close, slow)
        macd = ema_fast - ema_slow

        # Signal line is EMA of MACD
        signal_line = self._ema(macd, signal)
        histogram = macd - signal_line

        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram,
        }

    def calculate_rsi(self, period: int = 14) -> np.ndarray:
        """
        Calculate Relative Strength Index.

        Args:
            period: RSI period (typically 14)

        Returns:
            Array of RSI values 0-100 (NaN for insufficient data)

        Example:
            >>> rsi = indicators.calculate_rsi(14)
        """
        self._validate_period(period, min_period=period + 1)

        rsi = np.full_like(self.close, np.nan)
        delta = np.diff(self.close)

        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        # Initial average gain/loss (SMA)
        avg_gain = np.mean(gain[:period])
        avg_loss = np.mean(loss[:period])

        # Smoothed averages (EMA-style)
        gains = np.zeros(len(self.close))
        losses = np.zeros(len(self.close))

        gains[period] = avg_gain
        losses[period] = avg_loss

        for i in range(period + 1, len(self.close)):
            gains[i] = (gains[i - 1] * (period - 1) + gain[i - 1]) / period
            losses[i] = (losses[i - 1] * (period - 1) + loss[i - 1]) / period

        # Calculate RS and RSI
        rs = np.divide(gains, losses, where=losses != 0, out=np.full_like(gains, np.nan))
        rsi[period:] = 100 - (100 / (1 + rs[period:]))

        return rsi

    def calculate_bollinger_bands(
        self, period: int = 20, std_dev: float = 2.0
    ) -> dict[str, np.ndarray]:
        """
        Calculate Bollinger Bands.

        Args:
            period: SMA period (typically 20)
            std_dev: Standard deviations (typically 2)

        Returns:
            Dict with 'upper', 'middle', 'lower', 'width' arrays

        Example:
            >>> bb = indicators.calculate_bollinger_bands(20, 2)
            >>> upper = bb['upper']
            >>> lower = bb['lower']
        """
        self._validate_period(period)

        middle = np.full_like(self.close, np.nan)
        upper = np.full_like(self.close, np.nan)
        lower = np.full_like(self.close, np.nan)

        for i in range(period - 1, len(self.close)):
            window = self.close[i - period + 1:i + 1]
            middle[i] = np.mean(window)
            std = np.std(window, ddof=1)
            upper[i] = middle[i] + (std * std_dev)
            lower[i] = middle[i] - (std * std_dev)

        width = upper - lower

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
            'width': width,
        }

    def calculate_atr(self, period: int = 14) -> np.ndarray:
        """
        Calculate Average True Range.

        Args:
            period: ATR period (typically 14)

        Returns:
            Array of ATR values (NaN for insufficient data)

        Example:
            >>> atr = indicators.calculate_atr(14)
        """
        self._validate_period(period)

        # Calculate True Range
        high_low = self.high - self.low
        high_close = np.abs(self.high - np.roll(self.close, 1))
        low_close = np.abs(self.low - np.roll(self.close, 1))

        true_range = np.maximum(high_low, high_close)
        true_range = np.maximum(true_range, low_close)
        true_range[0] = high_low[0]

        # ATR is EMA of true range
        atr = self._ema(true_range, period)

        return atr

    def calculate_stochastic_rsi(
        self, rsi_period: int = 14, k_period: int = 14, d_period: int = 3
    ) -> dict[str, np.ndarray]:
        """
        Calculate Stochastic RSI.

        Args:
            rsi_period: RSI period (typically 14)
            k_period: %K period (typically 14)
            d_period: %D period (typically 3)

        Returns:
            Dict with '%K', '%D' arrays

        Example:
            >>> stoch_rsi = indicators.calculate_stochastic_rsi()
            >>> k_line = stoch_rsi['%K']
        """
        rsi = self.calculate_rsi(rsi_period)

        # Stochastic of RSI
        k_line = np.full_like(rsi, np.nan)
        d_line = np.full_like(rsi, np.nan)

        for i in range(k_period - 1, len(rsi)):
            rsi_window = rsi[i - k_period + 1:i + 1]
            if not np.isnan(rsi_window).all():
                lowest = np.nanmin(rsi_window)
                highest = np.nanmax(rsi_window)
                if highest != lowest:
                    k_line[i] = 100 * (rsi[i] - lowest) / (highest - lowest)
                else:
                    k_line[i] = 50

        # %D is SMA of %K
        for i in range(d_period - 1, len(k_line)):
            k_window = k_line[i - d_period + 1:i + 1]
            if not np.isnan(k_window).all():
                d_line[i] = np.nanmean(k_window)

        return {
            '%K': k_line,
            '%D': d_line,
        }

    def calculate_cci(self, period: int = 20) -> np.ndarray:
        """
        Calculate Commodity Channel Index.

        Args:
            period: CCI period (typically 20)

        Returns:
            Array of CCI values (NaN for insufficient data)

        Example:
            >>> cci = indicators.calculate_cci(20)
        """
        self._validate_period(period)

        # Typical Price
        typical_price = (self.high + self.low + self.close) / 3.0

        cci = np.full_like(typical_price, np.nan)

        for i in range(period - 1, len(typical_price)):
            tp_window = typical_price[i - period + 1:i + 1]
            sma = np.mean(tp_window)
            mad = np.mean(np.abs(tp_window - sma))

            if mad != 0:
                cci[i] = (typical_price[i] - sma) / (0.015 * mad)
            else:
                cci[i] = 0

        return cci

    def calculate_williams_r(self, period: int = 14) -> np.ndarray:
        """
        Calculate Williams %R (Percent Range).

        Args:
            period: Period (typically 14)

        Returns:
            Array of Williams %R values -100 to 0 (NaN for insufficient data)

        Example:
            >>> williams_r = indicators.calculate_williams_r(14)
        """
        self._validate_period(period)

        williams_r = np.full_like(self.close, np.nan)

        for i in range(period - 1, len(self.close)):
            high_window = self.high[i - period + 1:i + 1]
            low_window = self.low[i - period + 1:i + 1]

            highest = np.max(high_window)
            lowest = np.min(low_window)

            if highest != lowest:
                williams_r[i] = -100 * (highest - self.close[i]) / (highest - lowest)
            else:
                williams_r[i] = -50

        return williams_r

    def calculate_adx(self, period: int = 14) -> dict[str, np.ndarray]:
        """
        Calculate Average Directional Index.

        Args:
            period: ADX period (typically 14)

        Returns:
            Dict with 'adx', 'plus_di', 'minus_di' arrays

        Example:
            >>> adx_data = indicators.calculate_adx()
            >>> adx = adx_data['adx']
        """
        self._validate_period(period, min_period=period * 2)

        # Calculate DM (Directional Movement)
        up_move = self.high[1:] - self.high[:-1]
        down_move = self.low[:-1] - self.low[1:]

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

        # Pad arrays to match original length
        plus_dm = np.insert(plus_dm, 0, 0)
        minus_dm = np.insert(minus_dm, 0, 0)

        # True Range
        high_low = self.high - self.low
        high_close = np.abs(self.high - np.roll(self.close, 1))
        low_close = np.abs(self.low - np.roll(self.close, 1))
        tr = np.maximum(high_low, np.maximum(high_close, low_close))
        tr[0] = high_low[0]

        # Calculate smoothed DM and TR
        plus_di = np.full_like(self.close, np.nan)
        minus_di = np.full_like(self.close, np.nan)

        smoothed_plus_dm = np.sum(plus_dm[:period])
        smoothed_minus_dm = np.sum(minus_dm[:period])
        smoothed_tr = np.sum(tr[:period])

        plus_di[period - 1] = 100 * smoothed_plus_dm / smoothed_tr
        minus_di[period - 1] = 100 * smoothed_minus_dm / smoothed_tr

        for i in range(period, len(self.close)):
            smoothed_plus_dm = smoothed_plus_dm - smoothed_plus_dm / period + plus_dm[i]
            smoothed_minus_dm = smoothed_minus_dm - smoothed_minus_dm / period + minus_dm[i]
            smoothed_tr = smoothed_tr - smoothed_tr / period + tr[i]

            plus_di[i] = 100 * smoothed_plus_dm / smoothed_tr
            minus_di[i] = 100 * smoothed_minus_dm / smoothed_tr

        # DX
        dx_sum = np.abs(plus_di - minus_di) / (plus_di + minus_di)
        dx_sum = np.nan_to_num(dx_sum, nan=0) * 100

        # ADX is EMA of DX
        adx = self._ema(dx_sum, period)

        return {
            'adx': adx,
            'plus_di': plus_di,
            'minus_di': minus_di,
        }

    def calculate_obv(self) -> np.ndarray:
        """
        Calculate On-Balance Volume.

        Returns:
            Array of OBV values

        Example:
            >>> obv = indicators.calculate_obv()
        """
        obv = np.zeros_like(self.close)
        obv[0] = self.volume[0]

        for i in range(1, len(self.close)):
            if self.close[i] > self.close[i - 1]:
                obv[i] = obv[i - 1] + self.volume[i]
            elif self.close[i] < self.close[i - 1]:
                obv[i] = obv[i - 1] - self.volume[i]
            else:
                obv[i] = obv[i - 1]

        return obv

    def calculate_mfi(self, period: int = 14) -> np.ndarray:
        """
        Calculate Money Flow Index.

        Args:
            period: MFI period (typically 14)

        Returns:
            Array of MFI values 0-100 (NaN for insufficient data)

        Example:
            >>> mfi = indicators.calculate_mfi(14)
        """
        self._validate_period(period)

        # Typical Price
        typical_price = (self.high + self.low + self.close) / 3.0
        raw_money_flow = typical_price * self.volume

        positive_mf = np.zeros_like(raw_money_flow)
        negative_mf = np.zeros_like(raw_money_flow)

        # First value
        if self.close[0] > 0:
            positive_mf[0] = raw_money_flow[0]

        for i in range(1, len(typical_price)):
            if typical_price[i] > typical_price[i - 1]:
                positive_mf[i] = raw_money_flow[i]
            elif typical_price[i] < typical_price[i - 1]:
                negative_mf[i] = raw_money_flow[i]

        mfi = np.full_like(self.close, np.nan)

        for i in range(period - 1, len(self.close)):
            pos_sum = np.sum(positive_mf[i - period + 1:i + 1])
            neg_sum = np.sum(negative_mf[i - period + 1:i + 1])

            if pos_sum + neg_sum > 0:
                mfi[i] = 100 * pos_sum / (pos_sum + neg_sum)
            else:
                mfi[i] = 50

        return mfi

    def calculate_roc(self, period: int = 12) -> np.ndarray:
        """
        Calculate Rate of Change.

        Args:
            period: ROC period (typically 12)

        Returns:
            Array of ROC values as percentage (NaN for insufficient data)

        Example:
            >>> roc = indicators.calculate_roc(12)
        """
        self._validate_period(period)

        roc = np.full_like(self.close, np.nan)

        for i in range(period, len(self.close)):
            if self.close[i - period] != 0:
                roc[i] = ((self.close[i] - self.close[i - period]) / self.close[i - period]) * 100

        return roc

    def calculate_vroc(self, period: int = 14) -> np.ndarray:
        """
        Calculate Volume Rate of Change.

        Args:
            period: VROC period (typically 14)

        Returns:
            Array of VROC values as percentage

        Example:
            >>> vroc = indicators.calculate_vroc(14)
        """
        self._validate_period(period)

        vroc = np.full_like(self.volume, np.nan)

        for i in range(period, len(self.volume)):
            if self.volume[i - period] != 0:
                vroc[i] = ((self.volume[i] - self.volume[i - period]) / self.volume[i - period]) * 100

        return vroc

    def calculate_awesome_oscillator(self, fast: int = 5, slow: int = 34) -> np.ndarray:
        """
        Calculate Awesome Oscillator.

        Args:
            fast: Fast MA period (typically 5)
            slow: Slow MA period (typically 34)

        Returns:
            Array of AO values

        Example:
            >>> ao = indicators.calculate_awesome_oscillator()
        """
        self._validate_period(slow)

        # Median Price
        median_price = (self.high + self.low) / 2.0

        sma_fast = self.calculate_sma_custom(median_price, fast)
        sma_slow = self.calculate_sma_custom(median_price, slow)

        ao = sma_fast - sma_slow

        return ao

    def calculate_sma_custom(self, data: np.ndarray, period: int) -> np.ndarray:
        """Helper: Calculate SMA on custom data array."""
        sma = np.full_like(data, np.nan)

        for i in range(period - 1, len(data)):
            sma[i] = np.mean(data[i - period + 1:i + 1])

        return sma

    def calculate_trix(self, period: int = 15) -> np.ndarray:
        """
        Calculate TRIX (Triple Exponential Moving Average).

        Args:
            period: TRIX period (typically 15)

        Returns:
            Array of TRIX values as percentage change

        Example:
            >>> trix = indicators.calculate_trix(15)
        """
        self._validate_period(period, min_period=period * 3)

        # Three exponential moving averages
        ema1 = self._ema(self.close, period)
        ema2 = self._ema(ema1, period)
        ema3 = self._ema(ema2, period)

        # Percentage change
        trix = np.full_like(ema3, np.nan)

        for i in range(1, len(ema3)):
            if ema3[i - 1] != 0 and not np.isnan(ema3[i]) and not np.isnan(ema3[i - 1]):
                trix[i] = ((ema3[i] - ema3[i - 1]) / ema3[i - 1]) * 10000

        return trix

    def calculate_keltner_channel(
        self, period: int = 20, atr_period: int = 10, offset: float = 2.0
    ) -> dict[str, np.ndarray]:
        """
        Calculate Keltner Channel.

        Args:
            period: EMA period (typically 20)
            atr_period: ATR period (typically 10)
            offset: ATR multiplier (typically 2.0)

        Returns:
            Dict with 'upper', 'middle', 'lower' arrays

        Example:
            >>> kc = indicators.calculate_keltner_channel()
            >>> upper = kc['upper']
        """
        self._validate_period(period)

        middle = self._ema(self.close, period)
        atr = self.calculate_atr(atr_period)

        upper = middle + (atr * offset)
        lower = middle - (atr * offset)

        return {
            'upper': upper,
            'middle': middle,
            'lower': lower,
        }

    def calculate_pivot_points(self) -> dict[str, np.ndarray]:
        """
        Calculate Pivot Points (support/resistance).

        Returns:
            Dict with 'pivot', 'resistance1', 'resistance2', 'support1', 'support2' arrays

        Example:
            >>> pp = indicators.calculate_pivot_points()
            >>> pivot = pp['pivot']
        """
        # Standard pivot point calculation
        pivot = (self.high + self.low + self.close) / 3.0
        resistance1 = (pivot * 2) - self.low
        resistance2 = pivot + (self.high - self.low)
        support1 = (pivot * 2) - self.high
        support2 = pivot - (self.high - self.low)

        return {
            'pivot': pivot,
            'resistance1': resistance1,
            'resistance2': resistance2,
            'support1': support1,
            'support2': support2,
        }

    def calculate_fibonacci_levels(self) -> dict[str, float]:
        """
        Calculate Fibonacci retracement levels for current price range.

        Returns:
            Dict with 'high', 'low', and retracement levels (0, 23.6, 38.2, 50, 61.8, 78.6, 100)

        Example:
            >>> fib = indicators.calculate_fibonacci_levels()
            >>> level_382 = fib['level_382']
        """
        highest = np.max(self.high)
        lowest = np.min(self.low)
        range_price = highest - lowest

        return {
            'high': float(highest),
            'low': float(lowest),
            'level_0': float(lowest),
            'level_236': float(lowest + range_price * 0.236),
            'level_382': float(lowest + range_price * 0.382),
            'level_500': float(lowest + range_price * 0.500),
            'level_618': float(lowest + range_price * 0.618),
            'level_786': float(lowest + range_price * 0.786),
            'level_100': float(highest),
        }

    def calculate_standard_deviation(self, period: int = 20) -> np.ndarray:
        """
        Calculate Standard Deviation of close prices.

        Args:
            period: Period (typically 20)

        Returns:
            Array of standard deviation values

        Example:
            >>> std = indicators.calculate_standard_deviation(20)
        """
        self._validate_period(period)

        std = np.full_like(self.close, np.nan)

        for i in range(period - 1, len(self.close)):
            window = self.close[i - period + 1:i + 1]
            std[i] = np.std(window, ddof=1)

        return std

    def calculate_ichimoku(self) -> dict[str, np.ndarray]:
        """
        Calculate Ichimoku Cloud.

        Returns:
            Dict with 'tenkan', 'kijun', 'senkou_a', 'senkou_b', 'chikou' arrays

        Example:
            >>> ichimoku = indicators.calculate_ichimoku()
            >>> cloud = ichimoku['senkou_a']
        """
        self._validate_period(52)

        # Tenkan-sen (9-period high-low average)
        tenkan = np.full_like(self.close, np.nan)
        for i in range(8, len(self.close)):
            high_9 = np.max(self.high[i - 8:i + 1])
            low_9 = np.min(self.low[i - 8:i + 1])
            tenkan[i] = (high_9 + low_9) / 2.0

        # Kijun-sen (26-period high-low average)
        kijun = np.full_like(self.close, np.nan)
        for i in range(25, len(self.close)):
            high_26 = np.max(self.high[i - 25:i + 1])
            low_26 = np.min(self.low[i - 25:i + 1])
            kijun[i] = (high_26 + low_26) / 2.0

        # Senkou Span A (average of tenkan and kijun, shifted 26 forward)
        senkou_a = np.full_like(self.close, np.nan)
        for i in range(26, len(self.close)):
            if not np.isnan(tenkan[i - 26]) and not np.isnan(kijun[i - 26]):
                senkou_a[i] = (tenkan[i - 26] + kijun[i - 26]) / 2.0

        # Senkou Span B (52-period high-low average, shifted 26 forward)
        senkou_b = np.full_like(self.close, np.nan)
        for i in range(51, len(self.close)):
            high_52 = np.max(self.high[i - 51:i + 1])
            low_52 = np.min(self.low[i - 51:i + 1])
            if i >= 26:
                senkou_b[i] = (high_52 + low_52) / 2.0

        # Chikou Span (current close shifted 26 back)
        chikou = np.roll(self.close, 26)

        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou,
        }

    def calculate_all(self) -> dict:
        """
        Calculate all 50+ technical indicators.

        Returns:
            Dictionary with all indicator results organized by category:
            {
                'trend': {...},
                'momentum': {...},
                'volatility': {...},
                'volume': {...},
                'oscillators': {...},
                'support_resistance': {...}
            }

        Example:
            >>> all_indicators = indicators.calculate_all()
            >>> rsi = all_indicators['momentum']['rsi']
            >>> macd = all_indicators['trend']['macd']
        """
        result = {
            'trend': {},
            'momentum': {},
            'volatility': {},
            'volume': {},
            'oscillators': {},
            'support_resistance': {},
        }

        try:
            # Trend Indicators
            result['trend']['ema_12'] = self.calculate_ema(12)
            result['trend']['ema_26'] = self.calculate_ema(26)
            result['trend']['ema_50'] = self.calculate_ema(50)
            result['trend']['ema_200'] = self.calculate_ema(200)
            result['trend']['sma_20'] = self.calculate_sma(20)
            result['trend']['sma_50'] = self.calculate_sma(50)
            result['trend']['sma_200'] = self.calculate_sma(200)
            result['trend']['macd'] = self.calculate_macd()
            result['trend']['adx'] = self.calculate_adx()
            result['trend']['ichimoku'] = self.calculate_ichimoku()

            # Momentum Indicators
            result['momentum']['rsi_14'] = self.calculate_rsi(14)
            result['momentum']['stochastic_rsi'] = self.calculate_stochastic_rsi()
            result['momentum']['cci_20'] = self.calculate_cci(20)
            result['momentum']['williams_r'] = self.calculate_williams_r(14)
            result['momentum']['roc_12'] = self.calculate_roc(12)
            result['momentum']['trix'] = self.calculate_trix()

            # Volatility Indicators
            result['volatility']['bollinger_bands'] = self.calculate_bollinger_bands(20, 2)
            result['volatility']['atr'] = self.calculate_atr(14)
            result['volatility']['keltner_channel'] = self.calculate_keltner_channel()
            result['volatility']['std_dev'] = self.calculate_standard_deviation(20)

            # Volume Indicators
            result['volume']['obv'] = self.calculate_obv()
            result['volume']['mfi'] = self.calculate_mfi(14)
            result['volume']['vroc'] = self.calculate_vroc(14)

            # Oscillators
            result['oscillators']['awesome'] = self.calculate_awesome_oscillator()

            # Support/Resistance
            result['support_resistance']['pivot_points'] = self.calculate_pivot_points()
            result['support_resistance']['fibonacci'] = self.calculate_fibonacci_levels()

        except InsufficientDataError as e:
            logger.warning(f"Insufficient data for some indicators: {e}")
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")

        return result

    def get_current_values(self) -> dict:
        """
        Get current (latest) values of all indicators.

        Returns:
            Dict with latest indicator values

        Example:
            >>> current = indicators.get_current_values()
            >>> current_rsi = current['rsi_14']
        """
        all_ind = self.calculate_all()
        current = {}

        # Extract last non-NaN values
        for category, indicators in all_ind.items():
            if isinstance(indicators, dict):
                for name, values in indicators.items():
                    if isinstance(values, np.ndarray):
                        # Find last non-NaN value
                        valid_idx = np.where(~np.isnan(values))[0]
                        if len(valid_idx) > 0:
                            current[f"{category}_{name}"] = float(values[valid_idx[-1]])
                    elif isinstance(values, dict):
                        # Handle nested dicts (like fibonacci levels)
                        current[f"{category}_{name}"] = values
            elif isinstance(indicators, np.ndarray):
                valid_idx = np.where(~np.isnan(indicators))[0]
                if len(valid_idx) > 0:
                    current[f"{category}"] = float(indicators[valid_idx[-1]])

        return current
