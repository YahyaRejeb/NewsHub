import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test():
    print("Initializing Chrome driver...")
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=options)
    try:
        print("Navigating to http://localhost:4200/ ...")
        driver.get("http://localhost:4200/")
        time.sleep(3)
        print("Taking screenshot...")
        os.makedirs("screenshots_updated", exist_ok=True)
        driver.save_screenshot("screenshots_updated/test_home.png")
        print("Screenshot saved to screenshots_updated/test_home.png")
    finally:
        driver.quit()

if __name__ == "__main__":
    test()
