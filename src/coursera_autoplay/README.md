## 使用說明（Windows 使用者）

1. 安裝 Python 3.x 與 pip。
2. 安裝 Selenium：

3. 下載（須更新你的 Chrome 為最新版）：
- [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
- [ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/)
4. 修改 [coursera_autoplay_config.json](https://github.com/Jesse-Jumbo/tools/tree/main/src/coursera_autoplay/config.json) 中為你的路徑
   - chrome_binary_path
     - Mac 使用者需找到 `Google Chrome for Testing.app` 後點右鍵 → 顯示套件內容），找到 `/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing` 檔
     - windows 使用者則是 `chrome.exe` 檔案即可
5. 初次使用需登入你的 Coursera 帳號，使用完後請輸入 enter 結束程式運行 
6. 然後修改 [coursera_autoplay_config.json](https://github.com/Jesse-Jumbo/tools/tree/main/src/coursera_autoplay_config.json) 中的 `is_first_run` 欄位，為 `false`
6. 最後再次運行程式即可