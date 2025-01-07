from typing import Optional
import logging
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from config.constants import TRADINGVIEW_SESSION_TOKEN, TRADINGVIEW_SESSION_SIGNATURE
import json

logger = logging.getLogger(__name__)

class TradingViewWrapper:
    def __init__(self):
        self.driver = None
        if not TRADINGVIEW_SESSION_TOKEN or not TRADINGVIEW_SESSION_SIGNATURE:
            raise ValueError("TradingView session tokens not found in environment variables")

    def _setup_driver(self):
        """Initialize Chrome driver with complete auth data"""
        chrome_options = Options()
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load saved auth data
        try:
            with open('tradingview_auth.json', 'r') as f:
                auth_data = json.load(f)
            
            # Visit TradingView first
            driver.get("https://www.tradingview.com")
            time.sleep(2)
            
            # Set all cookies
            for cookie in auth_data['cookies']:
                driver.add_cookie(cookie)
            
            # Set local storage data
            for key, value in auth_data['local_storage'].items():
                driver.execute_script(f"localStorage.setItem('{key}', '{value}')")
            
            logger.info("Auth data loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load auth data: {str(e)}")
            raise
        
        return driver

    async def get_chart_image(self, chart_url: str) -> Optional[bytes]:
        """Capture chart screenshot using Selenium"""
        try:
            if not self.driver:
                self.driver = self._setup_driver()

            logger.info(f"Navigating to chart: {chart_url}")
            self.driver.get(chart_url)
            
            # Wait longer for initial load
            time.sleep(10)
            logger.info("Initial page load complete")
            
            # Wait for chart container and indicators
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, "chart-markup-table"))
                )
                logger.info("Chart panels found")
                
                # Additional wait for indicators
                indicators = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "pane-legend-line"))
                )
                logger.info(f"Found {indicators} indicators")
                
            except TimeoutException:
                logger.error("Timeout waiting for chart elements")
                return None
            
            # Clean up UI elements but keep chart intact
            self.driver.execute_script("""
                // Remove only non-essential UI elements
                [
                    '.layout__area--right',
                    '.header-chart-panel',
                    '.control-bar',
                    '.drawing-toolbar',
                    '.chart-controls-bar',
                    '.tv-floating-toolbar'
                ].forEach(selector => {
                    const elements = document.querySelectorAll(selector);
                    elements.forEach(el => el.remove());
                });
            """)
            
            # Wait for final render
            time.sleep(5)
            logger.info("Ready to capture screenshot")
            
            return self.driver.get_screenshot_as_png()

        except Exception as e:
            logger.error(f'Error capturing chart: {str(e)}')
            # Save debug screenshot
            if self.driver:
                self.driver.save_screenshot("error_state.png")
            return None

    async def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
