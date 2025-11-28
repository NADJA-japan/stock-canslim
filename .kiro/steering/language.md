# 言語設定

## 応答言語

**すべての応答とアウトプットは日本語で行ってください。**

- チャットでの会話は日本語で行う
- コードコメントは日本語で記述する
- ドキュメント（README、設計書など）は日本語で記述する
- ログメッセージは日本語で記述する
- エラーメッセージは日本語で記述する
- テストの説明やdocstringは日本語で記述する

## 例外

以下の場合は英語を使用してください：

- 変数名、関数名、クラス名（Pythonの命名規則に従う）
- ライブラリやフレームワークの公式名称
- 技術用語で日本語訳が不自然な場合（例：API、URL、JSON）
- コード内の文字列リテラルで英語が適切な場合（例：ログレベル "INFO", "ERROR"）

## コードスタイル

```python
# 良い例：日本語コメント、英語の変数名
def calculate_profit_target(current_price: float) -> float:
    """
    利益確定目標価格を計算する
    
    Args:
        current_price: 現在の株価
        
    Returns:
        利益確定目標価格（現在価格の120%）
    """
    return current_price * 1.20

# 悪い例：英語コメント
def calculate_profit_target(current_price: float) -> float:
    """
    Calculate profit target price
    
    Args:
        current_price: Current stock price
        
    Returns:
        Profit target price (120% of current price)
    """
    return current_price * 1.20
```

## ユーザーとのコミュニケーション

- ユーザーが日本語で質問した場合、必ず日本語で応答する
- 技術的な説明も日本語で行う
- エラーや問題が発生した場合も日本語で説明する
- 実装の進捗報告も日本語で行う
