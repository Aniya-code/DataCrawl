import os.path
import subprocess
import time
from lxml import etree
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

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

class Capture():
    def __init__(self, tshark_interface, tshark_path, chrome_driver_path, chrome_user_data_path, pcap_path,
                 url_csv_path=''):
        self.tshark_interface = tshark_interface
        self.tshark_path = tshark_path
        self.chrome_driver_path = chrome_driver_path
        self.chrome_user_data_path = chrome_user_data_path
        self.pcap_path = pcap_path
        self.url_csv_path = url_csv_path
        self.time_duration = 6 * 60

        self.driver = self.chrome_driver_init()

    def __del__(self):
        self.driver.close()

    # 初始化chrom driver
    def chrome_driver_init(self):
        options = webdriver.ChromeOptions()
        service = Service(self.chrome_driver_path)
        options.add_argument("--user-data-dir=" + self.chrome_user_data_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(1000, 30000)
        wait = WebDriverWait(driver, 100)
        return driver

    # 持续访问URL直到成功
    def loop_get_url(self, loop_count, video_url):
        for i in range(0, loop_count):
            try:
                time.sleep(3)
                self.driver.get(video_url)
                return 1
            except:
                continue
        return 0

    # 获取视频时长
    def get_video_duration(self):
        duration_xpath = '//span[starts-with(@class,"ytp-time-duration")]/text()'
        try:
            if duration_xpath != '':
                html = self.driver.page_source.encode("utf-8", "ignore")
                parseHtml = etree.HTML(html)
                video_duration = parseHtml.xpath(duration_xpath)
        except:
            video_duration = -1
            print('get video duration error')
        return video_duration

    # 确定视频实际播放时长
    def get_video_duration_second(self, video_duration):
        video_duration_s = -1
        if len(video_duration) > 0 and video_duration != -1:
            time_data = str(video_duration[0]).split(':')
            if len(time_data) == 2:
                video_duration_s = int(time_data[0]) * 60 + int(time_data[1])
            else:
                video_duration_s = int(time_data[0]) * 3600 + int(time_data[1]) * 60 + int(time_data[2])
        duration_of_the_video = video_duration_s
        return duration_of_the_video

    # 获取视频分辨率信息
    def get_video_resolution(self):
        video_resolution = []
        try:
            # 点击设置
            self.driver.find_element(By.XPATH, '//*[@class="ytp-button ytp-settings-button"]').click()
            # 点击画质
            self.driver.find_element(By.XPATH,
                                     '//*[@class="ytp-popup ytp-settings-menu"]//*[@class="ytp-menu-label-secondary"]').click()
            time.sleep(0.5)
            # 获取分辨率信息
            html = self.driver.page_source.encode("utf-8", "ignore")
            parseHtml = etree.HTML(html)
            video_resolution = parseHtml.xpath(
                '//*[@class="ytp-popup ytp-settings-menu"]//*[@class="ytp-menuitem-label"]/div/span/text()')
            # 复原
            self.driver.find_element(By.XPATH, '//*[@class="ytp-button ytp-settings-button"]').click()
        except:
            print('get resolution error')
        return video_resolution

    # 切换视频分辨率
    def video_resolution_switch(self, video_resolution):
        # 点击设置
        self.driver.find_element(By.XPATH, '//*[@class="ytp-button ytp-settings-button"]').click()
        # 点击画质
        self.driver.find_element(By.XPATH,
                                 '//*[@class="ytp-popup ytp-settings-menu"]//*[@class="ytp-menu-label-secondary"]').click()
        time.sleep(0.5)
        # 切换分辨率
        element_path = '//*[@class="ytp-popup ytp-settings-menu"]//*[@class="ytp-menuitem-label"]/div/span[text()=\'' + str(
            video_resolution).strip() + '\']'
        self.driver.find_element(By.XPATH, element_path).click()
        # 复原
        self.driver.find_element(By.XPATH, '//*[@class="ytp-button ytp-settings-button"]').click()

    # 目标分辨率与存在视频本身包含的分辨率取交集，作为最后的捕获分辨率
    def clawer_resolution_intersection(self, online_video_resolution):
        target_resolution = ['480p', '720p', '1080p']
        res = []
        for k in range(0, len(online_video_resolution)):
            for j in range(0, len(target_resolution)):
                if str(online_video_resolution[k]).__contains__(str(target_resolution[j])):
                    res.append(str(online_video_resolution[k]).strip())
                    break
        return res

    # 指定分辨率地播放单个播放视频URL，并记录pcap
    def capture_traffic(self, video_url):
        print('start capturing...')
        # 创建目录
        if not os.path.exists(self.pcap_path):
            os.makedirs(self.pcap_path)

        video_duration = -1
        loop_count = 10

        # 获取视频时长以及分辨率信息
        if self.loop_get_url(loop_count, video_url) == 0:
            print('get URL error')
            return

        time.sleep(3)
        # 获取视频的播放时长
        for i1 in range(0, loop_count):
            if video_duration == -1 or len(video_duration) == 0:
                video_duration = self.get_video_duration()
                time.sleep(1)
            else:
                print(video_duration[0])
                break
        # 获取视频的分辨率信息
        video_resolution = []
        for i2 in range(0, loop_count):
            if len(video_resolution) == 0:
                video_resolution = self.get_video_resolution()
                time.sleep(1)
        print(video_resolution)
        if video_duration == -1 or len(video_resolution) == 0:
            print('duration or resolution error')
            return
        # 确定视频采集的分辨率
        # target_resolution = self.clawer_resolution_intersection(video_resolution)
        # print(target_resolution)
        # 确定视频实际播放时长
        duration_of_the_video = self.get_video_duration_second(video_duration)
        if duration_of_the_video > self.time_duration:
            duration_of_the_video = self.time_duration
        # 对待采集分辨率列表进行逐一采集
        # for cur_resolution in target_resolution:
        for t in range(4):
            # 新建文件名
            t_time = time.strftime("%Y_%m_%d_%H_%M_%S")
            video_name = video_url.split('=')[-1]
            pcap_filename = video_name + ' ' + str(duration_of_the_video) + ' ' + t_time + '.pcap'
            pcap_filepath = self.pcap_path + pcap_filename

            time.sleep(5)
            # 开始记录网络流量
            tsharkCall = [self.tshark_path, "-F", "pcap", "-i", self.tshark_interface, "-w", pcap_filepath]
            tsharkProc = subprocess.Popen(tsharkCall, stderr=subprocess.PIPE, stdout=subprocess.PIPE, executable=self.tshark_path)
            if subprocess_stdio_has_kw(tsharkProc, "Capturing"):
                self.loop_get_url(loop_count, video_url)
            time.sleep(5)
            # 分辨率切换
            # self.video_resolution_switch(cur_resolution)
            # 等待视频播放
            time.sleep(duration_of_the_video)
            # 结束流量采集
            time.sleep(15)
            tsharkProc.kill()
            time.sleep(5)

    def batch_capture(self):
        csv_file = open(self.url_csv_path, mode='r', encoding='utf-8')
        csv_data = csv_file.read()
        video_urls = csv_data.split('\n')

        for i in range(0, len(video_urls)):
            self.capture_traffic(video_urls[i])


if __name__ == '__main__':
    tshark_interface = 'Ethernet'
    tshark_path = 'C:/Program Files/Wireshark/tshark.exe'
    chrome_driver_path = 'C:/Zenith/src/chromedriver.exe'
    chrome_user_data_path = 'C:/Users/fangxiaoyu/AppData/Local/Google/Chrome/User Data'
    pcap_path = 'C:/Zenith/data/record/pcap/'
    url_csv_path = 'C:/Zenith/data/temp/url_list.csv'
    capture = Capture(tshark_interface, tshark_path, chrome_driver_path, chrome_user_data_path, pcap_path, url_csv_path)

    # capture.capture_traffic('https://www.youtube.com/watch?v=rSR_9CJqJ60')
    capture.batch_capture()
