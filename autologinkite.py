import time
import json
import pyotp
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs
from kiteconnect import KiteConnect
from keys import *

def automate_login():
    # Step 1: Initialize the Selenium WebDriver
    driver = webdriver.Chrome()  # Ensure ChromeDriver is installed

    # Step 2: Open Zerodha Kite Login Page
    login_url = f'https://kite.trade/connect/login?v=3&api_key={api_key}'
    print(f"🔗 Opening login URL: {login_url}")
    driver.get(login_url)
    time.sleep(3)  # Wait for page to load

    # Step 3: Enter Username & Password
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "userid"))).send_keys(user_id)
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(user_password)

    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    # Wait for OTP field to appear instead of fixed sleep
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number'][id='userid']")))

    # Step 4: Wait for OTP field and enter PyOTP-generated OTP
    otp = pyotp.TOTP(totp_key).now()
    try:
        # Debugging: Print available input fields
        all_fields = driver.find_elements(By.TAG_NAME, "input")
        for field in all_fields:
            print(f"Field Name: {field.get_attribute('name')}, ID: {field.get_attribute('id')}, Type: {field.get_attribute('type')}, Value: {field.get_attribute('value')}")

        otp_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='number'][id='userid']")))
        otp_field.clear()
        otp_field.send_keys(otp)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
    except Exception as e:
        print(f"⚠️ OTP field not found! Error: {str(e)}")
        # Print page source for debugging
        print("\n--- PAGE SOURCE START ---\n")
        print(driver.page_source)
        print("\n--- PAGE SOURCE END ---\n")
        driver.quit()
        return None

    time.sleep(3)  # Wait for OTP authentication

    # Step 5: Capture Redirected URL After Authorization
    final_url = driver.current_url
    print(f"🔗 Final Redirected URL: {final_url}")

    # Step 6: Extract request_token
    query_params = parse_qs(urlparse(final_url).query)
    request_token = query_params.get('request_token', [None])[0]

    if not request_token:
        print("❌ request_token not found! Please manually check the redirected URL.")
        driver.quit()
        return None

    print(f"✅ Found request_token: {request_token}")

    # Step 7: Generate session using request_token
    kite = KiteConnect(api_key=api_key)
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data["access_token"]
        kite.set_access_token(access_token)
    except Exception as e:
        print(f"⚠️ Error generating session: {str(e)}")
        driver.quit()
        return None

    print("✅ Login successful!")
    driver.quit()  # Close browser
    return kite

kite = automate_login()
if kite:
    print("📜 Profile:", kite.profile())
else:
    print("❌ Login failed. Please check the error messages above.")
