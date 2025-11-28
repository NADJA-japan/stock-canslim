# Project Structure

## Directory Layout

```
can-slim-bot/
├── main.py              # エントリーポイント（オーケストレーター）
├── config.py            # 設定値（閾値、APIキー、パラメータ）
├── requirements.txt     # 依存ライブラリ
├── .env                 # 環境変数（LINE_CHANNEL_ACCESS_TOKEN）
├── .env.example         # 環境変数テンプレート
├── README.md            # セットアップ・使用方法
├── tickers.csv          # 対象銘柄リスト（S&P500/Nasdaq100）
│
├── modules/             # コアモジュール
│   ├── __init__.py
│   ├── data_loader.py   # データ取得（yfinance）
│   ├── screener.py      # フィルタリングロジック
│   ├── visualizer.py    # チャート生成（mplfinance）
│   └── notifier.py      # LINE公式アカウント通知
│
├── output/              # 生成チャート画像の一時保存
│   └── .gitkeep
│
└── tests/               # テストコード
    ├── __init__.py
    ├── conftest.py      # pytest設定
    ├── test_data_loader.py
    ├── test_screener.py
    ├── test_visualizer.py
    └── test_notifier.py
```

## Module Organization

### Data Layer
- `data_loader.py`: yfinance APIとのインターフェース、データ取得・変換

### Processing Layer
- `screener.py`: TechnicalFilter、FundamentalFilter、ExitStrategyCalculatorクラス

### Output Layer
- `visualizer.py`: ChartGeneratorクラス
- `notifier.py`: LineNotifierクラス

### Orchestration
- `main.py`: 全体フローの制御、エラーハンドリング、ログ出力

## Key Conventions

- データクラスは各モジュール内で定義（StockData、FinancialMetrics、ExitStrategy、NewsItem）
- 設定値は`config.py`のConfigクラスで管理
- エラーハンドリングは「ログ記録→スキップ→継続」パターン
- API呼び出しは1秒間隔でレート制限対策
