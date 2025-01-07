from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import os
import json

def capture_tradingview_chart():
    """
    Loads TradingView chart and captures a screenshot using Selenium
    """
    print('📸 Capturing TradingView chart...')
    
    # Configure Chrome options
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Initialize the Chrome driver from current directory
    chromedriver_path = os.path.join(os.getcwd(), 'chromedriver')
    service = Service(chromedriver_path)  # Use local path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # First navigate to tradingview.com domain to set cookies
        driver.get('https://www.tradingview.com')
        
        # Load cookies from JSON file
        # export your cookies using the EditThisCookie extension
        with open('cookies.json', 'r') as f:
            cookies = json.load(f)
        
        # Add all cookies
        for cookie in cookies:
            driver.add_cookie(cookie)
            
        # Now load the TradingView chart
        driver.get('https://www.tradingview.com/chart/urBxMZsa/')
        
        # Wait for chart to load (adjust timeout as needed)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'chart-container'))
        )
        
        # Give extra time for chart animations to complete
        time.sleep(5)
        
        # Take screenshot
        driver.save_screenshot('tradingview_chart.png')
        print('✅ Screenshot saved as tradingview_chart.png')
        
    except Exception as e:
        print(f'❌ Error capturing screenshot: {str(e)}')
        
    finally:
        driver.quit()

if __name__ == '__main__':
    capture_tradingview_chart()
