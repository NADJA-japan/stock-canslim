"""
CAN-SLIM US Stock Hunter スクリーニングモジュールのテスト

このモジュールは以下のクラスをテストします：
- TechnicalFilter
- FundamentalFilter
- ExitStrategyCalculator
"""

import pytest
from modules.screener import FundamentalFilter
from config import Config


class TestFundamentalFilter:
    """FundamentalFilterクラスのテスト"""
    
    @pytest.fixture
    def filter(self):
        """テスト用のFundamentalFilterインスタンスを作成"""
        return FundamentalFilter(Config())
    
    def test_check_current_earnings_eps_growth_passes(self, filter):
        """EPS成長率が20%以上の場合、現在収益基準を満たす"""
        financial_data = {
            'quarterly_eps': [1.25, 1.10, 1.05, 1.00, 1.00],  # 25%成長
            'quarterly_revenue': [100, 95, 90, 85, 90]  # 11%成長（閾値未満）
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is True
        assert eps_growth == pytest.approx(0.25, abs=0.01)
    
    def test_check_current_earnings_revenue_growth_passes(self, filter):
        """売上成長率が20%以上の場合、現在収益基準を満たす"""
        financial_data = {
            'quarterly_eps': [1.00, 0.95, 0.90, 0.85, 1.00],  # 0%成長
            'quarterly_revenue': [120, 110, 105, 100, 100]  # 20%成長
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is True
        assert revenue_growth == pytest.approx(0.20, abs=0.01)
    
    def test_check_current_earnings_both_fail(self, filter):
        """EPS成長率も売上成長率も20%未満の場合、現在収益基準を満たさない"""
        financial_data = {
            'quarterly_eps': [1.10, 1.05, 1.00, 0.95, 1.00],  # 10%成長
            'quarterly_revenue': [110, 105, 100, 95, 100]  # 10%成長
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is False
        assert eps_growth == pytest.approx(0.10, abs=0.01)
        assert revenue_growth == pytest.approx(0.10, abs=0.01)
    
    def test_check_current_earnings_insufficient_data(self, filter):
        """データが不足している場合、現在収益基準を満たさない"""
        financial_data = {
            'quarterly_eps': [1.20, 1.10],  # データ不足
            'quarterly_revenue': [120, 110]  # データ不足
        }
        
        passes, eps_growth, revenue_growth = filter.check_current_earnings(financial_data)
        
        assert passes is False
        assert eps_growth == 0.0
        assert revenue_growth == 0.0
    
    def test_check_annual_earnings_passes(self, filter):
        """ROEが15%以上の場合、年間収益基準を満たす"""
        financial_data = {
            'roe': 0.20  # 20%
        }
        
        passes, roe = filter.check_annual_earnings(financial_data)
        
        assert passes is True
        assert roe == 0.20
    
    def test_check_annual_earnings_fails(self, filter):
        """ROEが15%未満の場合、年間収益基準を満たさない"""
        financial_data = {
            'roe': 0.10  # 10%
        }
        
        passes, roe = filter.check_annual_earnings(financial_data)
        
        assert passes is False
        assert roe == 0.10
    
    def test_check_annual_earnings_no_data(self, filter):
        """ROEデータがない場合、年間収益基準を満たさない"""
        financial_data = {}
        
        passes, roe = filter.check_annual_earnings(financial_data)
        
        assert passes is False
        assert roe == 0.0
    
    def test_is_qualified_both_criteria_pass(self, filter):
        """C基準とA基準の両方を満たす場合、適格と判定される"""
        financial_data = {
            'quarterly_eps': [1.20, 1.10, 1.05, 1.00, 1.00],  # 20%成長
            'quarterly_revenue': [120, 110, 105, 100, 100],  # 20%成長
            'roe': 0.20,  # 20%
            'sector': 'Technology',
            'industry': 'Software'
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is True
        assert metrics['eps_growth_q'] == pytest.approx(0.20, abs=0.01)
        assert metrics['revenue_growth_q'] == pytest.approx(0.20, abs=0.01)
        assert metrics['roe'] == 0.20
        assert metrics['sector'] == 'Technology'
        assert metrics['industry'] == 'Software'
    
    def test_is_qualified_current_fails(self, filter):
        """C基準を満たさない場合、適格と判定されない"""
        financial_data = {
            'quarterly_eps': [1.10, 1.05, 1.00, 0.95, 1.00],  # 10%成長
            'quarterly_revenue': [110, 105, 100, 95, 100],  # 10%成長
            'roe': 0.20  # 20%
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is False
    
    def test_is_qualified_annual_fails(self, filter):
        """A基準を満たさない場合、適格と判定されない"""
        financial_data = {
            'quarterly_eps': [1.20, 1.10, 1.05, 1.00, 1.00],  # 20%成長
            'quarterly_revenue': [120, 110, 105, 100, 100],  # 20%成長
            'roe': 0.10  # 10%
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is False
    
    def test_is_qualified_both_fail(self, filter):
        """C基準とA基準の両方を満たさない場合、適格と判定されない"""
        financial_data = {
            'quarterly_eps': [1.10, 1.05, 1.00, 0.95, 1.00],  # 10%成長
            'quarterly_revenue': [110, 105, 100, 95, 100],  # 10%成長
            'roe': 0.10  # 10%
        }
        
        is_qualified, metrics = filter.is_qualified(financial_data)
        
        assert is_qualified is False
