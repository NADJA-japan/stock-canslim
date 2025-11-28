# 設計ドキュメント

## 概要

CAN-SLIM US Stock Hunterは、米国株式市場から成長株を自動的にスクリーニングし、Slackに通知するPythonアプリケーションです。システムは2段階のフィルタリングプロセス（テクニカル→ファンダメンタル）を採用し、処理効率を最適化しています。

主な特徴：
- yfinanceを使用した株価・財務データの取得
- 段階的フィルタリングによる効率的な処理
- mplfinanceによる視覚的なチャート生成
- Slack統合による即座の通知
- Exit戦略の自動計算

## アーキテクチャ

システムは以下のレイヤーで構成されます：

```
┌─────────────────────────────────────────┐
│         Main Orchestrator               │
│    (main.py - 実行フロー制御)           │
└─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Data    │ │ Screener │ │ Output   │
│  Layer   │ │  Layer   │ │  Layer   │
└──────────┘ └──────────┘ └──────────┘
     │            │            │
     ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│data_     │ │screener  │ │visualizer│
│loader.py │ │.py       │ │.py       │
└──────────┘ └──────────┘ └──────────┘
                              │
                              ▼
                         ┌──────────┐
                         │notifier  │
                         │.py       │
                         └──────────┘
```

### 処理フロー

1. **初期化**: 設定ファイルとティッカーリストの読み込み
2. **データ取得**: yfinanceで株価データを一括取得
3. **テクニカルフィルタリング**: 株価ベースの高速フィルタリング
4. **ファンダメンタルフィルタリング**: 財務データによる詳細評価
5. **Exit戦略計算**: 利益確定・損切り指標の算出
6. **出力生成**: チャート画像とSlackメッセージの作成
7. **通知**: Slackへの投稿

## コンポーネントとインターフェース

### 1. Configuration Module (config.py)

設定値を一元管理するモジュール。

```python
class Config:
    # スクリーニング基準
    MIN_PRICE: float = 10.0
    MIN_VOL_AVG: int = 200000
    EPS_GROWTH_THRESHOLD: float = 0.20
    REV_GROWTH_THRESHOLD: float = 0.20
    ROE_THRESHOLD: float = 0.15
    NEAR_HIGH_PCT: float = 0.85
    
    # Exit戦略パラメータ
    PROFIT_TARGET_PCT: float = 0.20  # 20%利益確定
    STOP_LOSS_PCT: float = 0.07      # 7%損切り
    MA_STOP_LOSS_PCT: float = 0.03   # 50MA下3%で損切り
    
    # Slack設定
    SLACK_CHANNEL: str = "#stock-alerts"
    SLACK_BOT_TOKEN: str  # 環境変数から取得
    
    # データソース
    TICKER_LIST_PATH: str = "tickers.csv"
    CHART_OUTPUT_DIR: str = "output"
```

### 2. Data Loader Module (modules/data_loader.py)

yfinanceを使用したデータ取得を担当。

```python
class DataLoader:
    def load_ticker_list(self, source: str) -> List[str]:
        """CSVまたはリストからティッカーを読み込む"""
        pass
    
    def fetch_price_data(self, tickers: List[str], period: str = "1y") -> pd.DataFrame:
        """複数ティッカーの株価データを一括取得"""
        pass
    
    def fetch_financial_data(self, ticker: str) -> Dict:
        """個別ティッカーの財務データを取得"""
        pass
    
    def fetch_company_info(self, ticker: str) -> Dict:
        """企業情報（セクター、業種）を取得"""
        pass
    
    def fetch_news(self, ticker: str, max_items: int = 2) -> List[Dict]:
        """最新ニュースを取得"""
        pass
```

### 3. Screener Module (modules/screener.py)

フィルタリングロジックを実装。

```python
class TechnicalFilter:
    def __init__(self, config: Config):
        self.config = config
    
    def apply_price_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """株価フィルター（$10以上）"""
        pass
    
    def apply_volume_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """出来高フィルター（50日平均200k以上）"""
        pass
    
    def apply_trend_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """トレンドフィルター（200MA以上）"""
        pass
    
    def apply_near_high_filter(self, data: pd.DataFrame) -> pd.DataFrame:
        """新高値近辺フィルター（52週高値の85%以上）"""
        pass
    
    def apply_rs_filter(self, data: pd.DataFrame, spy_data: pd.DataFrame) -> pd.DataFrame:
        """相対力フィルター（SPYを上回る）"""
        pass
    
    def filter_all(self, data: pd.DataFrame, spy_data: pd.DataFrame) -> List[str]:
        """すべてのテクニカルフィルターを適用"""
        pass

class FundamentalFilter:
    def __init__(self, config: Config):
        self.config = config
    
    def check_current_earnings(self, financial_data: Dict) -> Tuple[bool, float, float]:
        """C基準: EPS成長率または売上成長率が20%以上
        Returns: (合格, EPS成長率, 売上成長率)
        """
        pass
    
    def check_annual_earnings(self, financial_data: Dict) -> Tuple[bool, float]:
        """A基準: ROEが15%以上
        Returns: (合格, ROE)
        """
        pass
    
    def is_qualified(self, financial_data: Dict) -> Tuple[bool, Dict]:
        """CAN-SLIM適格判定
        Returns: (適格, メトリクス辞書)
        """
        pass

class ExitStrategyCalculator:
    def __init__(self, config: Config):
        self.config = config
    
    def calculate_profit_target(self, current_price: float, ma_10: float) -> Dict:
        """利益確定戦略を計算
        Returns: {
            'target_price': float,
            'condition': str,
            'reason': str
        }
        """
        pass
    
    def calculate_stop_loss(self, current_price: float, ma_50: float) -> Dict:
        """損切り戦略を計算
        Returns: {
            'stop_price': float,
            'ma_stop_condition': str,
            'reason': str
        }
        """
        pass
```

### 4. Visualizer Module (modules/visualizer.py)

チャート生成を担当。

```python
class ChartGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
    
    def generate_chart(self, ticker: str, data: pd.DataFrame) -> str:
        """ローソク足チャートを生成
        Args:
            ticker: ティッカーシンボル
            data: 株価データ（OHLCV）
        Returns:
            生成されたファイルパス
        """
        pass
    
    def _add_moving_averages(self, data: pd.DataFrame) -> pd.DataFrame:
        """50日・200日移動平均線を追加"""
        pass
```

### 5. Notifier Module (modules/notifier.py)

Slack通知を担当。

```python
class SlackNotifier:
    def __init__(self, token: str, channel: str):
        self.client = WebClient(token=token)
        self.channel = channel
    
    def post_stock_alert(self, 
                        ticker: str,
                        company_name: str,
                        current_price: float,
                        metrics: Dict,
                        exit_strategy: Dict,
                        chart_path: str,
                        news: List[Dict],
                        company_info: Dict) -> None:
        """適格銘柄をSlackに投稿"""
        pass
    
    def _format_message(self, ...) -> Dict:
        """Slackメッセージをフォーマット"""
        pass
    
    def _upload_chart(self, chart_path: str) -> str:
        """チャート画像をアップロード"""
        pass
```

### 6. Main Orchestrator (main.py)

全体の実行フローを制御。

```python
def main():
    # 1. 初期化
    config = Config()
    loader = DataLoader()
    tech_filter = TechnicalFilter(config)
    fund_filter = FundamentalFilter(config)
    exit_calc = ExitStrategyCalculator(config)
    chart_gen = ChartGenerator(config.CHART_OUTPUT_DIR)
    notifier = SlackNotifier(config.SLACK_BOT_TOKEN, config.SLACK_CHANNEL)
    
    # 2. ティッカーリスト読み込み
    tickers = loader.load_ticker_list(config.TICKER_LIST_PATH)
    
    # 3. 株価データ一括取得
    price_data = loader.fetch_price_data(tickers)
    spy_data = loader.fetch_price_data(["SPY"])
    
    # 4. テクニカルフィルタリング
    candidates = tech_filter.filter_all(price_data, spy_data)
    
    # 5. ファンダメンタルフィルタリング
    qualified_stocks = []
    for ticker in candidates:
        time.sleep(1)  # レート制限対策
        
        try:
            financial_data = loader.fetch_financial_data(ticker)
            is_qualified, metrics = fund_filter.is_qualified(financial_data)
            
            if is_qualified:
                qualified_stocks.append((ticker, metrics))
        except Exception as e:
            logger.warning(f"Skipping {ticker}: {e}")
            continue
    
    # 6. 出力生成と通知
    for ticker, metrics in qualified_stocks:
        try:
            # Exit戦略計算
            current_price = price_data[ticker]['Close'].iloc[-1]
            ma_10 = price_data[ticker]['Close'].rolling(10).mean().iloc[-1]
            ma_50 = price_data[ticker]['Close'].rolling(50).mean().iloc[-1]
            
            profit_strategy = exit_calc.calculate_profit_target(current_price, ma_10)
            stop_strategy = exit_calc.calculate_stop_loss(current_price, ma_50)
            exit_strategy = {
                'profit': profit_strategy,
                'stop_loss': stop_strategy
            }
            
            # チャート生成
            chart_path = chart_gen.generate_chart(ticker, price_data[ticker])
            
            # 企業情報・ニュース取得
            company_info = loader.fetch_company_info(ticker)
            news = loader.fetch_news(ticker)
            
            # Slack投稿
            notifier.post_stock_alert(
                ticker=ticker,
                company_name=company_info['name'],
                current_price=current_price,
                metrics=metrics,
                exit_strategy=exit_strategy,
                chart_path=chart_path,
                news=news,
                company_info=company_info
            )
        except Exception as e:
            logger.error(f"Failed to process {ticker}: {e}")
            continue
    
    # 7. サマリー出力
    logger.info(f"Processed: {len(tickers)}, Qualified: {len(qualified_stocks)}")
```

## データモデル

### StockData

```python
@dataclass
class StockData:
    ticker: str
    current_price: float
    volume_50d_avg: float
    sma_50: float
    sma_200: float
    high_52w: float
    return_1y: float
```

### FinancialMetrics

```python
@dataclass
class FinancialMetrics:
    eps_growth_q: float  # 四半期EPS成長率
    revenue_growth_q: float  # 四半期売上成長率
    roe: float  # 年間ROE
    sector: str
    industry: str
```

### ExitStrategy

```python
@dataclass
class ExitStrategy:
    profit_target_price: float
    profit_condition: str
    profit_reason: str
    stop_loss_price: float
    stop_loss_condition: str
    stop_loss_reason: str
```

### NewsItem

```python
@dataclass
class NewsItem:
    title: str
    url: str
    published_date: datetime
```


## 正確性プロパティ

*プロパティとは、システムのすべての有効な実行において真であるべき特性または動作のことです。本質的には、システムが何をすべきかについての形式的な記述です。プロパティは、人間が読める仕様と機械で検証可能な正確性保証との橋渡しとなります。*

### プロパティ1: ティッカーリスト読み込みの一貫性

*任意の*有効なCSVファイルまたはPythonリストに対して、読み込み関数は含まれるすべての有効なティッカーシンボルを返すものとする

**検証: 要件 1.1**

### プロパティ2: 無効ティッカーのスキップ

*任意の*ティッカーリストに対して、無効なシンボルが含まれる場合、システムはそれらをスキップし、有効なシンボルのみを処理するものとする

**検証: 要件 1.4**

### プロパティ3: 株価フィルターの正確性

*任意の*株価データに対して、現在株価が10ドル以下の銘柄は候補リストから除外されるものとする

**検証: 要件 2.2**

### プロパティ4: 出来高フィルターの正確性

*任意の*出来高データに対して、50日平均出来高が200,000株以下の銘柄は候補リストから除外されるものとする

**検証: 要件 2.3**

### プロパティ5: トレンドフィルターの正確性

*任意の*株価データに対して、現在株価が200日移動平均線以下の銘柄は候補リストから除外されるものとする

**検証: 要件 2.4**

### プロパティ6: 新高値近辺フィルターの正確性

*任意の*株価データに対して、現在株価が52週高値の85%未満の銘柄は候補リストから除外されるものとする

**検証: 要件 2.5**

### プロパティ7: 相対力フィルターの正確性

*任意の*株価データとベンチマークデータに対して、1年間リターンがベンチマーク以下の銘柄は候補リストから除外されるものとする

**検証: 要件 2.6**

### プロパティ8: テクニカルフィルター通過の一貫性

*任意の*株価データに対して、すべてのテクニカルフィルター条件を満たす銘柄は候補リストに追加されるものとする

**検証: 要件 2.7**

### プロパティ9: EPS成長率判定の正確性

*任意の*財務データに対して、直近四半期のEPS成長率が20%以上の場合、システムは現在収益基準を満たすとマークするものとする

**検証: 要件 3.2**

### プロパティ10: 売上成長率判定の正確性

*任意の*財務データに対して、直近四半期の売上成長率が20%以上の場合、システムは現在収益基準を満たすとマークするものとする

**検証: 要件 3.3**

### プロパティ11: ROE判定の正確性

*任意の*財務データに対して、直近年度のROEが15%以上の場合、システムは年間収益基準を満たすとマークするものとする

**検証: 要件 3.4**

### プロパティ12: CAN-SLIM適格判定の正確性

*任意の*財務データに対して、現在収益基準と年間収益基準の両方を満たす場合、システムは適格なCAN-SLIM銘柄として分類するものとする

**検証: 要件 3.5**

### プロパティ13: 財務データ欠損時のスキップ

*任意の*ティッカーに対して、財務データが利用できない場合、システムはエラーを発生させずにそのティッカーをスキップするものとする

**検証: 要件 3.6**

### プロパティ14: チャートファイル名の正確性

*任意の*ティッカーシンボルに対して、生成されるチャート画像のファイル名は"chart_{TICKER}.png"の形式であるものとする

**検証: 要件 4.6**

### プロパティ15: ニュース取得数の制約

*任意の*ティッカーに対して、取得されるニュース項目数は1件以上2件以下であるものとする（ニュースが利用可能な場合）

**検証: 要件 5.3**

### プロパティ16: ニュースデータ欠損時の継続

*任意の*ティッカーに対して、ニュースデータが利用できない場合、システムはエラーを発生させずに処理を継続するものとする

**検証: 要件 5.4**

### プロパティ17: Slackメッセージの完全性

*任意の*適格銘柄データに対して、生成されるSlackメッセージはティッカーシンボル、企業名、現在株価、EPS成長率、売上成長率、ROE、相対力評価、外部リンク、ニュース項目を含むものとする

**検証: 要件 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.9**

### プロパティ18: API呼び出し間隔の遵守

*任意の*連続する財務データ取得呼び出しに対して、呼び出し間隔は少なくとも1秒以上であるものとする

**検証: 要件 7.1**

### プロパティ19: レート制限エラー時の継続

*任意の*ティッカーリストに対して、APIレート制限エラーが発生した場合、システムはエラーをログに記録し、残りのティッカーの処理を継続するものとする

**検証: 要件 7.2**

### プロパティ20: ネットワークタイムアウト時のリトライ

*任意の*ネットワークリクエストに対して、タイムアウトが発生した場合、システムは指数バックオフで最大3回までリトライするものとする

**検証: 要件 7.3**

### プロパティ21: データ欠損時のログ記録

*任意の*ティッカーに対して、株価データまたは財務データの欠損に遭遇した場合、システムは警告メッセージをログに記録し、そのティッカーをスキップするものとする

**検証: 要件 8.1, 8.2**

### プロパティ22: 無効ティッカー時のログ記録

*任意の*ティッカーシンボルに対して、無効なシンボルに遭遇した場合、システムは警告メッセージをログに記録し、そのティッカーをスキップするものとする

**検証: 要件 8.3**

### プロパティ23: 処理サマリーの正確性

*任意の*処理実行に対して、報告される処理済みティッカー数、適格ティッカー数、スキップティッカー数の合計は、入力ティッカーリストの総数と一致するものとする

**検証: 要件 8.4**

### プロパティ24: 利益確定目標価格の計算精度

*任意の*現在株価に対して、計算される利益確定目標価格は現在株価の120%（現在株価 × 1.20）であるものとする

**検証: 要件 10.2**

### プロパティ25: 損切り価格の計算精度

*任意の*現在株価に対して、計算される損切り価格は現在株価の93%（現在株価 × 0.93）であるものとする

**検証: 要件 10.5**

### プロパティ26: Exit戦略情報の完全性

*任意の*適格銘柄に対して、Slackメッセージは利益確定目標価格、利益確定条件、利益確定理由、損切り価格、損切り条件、損切り理由を含むものとする

**検証: 要件 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**

## エラーハンドリング

### エラーカテゴリ

1. **データ取得エラー**
   - yfinance APIエラー（レート制限、タイムアウト、無効なティッカー）
   - 対応: ログ記録、リトライ（タイムアウトの場合）、スキップして継続

2. **データ欠損エラー**
   - 株価データの欠損
   - 財務データの欠損
   - ニュースデータの欠損
   - 対応: 警告ログ、該当ティッカーをスキップ、処理継続

3. **ファイルI/Oエラー**
   - ティッカーリストファイルの読み込みエラー
   - チャート画像の保存エラー
   - 対応: エラーログ、適切なエラーメッセージを表示して終了

4. **Slack APIエラー**
   - 認証エラー
   - チャンネルが存在しない
   - ファイルアップロードエラー
   - 対応: エラーログ、該当銘柄をスキップ、処理継続

### エラーハンドリング戦略

```python
# データ取得のリトライロジック
def fetch_with_retry(fetch_func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return fetch_func()
        except Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数バックオフ
                time.sleep(wait_time)
            else:
                logger.error("Max retries exceeded")
                raise
        except RateLimitError:
            logger.warning("Rate limit hit, skipping")
            return None

# データ欠損の処理
def safe_process_ticker(ticker):
    try:
        data = fetch_data(ticker)
        if data is None or data.empty:
            logger.warning(f"No data for {ticker}, skipping")
            return None
        return process_data(data)
    except Exception as e:
        logger.warning(f"Error processing {ticker}: {e}, skipping")
        return None
```

### ログレベル

- **INFO**: 正常な処理フロー（開始、完了、サマリー）
- **WARNING**: スキップされたティッカー、データ欠損
- **ERROR**: 重大なエラー（設定ファイル読み込み失敗、Slack認証失敗）

## テスト戦略

### ユニットテスト

各モジュールの個別機能をテストします：

1. **DataLoader**
   - CSVファイルからのティッカーリスト読み込み
   - 無効なティッカーのフィルタリング
   - yfinance APIのモック呼び出し

2. **TechnicalFilter**
   - 各フィルター条件の個別テスト
   - 境界値テスト（10ドルちょうど、85%ちょうど）
   - 複数フィルターの組み合わせ

3. **FundamentalFilter**
   - EPS成長率計算
   - 売上成長率計算
   - ROE計算
   - 適格判定ロジック

4. **ExitStrategyCalculator**
   - 利益確定価格計算（20%上昇）
   - 損切り価格計算（7%下落）
   - 移動平均線条件の設定

5. **ChartGenerator**
   - ファイル名生成
   - ファイル保存の確認
   - データ範囲の検証

6. **SlackNotifier**
   - メッセージフォーマット
   - 必須情報の含有確認
   - リンク生成

### プロパティベーステスト

Pythonのプロパティベーステストライブラリ**Hypothesis**を使用します。

各プロパティベーステストは最低100回の反復を実行するように設定します。

#### テスト例

```python
from hypothesis import given, strategies as st
import hypothesis

# プロパティ3: 株価フィルターの正確性
@given(st.floats(min_value=0.01, max_value=1000.0))
def test_price_filter_excludes_low_prices(price):
    """Feature: can-slim-screener, Property 3: 株価フィルターの正確性"""
    data = create_mock_data(current_price=price)
    filter = TechnicalFilter(Config())
    result = filter.apply_price_filter(data)
    
    if price <= 10.0:
        assert len(result) == 0, "Price <= $10 should be excluded"
    else:
        assert len(result) > 0, "Price > $10 should pass"

# プロパティ24: 利益確定目標価格の計算精度
@given(st.floats(min_value=10.0, max_value=10000.0))
def test_profit_target_calculation(current_price):
    """Feature: can-slim-screener, Property 24: 利益確定目標価格の計算精度"""
    calc = ExitStrategyCalculator(Config())
    result = calc.calculate_profit_target(current_price, current_price * 0.95)
    
    expected_target = current_price * 1.20
    assert abs(result['target_price'] - expected_target) < 0.01, \
        f"Target price should be {expected_target}, got {result['target_price']}"

# プロパティ23: 処理サマリーの正確性
@given(st.lists(st.text(min_size=1, max_size=5), min_size=1, max_size=100))
def test_processing_summary_accuracy(tickers):
    """Feature: can-slim-screener, Property 23: 処理サマリーの正確性"""
    # モックデータで処理を実行
    processed, qualified, skipped = process_tickers(tickers)
    
    assert processed + skipped == len(tickers), \
        "Total processed + skipped should equal input count"
    assert qualified <= processed, \
        "Qualified count should not exceed processed count"
```

### 統合テスト

エンドツーエンドのフローをテストします：

1. **完全なスクリーニングフロー**
   - 小規模なティッカーリスト（5-10銘柄）
   - モックされたyfinance API
   - モックされたSlack API
   - すべてのコンポーネントの統合

2. **エラーシナリオ**
   - APIエラーのシミュレーション
   - データ欠損のシミュレーション
   - ネットワークタイムアウトのシミュレーション

### テスト実行設定

```python
# conftest.py
import pytest
from hypothesis import settings

# Hypothesisの設定
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=20, deadline=None)
settings.load_profile("dev")  # デフォルトはdev、CIではciを使用
```

### テストカバレッジ目標

- ユニットテスト: 80%以上のコードカバレッジ
- プロパティベーステスト: すべての正確性プロパティをカバー
- 統合テスト: 主要なユーザーフローをカバー
