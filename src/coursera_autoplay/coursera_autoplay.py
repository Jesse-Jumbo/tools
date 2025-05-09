from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tkinter import messagebox
import tkinter as tk
import time
import json
import os
import platform
import re
import sys

MARK_COMPLETE_BTN = "//button[@data-testid='mark-complete']"
NEXT_BTN = "//button[@data-testid='next-item']"
CURRENT_TIME_DISPLAY = "current-time-display"

# 取得目前 Python 檔案所在資料夾
config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

is_first_run = config["is_first_run"]
chrome_binary_path = config["chrome_binary_path"]
chromedriver_path = config["chromedriver_path"]
user_profile_path = os.path.join(os.path.dirname(__file__), "coursera_profile")
# 確保 course_urls 一定是 list
course_urls = config["course_url"]
if isinstance(course_urls, str):
    course_urls = [course_urls]

# ========= 初始索引與總觀看時間 =========
current_course_idx = 0
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

# 首次執行登入
if is_first_run:
    driver.get("https://www.coursera.org/")
    input("👉 請手動登入帳號，完成後按 Enter 結束...")
    driver.quit()
    exit()

def notify(title, message):
    if platform.system() == "Windows":
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=10, threaded=True)
        except Exception:
            print("⚠️ 無法顯示 Windows 通知：", str(e))
            print(f"{title}: {message}")
    else:
        print(f"[通知模擬] {title}: {message}")


def play_notification_sound():
    system = platform.system()
    if system == "Darwin":  # macOS
        os.system("afplay /System/Library/Sounds/Glass.aiff")
    elif system == "Windows":
        import winsound
        winsound.MessageBeep()
    else:
        print("🔕 不支援的作業系統")


# 顯示完成訊息，並切換到下一門課程或結束
def show_completion_message():
    global current_course_idx, total_watch_seconds, is_run
    root = tk.Tk()
    root.withdraw()  # 隱藏主視窗
    minutes = total_watch_seconds // 60
    seconds = total_watch_seconds % 60
    play_notification_sound()

    # 如果還有下一門課程
    if current_course_idx < len(course_urls) - 1:
        print(f"📊 課程 {current_course_idx+1} 完成！總觀看時間：{minutes} 分 {seconds} 秒")
        current_course_idx += 1
        total_watch_seconds = 0  # 重置計時
        next_url = course_urls[current_course_idx]
        print(f"➡️ 自動跳轉至第 {current_course_idx+1} 門課程：{next_url}")
        driver.get(next_url)
        time.sleep(5)
        is_run = True
    else:
        # 最後一門也完成，顯示圖形化訊息後結束
        if platform.system() == "Windows":
            notify("完成所有課程", "🎉 恭喜你完成最後一門課程！")
        else:
            message = f"📊 全部完成！最後一門課程總觀看時間：{minutes} 分 {seconds} 秒"
            try:
                messagebox.showinfo("已完成所有課程", message)
                root.destroy()
            except Exception:
                print(message)

        is_run = False


# ========= 工具函式 =========
def parse_time_string(tstr):
    if not tstr:
        return 0

    # 例子：tstr = "2 minutes 40 seconds"
    minutes = 0
    seconds = 0

    min_match = re.search(r"(\d+)\s*minute", tstr)
    sec_match = re.search(r"(\d+)\s*second", tstr)

    if min_match:
        minutes = int(min_match.group(1))
    if sec_match:
        seconds = int(sec_match.group(1))

    return minutes * 60 + seconds


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


def click_play_button():
    try:
        play_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "rc-PlayToggle"))
        )
        ActionChains(driver).move_to_element(play_button).pause(0.5).click(play_button).perform()
        print("🖱️ 使用 ActionChains 模擬點擊播放按鈕")
        return True
    except Exception as e:
        print("⚠️ 播放按鈕點擊失敗：", str(e))
        return False


# ========= 影片處理 =========
from selenium.webdriver.common.action_chains import ActionChains

def wait_until_video_finished():
    global total_watch_seconds
    print("▶️ 偵測影片是否已在播放中")

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

    # ✅ 初次點擊播放（模擬滑鼠進入 + 點擊）
    print("▶️ 嘗試初次點擊播放")
    try:
        play_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "rc-PlayToggle"))
        )
        ActionChains(driver).move_to_element(play_button).pause(0.5).click(play_button).perform()
        print("⏯️ 已點擊播放按鈕，等待 video 開始播放...")
    except Exception as e:
        print("⚠️ 初次播放等待 video 播放失敗：", str(e))

    last_logged_sec = -1
    playback_stuck_count = 0

    while True:
        time.sleep(2)

        current_str = get_time_str(CURRENT_TIME_DISPLAY)
        if not current_str:
            print("⌛ 等待影片載入中（未取得時間）")
            continue

        current_sec = parse_time_string(current_str)

        # 初期緩衝：影片從非 0 秒開始播放（避免誤判）
        if 0 < current_sec < 5:
            print(f"⏳ 播放初期緩衝中：{current_sec} 秒（不判定卡住）")
            continue

        if current_sec == last_logged_sec:
            playback_stuck_count += 1
            print(f"⏸️ 偵測播放卡住，第 {playback_stuck_count} 次嘗試恢復播放")
            if playback_stuck_count <= 3:
                try:
                    play_button = driver.find_element(By.CLASS_NAME, "rc-PlayToggle")
                    ActionChains(driver).move_to_element(play_button).pause(0.5).click(play_button).perform()
                    print("⏯️ 已重新點擊播放按鈕")
                except Exception as e:
                    print("⚠️ 無法重新點擊播放按鈕：", str(e))
            else:
                print("❌ 多次重試播放失敗，略過本影片")
                return
        else:
            playback_stuck_count = 0

        last_logged_sec = current_sec

        # 🎯 處理 VideoQuiz
        try:
            quiz_container = driver.find_element(By.CLASS_NAME, "rc-VideoQuiz")
            for btn_label in ['Skip', 'Continue']:
                try:
                    quiz_button = quiz_container.find_element(By.XPATH, f".//button[.//span[text()='{btn_label}']]")
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})", quiz_button)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", quiz_button)
                    print(f"⏭️ 已跳過 VideoQuiz（{btn_label}）")
                    break
                except NoSuchElementException:
                    continue
        except NoSuchElementException:
            pass
        except Exception as e:
            print("⚠️ 嘗試處理 quiz 時出現例外：", str(e))

        if abs(current_sec - duration_sec) <= 2:
            print(f"✅ 播放成功完成，當前秒數：{current_sec} / 預期：{duration_sec}")
            break

    total_watch_seconds += duration_sec
    print(f"🎯 本影片播放：{duration_sec} 秒，總觀看時間：{total_watch_seconds // 60} 分 {total_watch_seconds % 60} 秒")

    # 導向下一課程（若有）
    try:
        next_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "start-button"))
        )
        from urllib.parse import urljoin
        next_href = urljoin("https://www.coursera.org", next_link.get_attribute("href"))
        if next_href:
            print(f"➡️ 準備跳轉至下一課程：{next_href}")
            driver.get(next_href)
        else:
            print("⚠️ 找到 start-button 但 href 為空")
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
        show_completion_message()


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
# 先導向第一門課程
driver.get(course_urls[current_course_idx])
time.sleep(5)
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

        # 若 is_run 在 show_completion_message 中被改為 True（切換課程），
        # 迴圈會繼續並自動偵測新的 URL。
        if not is_run:
            break

        # 一般項目跳轉邏輯：若頁面未變，強制重新整理
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
