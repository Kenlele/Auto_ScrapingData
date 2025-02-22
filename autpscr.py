import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO

#安裝要求：
"""如果你第一次用就在終端機輸入: pip install selenium webdriver-manager requests pillow
"""

# 設定 Selenium
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
# options.add_argument("--headless")  # 測試時請關閉 headless

# 啟動 Chrome 瀏覽器
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# 目標網站
url = "https://archive.org/details/sovereignrightst0000suga/mode/2up"  ##在""裡面換想要的網址
driver.get(url)
time.sleep(5)  # 初始等待

# 建立儲存資料夾
save_folder = "bookkkkkkkkk" ##這裡你不需要特別先去設立資料夾,只要輸入你想要取名的資料夾名稱就好 他會自動幫你建立並把圖片都放進去,建議英文
if not os.path.exists(save_folder):
    os.makedirs(save_folder)

# 建立 Log 檔案
log_file = "log.txt"
with open(log_file, "w") as log:
    log.write("爬蟲錯誤紀錄:\n")

# 記錄已下載的圖片 URL，避免重複下載
downloaded_images = set()

# 設定 headers，隨機 `User-Agent`
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# 自動翻頁 & 抓取圖片
page = 1
while True:
    try:
        # 🔹 增加等待時間，確保圖片完全加載
        delay = random.uniform(7, 12)
        print(f"⏳ 翻頁等待 {round(delay, 2)} 秒...")
        time.sleep(delay)

        # 🔹 等待圖片元素載入
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "BRpageimage"))
        )
        img_elements = driver.find_elements(By.CLASS_NAME, "BRpageimage")

        # 🔹 下載所有圖片（確保不下載重複的）
        for index, img_element in enumerate(img_elements):
            img_url = img_element.get_attribute("src")

            if not img_url or img_url.strip() == "":
                print(f"⚠️ [Page {page}] 找到的圖片網址為空，跳過...")
                continue

            if img_url not in downloaded_images:
                downloaded_images.add(img_url)  # 記錄已下載的圖片

                headers = {
                    "User-Agent": random.choice(user_agents)
                }

                try:
                    response = requests.get(img_url, headers=headers, timeout=10)
                    response.raise_for_status()  # 確保 HTTP 200 OK
                    image = Image.open(BytesIO(response.content))

                    # 🔹 自動判斷圖片格式
                    img_format = image.format  # 取得圖片格式 (JPEG, PNG, GIF)
                    img_ext = img_format.lower()  # 轉換為小寫副檔名

                    # 如果是 PNG 或 GIF，直接存檔
                    if img_format in ["PNG", "GIF"]:
                        img_path = os.path.join(save_folder, f"page_{page}_{index}.{img_ext}")
                        image.save(img_path, img_format)
                        print(f"✅ [Page {page}] 下載成功 (格式: {img_format}): {img_path}")

                    else:
                        # 🔹 若為 P (Palette-based)，轉為 RGB 再存 JPEG
                        if image.mode != "RGB":
                            image = image.convert("RGB")

                        img_path = os.path.join(save_folder, f"page_{page}_{index}.jpg")
                        image.save(img_path, "JPEG")
                        print(f"✅ [Page {page}] 下載成功 (格式: JPEG): {img_path}")

                except requests.exceptions.RequestException as e:
                    print(f"❌ [Page {page}] 無法下載圖片: {img_url}, 錯誤: {e}")
                    with open(log_file, "a") as log:
                        log.write(f"❌ [Page {page}] 無法下載圖片: {img_url}, 錯誤: {e}\n")
                    continue
                except Exception as e:
                    print(f"❌ [Page {page}] 圖片存儲失敗: {img_url}, 錯誤: {e}")
                    with open(log_file, "a") as log:
                        log.write(f"❌ [Page {page}] 圖片存儲失敗: {img_url}, 錯誤: {e}\n")
                    continue

        # 🔹 翻頁機制（按鈕點擊 or 鍵盤翻頁）
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button.br-bookpage-next")
            driver.execute_script("arguments[0].scrollIntoView();", next_button)
            next_button.click()
            print(f"🔹 點擊「下一頁」按鈕，翻到第 {page+1} 頁")
        except:
            body = driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ARROW_RIGHT)
            print(f"🔹 使用鍵盤翻頁，翻到第 {page+1} 頁")

        page += 1

    except Exception as e:
        print(f"⚠️ 發生錯誤: {e}")
        with open(log_file, "a") as log:
            log.write(f"⚠️ 發生錯誤 (Page {page}): {e}\n")
        print(f"🚀 爬取結束，總共抓取 {page-1} 頁")
        break  # 退出爬蟲

# 關閉瀏覽器
driver.quit()