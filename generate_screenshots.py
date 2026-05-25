import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def run_screenshot_suite():
    print("==================================================")
    print("   Starting Automated NewsHub Screenshot Suite    ")
    print("==================================================")
    
    # 1. Setup Headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    
    # Ensure folders exist
    os.makedirs("screenshots_linkedin", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    
    try:
        # --- STEP 1: Register Page (Step 1: Identity) ---
        print("\n[Step 1] Capturing Register Feature (Identity Form)...")
        driver.get("http://localhost:4200/register")
        time.sleep(2)
        
        # Populate Register Form fields
        name_input = driver.find_element(By.NAME, "name")
        email_input = driver.find_element(By.NAME, "email")
        pass_input = driver.find_element(By.NAME, "password")
        confirm_input = driver.find_element(By.NAME, "confirmPassword")
        
        name_input.send_keys("Aziz Benslimen")
        email_input.send_keys("aziz@newshub.com")
        pass_input.send_keys("Password123!")
        confirm_input.send_keys("Password123!")
        
        time.sleep(1)
        driver.save_screenshot("screenshots_linkedin/01_register_identity.png")
        driver.save_screenshot("screenshots/01_register_page.png")
        print("-> Saved Register Page Step 1 (Identity).")
        
        # Click Continue to Step 2 (Interests Selection)
        continue_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", continue_btn)
        time.sleep(2)
        
        # --- STEP 2: Register Page (Step 2: Interests) ---
        print("\n[Step 2] Capturing Register Feature (Interests Form)...")
        # Find interest boxes and click a few of them
        interest_boxes = driver.find_elements(By.XPATH, "//div[contains(@class, 'border rounded')]")
        clicked = 0
        for box in interest_boxes:
            text = box.text.strip()
            if text in ["Technology", "Science", "Business"]:
                driver.execute_script("arguments[0].click();", box)
                print(f"   Checked interest: {text}")
                clicked += 1
                if clicked >= 3:
                    break
        
        time.sleep(1)
        driver.save_screenshot("screenshots_linkedin/02_register_interests.png")
        print("-> Saved Register Page Step 2 (Interests Selection).")
        
        # --- STEP 3: Login as Premium Editor ---
        print("\n[Step 3] Logging in as Premium Editor...")
        driver.get("http://localhost:4200/login")
        time.sleep(2)
        
        email_login = driver.find_element(By.NAME, "email")
        pass_login = driver.find_element(By.NAME, "password")
        
        email_login.send_keys("alex@newshub.com")
        pass_login.send_keys("Password123!")
        
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].click();", login_btn)
        time.sleep(3) # Wait for login transition and redirection
        
        # --- STEP 4: Home News Feed (Live Home Page) ---
        print("\n[Step 4] Capturing Live Home Page Feed...")
        driver.get("http://localhost:4200/")
        time.sleep(4) # Wait for articles to load from NewsData API
        
        driver.save_screenshot("screenshots_linkedin/03_home_feed.png")
        driver.save_screenshot("screenshots/03_home_feed.png")
        print("-> Saved Live Home Page Feed.")
        
        # --- STEP 5: Live Stream Hub (Live Hub / Live Room List) ---
        print("\n[Step 5] Capturing Live Stream Hub Page...")
        driver.get("http://localhost:4200/live")
        time.sleep(3)
        
        driver.save_screenshot("screenshots_linkedin/04_live_stream_hub.png")
        driver.save_screenshot("screenshots/04_filtered_feed.png") # (Optionally reuse filtered slot or save custom)
        print("-> Saved Live Stream Hub (Live Home).")
        
        # --- STEP 6: Article Details & Comments Section ---
        print("\n[Step 6] Navigating to article and posting comment...")
        driver.get("http://localhost:4200/")
        time.sleep(3)
        
        # Get first article link and go to it directly
        first_article = driver.find_element(By.CSS_SELECTOR, "article.news-card a")
        href = first_article.get_attribute("href")
        print(f"   Navigating directly to: {href}")
        driver.get(href)
        time.sleep(3)
        
        # Scroll to Comments Section
        comments_heading = driver.find_element(By.ID, "comments-heading")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comments_heading)
        time.sleep(1)
        
        # Type and post a comment
        comment_input = driver.find_element(By.CLASS_NAME, "comment-input")
        comment_input.clear()
        comment_input.send_keys("This is a remarkable feature implementation. The combination of clean layout with real-time updates and seamless WebRTC streaming represents a fantastic engineering standard! 🚀")
        
        # Scroll slightly to show text input and button
        time.sleep(1)
        driver.save_screenshot("screenshots_linkedin/05_comment_typing.png")
        
        post_btn = driver.find_element(By.CSS_SELECTOR, ".comment-box button")
        driver.execute_script("arguments[0].click();", post_btn)
        time.sleep(2) # Wait for comment to post
        
        # Center comment section for final screenshot
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", comments_heading)
        time.sleep(1)
        driver.save_screenshot("screenshots_linkedin/06_comments_section.png")
        driver.save_screenshot("screenshots/06_comments_section.png")
        print("-> Saved Comments Feature Screenshot.")
        
        # --- STEP 7: Premium AI Chatbot (Qwen3 Assistant Panel) ---
        print("\n[Step 7] Capturing Premium AI Chatbot feature...")
        # Scroll to the chatbot panel
        # The chatbot panel template has selector app-article-assistant-panel
        assistant_panel = driver.find_element(By.CSS_SELECTOR, "app-article-assistant-panel")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", assistant_panel)
        time.sleep(1)
        
        # Find the quick prompt button for summary and click it
        # Quick prompts are in button tags inside the panel
        quick_btns = driver.find_elements(By.CSS_SELECTOR, "app-article-assistant-panel button")
        summary_btn = None
        for btn in quick_btns:
            if "Summarize" in btn.text:
                summary_btn = btn
                break
        
        if summary_btn:
            driver.execute_script("arguments[0].click();", summary_btn)
            print("   Clicked quick prompt: 'Summarize this article.'")
        else:
            # Fallback typing in assistant text area
            chat_area = driver.find_element(By.CSS_SELECTOR, "app-article-assistant-panel textarea")
            chat_area.send_keys("Summarize this article.")
            send_btn = driver.find_element(By.CSS_SELECTOR, "app-article-assistant-panel button.btn-dark") # Dark send button
            driver.execute_script("arguments[0].click();", send_btn)
            print("   Typed and sent: 'Summarize this article.'")
            
        time.sleep(3) # Wait for the AI mock response to render
        
        # Recenter assistant panel
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", assistant_panel)
        time.sleep(1)
        
        driver.save_screenshot("screenshots_linkedin/09_chatbot_unlocked.png")
        driver.save_screenshot("screenshots/09_chatbot_unlocked.png")
        print("-> Saved Premium AI Chatbot.")
        
        # --- STEP 8: Profile page ---
        print("\n[Step 8] Capturing Profile Page...")
        driver.get("http://localhost:4200/profile")
        time.sleep(3)
        
        driver.save_screenshot("screenshots_linkedin/07_profile_management.png")
        driver.save_screenshot("screenshots/07_profile_management.png")
        print("-> Saved Profile Management.")
        
        print("\n==================================================")
        print("   All screenshots captured successfully!         ")
        print("==================================================")
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred during automation: {e}")
        # Capture error state if possible
        try:
            driver.save_screenshot("screenshots_linkedin/error_state.png")
            print("-> Saved error state screenshot to screenshots_linkedin/error_state.png")
        except:
            pass
    finally:
        driver.quit()

if __name__ == "__main__":
    run_screenshot_suite()
