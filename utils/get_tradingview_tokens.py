import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

def extract_tradingview_tokens():
    """Extract all authentication data from a logged-in browser session"""
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        driver.get("https://www.tradingview.com")
        print("Please log in to TradingView...")
        input("After logging in, press Enter to continue...")
        
        # Get all cookies
        cookies = driver.get_cookies()
        
        # Get local storage data
        local_storage = driver.execute_script("""
            let items = {};
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                items[key] = localStorage.getItem(key);
            }
            return items;
        """)
        
        # Extract all relevant authentication data
        auth_data = {
            'cookies': cookies,
            'local_storage': local_storage,
            'session_token': next((c['value'] for c in cookies if c['name'] == 'sessionid'), None),
            'session_signature': next((c['value'] for c in cookies if c['name'] == 'sessionid_sign'), None),
            'device_token': next((c['value'] for c in cookies if c['name'] == 'device_t'), None),
            'user_token': next((c['value'] for c in cookies if c['name'] == 'user_t'), None),
        }
        
        # Save all auth data to file
        with open('tradingview_auth.json', 'w') as f:
            json.dump(auth_data, f, indent=2)
            
        # Save essential tokens to .env.local
        with open('.env.local', 'w') as f:
            for key, value in auth_data.items():
                if key != 'cookies' and key != 'local_storage' and value:
                    f.write(f"TRADINGVIEW_{key.upper()}={value}\n")
        
        print("\nAuth data has been saved to tradingview_auth.json")
        print("Essential tokens have been saved to .env.local")
        print("\nAdd these to your environment variables:")
        for key, value in auth_data.items():
            if key != 'cookies' and key != 'local_storage' and value:
                print(f"TRADINGVIEW_{key.upper()}={value}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    extract_tradingview_tokens()
