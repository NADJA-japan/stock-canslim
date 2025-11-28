# Technical Stack

## Language & Runtime

- Python 3.9+

## Core Dependencies

- **yfinance**: Yahoo Finance APIラッパー（株価・財務データ取得）
- **pandas**: データ処理・分析
- **numpy**: 数値計算
- **mplfinance**: 金融チャート生成
- **requests**: LINE Messaging API統合

## Testing & Quality

- **pytest**: テストフレームワーク
- **hypothesis**: プロパティベーステスト（最低100回反復）

## Execution Environment

**推奨: GitHub Actions**（定期実行 + CI/CD統合）

その他のオプション:
- ローカルPC（開発・テスト用）
- AWS Lambda（必要に応じて検討）

## Common Commands

```bash
# 依存関係のインストール
pip install -r requirements.txt

# テスト実行
pytest

# プロパティベーステスト（CI環境）
pytest --hypothesis-profile=ci

# メインスクリプト実行
python main.py
```

## Configuration

- 設定値は`config.py`で一元管理
- 環境変数は`.env`ファイルで管理（LINE_CHANNEL_ACCESS_TOKEN等）
- スクリーニング閾値は定数として設定可能
