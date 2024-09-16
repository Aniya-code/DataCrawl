# -*- coding: utf-8 -*-
import csv
import json
import subprocess
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime
import time,os,gc
from tqdm import tqdm
import chardet



def execution_time_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    return wrapper


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

def get_chrome_options(resolution, is_headless=False, is_quic=False):
    chrome_options =  webdriver.ChromeOptions()
    chrome_options.add_argument(f"load-extension={CUR_ABS_PATH}/plugin/{resolution}fjdmkanbdloodhegphphhklnjfngoffa/1.5_0")  # 加载插件，win/linux均通过测试
    if is_headless:
        chrome_options.add_argument("--headless")
    if is_quic:
        chrome_options.add_argument('--enable-quic') # 是否启用quic
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--blink-settings=imagesEnabled=false')
    chrome_options.add_argument('--proxy-server=http://127.0.0.1:8080')
    chrome_options.add_argument("--lang=en-US")
    chrome_options.binary_location = CHROME_PATH # only for remote test \\192.168.107.62\c
    return chrome_options

def start_chrome(chrome_options):
    # driver = webdriver.Chrome(options=chrome_options, service=Service(CHROMEDRIVER_PATH))
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def driver_get(url: str):
    global webpage_load_seconds
    start_time = time.time()
    # 加载cookie
    driver.get('https://www.youtube.com/')
    load_cookies(driver)
    driver.get(url)
    try:
        playbtn = driver.find_element(By.CSS_SELECTOR, 'button.ytp-play-button')
        if (state:=playbtn.get_attribute("data-title-no-tooltip")) and state.upper() in ['PLAY', '播放']:
            playbtn.click()
            print(f"=-=【未自动播放，已模拟人工播放】=-=")
        else:
            print(f"=-=【视频自动播放】=-=")
    except Exception:
        print(f"=-=【未找到播放按钮】=-=")
    webpage_load_seconds = time.time() - start_time

def _get_duration_text():
    try:
        _e = driver.find_element(By.CSS_SELECTOR, '#movie_player > div.ytp-chrome-bottom > div.ytp-chrome-controls > div.ytp-left-controls > div.ytp-time-display.notranslate > span:nth-child(2) > span.ytp-time-duration') or driver.find_element(By.XPATH, '//*[@id="movie_player"]/div[28]/div[2]/div[1]/div[1]/span[2]/span[3]') or driver.find_element(By.XPATH, '//span[starts-with(@class,"ytp-time-duration")]/text()')
        return _e.text
    except Exception:
        return None     

def _get_played_text():
    try:
        return driver.find_element(By.CSS_SELECTOR, 'span.ytp-time-current').text
    except Exception:
        return None

def get_player_seconds(get_played=False):
    _get = _get_duration_text if not get_played else _get_played_text
    while not (duration_text:=_get()):
        time.sleep(0.1)
    h_m_s = duration_text.split(":")
    if len(h_m_s) == 2:
        h_m_s.insert(0, 0)
    h_m_s = list(map(int, h_m_s))
    duration = h_m_s[-1] + h_m_s[-2]*60 + h_m_s[-3]*3600
    return int(duration)

@execution_time_decorator
def get_played_seconds():
    '''
    当前已播时长（秒）
    '''
    return get_player_seconds(get_played=True)

@execution_time_decorator
def get_duration_seconds():
    '''
    视频总时长（秒）
    '''
    return get_player_seconds(get_played=False)

def run_for_seconds(func, seconds, *args, **kwargs):
    '''
    运行一个函数多少秒
    '''
    assert seconds > 0, "参数不合法"
    start_time = time.time()
    end_time = start_time + seconds
    while time.time() < end_time:
        func(*args, **kwargs)
    print(f"=-=【Run for seconds 结束】=-=")

def subprocess_stdio_has_kw(process_pointer, keywords, try_lines=-1, verbose=False):
    '''
        实时监测子进程是否在stdout中打印了指定关键字。
        Note:
        1.如果需要监听其他输出流，如stderr+stdout，请将其他流重定向到stdout。
        @try_lines 尝试监测的输出行数，-1表示无限轮询
    '''
    import sys
    out = process_pointer.stdout
    while try_lines == -1 or try_lines > 0:
        sys.stderr.flush() # to delete
        sys.stdout.flush()
        # print(type(out.readline()))
        # print(f"out.readline()=", out.readline())
        # print()
        # sys.stderr.flush() # to delete
        # sys.stdout.flush()
        l = out.readline()
        if (msg:=l.decode(chardet.detect(l)['encoding']).strip()):
            if verbose and msg:
                print(msg)
            if keywords in msg:
                return True
        
        if try_lines > 0:
            try_lines -= 1
        time.sleep(0.01)
    return False

def capture_traffic(tshark_path, interface, pcap_fullpath, body_path, base_filename, python_path="python", mitm_script_path="mitm_http.py", loopcount=1):
    if not os.path.exists(pcap_fullpath):
        os.makedirs(pcap_fullpath, exist_ok=True)

    pcap_fullname = os.path.join(pcap_fullpath, f"{base_filename}.pcap")

    for _ in range(loopcount):
        write_mitm_meta(base_filename, body_path)
        mitm_cmd = [python_path, mitm_script_path]
        print(f"=-=【MITM CMD】=-=：{mitm_cmd}")
        mitm_process = subprocess.Popen(mitm_cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        if subprocess_stdio_has_kw(mitm_process, "listening", verbose=True):
            tshark_cmd = [tshark_path, "-F", "pcap", "-i", interface, "-w", pcap_fullname]
            print(f"=-=【tshark CMD】=-=：{tshark_cmd}")
            tshark_process = subprocess.Popen(tshark_cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            if subprocess_stdio_has_kw(tshark_process, "Capturing"):
                yield mitm_process
                print(f'=-=【Attempt to Kill...】=-=')
                tshark_process.kill()
                mitm_process.kill()
                print(f'=-=【All Killed】=-=')
                print(f'-Catpured: {pcap_fullname}')
            else:
                mitm_process.kill()
                tshark_process.kill()
                raise Exception("=-=【未检测到tshark启动】=-=")
        else:
            mitm_process.kill()
            raise Exception("=-=【未检测到mitm启动】=-=")

def write_mitm_meta(base_filename, body_path) -> str:
    '''
    用于写body_log每一行视频的元数据, 即: 非body_list字段
    '''
    videoid, resolution, datetime_ = base_filename.split("--")
    url = f"https://www.youtube.com/watch?v={videoid}"
    with open(body_path, 'a+', encoding="utf8") as f:
        f.write(f"\n{url},{resolution},{datetime_},")
    
    return body_path

def modify_csv(input_file, output_file):
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        rows = list(reader)  

    for row in rows:
        if row:  # 确保行不为空
            body_list = list(map(int, row[-1].split('/')))   
            new_body_list = [x for x in body_list if x > 500]
            row[-1] = '/'.join(list(map(str, new_body_list)))

    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(rows)

if __name__ == '__main__':
    ############支持通过RESOLUTION自动切换360、480、720、1080#########
    global CHROME_PATH, CHROMEDRIVER_PATH, COOKIE_FILE
    CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    CHROMEDRIVER_PATH = r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'
    TSHARK_PATH = r'E:\Wireshark\tshark.exe'
    PYTHON_PATH = r'E:\Python\python.exe' # 要用和当前环境不同的python，否则会阻塞
    COOKIE_FILE = r'data\youtube_cookies.json'

    protocal = "tls" # 二选一 mitmproxy目前只支持tls采集
    # protocal = "quic"
    
    CUR_ABS_PATH = os.path.dirname(__file__)
    DEFAULT_DOWN_PATH = os.path.join(CUR_ABS_PATH, f'data\\{protocal}_traffic_result')
    BODY_PATH = f"data\\{protocal}_body_log.csv" # 同步修改mitm_http的路径
    FINAL_BODY_PATH = "data\\final_body_log.csv"

    RESOLUTION = '1080'
    TAKE_SECONDS = 60*5 # 默认采集前xx秒***
    INTERFACE = 'localnet'
    
    url_path = 'data\\input_url.txt'
    url_info_path = 'data\\url_info.csv'
    # URL_LIST = [
    #     "https://www.youtube.com/watch?v=_iaEOlewwNQ",
    #     "https://www.youtube.com/watch?v=2xyo2sqmb1k"
    # ]
    ################################################################
    
    with open(url_path, 'r', encoding='utf-8') as url_file:
        URL_LIST = list(map(str.strip, url_file.readlines()))
        print(f"Tasks: 共{len(URL_LIST)}个URL")

    url_info = []
    with open(url_info_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            url_info.append(row)
    
    # main
    webpage_load_seconds = 0 # 网页加载的时间,结果正确但暂没用上
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
        if duration <= 60:
            print('=-=【视频下架/时间<1min~】=-=')
            continue

        driver = start_chrome(get_chrome_options(RESOLUTION, is_headless=True, is_quic=False)) # 启动
        
        base_filename = f"{url[-11:]}--{RESOLUTION}--{datetime.now():%Y%m%d%H%M%S}"
        capture_generator = capture_traffic(TSHARK_PATH, INTERFACE, \
                                     pcap_fullpath=os.path.join(DEFAULT_DOWN_PATH, f'{url[-11:]}--PCAP'), \
                                     body_path = os.path.join(CUR_ABS_PATH, BODY_PATH).replace('/', '\\'),\
                                     base_filename=f'{base_filename}', \
                                     python_path=PYTHON_PATH, \
                                     mitm_script_path = r'mitm_http.py',\
                                     )
        mitm_process = next(capture_generator) # 启动子进程开始捕获body和pcap，返回mitm进程指针
        print('=-=【All Started~】=-=')

        threading.Thread(target=driver_get, args=(url,)).start() # 生成一个全局变量：网页加载时长

        MIN_SECONDS = min(TAKE_SECONDS, duration) # 采集时长：选视频实际市场和默认时长的较小者
        print(f'=-=【即将播放{MIN_SECONDS}秒】=-=')
        run_for_seconds(subprocess_stdio_has_kw, MIN_SECONDS, mitm_process, "!@#$%^&*", verbose=True, try_lines=1) # 用垃圾值拉取日志

        played_seconds, exec_seconds = get_played_seconds() # exec_seconds通常小于1s，有时会1~5s
        if played_seconds < MIN_SECONDS: # 用于保证采集时长的精确，同时保证不小于配置的时长：从网页开始加载到视频开始播放有一段时间间隔，可以达到5秒左右，预估该值差异性较大，受网速、设备性能等影响波动较大。
            left_seconds = MIN_SECONDS-played_seconds
            print(f"=-=【已播放{played_seconds}秒，还剩{left_seconds}秒...】=-=") #理论上left_seconds=网页开始加载到视频播放的时间间隔-exec_seconds
            run_for_seconds(subprocess_stdio_has_kw, left_seconds, mitm_process, "!@#$%^&*", verbose=True, try_lines=1)
                
        next(capture_generator, 'Kill all subprocesses') # kill

        driver.close()
        driver.quit()
        del driver
        gc.collect()

    modify_csv(os.path.join(CUR_ABS_PATH, BODY_PATH), os.path.join(CUR_ABS_PATH, FINAL_BODY_PATH))