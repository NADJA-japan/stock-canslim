"""
CAN-SLIM US Stock Hunter メインオーケストレーター

このスクリプトは以下の処理フローを実行します：
1. 設定とコンポーネントの初期化
2. ティッカーリストの読み込み
3. 株価データの一括取得
4. テクニカルフィルタリング
5. ファンダメンタルフィルタリング
6. Exit戦略の計算
7. チャート生成とSlack通知
8. 処理サマリーの出力
"""

import logging
import time
import sys
from typing import List, Tuple, Dict, Callable, TypeVar, Optional, Any
import pandas as pd
from requests.exceptions import Timeout, RequestException

from config import Config, setup_logging
from modules.data_loader import DataLoader
from modules.screener import TechnicalFilter, FundamentalFilter, ExitStrategyCalculator
from modules.visualizer import ChartGenerator
from modules.notifier import SlackNotifier
from modules.models import ExitStrategy, NewsItem

# ロギング設定
setup_logging()
logger = logging.getLogger(__name__)

# 型変数
T = TypeVar('T')


def fetch_with_retry(
    fetch_func: Callable[[], T],
    max_retries: int = 3,
    backoff_base: float = 2.0,
    operation_name: str = "操作"
) -> Optional[T]:
    """
    リトライロジック付きで関数を実行する
    
    ネットワークタイムアウトやレート制限エラーが発生した場合、
    指数バックオフで最大max_retries回までリトライします。
    
    Args:
        fetch_func: 実行する関数（引数なし）
        max_retries: 最大リトライ回数（デフォルト: 3）
        backoff_base: 指数バックオフの基数（デフォルト: 2.0）
        operation_name: 操作名（ログ出力用）
    
    Returns:
        関数の実行結果、または失敗時はNone
    
    Examples:
        >>> def get_data():
        ...     return api.fetch_data()
        >>> result = fetch_with_retry(get_data, max_retries=3, operation_name="データ取得")
    
    要件: 7.3
    """
    for attempt in range(max_retries):
        try:
            result = fetch_func()
            return result
        
        except Timeout:
            if attempt < max_retries - 1:
                wait_time = backoff_base ** attempt
                logger.warning(
                    f"{operation_name}がタイムアウトしました。"
                    f"{wait_time}秒後にリトライします（試行 {attempt + 1}/{max_retries}）"
                )
                time.sleep(wait_time)
            else:
                logger.error(f"{operation_name}が最大リトライ回数を超えました")
                return None
        
        except RequestException as e:
            # レート制限エラーなど
            if attempt < max_retries - 1:
                wait_time = backoff_base ** attempt
                logger.warning(
                    f"{operation_name}でネットワークエラーが発生しました: {e}。"
                    f"{wait_time}秒後にリトライします（試行 {attempt + 1}/{max_retries}）"
                )
                time.sleep(wait_time)
            else:
                logger.error(f"{operation_name}が最大リトライ回数を超えました")
                return None
        
        except Exception as e:
            logger.error(f"{operation_name}で予期しないエラーが発生しました: {e}")
            return None
    
    return None


def safe_process_ticker(
    ticker: str,
    process_func: Callable[[str], Optional[Any]],
    operation_name: str = "処理"
) -> Optional[Any]:
    """
    ティッカー処理を安全に実行する
    
    データ欠損や無効なティッカーに遭遇した場合、警告ログを記録し、
    Noneを返します。これにより、処理を継続できます。
    
    Args:
        ticker: ティッカーシンボル
        process_func: 実行する処理関数（ティッカーを引数に取る）
        operation_name: 操作名（ログ出力用）
    
    Returns:
        処理関数の実行結果、または失敗時はNone
    
    Examples:
        >>> def process_data(ticker):
        ...     return loader.fetch_financial_data(ticker)
        >>> result = safe_process_ticker("AAPL", process_data, "財務データ取得")
    
    要件: 8.1, 8.2, 8.3
    """
    try:
        result = process_func(ticker)
        
        if result is None:
            logger.warning(f"{ticker}: {operation_name}でデータが利用できません。スキップします。")
            return None
        
        # DataFrameの場合、空かどうかをチェック
        if isinstance(result, pd.DataFrame) and result.empty:
            logger.warning(f"{ticker}: {operation_name}でデータが空です。スキップします。")
            return None
        
        # 辞書の場合、空かどうかをチェック
        if isinstance(result, dict) and not result:
            logger.warning(f"{ticker}: {operation_name}でデータが空です。スキップします。")
            return None
        
        return result
    
    except ValueError as e:
        # 無効なティッカーシンボル
        logger.warning(f"{ticker}: 無効なティッカーシンボルです: {e}。スキップします。")
        return None
    
    except Exception as e:
        # その他のエラー
        logger.warning(f"{ticker}: {operation_name}中にエラーが発生しました: {e}。スキップします。")
        return None


def main():
    """
    メイン実行関数
    
    CAN-SLIMスクリーニングプロセス全体を制御します。
    
    処理フロー:
    1. コンポーネントの初期化
    2. ティッカーリスト読み込み
    3. 株価データ一括取得（SPYを含む）
    4. テクニカルフィルタリング実行
    5. ファンダメンタルフィルタリングループ
    6. 出力生成と通知ループ
    7. 処理サマリーの出力
    """
    logger.info("=" * 80)
    logger.info("CAN-SLIM US Stock Hunter 開始")
    logger.info("=" * 80)
    
    # ==================== 1. 初期化 ====================
    logger.info("コンポーネントを初期化中...")
    
    config = Config()
    
    # 設定を検証
    if not config.validate():
        logger.error("設定の検証に失敗しました。環境変数を確認してください。")
        sys.exit(1)
    
    # コンポーネントを初期化
    loader = DataLoader(config)
    tech_filter = TechnicalFilter(config)
    fund_filter = FundamentalFilter(config)
    exit_calc = ExitStrategyCalculator(config)
    chart_gen = ChartGenerator(config.CHART_OUTPUT_DIR)
    notifier = SlackNotifier(config.SLACK_BOT_TOKEN, config.SLACK_CHANNEL)
    
    logger.info("コンポーネントの初期化完了")
    
    # ==================== 2. ティッカーリスト読み込み ====================
    logger.info(f"ティッカーリストを読み込み中: {config.TICKER_LIST_PATH}")
    
    try:
        tickers = loader.load_ticker_list(config.TICKER_LIST_PATH)
        
        if not tickers:
            logger.error("有効なティッカーが見つかりませんでした。処理を終了します。")
            sys.exit(1)
        
        logger.info(f"ティッカーリスト読み込み完了: {len(tickers)}銘柄")
    
    except Exception as e:
        logger.error(f"ティッカーリスト読み込みエラー: {e}")
        sys.exit(1)
    
    # ==================== 3. 株価データ一括取得（SPYを含む） ====================
    logger.info("株価データを一括取得中...")
    
    # SPYを含むティッカーリストを作成
    all_tickers = tickers + [config.BENCHMARK_TICKER]
    
    try:
        price_data_dict = loader.fetch_price_data(all_tickers, period=config.PRICE_DATA_PERIOD)
        
        if not price_data_dict:
            logger.error("株価データの取得に失敗しました。処理を終了します。")
            sys.exit(1)
        
        # SPYデータを分離
        if config.BENCHMARK_TICKER not in price_data_dict:
            logger.error(f"ベンチマーク（{config.BENCHMARK_TICKER}）のデータ取得に失敗しました。処理を終了します。")
            sys.exit(1)
        
        spy_data = price_data_dict.pop(config.BENCHMARK_TICKER)
        
        logger.info(f"株価データ取得完了: {len(price_data_dict)}銘柄 + {config.BENCHMARK_TICKER}")
    
    except Exception as e:
        logger.error(f"株価データ取得エラー: {e}")
        sys.exit(1)
    
    # ==================== 4. テクニカルフィルタリング実行 ====================
    logger.info("テクニカルフィルタリングを開始...")
    
    try:
        # DataFrameをMultiIndexに変換（ticker, date）
        price_data_list = []
        for ticker, df in price_data_dict.items():
            df_copy = df.copy()
            df_copy['ticker'] = ticker
            df_copy = df_copy.reset_index()
            df_copy = df_copy.set_index(['ticker', 'Date'])
            price_data_list.append(df_copy)
        
        if price_data_list:
            price_data_multi = pd.concat(price_data_list)
        else:
            logger.error("株価データの変換に失敗しました。処理を終了します。")
            sys.exit(1)
        
        # テクニカルフィルターを適用
        candidates = tech_filter.filter_all(price_data_multi, spy_data)
        
        logger.info(f"テクニカルフィルタリング完了: {len(candidates)}銘柄が候補")
        
        if not candidates:
            logger.info("テクニカルフィルターを通過した銘柄がありません。処理を終了します。")
            sys.exit(0)
    
    except Exception as e:
        logger.error(f"テクニカルフィルタリングエラー: {e}")
        sys.exit(1)
    
    # ==================== 5. ファンダメンタルフィルタリングループ ====================
    logger.info("ファンダメンタルフィルタリングを開始...")
    
    qualified_stocks = []
    processed_count = 0
    skipped_count = 0
    
    for ticker in candidates:
        processed_count += 1
        
        # API呼び出し間隔の制御（1秒待機）
        if processed_count > 1:
            logger.debug(f"API呼び出し間隔制御: {config.API_CALL_DELAY}秒待機")
            time.sleep(config.API_CALL_DELAY)
        
        try:
            logger.info(f"財務データ取得中 ({processed_count}/{len(candidates)}): {ticker}")
            
            # 財務データを取得
            financial_data = loader.fetch_financial_data(ticker)
            
            if financial_data is None:
                logger.warning(f"{ticker}: 財務データが利用できません。スキップします。")
                skipped_count += 1
                continue
            
            # 財務データを解析
            quarterly_earnings = financial_data.get('quarterly_earnings')
            quarterly_financials = financial_data.get('quarterly_financials')
            info = financial_data.get('info', {})
            
            # EPSと売上のリストを作成
            eps_list = []
            revenue_list = []
            
            if quarterly_earnings is not None and not quarterly_earnings.empty:
                # EPSデータを取得（新しい順）
                if 'Earnings' in quarterly_earnings.columns:
                    eps_list = quarterly_earnings['Earnings'].tolist()
            
            if quarterly_financials is not None and not quarterly_financials.empty:
                # 売上データを取得（新しい順）
                if 'Total Revenue' in quarterly_financials.index:
                    revenue_list = quarterly_financials.loc['Total Revenue'].tolist()
            
            # ROEを取得
            roe = info.get('returnOnEquity', 0)
            if roe is None:
                roe = 0
            
            # セクターと業種を取得
            sector = info.get('sector', 'N/A')
            industry = info.get('industry', 'N/A')
            
            # 財務データ辞書を作成
            financial_dict = {
                'quarterly_eps': eps_list,
                'quarterly_revenue': revenue_list,
                'roe': roe,
                'sector': sector,
                'industry': industry
            }
            
            # 適格判定
            is_qualified, metrics = fund_filter.is_qualified(financial_dict)
            
            if is_qualified:
                logger.info(f"{ticker}: CAN-SLIM基準を満たしています ✓")
                qualified_stocks.append((ticker, metrics))
            else:
                logger.info(f"{ticker}: CAN-SLIM基準を満たしていません")
                skipped_count += 1
        
        except Exception as e:
            logger.warning(f"{ticker}: 処理中にエラーが発生しました: {e}。スキップします。")
            skipped_count += 1
            continue
    
    logger.info(f"ファンダメンタルフィルタリング完了: {len(qualified_stocks)}銘柄が適格")
    
    if not qualified_stocks:
        logger.info("適格銘柄が見つかりませんでした。")
        # 処理サマリーを出力
        logger.info("=" * 80)
        logger.info("処理サマリー")
        logger.info("=" * 80)
        logger.info(f"処理済みティッカー数: {len(tickers)}")
        logger.info(f"テクニカルフィルター通過: {len(candidates)}")
        logger.info(f"適格銘柄数: 0")
        logger.info(f"スキップ数: {skipped_count}")
        logger.info("=" * 80)
        sys.exit(0)
    
    # ==================== 6. 出力生成と通知ループ ====================
    logger.info("出力生成とSlack通知を開始...")
    
    notification_success_count = 0
    notification_failed_count = 0
    
    for ticker, metrics in qualified_stocks:
        try:
            logger.info(f"出力生成中: {ticker}")
            
            # 株価データを取得
            ticker_price_data = price_data_dict.get(ticker)
            
            if ticker_price_data is None or ticker_price_data.empty:
                logger.warning(f"{ticker}: 株価データが見つかりません。スキップします。")
                notification_failed_count += 1
                continue
            
            # Exit戦略を計算
            current_price = ticker_price_data['Close'].iloc[-1]
            ma_10 = ticker_price_data['Close'].rolling(window=config.MA_10_PERIOD).mean().iloc[-1]
            ma_50 = ticker_price_data['Close'].rolling(window=config.MA_50_PERIOD).mean().iloc[-1]
            
            profit_strategy = exit_calc.calculate_profit_target(current_price, ma_10)
            stop_strategy = exit_calc.calculate_stop_loss(current_price, ma_50)
            
            exit_strategy = ExitStrategy(
                profit_target_price=profit_strategy['target_price'],
                profit_condition=profit_strategy['condition'],
                profit_reason=profit_strategy['reason'],
                stop_loss_price=stop_strategy['stop_price'],
                stop_loss_condition=stop_strategy['ma_stop_condition'],
                stop_loss_reason=stop_strategy['reason']
            )
            
            # チャート画像を生成
            chart_path = chart_gen.generate_chart(ticker, ticker_price_data)
            
            # 企業情報を取得
            company_info = loader.fetch_company_info(ticker)
            
            if company_info is None:
                company_info = {
                    'name': ticker,
                    'sector': metrics.get('sector', 'N/A'),
                    'industry': metrics.get('industry', 'N/A')
                }
            
            # ニュースを取得
            news_data = loader.fetch_news(ticker, max_items=config.MAX_NEWS_ITEMS)
            news_items = [
                NewsItem(
                    title=item['title'],
                    url=item['url'],
                    published_date=item['published_date']
                )
                for item in news_data
            ]
            
            # 相対力評価を計算
            ticker_prices = ticker_price_data['Close']
            ticker_return_1y = (ticker_prices.iloc[-1] - ticker_prices.iloc[0]) / ticker_prices.iloc[0]
            spy_prices = spy_data['Close']
            spy_return_1y = (spy_prices.iloc[-1] - spy_prices.iloc[0]) / spy_prices.iloc[0]
            
            rs_rating = f"市場比 +{(ticker_return_1y - spy_return_1y) * 100:.1f}%"
            metrics['rs_rating'] = rs_rating
            
            # Slackに投稿
            notifier.post_stock_alert(
                ticker=ticker,
                company_name=company_info['name'],
                current_price=current_price,
                metrics=metrics,
                exit_strategy=exit_strategy,
                chart_path=chart_path,
                news=news_items,
                company_info=company_info
            )
            
            notification_success_count += 1
            logger.info(f"{ticker}: Slack通知完了 ✓")
        
        except Exception as e:
            logger.error(f"{ticker}: 出力生成またはSlack通知中にエラーが発生しました: {e}。スキップします。")
            notification_failed_count += 1
            continue
    
    # ==================== 7. 処理サマリーの出力 ====================
    logger.info("=" * 80)
    logger.info("処理サマリー")
    logger.info("=" * 80)
    logger.info(f"処理済みティッカー数: {len(tickers)}")
    logger.info(f"テクニカルフィルター通過: {len(candidates)}")
    logger.info(f"適格銘柄数: {len(qualified_stocks)}")
    logger.info(f"Slack通知成功: {notification_success_count}")
    logger.info(f"Slack通知失敗: {notification_failed_count}")
    logger.info(f"スキップ数: {skipped_count}")
    logger.info("=" * 80)
    logger.info("CAN-SLIM US Stock Hunter 完了")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n処理が中断されました")
        sys.exit(0)
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
