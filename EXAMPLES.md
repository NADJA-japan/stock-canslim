# 実行例とユースケース

このドキュメントでは、CAN-SLIM US Stock Hunterの具体的な実行例とユースケースを紹介します。

## 基本的な実行フロー

### 1. 初回セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/your-username/can-slim-bot.git
cd can-slim-bot

# 依存関係をインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .envファイルを編集してSLACK_BOT_TOKENを設定
```

### 2. ティッカーリストのカスタマイズ

`tickers.csv`を編集して、スクリーニング対象の銘柄を選択します：

```csv
ticker
AAPL
MSFT
NVDA
GOOGL
AMZN
```

### 3. 実行

```bash
python main.py
```

## 実行結果の例

### ケース1: 適格銘柄が見つかった場合

```
2024-01-15 10:00:00 - INFO - CAN-SLIM US Stock Hunterを開始します
2024-01-15 10:00:00 - INFO - ティッカーリストを読み込みました: 50銘柄
2024-01-15 10:00:05 - INFO - 株価データを取得しました
2024-01-15 10:00:05 - INFO - テクニカルフィルタリングを実行中...
2024-01-15 10:00:06 - INFO - テクニカルフィルター通過: 12銘柄
2024-01-15 10:00:06 - INFO - ファンダメンタルフィルタリングを実行中...
2024-01-15 10:00:15 - INFO - NVDA: CAN-SLIM基準を満たしています
2024-01-15 10:00:15 - INFO - チャートを生成しました: output/chart_NVDA.png
2024-01-15 10:00:16 - INFO - Slackに投稿しました: NVDA
2024-01-15 10:00:20 - INFO - AMD: CAN-SLIM基準を満たしています
2024-01-15 10:00:20 - INFO - チャートを生成しました: output/chart_AMD.png
2024-01-15 10:00:21 - INFO - Slackに投稿しました: AMD
2024-01-15 10:00:25 - INFO - META: CAN-SLIM基準を満たしています
2024-01-15 10:00:25 - INFO - チャートを生成しました: output/chart_META.png
2024-01-15 10:00:26 - INFO - Slackに投稿しました: META
2024-01-15 10:01:30 - INFO - 処理完了 - 処理済み: 50, 適格: 3, スキップ: 0
```

### ケース2: 適格銘柄が見つからなかった場合

```
2024-01-15 10:00:00 - INFO - CAN-SLIM US Stock Hunterを開始します
2024-01-15 10:00:00 - INFO - ティッカーリストを読み込みました: 30銘柄
2024-01-15 10:00:05 - INFO - 株価データを取得しました
2024-01-15 10:00:05 - INFO - テクニカルフィルタリングを実行中...
2024-01-15 10:00:06 - INFO - テクニカルフィルター通過: 5銘柄
2024-01-15 10:00:06 - INFO - ファンダメンタルフィルタリングを実行中...
2024-01-15 10:00:30 - INFO - 処理完了 - 処理済み: 30, 適格: 0, スキップ: 0
```

### ケース3: エラーが発生した場合

```
2024-01-15 10:00:00 - INFO - CAN-SLIM US Stock Hunterを開始します
2024-01-15 10:00:00 - INFO - ティッカーリストを読み込みました: 30銘柄
2024-01-15 10:00:05 - INFO - 株価データを取得しました
2024-01-15 10:00:05 - INFO - テクニカルフィルタリングを実行中...
2024-01-15 10:00:06 - INFO - テクニカルフィルター通過: 8銘柄
2024-01-15 10:00:06 - INFO - ファンダメンタルフィルタリングを実行中...
2024-01-15 10:00:10 - WARNING - XYZ: 株価データが取得できませんでした。スキップします
2024-01-15 10:00:15 - WARNING - ABC: 財務データが不完全です。スキップします
2024-01-15 10:00:20 - INFO - NVDA: CAN-SLIM基準を満たしています
2024-01-15 10:00:20 - INFO - チャートを生成しました: output/chart_NVDA.png
2024-01-15 10:00:21 - INFO - Slackに投稿しました: NVDA
2024-01-15 10:00:30 - INFO - 処理完了 - 処理済み: 30, 適格: 1, スキップ: 2
```

## Slack通知の詳細例

### 通知メッセージの構造

適格銘柄が見つかると、以下の情報を含むメッセージがSlackに投稿されます：

```
📈 NVDA - NVIDIA Corporation - $495.50

💰 財務指標:
• 四半期EPS成長率: +125.3%
• 四半期売上成長率: +88.7%
• 年間ROE: 45.2%
• 相対力評価: S&P500を上回る

🎯 Exit戦略:
利益確定: $594.60 (現在価格+20%)
  → 株価が10日移動平均線を下回ったら利益確定を検討

損切り: $460.82 (現在価格-7%)
  → 株価が購入価格から7%下落、または50日移動平均線を3%以上下回ったら損切り

🔗 リンク:
• Yahoo Finance: https://finance.yahoo.com/quote/NVDA
• TradingView: https://www.tradingview.com/symbols/NVDA

📰 最新ニュース:
• NVIDIA Announces Record Quarterly Revenue
  https://nvidianews.nvidia.com/...
• NVIDIA Stock Hits New All-Time High
  https://finance.yahoo.com/...

[チャート画像が添付されます]
```

### チャート画像の内容

添付されるチャート画像には以下が含まれます：

- ローソク足チャート（過去252取引日）
- 50日移動平均線（青色）
- 200日移動平均線（赤色）
- 出来高バー（下部パネル）
- ダークテーマスタイル

## ユースケース

### ユースケース1: 毎日の市場終了後スクリーニング

GitHub Actionsを使用して、毎日市場終了後に自動実行：

```yaml
# .github/workflows/daily-screening.yml
name: Daily Stock Screening

on:
  schedule:
    - cron: '0 22 * * 1-5'  # 月-金 22:00 UTC (米国市場終了後)

jobs:
  screen:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: python main.py
        env:
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
          SLACK_CHANNEL: ${{ secrets.SLACK_CHANNEL }}
```

### ユースケース2: 特定セクターのスクリーニング

テクノロジーセクターのみをスクリーニングする場合：

```csv
# tickers_tech.csv
ticker
AAPL
MSFT
NVDA
GOOGL
AMZN
META
TSLA
NFLX
CRM
AMD
ADBE
ORCL
CSCO
INTC
QCOM
```

実行：
```bash
# config.pyでTICKER_LIST_PATHを変更
python main.py
```

### ユースケース3: カスタム閾値でのスクリーニング

より厳しい基準でスクリーニングする場合、`config.py`を編集：

```python
class Config:
    # より厳しい基準
    MIN_PRICE: float = 20.0  # デフォルト: 10.0
    MIN_VOL_AVG: int = 500000  # デフォルト: 200000
    EPS_GROWTH_THRESHOLD: float = 0.30  # デフォルト: 0.20
    REV_GROWTH_THRESHOLD: float = 0.30  # デフォルト: 0.20
    ROE_THRESHOLD: float = 0.20  # デフォルト: 0.15
    NEAR_HIGH_PCT: float = 0.90  # デフォルト: 0.85
```

### ユースケース4: 複数のSlackチャンネルへの通知

異なる基準で複数のチャンネルに通知する場合：

1. 成長株チャンネル（#growth-stocks）: デフォルト基準
2. 超成長株チャンネル（#super-growth）: 厳しい基準

それぞれ別の設定ファイルとワークフローを作成します。

## トラブルシューティング

### 問題1: Slack投稿が失敗する

**症状:**
```
ERROR - Slack投稿に失敗しました: invalid_auth
```

**解決策:**
1. SLACK_BOT_TOKENが正しく設定されているか確認
2. ボットがチャンネルに招待されているか確認（`/invite @bot-name`）
3. ボットに必要な権限（`chat:write`, `files:write`）があるか確認

### 問題2: データ取得が遅い

**症状:**
処理に非常に時間がかかる

**解決策:**
1. ティッカーリストを減らす
2. API呼び出し間隔を調整（`config.py`）
3. テクニカルフィルターで多くの銘柄が除外されるように閾値を調整

### 問題3: 適格銘柄が見つからない

**症状:**
```
INFO - 処理完了 - 処理済み: 50, 適格: 0, スキップ: 0
```

**解決策:**
1. 市場環境によっては適格銘柄が少ない場合があります
2. 閾値を緩和する（`config.py`）
3. より多くの銘柄をスクリーニング対象に追加

## パフォーマンス最適化

### 大量の銘柄をスクリーニングする場合

S&P500全体（500銘柄）をスクリーニングする場合：

1. **テクニカルフィルターの最適化**: 
   - 一括データ取得により高速化
   - 通常、500銘柄から50-100銘柄程度に絞り込まれます

2. **ファンダメンタルフィルターの最適化**:
   - API呼び出し間隔を1秒に設定（レート制限対策）
   - 50銘柄の場合、約1分で完了

3. **推定実行時間**:
   - 500銘柄: 約5-10分
   - 100銘柄: 約2-5分
   - 50銘柄: 約1-2分

## まとめ

CAN-SLIM US Stock Hunterは、効率的な2段階フィルタリングにより、大量の銘柄から成長株を自動的に発見します。GitHub Actionsと組み合わせることで、完全自動化された投資機会の発見システムを構築できます。
