"""
CAN-SLIM US Stock Hunter データローダーモジュール

このモジュールはyfinanceを使用してデータ取得を担当します：
- ティッカーリストの読み込み
- 株価データの取得
- 財務データの取得
- 企業情報とニュースの取得
"""

import csv
import logging
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
import yfinance as yf
from requests.exceptions import Timeout, RequestException

from config import Config

logger = logging.getLogger(__name__)


class DataLoader:
    """yfinanceを使用したデータ取得クラス"""
    
    def __init__(self, config: Config = Config()):
        """
        DataLoaderを初期化する
        
        Args:
            config: 設定オブジェクト
        """
        self.config = config
    
    def load_ticker_list(self, source: str) -> List[str]:
        """
        CSVファイルまたはリストからティッカーシンボルを読み込む
        
        無効なティッカーシンボル（空文字、空白のみ、非ASCII文字を含むもの）は
        自動的にフィルタリングされます。
        
        Args:
            source: CSVファイルパスまたはティッカーリスト
        
        Returns:
            有効なティッカーシンボルのリスト
        
        Raises:
            FileNotFoundError: CSVファイルが存在しない場合
            ValueError: ソースが無効な場合
        
        Examples:
            >>> loader = DataLoader()
            >>> tickers = loader.load_ticker_list("tickers.csv")
            >>> print(tickers)
            ['AAPL', 'NVDA', 'MSFT']
        """
        tickers = []
        
        # CSVファイルから読み込み
        if isinstance(source, str) and source.endswith('.csv'):
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    # ヘッダー行をスキップ（存在する場合）
                    first_row = next(reader, None)
                    if first_row and self._is_valid_ticker(first_row[0]):
                        tickers.append(first_row[0].strip().upper())
                    
                    # 残りの行を読み込み
                    for row in reader:
                        if row and len(row) > 0:
                            ticker = row[0].strip().upper()
                            if self._is_valid_ticker(ticker):
                                tickers.append(ticker)
                
                logger.info(f"CSVファイル '{source}' から {len(tickers)} 個のティッカーを読み込みました")
            
            except FileNotFoundError:
                logger.error(f"ティッカーリストファイルが見つかりません: {source}")
                raise
            except Exception as e:
                logger.error(f"ティッカーリスト読み込みエラー: {e}")
                raise ValueError(f"ティッカーリストの読み込みに失敗しました: {e}")
        
        # Pythonリストから読み込み
        elif isinstance(source, list):
            for ticker in source:
                if isinstance(ticker, str):
                    ticker_clean = ticker.strip().upper()
                    if self._is_valid_ticker(ticker_clean):
                        tickers.append(ticker_clean)
            
            logger.info(f"リストから {len(tickers)} 個のティッカーを読み込みました")
        
        else:
            raise ValueError(f"無効なソース形式: {type(source)}。CSVファイルパスまたはリストを指定してください")
        
        # 重複を削除
        tickers = list(dict.fromkeys(tickers))
        
        if not tickers:
            logger.warning("有効なティッカーが見つかりませんでした")
        
        return tickers
    
    def _is_valid_ticker(self, ticker: str) -> bool:
        """
        ティッカーシンボルが有効かどうかを検証する
        
        有効なティッカーの条件：
        - 空文字でない
        - 空白のみでない
        - ASCII文字のみで構成される
        - 長さが1〜10文字
        
        Args:
            ticker: 検証するティッカーシンボル
        
        Returns:
            有効な場合True、そうでない場合False
        """
        if not ticker or not ticker.strip():
            return False
        
        # ASCII文字のみを許可
        if not ticker.isascii():
            logger.debug(f"無効なティッカー（非ASCII文字）: {ticker}")
            return False
        
        # 長さチェック（1〜10文字）
        if len(ticker) < 1 or len(ticker) > 10:
            logger.debug(f"無効なティッカー（長さ）: {ticker}")
            return False
        
        # 英数字とハイフン、ドットのみを許可
        if not all(c.isalnum() or c in ['-', '.'] for c in ticker):
            logger.debug(f"無効なティッカー（無効な文字）: {ticker}")
            return False
        
        return True

    def fetch_price_data(self, tickers: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """
        複数ティッカーの株価データを一括取得する
        
        過去252取引日（約1年）の日次株価データ（OHLCV）を取得します。
        リトライロジック（指数バックオフ、最大3回）を実装しています。
        
        Args:
            tickers: ティッカーシンボルのリスト
            period: データ取得期間（デフォルト: "1y"）
        
        Returns:
            ティッカーをキーとし、DataFrameを値とする辞書
            各DataFrameには以下のカラムが含まれます：
            - Open: 始値
            - High: 高値
            - Low: 安値
            - Close: 終値
            - Volume: 出来高
        
        Examples:
            >>> loader = DataLoader()
            >>> data = loader.fetch_price_data(["AAPL", "NVDA"])
            >>> print(data["AAPL"].head())
        """
        price_data = {}
        
        for ticker in tickers:
            try:
                logger.debug(f"株価データ取得中: {ticker}")
                df = self._fetch_with_retry(ticker, period)
                
                if df is not None and not df.empty:
                    price_data[ticker] = df
                    logger.debug(f"{ticker} の株価データ取得成功: {len(df)} 行")
                else:
                    logger.warning(f"{ticker} の株価データが空です。スキップします")
            
            except Exception as e:
                logger.warning(f"{ticker} の株価データ取得に失敗しました: {e}。スキップします")
                continue
        
        logger.info(f"{len(price_data)}/{len(tickers)} 個のティッカーの株価データを取得しました")
        return price_data
    
    def _fetch_with_retry(self, ticker: str, period: str) -> Optional[pd.DataFrame]:
        """
        リトライロジック付きで株価データを取得する
        
        ネットワークタイムアウトやレート制限エラーが発生した場合、
        指数バックオフで最大3回までリトライします。
        
        Args:
            ticker: ティッカーシンボル
            period: データ取得期間
        
        Returns:
            株価データのDataFrame、または取得失敗時はNone
        """
        for attempt in range(self.config.MAX_RETRIES):
            try:
                stock = yf.Ticker(ticker)
                df = stock.history(period=period)
                
                if df is not None and not df.empty:
                    return df
                else:
                    logger.debug(f"{ticker} のデータが空です（試行 {attempt + 1}/{self.config.MAX_RETRIES}）")
                    return None
            
            except Timeout:
                if attempt < self.config.MAX_RETRIES - 1:
                    wait_time = self.config.RETRY_BACKOFF_BASE ** attempt
                    logger.warning(
                        f"{ticker} のデータ取得がタイムアウトしました。"
                        f"{wait_time}秒後にリトライします（試行 {attempt + 1}/{self.config.MAX_RETRIES}）"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"{ticker} のデータ取得が最大リトライ回数を超えました")
                    return None
            
            except RequestException as e:
                # レート制限エラーなど
                logger.warning(f"{ticker} のデータ取得でネットワークエラーが発生しました: {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    wait_time = self.config.RETRY_BACKOFF_BASE ** attempt
                    logger.info(f"{wait_time}秒後にリトライします（試行 {attempt + 1}/{self.config.MAX_RETRIES}）")
                    time.sleep(wait_time)
                else:
                    logger.error(f"{ticker} のデータ取得が最大リトライ回数を超えました")
                    return None
            
            except Exception as e:
                logger.error(f"{ticker} のデータ取得で予期しないエラーが発生しました: {e}")
                return None
        
        return None

    def fetch_financial_data(self, ticker: str) -> Optional[Dict]:
        """
        個別ティッカーの財務データを取得する
        
        四半期財務データ（EPS、売上、ROE）を取得します。
        データが欠損している場合はNoneを返します。
        
        Args:
            ticker: ティッカーシンボル
        
        Returns:
            財務データを含む辞書、または取得失敗時はNone
            辞書には以下のキーが含まれます：
            - quarterly_earnings: 四半期EPS（DataFrame）
            - quarterly_revenue: 四半期売上（DataFrame）
            - financials: 年次財務データ（DataFrame）
            - info: 企業情報（辞書）
        
        Examples:
            >>> loader = DataLoader()
            >>> data = loader.fetch_financial_data("AAPL")
            >>> if data:
            ...     print(data['quarterly_earnings'].head())
        """
        try:
            logger.debug(f"財務データ取得中: {ticker}")
            stock = yf.Ticker(ticker)
            
            # 四半期財務データを取得
            quarterly_earnings = stock.quarterly_earnings
            quarterly_revenue = stock.quarterly_revenue
            quarterly_financials = stock.quarterly_financials
            info = stock.info
            
            # データが存在するか確認
            if quarterly_earnings is None or quarterly_earnings.empty:
                logger.warning(f"{ticker} の四半期EPSデータが利用できません")
                return None
            
            if quarterly_revenue is None or quarterly_revenue.empty:
                logger.warning(f"{ticker} の四半期売上データが利用できません")
                return None
            
            financial_data = {
                'quarterly_earnings': quarterly_earnings,
                'quarterly_revenue': quarterly_revenue,
                'quarterly_financials': quarterly_financials,
                'info': info
            }
            
            logger.debug(f"{ticker} の財務データ取得成功")
            return financial_data
        
        except Exception as e:
            logger.warning(f"{ticker} の財務データ取得に失敗しました: {e}")
            return None

    def fetch_company_info(self, ticker: str) -> Optional[Dict]:
        """
        企業情報（セクター、業種、企業名）を取得する
        
        Args:
            ticker: ティッカーシンボル
        
        Returns:
            企業情報を含む辞書、または取得失敗時はNone
            辞書には以下のキーが含まれます：
            - name: 企業名
            - sector: セクター
            - industry: 業種
        
        Examples:
            >>> loader = DataLoader()
            >>> info = loader.fetch_company_info("AAPL")
            >>> if info:
            ...     print(f"{info['name']} - {info['sector']}")
        """
        try:
            logger.debug(f"企業情報取得中: {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info:
                logger.warning(f"{ticker} の企業情報が利用できません")
                return None
            
            company_info = {
                'name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A')
            }
            
            logger.debug(f"{ticker} の企業情報取得成功: {company_info['name']}")
            return company_info
        
        except Exception as e:
            logger.warning(f"{ticker} の企業情報取得に失敗しました: {e}")
            return None
    
    def fetch_news(self, ticker: str, max_items: int = None) -> List[Dict]:
        """
        最新ニュースを取得する
        
        タイトルとURLを含む最新ニュース項目を取得します。
        ニュースが利用できない場合は空のリストを返します。
        
        Args:
            ticker: ティッカーシンボル
            max_items: 取得する最大ニュース数（デフォルト: Config.MAX_NEWS_ITEMS）
        
        Returns:
            ニュース項目のリスト
            各項目は以下のキーを含む辞書：
            - title: ニュースのタイトル
            - url: ニュース記事のURL
            - published_date: 公開日時（datetime）
        
        Examples:
            >>> loader = DataLoader()
            >>> news = loader.fetch_news("AAPL", max_items=2)
            >>> for item in news:
            ...     print(f"{item['title']}: {item['url']}")
        """
        if max_items is None:
            max_items = self.config.MAX_NEWS_ITEMS
        
        try:
            logger.debug(f"ニュース取得中: {ticker}（最大{max_items}件）")
            stock = yf.Ticker(ticker)
            news_data = stock.news
            
            if not news_data:
                logger.debug(f"{ticker} のニュースデータが利用できません")
                return []
            
            news_items = []
            for item in news_data[:max_items]:
                try:
                    # タイムスタンプをdatetimeに変換
                    published_timestamp = item.get('providerPublishTime', 0)
                    published_date = datetime.fromtimestamp(published_timestamp) if published_timestamp else datetime.now()
                    
                    news_item = {
                        'title': item.get('title', 'タイトルなし'),
                        'url': item.get('link', ''),
                        'published_date': published_date
                    }
                    news_items.append(news_item)
                except Exception as e:
                    logger.debug(f"ニュース項目の解析に失敗しました: {e}")
                    continue
            
            # 最小件数と最大件数の制約を確認
            if news_items:
                logger.debug(f"{ticker} のニュース取得成功: {len(news_items)} 件")
            else:
                logger.debug(f"{ticker} のニュースが解析できませんでした")
            
            return news_items
        
        except Exception as e:
            logger.debug(f"{ticker} のニュース取得に失敗しました: {e}")
            return []
