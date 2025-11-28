# CAN-SLIM US Stock Hunter

米国株式市場から成長株を自動的にスクリーニングし、LINE公式アカウントに通知するPythonアプリケーションです。

## 概要

William O'NeilのCAN-SLIM基準を満たす銘柄を効率的に発見し、投資家に視覚的なチャートと主要指標を提供します。

## 主な機能

- S&P500/Nasdaq100銘柄の2段階スクリーニング（テクニカル→ファンダメンタル）
- 自動チャート生成（ローソク足、移動平均線、出来高）
- Exit戦略の自動計算（利益確定20%、損切り7%）
- LINE公式アカウント統合による即座の通知
- 企業情報とニュースの自動収集

## セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、LINE Channel Access Tokenを設定します：

```bash
cp .env.example .env
```

`.env`ファイルを編集：

```
LINE_CHANNEL_ACCESS_TOKEN=your-actual-line-channel-access-token
```

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
│   └── notifier.py      # LINE公式アカウント通知
├── output/              # チャート画像保存先
└── tests/               # テストコード
```

## 設定のカスタマイズ

`config.py`で以下の設定をカスタマイズできます：

- スクリーニング閾値（最低株価、出来高、成長率など）
- Exit戦略パラメータ（利益確定、損切り）
- LINE通知設定
- データ取得期間

## GitHub Actions での実行

定期実行を設定する場合は、GitHub Actionsワークフローを使用できます。詳細は`.github/workflows/`を参照してください。

## ライセンス

MIT License
