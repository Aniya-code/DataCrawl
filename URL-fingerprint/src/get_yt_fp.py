import csv
import json
import math
import os
import re
import subprocess
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from itertools import accumulate
import numpy as np
class Reference():
    def __init__(self, Reference_Type, Reference_Size, Subsegment_Duration, Starts_with_SAP, SAP_Type):
        self.Reference_Type = Reference_Type
        self.Reference_Size = Reference_Size
        self.Subsegment_Duration = Subsegment_Duration
        self.Starts_with_SAP = Starts_with_SAP
        self.SAP_Type = SAP_Type


class Track():
    def __init__(self, Track_Time, Track_Number, Track_Position):
        self.Track_Time = Track_Time
        self.Track_Number = Track_Number
        self.Track_Position = Track_Position


class Box():
    def __init__(self, itag, start, end, video_name):
        self.itag = itag
        self.start = start
        self.end = end
        video_mp4_itag = [135, 136, 137, 298, 299, 397, 398, 399, 400, 401, 571, 697, 698, 699, 700, 701, 702]
        video_webm_itag = [244, 247, 248, 271, 313, 302, 303, 308, 315, 272, 333, 334, 335, 336, 337]
        audio_webm_itag = [249, 250, 251, "249-drc", "250-drc", "251-drc"]
        audio_mp4_itag = [140, "140-drc"]
        if self.itag in (video_mp4_itag + audio_mp4_itag):
            self.get_metedata_mp4(video_name)
        elif self.itag in (video_webm_itag + audio_webm_itag):
            self.get_metedata_webm(video_name)

        # else:
        #     raise ValueError('Itag Wrong')

    def get_metedata_mp4(self, video_name):
        videopath = down_path + 'download_yt/video/{}/{}_{}.mp4'.format(video_name, video_name, self.itag)
        if not os.path.exists(videopath):
            with open(videopath+'.part', 'rb') as f:
                header_data = f.read(10000)
        else:
            with open(videopath, 'rb') as f:
                header_data = f.read(10000)
        sidx = header_data[self.start:self.end + 1]#index_range
        #index_range包含以下信息+各片段信息
        self.Box_Size = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        self.Box_Type = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        self.Version = int.from_bytes(sidx[:1], byteorder='big')
        sidx = sidx[1:]
        self.Flags = int.from_bytes(sidx[:3], byteorder='big')
        sidx = sidx[3:]
        self.Reference_ID = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        self.Timescale = int.from_bytes(sidx[:4], byteorder='big')
        sidx = sidx[4:]
        if self.Version == 0:
            self.Earliest_Presentation_Time = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
            self.First_Offset = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
        elif self.Version == 1:
            self.Earliest_Presentation_Time = int.from_bytes(sidx[:8], byteorder='big')
            sidx = sidx[8:]
            self.First_Offset = int.from_bytes(sidx[:8], byteorder='big')
            sidx = sidx[8:]
        else:
            print("version wrong")
            self.Earliest_Presentation_Time = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
            self.First_Offset = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
            # raise Exception('Version Inexistence')

        self.Reserved = int.from_bytes(sidx[:2], byteorder='big')
        sidx = sidx[2:]
        self.Reference_Count = int.from_bytes(sidx[:2], byteorder='big')
        sidx = sidx[2:]

        self.reference = []
        self.reference_list = []
        self.duration_list = []
        while len(sidx) != 0:
            Reference_Type = int.from_bytes(sidx[:1], byteorder='big')
            sidx = sidx[1:]
            Reference_Size = int.from_bytes(sidx[:3], byteorder='big')
            sidx = sidx[3:]
            Subsegment_Duration = int.from_bytes(sidx[:4], byteorder='big')
            sidx = sidx[4:]
            Starts_with_SAP = int.from_bytes(sidx[:1], byteorder='big')
            sidx = sidx[1:]
            SAP_Type = int.from_bytes(sidx[:3], byteorder='big')
            sidx = sidx[3:]

            ref = Reference(Reference_Type, Reference_Size, Subsegment_Duration, Starts_with_SAP, SAP_Type)
            self.reference.append(ref)
            self.reference_list.append(Reference_Size)
            self.duration_list.append(Subsegment_Duration)

    def get_metedata_webm(self, video_name):
        videopath = down_path + 'download_yt/video/{}/{}_{}.webm'.format(video_name, video_name, self.itag)
        if os.path.exists(videopath):
            with open(videopath, 'rb') as f:
                header_data = f.read(10000)
        else:
            with open(videopath+'.part', 'rb') as f:
                header_data = f.read(10000)
        cues = header_data[self.start:self.end + 1]

        self.Cues_Header = cues[:6]
        cues = cues[6:]

        self.track = []
        self.track_list = []
        self.timeline = []
        while len(cues) != 0:
            Track_Time_Flag = int.from_bytes(cues[3:4], byteorder='big')
            cues = cues[4:]
            Track_Time_Length = Track_Time_Flag - 0x80
            Track_Time = int.from_bytes(cues[:Track_Time_Length], byteorder='big') # ms timescale默认1000？
            cues = cues[Track_Time_Length:]

            Track_Number_Flag = int.from_bytes(cues[3:4], byteorder='big')
            cues = cues[4:]
            Track_Number_Length = Track_Number_Flag - 0x80
            Track_Number = int.from_bytes(cues[:Track_Number_Length], byteorder='big')
            cues = cues[Track_Number_Length:]

            Track_Position_Flag = int.from_bytes(cues[1:2], byteorder='big')
            Track_Position_Length = Track_Position_Flag - 0x80
            cues = cues[2:]

            Track_Position = int.from_bytes(cues[:Track_Position_Length], byteorder='big')
            cues = cues[Track_Position_Length:]

            tra = Track(Track_Time, Track_Number, Track_Position)
            self.track.append(tra)
            if len(self.track) > 1:
                self.track_list.append(self.track[-1].Track_Position - self.track[-2].Track_Position)
            self.timeline.append(Track_Time)

class Video():
    def __init__(self, ID, url):
        self.ID = ID
        self.url = url
        self.video_name = self.url.split('=')[1]
        self.video_mp4_itag = [135, 136, 137, 298, 299, 397, 398, 399, 400, 401, 571, 697, 698, 699, 700, 701, 702]
        self.video_webm_itag = [244, 247, 248, 271, 313, 302, 303, 308, 315, 272, 333, 334, 335, 336, 337]
        self.audio_webm_itag = [249, 250, 251, "249-drc", "250-drc", "251-drc"]
        self.audio_mp4_itag = [140, "140-drc"]
        self.cookie_txt = r"data\cookie\youtube_cookies.txt"  # for test 改为了相对地址


    def get_websource(self):
        print("############################# Start parsing: ", self.url, "#############################")
        if not os.path.exists(down_path + 'download_yt/websource/'):
            os.makedirs(down_path + 'download_yt/websource/')
        response_path = down_path + 'download_yt/websource/' + self.video_name + '.html'
        #避免下载失败/重复下载
        while not os.path.exists(response_path):
            print("\nWebsource is downloading...")
            response = requests.get(self.url)# 直接请求
            if response.status_code == 200:
                with open(down_path + 'download_yt/websource/' + self.video_name + '.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
        print("Websource exists.\n")

    def analyse_websource(self):
        with open(down_path + 'download_yt/websource/' + self.video_name + '.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script')#找到所有script标签
        pattern = re.compile(r'var\s+ytInitialPlayerResponse\s*=\s*({.*?});', re.DOTALL)

        for script_tag in script_tags:
            script_content = ''.join(map(str, script_tag.contents))#contents转为一个完整长字符串
            match = pattern.search(script_content)
            if match:
                javascript_code = match.group(1)
        data = json.loads(javascript_code)
        service_tracking_params = data.get('streamingData', {}).get('adaptiveFormats', [])

        self.itag_list = []
        self.itag_quality = {}
        self.itag_vcodec = {}
        self.itag_indexrange = {}
        self.itag_contentlength = {}
        self.itag_quality = {}
        for param in service_tracking_params:
            itag = param.get('itag')
            is_drc = param.get('isDrc') # None/True
            if is_drc: 
                itag = str(itag) + "-drc"
            if itag in (self.video_mp4_itag + self.video_webm_itag):
                self.itag_list.append(itag)

                width = param['width']
                height = param['height']
                quality = str(width)+'x'+str(height)
                self.itag_quality[itag] = quality #

                codecs = param['mimeType'].split("\"")[1].split('.')[0] #'video/mp4; codecs="avc1.640028"'
                self.itag_vcodec[itag] = codecs

                indexRange = param.get('indexRange')
                indexRange['start'] = int(indexRange['start'])
                indexRange['end'] = int(indexRange['end'])
                self.itag_indexrange[itag] = indexRange

                self.itag_contentlength[itag] = int(param.get('contentLength'))

            elif itag in (self.audio_mp4_itag + self.audio_webm_itag):
                self.itag_list.append(itag)

                quality = param['quality']
                self.itag_quality[itag] = quality #

                codecs = param['mimeType'].split("\"")[1].split('.')[0] 
                self.itag_vcodec[itag] = codecs

                indexRange = param.get('indexRange')
                indexRange['start'] = int(indexRange['start'])
                indexRange['end'] = int(indexRange['end'])
                self.itag_indexrange[itag] = indexRange

                self.itag_contentlength[itag] = int(param.get('contentLength'))

            elif itag not in [160, 133, 134, 394, 395, 396, 694, 695, 696, 278, 242, 243, 330, 331, 332]:
                with open(down_path + 'newitag.log', 'a', encoding='utf-8') as f:
                    f.write(self.url+str(itag)+ '\n')

    def download_video(self):
        if not os.path.exists(down_path + 'download_yt/video/' + self.video_name):
            os.makedirs(down_path + 'download_yt/video/' + self.video_name)
        for itag in self.itag_list:
            if itag in self.video_mp4_itag + self.audio_mp4_itag:
                videopath = down_path + 'download_yt/video/{}/{}_{}.mp4'.format(self.video_name, self.video_name, itag)
            elif itag in self.video_webm_itag + self.audio_webm_itag:
                videopath = down_path + 'download_yt/video/{}/{}_{}.webm'.format(self.video_name, self.video_name, itag)
            else:
                raise ValueError('Itag Wrong')
            # @add
            #既避免重复下载，又能反复尝试下载
            while not os.path.exists(videopath+'.part') and not os.path.exists(videopath): 
                print("\nitag={} is downloading...".format(itag))
                # @ modify
                command = 'yt-dlp --cookies {} -f {} {} -o {}'.format(self.cookie_txt, itag, self.url, videopath)
                command = command.split(' ')
                process = subprocess.Popen(command)
                time.sleep(20)#进程持续10s
                process.kill()
            print(" itag={} exits.".format(itag))
            
    def analyse_video(self):
        self.itag_box = {}
        #以下使用csv模块a模式追加指纹
        with open(down_path + 'yt_temp.csv', 'a', newline='', encoding='utf-8') as file: 
            writer = csv.writer(file)
            for itag in self.itag_list:
                start, end = self.itag_indexrange[itag]['start'], self.itag_indexrange[itag]['end']
                ############获取视频指纹#####################
                box = Box(itag, start, end, self.video_name)
                quality = self.itag_quality[itag]
                vcodec = self.itag_vcodec[itag]
                contentLength = self.itag_contentlength[itag]
                self.itag_box[itag] = box
                if hasattr(box, 'reference_list'): # MP4
                    duration_list = [1000*x // box.Timescale for x in box.duration_list] # 1000*x // box.Timescale片段时长换算为毫秒
                    timeline = [0] + list(accumulate(duration_list))
                    condition = (contentLength==end+1+sum(box.reference_list))
                    print(itag, self.itag_contentlength[itag], 'fmp4', end+1+sum(box.reference_list), condition if condition == False else '', contentLength-(end+1+sum(box.reference_list)))
                    if itag !=140  or (itag == 140 and condition):
                        writer.writerow([self.ID, self.url, itag, quality, 'fmp4', vcodec, start, end, contentLength, '/'.join(map(str, box.reference_list)), box.Timescale, '/'.join(map(str, box.duration_list)), '/'.join(map(str, timeline))])
                else: # webm
                    duration_list = (np.diff(box.timeline)).tolist()
                    writer.writerow([self.ID, self.url, itag, quality, 'webm', vcodec, start, end, contentLength, '/'.join(map(str, box.track_list)), '1000', '/'.join(map(str, duration_list)), '/'.join(map(str, box.timeline))])
                    print(itag, self.itag_contentlength[itag], 'webm', end+1+sum(box.track_list), contentLength==end+1+sum(box.track_list), contentLength-(end+1+sum(box.track_list)))

down_path = r'data\yt_download\test'
video = Video(1, "https://www.youtube.com/watch?v=RagTZHPrn_o") 
video.get_websource()
video.analyse_websource()

video.download_video()
video.analyse_video()
    