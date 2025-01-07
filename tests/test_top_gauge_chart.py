import asyncio
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from api.tradingview_wrapper import TradingViewWrapper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOP_GAUGE_URL = "https://www.tradingview.com/chart/DU9F778n/"

class HeadedTradingViewWrapper(TradingViewWrapper):
    def _setup_driver(self):
        """Initialize Chrome driver with visible browser"""
        chrome_options = Options()
        # Remove headless mode
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

async def test_top_gauge_chart():
    """Test Top Gauge chart capture specifically"""
    try:
        # Initialize wrapper with visible browser
        tv = HeadedTradingViewWrapper()
        
        # Create charts directory
        charts_dir = Path("charts/debug")
        charts_dir.mkdir(parents=True, exist_ok=True)
        
        chart_path = charts_dir / "2W_Top_Gauge_debug.png"
        
        logger.info("Capturing Top Gauge chart...")
        chart_data = await tv.get_chart_image(TOP_GAUGE_URL)
        
        if chart_data:
            with open(chart_path, "wb") as f:
                f.write(chart_data)
            logger.info(f"✓ Chart saved to: {chart_path}")
        else:
            logger.error("✗ Failed to capture chart")
            
        # Keep browser open for inspection
        input("Press Enter to close the browser...")
    
    finally:
        await tv.close()

if __name__ == "__main__":
    asyncio.run(test_top_gauge_chart())
