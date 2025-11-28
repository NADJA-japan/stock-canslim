# CAN-SLIM US Stock Hunter

米国株式市場から成長株を自動的にスクリーニングし、Slackに通知するPythonアプリケーションです。

## 概要

William O'NeilのCAN-SLIM基準を満たす銘柄を効率的に発見し、投資家に視覚的なチャートと主要指標を提供します。

## 主な機能

- S&P500/Nasdaq100銘柄の2段階スクリーニング（テクニカル→ファンダメンタル）
- 自動チャート生成（ローソク足、移動平均線、出来高）
- Exit戦略の自動計算（利益確定20%、損切り7%）
- Slack統合による即座の通知
- 企業情報とニュースの自動収集

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、Slack Bot Tokenを設定します：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```
SLACK_BOT_TOKEN=xoxb-your-actual-slack-bot-token
SLACK_CHANNEL=#stock-alerts
```

#### Slack Bot Tokenの取得方法

1. [Slack API](https://api.slack.com/apps)にアクセス
2. 「Create New App」をクリック
3. 「From scratch」を選択し、アプリ名とワークスペースを設定
4. 「OAuth & Permissions」に移動
5. 「Bot Token Scopes」に以下の権限を追加：
   - `chat:write` - メッセージ投稿
   - `files:write` - ファイルアップロード
6. 「Install to Workspace」をクリック
7. 表示される「Bot User OAuth Token」（xoxb-で始まる）をコピー
8. Slackチャンネルにボットを招待：`/invite @your-bot-name`

### 3. ティッカーリストの準備

`tickers.csv`ファイルにスクリーニング対象の銘柄を記載します（デフォルトでS&P500の主要銘柄が含まれています）。

## 使用方法

### 基本実行

```bash
python main.py
```

### テスト実行

```bash
# ユニットテスト
pytest

# プロパティベーステスト（CI環境）
pytest --hypothesis-profile=ci
```

## プロジェクト構造

```
can-slim-bot/
├── main.py              # エントリーポイント
├── config.py            # 設定値
├── requirements.txt     # 依存ライブラリ
├── .env                 # 環境変数
├── tickers.csv          # 対象銘柄リスト
├── modules/             # コアモジュール
│   ├── data_loader.py   # データ取得
│   ├── screener.py      # フィルタリング
│   ├── visualizer.py    # チャート生成
│   └── notifier.py      # Slack通知
├── output/              # チャート画像保存先
└── tests/               # テストコード
```

## 設定のカスタマイズ

`config.py`で以下の設定をカスタマイズできます：

- スクリーニング閾値（最低株価、出来高、成長率など）
- Exit戦略パラメータ（利益確定、損切り）
- Slack通知設定
- データ取得期間

## 実行例

### 正常実行時の出力例

```
2024-01-15 10:00:00 - INFO - CAN-SLIM US Stock Hunterを開始します
2024-01-15 10:00:00 - INFO - ティッカーリストを読み込みました: 30銘柄
2024-01-15 10:00:05 - INFO - 株価データを取得しました
2024-01-15 10:00:05 - INFO - テクニカルフィルタリングを実行中...
2024-01-15 10:00:06 - INFO - テクニカルフィルター通過: 8銘柄
2024-01-15 10:00:06 - INFO - ファンダメンタルフィルタリングを実行中...
2024-01-15 10:00:15 - INFO - NVDA: CAN-SLIM基準を満たしています
2024-01-15 10:00:15 - INFO - チャートを生成しました: output/chart_NVDA.png
2024-01-15 10:00:16 - INFO - Slackに投稿しました: NVDA
2024-01-15 10:00:20 - INFO - AMD: CAN-SLIM基準を満たしています
2024-01-15 10:00:20 - INFO - チャートを生成しました: output/chart_AMD.png
2024-01-15 10:00:21 - INFO - Slackに投稿しました: AMD
2024-01-15 10:00:30 - INFO - 処理完了 - 処理済み: 30, 適格: 2, スキップ: 0
```

### Slack通知の例

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
  https://...

[チャート画像が添付されます]
```

### エラーハンドリングの例

データ取得に失敗した場合でも、処理は継続されます：

```
2024-01-15 10:00:10 - WARNING - XYZ: 株価データが取得できませんでした。スキップします
2024-01-15 10:00:15 - WARNING - ABC: 財務データが不完全です。スキップします
2024-01-15 10:00:20 - INFO - 処理完了 - 処理済み: 30, 適格: 2, スキップ: 2
```

## GitHub Actions での実行

定期実行を設定する場合は、GitHub Actionsワークフローを使用できます。詳細は`.github/workflows/`を参照してください。

### GitHub Secretsの設定

1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」に移動
2. 「New repository secret」をクリック
3. 以下のシークレットを追加：
   - `SLACK_BOT_TOKEN`: Slack Bot Token
   - `SLACK_CHANNEL`: 通知先チャンネル（例: #stock-alerts）

## ライセンス

MIT License
