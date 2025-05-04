from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
import tkinter as tk
import time
import json
import os


MARK_COMPLETE_BTN = "//button[@data-testid='mark-complete']"
NEXT_BTN = "//button[@data-testid='next-item']"

# 取得目前 Python 檔案所在資料夾
config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

is_first_run = config["is_first_run"]
chrome_binary_path = config["chrome_binary_path"]
chromedriver_path = config["chromedriver_path"]
user_profile_path = config["user_profile_path"]
course_url = config["course_url"]


# ========= 總觀看時數 =========
total_watch_seconds = 0

# ========= 初始化 Chrome =========
chrome_options = Options()
chrome_options.binary_location = chrome_binary_path
chrome_options.add_argument(f"--user-data-dir={user_profile_path}")
chrome_options.add_argument("--start-maximized")

try:
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("document.body.style.zoom='80%'")
except Exception as e:
    print(f"❌ 啟動 Chrome 失敗，請檢查路徑是否正確：{str(e)}")
    exit(1)


if is_first_run:
    driver.get("https://www.coursera.org/")
    input("👉 請手動登入帳號，完成後按 Enter 結束...")
    driver.quit()
    exit()

driver.get(course_url)
time.sleep(5)


# 課程完成提示
def show_completion_message():
    global is_run
    root = tk.Tk()
    root.withdraw()  # 隱藏主視窗
    minutes = total_watch_seconds // 60
    seconds = total_watch_seconds % 60
    try:
        messagebox.showinfo("已完成課程", f"📊 完成所有項目！\n總觀看時間：{minutes} 分 {seconds} 秒")
        root.destroy()
    except Exception:
        print(f"📊 完成所有項目！總觀看時間：{minutes} 分 {seconds} 秒")

    is_run = False


# ========= 工具函式 =========
def parse_time_string(tstr):
    if not tstr:
        return 0
    parts = tstr.replace(" seconds", "").replace(" second", "") \
                .replace(" minutes", ":").replace(" minute", ":").split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 1:
            return int(parts[0])
    except Exception as e:
        print("⚠️ 發生錯誤：", str(e))
        return 0
    return 0

def get_time_str(class_name):
    try:
        time_element = driver.find_element(By.CLASS_NAME, class_name)
        return time_element.get_attribute("aria-label")
    except NoSuchElementException:
        return None

def detect_content_type():
    try:
        driver.find_element(By.CLASS_NAME, "vjs-tech")
        print("✅ 這是一個影片頁面")
        return "video"
    except Exception as e:
        print("⚠️ 發生錯誤：", str(e))
        pass
    try:
        driver.find_element(By.CLASS_NAME, "rc-ReadingItem")
        print("✅ 這是一個文章頁面")
        return "article"
    except Exception as e:
        print("⚠️ 發生錯誤：", str(e))
        pass
    print("⚠️ 無法判斷內容型態")
    return "unknown"


def scroll_article_to_bottom():
    try:
        scrollable = driver.find_element(By.ID, "main-container")
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
        print("✅ 成功滑動 #main-container 到最底部")
    except Exception as e:
        print("⚠️ 無法滑動 #main-container：", str(e))



# ========= 影片處理 =========
def wait_until_video_finished():
    global total_watch_seconds
    print("▶️ 開始播放影片")

    try:
        play_button = driver.find_element(By.CLASS_NAME, "rc-PlayToggle")
        play_button.click()
        print("⏯️ 已點擊播放")
    except NoSuchElementException:
        print("⚠️ 找不到播放按鈕")
        return

    # 嘗試取得影片總時長
    for _ in range(10):
        duration_str = get_time_str("duration-display")
        duration_sec = parse_time_string(duration_str)
        if duration_sec > 0:
            break
        elif duration_sec == 0:
            print("⚠️ 擷取到影片時間為 0，可能尚未載入完成")

        time.sleep(1)
    else:
        print("⚠️ 無法擷取影片總長度")
        return

    print(f"📺 影片總時長：{duration_sec} 秒")

    # 影片播放中，每秒檢查進度直到完成
    last_logged_sec = -1
    retry_count = 0
    while True:
        time.sleep(1)

        current_str = get_time_str("current-time-display")
        current_sec = parse_time_string(current_str)

        # ▶️ 若播放秒數未變，試著重新點擊播放按鈕
        if current_sec >= 0 and current_sec == last_logged_sec:
            retry_count += 1
            print(f"⚠️ 播放秒數未變，重試播放 {retry_count}/3")
            try:
                play_button = driver.find_element(By.CLASS_NAME, "rc-PlayToggle")
                driver.execute_script("arguments[0].click();", play_button)
            except Exception as e:
                print("❌ 播放鍵點擊失敗：", str(e))
            time.sleep(1)
            if retry_count >= 3:
                return 0
            continue  # 不記錄這秒，繼續下一秒
        else:
            retry_count = 0  # 秒數有變，清除重試計數

        # 每 10 秒印一次
        if current_sec >= 0 and current_sec != last_logged_sec and current_sec % 10 == 0:
            print(f"⏱️ 目前播放時間：{current_sec} 秒")
            last_logged_sec = current_sec

        # 👉 檢查是否出現 VideoQuiz，點擊 Skip 或 Continue
        try:
            quiz_container = driver.find_element(By.CLASS_NAME, "rc-VideoQuiz")
            try:
                skip_button = quiz_container.find_element(By.XPATH, ".//button[.//span[text()='Skip']]")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", skip_button)
                time.sleep(0.2)
                driver.execute_script("arguments[0].click();", skip_button)
                print("⏭️ 已跳過 VideoQuiz（Skip）")
            except NoSuchElementException:
                try:
                    continue_button = quiz_container.find_element(By.XPATH, ".//button[.//span[text()='Continue']]")
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", continue_button)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].click();", continue_button)
                    print("⏭️ 已跳過 VideoQuiz（Continue）")
                except NoSuchElementException:
                    print("ℹ️ 偵測到 quiz，但無 Skip 或 Continue 按鈕")
            time.sleep(1)
        except NoSuchElementException:
            pass
        except Exception as e:
            print("⚠️ 嘗試處理 quiz 時出現例外：", str(e))

        # ✅ 播放完成檢查
        if abs(current_sec - duration_sec) <= 2:
            print(f"✅ 播放成功完成，當前秒數：{current_sec} / 預期：{duration_sec}")
            break

    total_watch_seconds += duration_sec
    print(f"🎯 本影片播放：{duration_sec} 秒，總觀看時間：{total_watch_seconds // 60} 分 {total_watch_seconds % 60} 秒")

    # ✅ 播放後抓取 <a> 的 href，並跳轉
    try:
        next_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "start-button"))
        )
        from urllib.parse import urljoin

        base_url = "https://www.coursera.org"
        next_href = urljoin(base_url, next_link.get_attribute("href"))
        if next_href:
            print(f"➡️ 準備跳轉至下一課程：{next_href}")
            driver.get(next_href)
        else:
            print("⚠️ 找到 start-button 但 href 為空")
    except NoSuchElementException:
        print("ℹ️ 找不到下一個課程的連結（start-button）")
    except Exception as e:
        print(f"⚠️ 嘗試導向下一課程時出現例外：{str(e)}")


# ========= 文章處理 =========
def complete_article_and_proceed():
    print("📄 偵測為文章，準備標記完成")
    # 滾動到頁面最底部
    scroll_article_to_bottom()

    time.sleep(2)  # 等內容完全載入

    # 👉 等待並點擊 "Mark as completed" 按鈕
    try:
        mark_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, MARK_COMPLETE_BTN)))
        mark_btn.click()
        print("✅ 已點擊 Mark as completed")
    except Exception as e:
        print("⚠️ 無法點擊 Mark as completed：", str(e))

    time.sleep(1)

    # 👉 等待並點擊 "Go to next item" 按鈕
    try:
        next_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, NEXT_BTN))
        )
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", next_btn)
        time.sleep(0.5)

        old_url = driver.current_url
        driver.execute_script("arguments[0].click();", next_btn)
        print("➡️ 已使用 JS 點擊 Go to next item")

        WebDriverWait(driver, 10).until(lambda d: d.current_url != old_url)
    except Exception as e:
        driver.save_screenshot("go_to_next_failed.png")
        print("⚠️ 無法點擊 Go to next item（或頁面未變動）：", str(e))


# ========= 其他類型處理 =========
def handle_other_and_proceed():
    print("📘 非影片或文章類型，嘗試按完成與下一步")
    try:
        mark_btn = driver.find_element(By.XPATH, MARK_COMPLETE_BTN)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", mark_btn)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", mark_btn)
        print("✅ 已點擊 Mark as completed")
    except Exception as e:
        print("⚠️ 發生錯誤：", str(e))
        print("ℹ️ 無完成按鈕，跳過")
    time.sleep(1)
    try:
        next_btn = driver.find_element(By.XPATH, NEXT_BTN)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", next_btn)
        time.sleep(0.3)
        driver.execute_script("arguments[0].click();", next_btn)
        print("➡️ 已點擊 Go to next item")
    except:
        try:
            fallback_btn = driver.find_element(By.XPATH, "//button[@aria-label='Next Item']")
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", fallback_btn)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", fallback_btn)
            print("➡️ 已點擊 Fallback 的 Next 按鈕")
        except Exception as e:
            print("⚠️ 發生錯誤：", str(e))
            show_completion_message()


# ========= 主流程迴圈 =========
is_run = True
try:
    while is_run:
        time.sleep(5)
        content_type = detect_content_type()

        if content_type == "video":
            wait_until_video_finished()
        elif content_type == "article":
            complete_article_and_proceed()
        else:
            handle_other_and_proceed()

        if not is_run:
            break
        prev_url = driver.current_url
        time.sleep(2)
        if driver.current_url == prev_url:
            print("⚠️ 頁面未成功切換，將自動重新整理")
            driver.refresh()
            time.sleep(5)
            continue  # 再跑一次頁面類型判斷
except KeyboardInterrupt:
    print("\n🛑 手動中斷程式")
finally:
    driver.quit()
