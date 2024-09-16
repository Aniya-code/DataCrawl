import subprocess
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from datetime import datetime
import time,os,gc
from tqdm import tqdm
import csv,json


def load_cookies(driver):
    """
    从指定的 JSON 文件加载 cookies，并添加到当前的 WebDriver 会话中。
    
    参数:
    driver: Selenium WebDriver 实例
    cookies_file: 包含 cookies 的 JSON 文件的路径
    """
    with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
        for cookie in cookies:
            if 'sameSite' in cookie:
                del cookie['sameSite']
            driver.add_cookie(cookie)

def get_chrome_options(resolution, is_quic=False):
    chrome_options =  webdriver.ChromeOptions()
    if is_quic:
        chrome_options.add_argument('--enable-quic') # 是否启用quic

    chrome_options.add_argument("--auto-open-devtools-for-tabs")  # 打开开发者模式
    chrome_options.add_argument(f"load-extension=E:/ZLJ_code/yt-url-har-pcap/plugin/{resolution}fjdmkanbdloodhegphphhklnjfngoffa/1.5_0")  # 加载插件，win/linux均通过测试
    # chrome_options.add_argument(f"--user-data-dir={os.path.join(CUR_ABS_PATH, 'chrome_user_data')}")  # 必要時使用，由於緩存，容易觸發廣告
    
    chrome_options.add_experimental_option("prefs", {
	'download.default_directory': DEFAULT_DOWN_PATH,  # 设置默认下载路径
    # 'devtools.preferences.panel-selectedTab': '"network"', # 设置默认devtools-panel 理论正确但是doesn't work
    "devtools.preferences.currentDockState": '"bottom"',
    })
    chrome_options.add_argument("--lang=en-US")
    # chrome_options.binary_location = CHROME_PATH # only for remote test \\192.168.107.62\c
    return chrome_options

def start_chrome(chrome_options):
    # driver = webdriver.Chrome(options=chrome_options, service=Service(CHROMEDRIVER_PATH))
    # #, executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver'
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_position(0, 0) # left top
    driver.set_window_size(width=1000, height=800) # 
    # driver.maximize_window()
    print(driver.get_window_size())
    return driver

def execution_time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper

@execution_time_decorator
def switchto_network_and_filter():
    try:
        pyautogui.click(pyautogui.locateCenterOnScreen(r'png\play.png', confidence=0.85))
    except Exception as e:
        print("=-=【video-auto-played】=-=")
    try:
        time.sleep(3) # sometimes 播放器會變形一下 需要等一等再定位
        pyautogui.click(pyautogui.locateCenterOnScreen(r'png\1.png', confidence=0.8))  # 更多
        time.sleep(0.2)
        pyautogui.click(pyautogui.locateCenterOnScreen(r'png\2.png', confidence=0.8))  # 点击Network标签
    except Exception as e:
        pyautogui.click(pyautogui.locateCenterOnScreen(r'png\2_.png', confidence=0.8))  # 点击Network标签
    finally:
        try:
            pyautogui.click(pyautogui.locateCenterOnScreen(r'png\clear_filter.png', confidence=0.8))
        except: pass
        # except Exception as e:
        #     pyautogui.click(pyautogui.locateCenterOnScreen(r'png\filter.png', confidence=0.7))
        finally:
            time.sleep(0.5)
            pyautogui.write('videoplayback', interval=0.1)  # 输入筛选条件
            pyautogui.hotkey('enter')

def _get_duration_text(driver):
    return driver.find_element(By.CSS_SELECTOR, '#movie_player > div.ytp-chrome-bottom > div.ytp-chrome-controls > div.ytp-left-controls > div.ytp-time-display.notranslate > span:nth-child(2) > span.ytp-time-duration') or driver.find_element(By.XPATH, '//*[@id="movie_player"]/div[28]/div[2]/div[1]/div[1]/span[2]/span[3]') or driver.find_element(By.XPATH, '//span[starts-with(@class,"ytp-time-duration")]/text()')

@execution_time_decorator
def get_wait_second():
    while not (duration_text:=_get_duration_text(driver).text):
        ...
    h_m_s = duration_text.split(":")
    if len(h_m_s) == 2:
        h_m_s.insert(0, 0)
    h_m_s = list(map(int, h_m_s))
    duration = h_m_s[-1] + h_m_s[-2]*60 + h_m_s[-3]*3600
    return int(duration)-10


def subprocess_stdio_has_kw(process_pointer, keywords, try_lines=-1, decoding='utf8'):
    '''
        实时监测子进程是否在stdio中打印了指定关键字，包括stdout、stderr。
        @try_lines 尝试监测的输出行数，-1表示无限轮询
    '''
    import sys
    while try_lines == -1 or try_lines > 0:
        sys.stderr.flush()
        sys.stdout.flush()
        out = process_pointer.stderr or process_pointer.stdout
        if out and keywords in out.readline().decode(decoding):
            return True
        
        if try_lines > 0:
            try_lines -= 1
    
    return False


def export_har_file(dir_name, file_name):
    

    pyautogui.click(pyautogui.locateCenterOnScreen(r'png\save_har.png', confidence=0.85))  # >=0.8
    time.sleep(2)
    file_fullname = os.path.join(DEFAULT_DOWN_PATH, dir_name, file_name)
    if not os.path.exists(file_fullname):
        pyautogui.write(os.path.join(dir_name, file_name)) 
        time.sleep(0.5)
        pyautogui.press('enter')  # 保存文件
        time.sleep(3)

def capture_traffic(tshark_path, interface, pcap_path, pcap_name, loopcount=1):
    if not os.path.exists(pcap_path):
        os.makedirs(pcap_path)

    pcap_fullname = os.path.join(pcap_path, pcap_name)

    for _ in range(loopcount):
        tshark_cmd = [tshark_path, "-F", "pcap", "-i", interface, "-w", pcap_fullname]
        tshark_process = subprocess.Popen(tshark_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, executable=tshark_path)
        if subprocess_stdio_has_kw(tshark_process, "Capturing"):
            yield
        tshark_process.kill()
        time.sleep(1)
        print(f'-Catpured: {pcap_fullname}')

if __name__ == '__main__':
    ###########修改默认分辨率 1.here  2.content.js; ENUS###########
    TSHARK_PATH = r'E:\Wireshark\tshark.exe'
    COOKIE_FILE = r'data\cookie\youtube_cookies.json'

    # protocal = "tls" # 二选一 
    protocal = "quic"
    RESOLUTION = '720'
    DEFAULT_SECONDS = 60*5 # 默认采集前xx秒***
    INTERFACE = 'localnet'

    # CUR_ABS_PATH = os.path.dirname(__file__)
    DEFAULT_DOWN_PATH = f'E:\\ZLJ_code\\yt-url-har-pcap\\data\\{RESOLUTION}_{protocal}_traffic_result4'

    url_path = 'data\\input_url.txt'
    url_info_path = 'data\\url_info.csv'
    # URL_LIST = [
    #     # "https://www.youtube.com/watch?v=pzKerr0JIPA",  #just for test
    #     "https://www.youtube.com/watch?v=_iaEOlewwNQ",
    #     ]
    ########################################################
    with open(url_path, 'r', encoding='utf-8') as url_file:
        URL_LIST = list(map(str.strip, url_file.readlines()))
        print(f"Tasks: 共{len(URL_LIST)}个URL")

    url_info = []
    with open(url_info_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            url_info.append(row)

    # main
    for i, url in enumerate(tqdm(URL_LIST, desc="总进度")):
        if  i != 0 and i % 50 == 0:
            print('=-=【进入休眠600s~】=-=')
            time.sleep(600)

        print(f"'=-=【开始采集 {url}~】=-='")
        duration = 0
        for row in url_info:
            if row['url'] == url:
                duration = int(row['duration'])//1000
                break
        if duration <= 60 or duration >= 1800:
            print('=-=【视频下架/时间<1min/>30min~】=-=')
            continue

        driver = start_chrome(get_chrome_options(RESOLUTION, is_quic=True)) #启动

        base_filename = f"{url[-11:]}--{RESOLUTION}--{datetime.now():%Y%m%d%H%M%S}"

        ensure_tshark_gen = capture_traffic(TSHARK_PATH, INTERFACE, \
                                            os.path.join(DEFAULT_DOWN_PATH, f'{url[-11:]}--PCAP'), \
                                            f'{base_filename}.pcap') # yield
        next(ensure_tshark_gen)  # ensure tshark started
        print('=-=【Tshark Started~】=-=')

        # 加载cookie
        driver.get('https://www.youtube.com/')
        load_cookies(driver)
        driver.get(url) # 阻塞，直到网页加载完成deo
        
        TAKE_SECONDS = min(DEFAULT_SECONDS, duration)
        print(f'=-=【即将播放{TAKE_SECONDS}秒】=-=')
        _, waste_second1 = switchto_network_and_filter() # sleep around 1s
        waste_second2 = 10  # 固定采集前x分钟
        # TAKE_SECONDS, waste_second2 = get_wait_second() # 全采
        if (sleep_time:=TAKE_SECONDS - waste_second1 - waste_second2) > 0:
            time.sleep(sleep_time)

        if not os.path.exists(os.path.join(DEFAULT_DOWN_PATH, url[-11:])):
            os.makedirs(os.path.join(DEFAULT_DOWN_PATH, url[-11:]))
            
        next(ensure_tshark_gen, 'capture done') # kill tshark
        export_har_file(dir_name=url[-11:], 
                        file_name=f"{base_filename}.har") # cost much time cuz of sleep

        # ensure the save is successful (the save process took much time)
        time.sleep(TAKE_SECONDS / 60 / 2 + 3) # 10min -> 5s  60min -> 30s

        driver.quit()
        del driver # chrome实例内存占用较大，反复创建最好还是手动释放内存，避免内存溢出引起故障
        gc.collect()
        # 