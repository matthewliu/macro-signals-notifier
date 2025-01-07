import asyncio
import logging
from pathlib import Path

from api.tradingview_wrapper import TradingViewWrapper
from notifications.source_urls import TECHDEV_METRIC_URLS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chart_capture():
    """Test TradingView chart capture with different URLs"""
    try:
        # Initialize TradingView wrapper
        tv = TradingViewWrapper()
        
        # Create charts directory in project root
        charts_dir = Path("charts/techdev")
        charts_dir.mkdir(parents=True, exist_ok=True)
        
        # Test each TechDev metric URL
        for name, url in TECHDEV_METRIC_URLS.items():
            logger.info(f"\nTesting chart capture for: {name}")
            logger.info(f"URL: {url}")
            
            chart_path = charts_dir / f"{name.replace(' ', '_')}.png"
            
            # Capture chart
            chart_data = await tv.get_chart_image(url)
            
            if chart_data:
                with open(chart_path, "wb") as f:
                    f.write(chart_data)
                logger.info(f"✓ Chart saved to: {chart_path}")
            else:
                logger.error(f"✗ Failed to capture chart")
    
    finally:
        await tv.close()

if __name__ == "__main__":
    asyncio.run(test_chart_capture())
