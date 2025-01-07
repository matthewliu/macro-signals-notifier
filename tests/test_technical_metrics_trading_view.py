import asyncio
import logging
from techdev_metrics.one_month_macd_trendline import MACDTrendlineMetric
from techdev_metrics.one_month_cmf import ChaikinMoneyFlowMetric
from techdev_metrics.two_month_macd_histogram import TwoMonthMACDHistogramMetric
from api.tradingview_wrapper import TradingViewWrapper

# Configure logging with a cleaner format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def test_metrics():
    tv_client = TradingViewWrapper()
    
    # Test MACD Trendline
    macd_metric = MACDTrendlineMetric(tv_client)
    macd_status = await macd_metric.get_status()
    
    print("\n=== MACD Trendline Analysis ===")
    print(f"\nMetric Configuration:")
    print(f"  Name: {macd_status['name']}")
    print(f"  Description: {macd_status['description']}")
    print(f"  Reference: {macd_status['reference_urls'][0]}")
    print(f"\nCurrent Status:")
    print(f"  Current Value: {macd_status['current_value']:.4f}")
    print(f"  Trigger Value: {macd_status['trigger_value']:.4f}")
    print(f"  Trigger %: {macd_status['trigger_percentage']:.2f}%")
    print(f"  Is Triggered: {macd_status['is_triggered']}")
    
    # Test MACD Histogram
    hist_metric = TwoMonthMACDHistogramMetric(tv_client)
    hist_status = await hist_metric.get_status()
    
    print("\n=== MACD Histogram Analysis ===")
    print(f"\nMetric Configuration:")
    print(f"  Name: {hist_status['name']}")
    print(f"  Description: {hist_status['description']}")
    print(f"  Reference: {hist_status['reference_urls'][0]}")
    print(f"\nCurrent Status:")
    print(f"  Current Value: {hist_status['current_value']:.4f}")
    print(f"  Trigger Value: {hist_status['trigger_value']:.4f}")
    print(f"  Trigger %: {hist_status['trigger_percentage']:.2f}%")
    print(f"  Is Triggered: {hist_status['is_triggered']}")
    
    # Test CMF
    cmf_metric = ChaikinMoneyFlowMetric(tv_client)
    cmf_status = await cmf_metric.get_status()
    
    print("\n=== Chaikin Money Flow Analysis ===")
    print(f"\nMetric Configuration:")
    print(f"  Name: {cmf_status['name']}")
    print(f"  Description: {cmf_status['description']}")
    print(f"  Reference: {cmf_status['reference_urls'][0]}")
    print(f"\nCurrent Status:")
    print(f"  Current Value: {cmf_status['current_value']:.4f}")
    print(f"  Trigger Value: {cmf_status['trigger_value']:.4f}")
    print(f"  Trigger %: {cmf_status['trigger_percentage']:.2f}%")
    print(f"  Is Triggered: {cmf_status['is_triggered']}")

if __name__ == "__main__":
    asyncio.run(test_metrics())