import time
import random  # 新增隨機模組
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import tkinter as tk
from tkinter import messagebox
import pygame  # 新增pygame模組
import sys  # 用於退出程式

def setup_driver():
    options = Options()
    options.add_argument("--headless")  # 注釋掉這行以禁用無頭模式
    options.add_argument("--disable-gpu")  # 如果系統不支持GPU加速
    options.add_argument("--lang=zh-TW")  # 設置語言為繁體中文
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def play_sound():
    """使用pygame播放音效"""
    pygame.mixer.init()
    pygame.mixer.music.load("rolling_in_the_deep.mp3")  # 確保音檔在程式碼相同目錄下
    pygame.mixer.music.play(-1)  # 無限循環播放音效

def stop_sound():
    """停止播放音效"""
    pygame.mixer.music.stop()

def show_popup_and_exit(driver, message):
    """顯示彈出視窗並退出程序"""
    play_sound()  # 播放提示音效
    root = tk.Tk()
    root.withdraw()  # 隱藏主視窗
    messagebox.showinfo("通知", message)  # 顯示彈出視窗
    stop_sound()  # 關閉彈出視窗後停止播放音效
    root.destroy()
    driver.quit()  # 關閉 Selenium 瀏覽器
    sys.exit()  # 退出程式

def check_course_status_in_same_dept(driver, courses, dept_name):
    # 不再需要重新加載頁面，直接在已加載的頁面中檢查
    for course_code in courses:
        try:
            print(f"嘗試抓取課程狀態 for {course_code}...")
            # 使用更具體的 XPath 來定位特定課程的狀態
            course_xpath = f"//td[contains(text(), '{course_code}')]/following-sibling::td[6]"  # 修改為正確的 XPath 路徑
            course_status_element = driver.find_element(By.XPATH, course_xpath)

            if not course_status_element:
                print("無法找到課程狀態元素，頁面可能尚未加載完全。")
                driver.save_screenshot('error_screenshot_after_load.png')  # 加載後的截圖
                return False

            status_text = course_status_element.text
            print(f"找到的課程狀態文本：{status_text}")
            if "額滿" not in status_text and "full" not in status_text:
                print(f"課程 {course_code} 名額已開放！")
                show_popup_and_exit(driver, f"課程 {course_code} 名額已開放！")  # 彈出提示視窗並退出
                return True  # 不會到達這一行，因為已經退出程式
            print(f"課程 {course_code} 仍然額滿。")

        except Exception as e:
            print(f"檢查過程中出現錯誤：{e}")
            driver.save_screenshot('error_screenshot.png')
            return False

    return False  # 所有課程仍然額滿，返回 False

def job():
    driver = setup_driver()
    
    # 定義需要檢查的科系和課程
    departments_to_check = [
        {
            "dept_code": "B3", 
            "dept_name": "History HIS", 
            "courses": ["B338500", "B331010"]
        },
        {
            "dept_code": "F7", 
            "dept_name": "CSIE", 
            "courses": ["F725000"]
        }
    ]

    for dept in departments_to_check:
        driver.get("https://course.ncku.edu.tw/index.php?c=qry_all")

        # 點擊指定科系按鈕
        try:
            dept_button = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, f"//li[@class='btn_dept' and @data-dept='{dept['dept_code']}']"))
            )
            driver.execute_script("arguments[0].click();", dept_button)  # 使用JavaScript點擊
            print(f"{dept['dept_name']}按鈕點擊成功")

            # 等待新頁面加載完成
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{dept['dept_name']}')]"))
            )
            print(f"{dept['dept_name']}頁面加載完成")

        except Exception as e:
            print(f"無法點擊{dept['dept_name']}按鈕或頁面加載失敗：{e}")
            driver.save_screenshot('error_screenshot.png')
            continue  # 繼續檢查下一個科系

        # 檢查該科系中的所有課程狀態
        if check_course_status_in_same_dept(driver, dept["courses"], dept["dept_name"]):
            driver.quit()
            return

    driver.quit()

# 用 while 迴圈控制執行間隔
while True:
    job()  # 每次執行 job()
    wait_time = random.randint(10, 30)  # 隨機等待10到30秒
    print(f"等待 {wait_time} 秒後重新檢查...")
    time.sleep(wait_time)
