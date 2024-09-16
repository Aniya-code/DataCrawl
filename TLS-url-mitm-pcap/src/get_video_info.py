import re
import csv
import json
import requests
import tqdm
from datetime import datetime
from bs4 import BeautifulSoup


def get_websource(url, url_info_path):
    response = None
    while not response:
        try:
            response = requests.get(url, timeout=5, headers={'Accept-Encoding':'utf-8'})
            response.raise_for_status()
        except Exception as e:
            print(f"请求失败：{e}")
        if response and response.status_code == 200:
            print("Success~")
            soup = BeautifulSoup(response.text, 'html.parser')
            script_tags = soup.find_all('script')
            pattern = re.compile(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', re.DOTALL)

            for script_tag in script_tags:
                script_content = ''.join(map(str, script_tag.contents))#contents转为一个完整长字符串
                match = pattern.search(script_content)
                if match:
                    javascript_code = match.group(1)
            data = json.loads(javascript_code)
            service_tracking_params = data.get('streamingData', {}).get('adaptiveFormats', [])
            
            # 开始获取有效信息
            # 视频时长、视频分辨率范围、视频itag列表
            duration = 0
            resolutions = set()
            video_itag = []
            video_contentlength = []
            video_bitrate = []
            audio_itag = []
            audio_contentlength = []
            audio_bitrate = []
            
            for param in service_tracking_params:
                itag = param.get('itag')
                mime_type = param.get('mimeType')
                contentlength = param.get('contentLength')
                bitrate = param.get('bitrate')
                if 'video' in mime_type:
                    duration = param.get('approxDurationMs')
                    
                    video_itag.append(itag)
                    video_contentlength.append(contentlength)
                    video_bitrate.append(bitrate)

                    
                    resolution = str(param.get('width')) + 'x' + str(param.get('height'))
                    resolutions.add(resolution)
                else:
                    audio_itag.append(itag)
                    audio_contentlength.append(contentlength)
                    audio_bitrate.append(bitrate)
            
            with open(url_info_path, '+a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([datetime.now().strftime("%Y-%m-%d"), url, duration, '/'.join(resolutions), '/'.join(map(str, video_itag)),  '/'.join(map(str, video_contentlength)), '/'.join(map(str, video_bitrate)), '/'.join(map(str, audio_itag)), '/'.join(map(str, audio_contentlength)), '/'.join(map(str, audio_bitrate))])
                
#####################################################
input_url_path = r'data\DJYNews_url_20240611162957.csv'
url_info_path = r'data\url_info.csv'
#####################################################

with open(input_url_path, 'r', encoding='utf-8') as file:
    url_list = list(map(str.strip, file.readlines()))

for i, url in enumerate(url_list):
    print(f"request {i}: {url}...")
    get_websource(url, url_info_path)