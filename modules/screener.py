"""
CAN-SLIM US Stock Hunter スクリーニングモジュール

このモジュールは以下のクラスを提供します：
- TechnicalFilter: テクニカル分析に基づくフィルタリング
- FundamentalFilter: ファンダメンタル分析に基づくフィルタリング
- ExitStrategyCalculator: Exit戦略の計算
"""

import logging
from typing import List, Dict, Tuple
import pandas as pd
import numpy as np

from config import Config

logger = logging.getLogger(__name__)


class TechnicalFilter:
    """
    テクニカル分析に基づくフィルタリングクラス
    
    株価データを使用して、CAN-SLIM基準のテクニカル条件を満たす銘柄を
    フィルタリングします。
    
    Attributes:
        config: 設定オブジェクト
    """
    
    def __init__(self, config: Config):
        """
        TechnicalFilterを初期化する
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        logger.info("TechnicalFilterを初期化しました")
    
    def apply_price_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        株価フィルターを適用する（$10以上）
        
        要件2.2: 現在の株価が10ドル以下であるとき、システムはそのティッカーを
        それ以降の処理から除外するものとする
        
        Args:
            data: 株価データ（'Close'列を含む）
        
        Returns:
            フィルター後のデータフレーム
        """
        if data.empty:
            return data
        
        # 最新の終値を取得
        latest_prices = data.groupby(level=0)['Close'].last()
        
        # 株価が閾値以上の銘柄を抽出
        valid_tickers = latest_prices[latest_prices >= self.config.MIN_PRICE].index.tolist()
        
        filtered_count = len(latest_prices) - len(valid_tickers)
        logger.info(f"株価フィルター: {filtered_count}銘柄を除外（${self.config.MIN_PRICE}未満）")
        
        # 有効な銘柄のデータのみを返す
        if valid_tickers:
            return data.loc[valid_tickers]
        else:
            return pd.DataFrame()
    
    def apply_volume_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        出来高フィルターを適用する（50日平均200k以上）
        
        要件2.3: 50日平均出来高が200,000株以下であるとき、システムはそのティッカーを
        それ以降の処理から除外するものとする
        
        Args:
            data: 株価データ（'Volume'列を含む）
        
        Returns:
            フィルター後のデータフレーム
        """
        if data.empty:
            return data
        
        valid_tickers = []
        
        # 各ティッカーの50日平均出来高を計算
        for ticker in data.index.get_level_values(0).unique():
            ticker_data = data.loc[ticker]
            
            # 50日平均出来高を計算
            avg_volume_50d = ticker_data['Volume'].tail(50).mean()
            
            if avg_volume_50d >= self.config.MIN_VOL_AVG:
                valid_tickers.append(ticker)
        
        filtered_count = len(data.index.get_level_values(0).unique()) - len(valid_tickers)
        logger.info(f"出来高フィルター: {filtered_count}銘柄を除外（50日平均{self.config.MIN_VOL_AVG}株未満）")
        
        # 有効な銘柄のデータのみを返す
        if valid_tickers:
            return data.loc[valid_tickers]
        else:
            return pd.DataFrame()

    def apply_trend_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        トレンドフィルターを適用する（200MA以上）
        
        要件2.4: 現在の株価が200日単純移動平均線以下であるとき、システムはそのティッカーを
        それ以降の処理から除外するものとする
        
        Args:
            data: 株価データ（'Close'列を含む）
        
        Returns:
            フィルター後のデータフレーム
        """
        if data.empty:
            return data
        
        valid_tickers = []
        
        # 各ティッカーの200日移動平均線を計算
        for ticker in data.index.get_level_values(0).unique():
            ticker_data = data.loc[ticker]
            
            # 200日移動平均線を計算
            sma_200 = ticker_data['Close'].rolling(window=self.config.MA_200_PERIOD).mean()
            
            # 最新の株価と200日移動平均線を比較
            latest_price = ticker_data['Close'].iloc[-1]
            latest_sma_200 = sma_200.iloc[-1]
            
            if pd.notna(latest_sma_200) and latest_price >= latest_sma_200:
                valid_tickers.append(ticker)
        
        filtered_count = len(data.index.get_level_values(0).unique()) - len(valid_tickers)
        logger.info(f"トレンドフィルター: {filtered_count}銘柄を除外（200日移動平均線未満）")
        
        # 有効な銘柄のデータのみを返す
        if valid_tickers:
            return data.loc[valid_tickers]
        else:
            return pd.DataFrame()
    
    def apply_near_high_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        新高値近辺フィルターを適用する（52週高値の85%以上）
        
        要件2.5: 現在の株価が52週高値の85%未満であるとき、システムはそのティッカーを
        それ以降の処理から除外するものとする
        
        Args:
            data: 株価データ（'Close'列を含む）
        
        Returns:
            フィルター後のデータフレーム
        """
        if data.empty:
            return data
        
        valid_tickers = []
        
        # 各ティッカーの52週高値を計算
        for ticker in data.index.get_level_values(0).unique():
            ticker_data = data.loc[ticker]
            
            # 52週（約252取引日）の高値を取得
            high_52w = ticker_data['Close'].tail(252).max()
            
            # 最新の株価を取得
            latest_price = ticker_data['Close'].iloc[-1]
            
            # 52週高値の85%以上かチェック
            if latest_price >= (high_52w * self.config.NEAR_HIGH_PCT):
                valid_tickers.append(ticker)
        
        filtered_count = len(data.index.get_level_values(0).unique()) - len(valid_tickers)
        logger.info(f"新高値近辺フィルター: {filtered_count}銘柄を除外（52週高値の{self.config.NEAR_HIGH_PCT*100}%未満）")
        
        # 有効な銘柄のデータのみを返す
        if valid_tickers:
            return data.loc[valid_tickers]
        else:
            return pd.DataFrame()
    
    def apply_rs_filter(self, data: pd.DataFrame, spy_data: pd.DataFrame) -> pd.DataFrame:
        """
        相対力フィルターを適用する（SPYを上回る）
        
        要件2.6: ティッカーの1年間リターンがS&P500指数リターン以下であるとき、
        システムはそのティッカーをそれ以降の処理から除外するものとする
        
        Args:
            data: 株価データ（'Close'列を含む）
            spy_data: SPYの株価データ（'Close'列を含む）
        
        Returns:
            フィルター後のデータフレーム
        """
        if data.empty or spy_data.empty:
            return data
        
        # SPYの1年間リターンを計算
        spy_prices = spy_data['Close']
        spy_return_1y = (spy_prices.iloc[-1] - spy_prices.iloc[0]) / spy_prices.iloc[0]
        
        valid_tickers = []
        
        # 各ティッカーの1年間リターンを計算
        for ticker in data.index.get_level_values(0).unique():
            ticker_data = data.loc[ticker]
            ticker_prices = ticker_data['Close']
            
            # 1年間リターンを計算
            ticker_return_1y = (ticker_prices.iloc[-1] - ticker_prices.iloc[0]) / ticker_prices.iloc[0]
            
            # SPYを上回るかチェック
            if ticker_return_1y > spy_return_1y:
                valid_tickers.append(ticker)
        
        filtered_count = len(data.index.get_level_values(0).unique()) - len(valid_tickers)
        logger.info(f"相対力フィルター: {filtered_count}銘柄を除外（SPYリターン{spy_return_1y:.2%}以下）")
        
        # 有効な銘柄のデータのみを返す
        if valid_tickers:
            return data.loc[valid_tickers]
        else:
            return pd.DataFrame()
    
    def filter_all(self, data: pd.DataFrame, spy_data: pd.DataFrame) -> List[str]:
        """
        すべてのテクニカルフィルターを順次適用する
        
        要件2.7: ティッカーがすべてのテクニカルフィルターを通過したとき、
        システムはそのティッカーをファンダメンタル分析の候補リストに追加するものとする
        
        Args:
            data: 株価データ（MultiIndex: ticker, date）
            spy_data: SPYの株価データ
        
        Returns:
            すべてのフィルターを通過したティッカーのリスト
        """
        logger.info(f"テクニカルフィルタリング開始: {len(data.index.get_level_values(0).unique())}銘柄")
        
        # 1. 株価フィルター
        filtered_data = self.apply_price_filter(data)
        
        if filtered_data.empty:
            logger.info("テクニカルフィルタリング完了: 0銘柄が通過")
            return []
        
        # 2. 出来高フィルター
        filtered_data = self.apply_volume_filter(filtered_data)
        
        if filtered_data.empty:
            logger.info("テクニカルフィルタリング完了: 0銘柄が通過")
            return []
        
        # 3. トレンドフィルター
        filtered_data = self.apply_trend_filter(filtered_data)
        
        if filtered_data.empty:
            logger.info("テクニカルフィルタリング完了: 0銘柄が通過")
            return []
        
        # 4. 新高値近辺フィルター
        filtered_data = self.apply_near_high_filter(filtered_data)
        
        if filtered_data.empty:
            logger.info("テクニカルフィルタリング完了: 0銘柄が通過")
            return []
        
        # 5. 相対力フィルター
        filtered_data = self.apply_rs_filter(filtered_data, spy_data)
        
        # 通過した銘柄のリストを取得
        if filtered_data.empty:
            candidates = []
        else:
            candidates = filtered_data.index.get_level_values(0).unique().tolist()
        
        logger.info(f"テクニカルフィルタリング完了: {len(candidates)}銘柄が通過")
        
        return candidates


class FundamentalFilter:
    """
    ファンダメンタル分析に基づくフィルタリングクラス
    
    財務データを使用して、CAN-SLIM基準のファンダメンタル条件を満たす銘柄を
    フィルタリングします。
    
    Attributes:
        config: 設定オブジェクト
    """
    
    def __init__(self, config: Config):
        """
        FundamentalFilterを初期化する
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
        logger.info("FundamentalFilterを初期化しました")
    
    def check_current_earnings(self, financial_data: Dict) -> Tuple[bool, float, float]:
        """
        C基準: EPS成長率または売上成長率が20%以上
        
        要件3.2: 直近四半期のEPS成長率が1年前の同四半期と比較して20%以上であるとき、
        システムはそのティッカーを現在収益基準を満たすものとしてマークするものとする
        
        要件3.3: 直近四半期の売上成長率が1年前の同四半期と比較して20%以上であるとき、
        システムはそのティッカーを現在収益基準を満たすものとしてマークするものとする
        
        Args:
            financial_data: 財務データ辞書
                - 'quarterly_eps': 四半期EPSのリスト（最新から古い順）
                - 'quarterly_revenue': 四半期売上のリスト（最新から古い順）
        
        Returns:
            Tuple[bool, float, float]: (合格, EPS成長率, 売上成長率)
        """
        eps_growth = 0.0
        revenue_growth = 0.0
        
        # EPS成長率の計算
        if 'quarterly_eps' in financial_data and financial_data['quarterly_eps']:
            eps_list = financial_data['quarterly_eps']
            # 最新四半期と1年前の同四半期（4四半期前）を比較
            if len(eps_list) >= 5:  # 最低5四半期のデータが必要
                current_eps = eps_list[0]
                year_ago_eps = eps_list[4]
                
                if year_ago_eps and year_ago_eps != 0 and current_eps:
                    eps_growth = (current_eps - year_ago_eps) / abs(year_ago_eps)
        
        # 売上成長率の計算
        if 'quarterly_revenue' in financial_data and financial_data['quarterly_revenue']:
            revenue_list = financial_data['quarterly_revenue']
            # 最新四半期と1年前の同四半期（4四半期前）を比較
            if len(revenue_list) >= 5:  # 最低5四半期のデータが必要
                current_revenue = revenue_list[0]
                year_ago_revenue = revenue_list[4]
                
                if year_ago_revenue and year_ago_revenue != 0 and current_revenue:
                    revenue_growth = (current_revenue - year_ago_revenue) / abs(year_ago_revenue)
        
        # EPS成長率または売上成長率が閾値以上であれば合格
        passes = (eps_growth >= self.config.EPS_GROWTH_THRESHOLD or 
                 revenue_growth >= self.config.REV_GROWTH_THRESHOLD)
        
        return passes, eps_growth, revenue_growth
    
    def check_annual_earnings(self, financial_data: Dict) -> Tuple[bool, float]:
        """
        A基準: ROEが15%以上
        
        要件3.4: 直近年度のROEが15%以上であるとき、システムはそのティッカーを
        年間収益基準を満たすものとしてマークするものとする
        
        Args:
            financial_data: 財務データ辞書
                - 'roe': 年間ROE（小数表記、例: 0.15 = 15%）
        
        Returns:
            Tuple[bool, float]: (合格, ROE)
        """
        roe = 0.0
        
        if 'roe' in financial_data and financial_data['roe'] is not None:
            roe = financial_data['roe']
        
        # ROEが閾値以上であれば合格
        passes = roe >= self.config.ROE_THRESHOLD
        
        return passes, roe
    
    def is_qualified(self, financial_data: Dict) -> Tuple[bool, Dict]:
        """
        CAN-SLIM適格判定
        
        要件3.5: ティッカーが現在収益基準と年間収益基準の両方を満たすとき、
        システムはそのティッカーを適格なCAN-SLIM銘柄として分類するものとする
        
        Args:
            financial_data: 財務データ辞書
        
        Returns:
            Tuple[bool, Dict]: (適格, メトリクス辞書)
                メトリクス辞書には以下が含まれる：
                - 'eps_growth_q': 四半期EPS成長率
                - 'revenue_growth_q': 四半期売上成長率
                - 'roe': 年間ROE
                - 'sector': セクター
                - 'industry': 業種
        """
        # C基準（現在収益）をチェック
        current_passes, eps_growth, revenue_growth = self.check_current_earnings(financial_data)
        
        # A基準（年間収益）をチェック
        annual_passes, roe = self.check_annual_earnings(financial_data)
        
        # 両方の基準を満たす必要がある
        is_qualified = current_passes and annual_passes
        
        # メトリクス辞書を生成
        metrics = {
            'eps_growth_q': eps_growth,
            'revenue_growth_q': revenue_growth,
            'roe': roe,
            'sector': financial_data.get('sector', 'N/A'),
            'industry': financial_data.get('industry', 'N/A')
        }
        
        return is_qualified, metrics
