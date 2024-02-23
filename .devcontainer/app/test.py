import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time
import uuid
import os
import signal
from flask import Flask, request, jsonify
import threading
import queue
if os.name != 'nt':  # nix system
    signal.signal(signal.SIGCLD, signal.SIG_IGN)

# 定义队列和队列长度
q = queue.Queue(maxsize=5)
# 在后台线程中运行函数并将结果存储到队列中
def worker():
    # 填满队列
    while not q.full():
        result = bypass_clf()
        if result is not None and result != '':
            q.put(result)

    # 当队列不满时，继续添加元素
    while True:
        time.sleep(0.001)
        if not q.full():
            result = bypass_clf()
            if result is not None and result != '':
                q.put(result)

def bypass_clf(xff=None):
    options = uc.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--auto-open-devtools-for-tabs')
    driver = uc.Chrome(options=options)
    driver.execute_cdp_cmd('Network.enable', {})
    if xff:
        driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'X-Forwarded-For': xff}})
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'})
    driver.execute_script(f'window.open("https://www.bing.com/turing/captcha/challenge?q=&iframeid=local-gen-{uuid.uuid4()}","_blank");') # open page in new tab
    time.sleep(random.uniform(10,15))  # wait until page has loaded
    try:
        driver.switch_to.window(window_name=driver.window_handles[0])   # print("switch to first tab")
        driver.close()  # close first tab
        driver.switch_to.window(window_name=driver.window_handles[0])  # switch back to new tab
        #print(driver.page_source)
        if not any(item['name'] == 'cct' for item in driver.get_cookies()):
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if len(iframes)>0:
                driver.switch_to.frame(0)
            print("页面加载完成")
            check_mark = driver.find_element(By.ID, "challenge-stage").find_element(By.CLASS_NAME,"ctp-checkbox-container").find_element(By.CLASS_NAME, "ctp-checkbox-label").find_element(By.CSS_SELECTOR, "input")
            print("查找到勾选框")
            check_mark.click()
            print("点击勾选框")
            time.sleep(random.uniform(3, 5))
            driver.switch_to.default_content()
            print("切回默认")
            time.sleep(random.uniform(1, 2))
    except:
        pass
    finally:
        try:
            cookie_Verified=driver.get_cookies()
            cookie_Verified=[{"name": cookie["name"], "value": cookie["value"]} for cookie in cookie_Verified]
            if any(item['name'] == 'cct' for item in cookie_Verified):
                print("验证成功")
                print(cookie_Verified)
                cookie_Verified = '; '.join(f"{item['name']}={item['value']}" for item in cookie_Verified)
            else:
                print("验证失败")
                cookie_Verified = ''
        except:
            print("验证失败")
            cookie_Verified = ''
        try:
            driver.close()
        except:
            pass
        driver.quit()
        return cookie_Verified

app = Flask(__name__)

@app.route('/postdata', methods=['POST'])
def handle_post():
    # 检查请求是否包含JSON数据
    if request.is_json:
        # 获取JSON数据
        data = request.get_json()

        # 这里可以对数据进行处理
        # 例如：data_processed = process(data)
        # 返回一个JSON响应
        if not q.empty():
            cookies = q.get()
            return jsonify({"error": None, "result": {"cookies": cookies}}), 200
        return jsonify({"error": "failed"}), 500
    else:
        return jsonify({"error": "Request must be JSON"}), 400


if __name__ == '__main__':
    # 启动后台线程
    t = threading.Thread(target=worker)
    t.start()
    app.run(host='0.0.0.0', port=8080)
    #bypass_clf()
