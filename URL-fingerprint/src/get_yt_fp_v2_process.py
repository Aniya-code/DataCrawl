# 支持视频+音频指纹，支持获取时间线
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
from datetime import datetime
import sys


# 设置整数转换为字符串时允许的最大位数
# sys.set_int_max_str_digits(10000)  # 根据需要调整数字

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
    def __init__(self, itag, start, end, video_name, down_path):
        self.itag = itag
        self.start = start
        self.end = end
        video_mp4_itag = [135, 136, 137, 298, 299, 397, 398, 399, 400, 401, 571, 697, 698, 699, 700, 701, 702]
        video_webm_itag = [244, 247, 248, 271, 313, 302, 303, 308, 315, 272, 333, 334, 335, 336, 337]
        audio_webm_itag = [249, 250, 251, "249-drc", "250-drc", "251-drc"]
        audio_mp4_itag = [140, "140-drc"]

        if self.itag in (video_mp4_itag + audio_mp4_itag):
            self.get_metedata_mp4(video_name, down_path)
        elif self.itag in (video_webm_itag + audio_webm_itag):
            self.get_metedata_webm(video_name, down_path)

        # else:
        #     raise ValueError('Itag Wrong')

    def get_metedata_mp4(self, video_name, down_path):
        videopath = down_path+'video/{}/{}_{}.mp4'.format(video_name, video_name, self.itag)
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
            with open(run_log_dir + 'ERROR.log', 'a', encoding='utf-8') as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + video_name + ', ' + str(self.itag) + " version wrong\n" )# version有误, 大概率是140
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



    def get_metedata_webm(self, video_name, down_path):
        videopath = down_path+'video/{}/{}_{}.webm'.format(video_name, video_name, self.itag)
        if os.path.exists(videopath):
            with open(videopath, 'rb') as f:
                header_data = f.read(10000)
        elif os.path.exists(videopath +'.part'):
            with open(videopath+'.part', 'rb') as f:
                header_data = f.read(10000)
        else:
            
            with open(run_log_dir + 'ERROR.log', 'a', encoding='utf-8') as f:
                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + video_name + ', ' + str(self.itag) + ', no wemb or webm.part.\n') # 未下载该视频
                return
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
    def __init__(self, ID, url, down_path, yt_fp_path):
        self.ID = ID
        self.url = url
        self.down_path = down_path
        self.yt_fp_path = yt_fp_path
        self.video_name = self.url.split('=')[1]
        # self.video_mp4_itag = [160, 133, 134, 135, 136, 137, 298, 299, 394, 395, 396, 397, 398, 399, 400, 401, 571, 694, 695,
        #                  696, 697, 698, 699, 700, 701, 702]
        # self.video_webm_itag = [278, 242, 243, 244, 247, 248, 271, 313, 302, 303, 308, 315, 272, 330, 331, 332, 333, 334, 335,
        #                   336, 337]
        # 以下itag不含360及以下
        self.video_mp4_itag = [135, 136, 137, 298, 299, 397, 398, 399, 400, 401, 571, 697, 698, 699, 700, 701, 702]
        self.video_webm_itag = [244, 247, 248, 271, 313, 302, 303, 308, 315, 272, 333, 334, 335, 336, 337]
        self.audio_webm_itag = [249, 250, 251, "249-drc", "250-drc", "251-drc"]
        self.audio_mp4_itag = [140, "140-drc"]
        self.cookie_txt = r"data\cookie\www.youtube.com_cookies.txt"



    def get_websource(self):
        print("############################# Start parsing: ", self.url, "#############################")
        if not os.path.exists(self.down_path+'websource/'):
            os.makedirs(self.down_path+'websource/')
        response_path = self.down_path+'websource/' + self.video_name + '.html'
        #避免下载失败/重复下载
        response = None  # 初始化 response 变量为 None
        while not os.path.exists(response_path): 
            print("\nWebsource is downloading...")
            try:
                response = requests.get(self.url, timeout=5, headers={'Accept-Encoding': 'utf-8'})  # 设置超时时间为5秒
                response.raise_for_status()
            except Exception as e:
                print(f"请求失败: {e}")
            if response and response.status_code == 200:
                with open(self.down_path+'websource/' + self.video_name + '.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
            else:
                
                with open(run_log_dir + 'ERROR.log', 'a', encoding='utf-8') as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + self.url+ ', request error .\n') # websource请求失败一次
                # break
           
            print("Websource exists.\n")

    def analyse_websource(self):
        with open(self.down_path+'websource/' + self.video_name + '.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script')# 找到所有script标签
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
                indexRange = param.get('indexRange', {'start':0, 'end':0}) #modify
                if indexRange == {'start':0, 'end':0}:
                    with open(run_log_dir + 'ERROR.log', 'a', encoding='utf-8') as f:
                        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + self.url + ', '+ str(itag)+ ' no indexRange.\n') # 该itag没有indexRange
                else:
                    self.itag_list.append(itag) # 只下载有IndexRange的

                    width = param['width']
                    height = param['height']
                    quality = str(width)+'x'+str(height)
                    self.itag_quality[itag] = quality #

                    codecs = param['mimeType'].split("\"")[1].split('.')[0] #'video/mp4; codecs="avc1.640028"'
                    self.itag_vcodec[itag] = codecs
                    
                    indexRange['start'] = int(indexRange['start'])
                    indexRange['end'] = int(indexRange['end'])
                    self.itag_indexrange[itag] = indexRange

                    self.itag_contentlength[itag] = int(param.get('contentLength', 0))

            elif itag in (self.audio_mp4_itag + self.audio_webm_itag):
                indexRange = param.get('indexRange', {'start':0, 'end':0}) #modify
                if indexRange == {'start':0, 'end':0}:
                    with open(run_log_dir + 'ERROR.log', 'a', encoding='utf-8') as f:
                        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + self.url+', '+str(itag)+ ' no indexRange.\n')  # 该itag没有indexRange
                else:
                    self.itag_list.append(itag) # 只下载有IndexRange的

                    quality = param['quality']
                    self.itag_quality[itag] = quality #

                    codecs = param['mimeType'].split("\"")[1].split('.')[0] 
                    self.itag_vcodec[itag] = codecs

                    indexRange['start'] = int(indexRange['start'])
                    indexRange['end'] = int(indexRange['end'])
                    self.itag_indexrange[itag] = indexRange

                    self.itag_contentlength[itag] = int(param.get('contentLength'))

            elif itag not in [160, 133, 134, 394, 395, 396, 694, 695, 696, 278, 242, 243, 330, 331, 332]:
                with open(run_log_dir + 'newitag.log', 'a', encoding='utf-8') as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + self.url + ', newitag:' + str(itag)+ '\n') # 新的itag
                    
        

    
    def analyse_video(self):
        self.itag_box = {}
        #以下使用csv模块a模式追加指纹
        with open(self.yt_fp_path, 'a', newline='', encoding='utf-8') as file: 
            writer = csv.writer(file)
            for itag in self.itag_list:
                start, end = self.itag_indexrange[itag]['start'], self.itag_indexrange[itag]['end']
                ##################获取一个itag的视频指纹##################
                box = Box(itag, start, end, self.video_name, self.down_path)
                quality = self.itag_quality[itag]
                vcodec = self.itag_vcodec[itag]
                contentLength = self.itag_contentlength[itag]
                self.itag_box[itag] = box
                if hasattr(box, 'reference_list'):
                    # 判断指纹解析是否有误
                    if np.any(np.array(box.duration_list) < 0):
                        with open(run_log_dir + 'ERROR.log', 'a', encoding='utf-8') as f:
                                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + self.url + ', '+ str(itag)+ ' fp error: nagtive value.\n') # 指纹解析错误
                        continue
                    duration_list = [1000*x // box.Timescale for x in box.duration_list]
                    timeline = [0] + list(accumulate(duration_list))
                    condition = (contentLength==end+1+sum(box.reference_list))
                    # print(itag, self.itag_contentlength[itag], 'fmp4', end+1+sum(box.reference_list), condition if condition == False else '', contentLength-(end+1+sum(box.reference_list)))
                    if itag !=140  or (itag == 140 and condition):
                        try:
                            writer.writerow([self.ID, self.url, itag, quality, 'fmp4', vcodec, start, end, contentLength, '/'.join(map(str, box.reference_list)), '/'.join(map(str, box.duration_list)), '/'.join(map(str, timeline))])
                        except Exception as e:
                            print(f"写文件失败: {e}")
                           
                   
                elif hasattr(box, 'track_list'):
                    if np.any(np.array(box.track_list) < 0):
                        with open(run_log_dir + 'ERROR.log', 'a', encoding='utf-8') as f:
                                f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S  ") + username + ' ' + self.url+', '+str(itag)+ ' fp error: nagtive value.\n')
                        continue
                    duration_list = (np.diff(box.timeline)).tolist()
                    try:
                        writer.writerow([self.ID, self.url, itag, quality, 'webm', vcodec, start, end, contentLength, '/'.join(map(str, box.track_list)), '/'.join(map(str, duration_list)), '/'.join(map(str, box.timeline))])
                    except Exception as e:
                        print(f"写文件失败: {e}")
                       
                    # print(itag, self.itag_contentlength[itag], 'webm', end+1+sum(box.track_list)) #, contentLength==end+1+sum(box.track_list), contentLength-(end+1+sum(box.track_list))
                else:
                    writer.writerow([self.ID, self.url, itag, quality])


    def download_video(self, down_process_list):
        if not os.path.exists(self.down_path+'video/' + self.video_name):
            os.makedirs(self.down_path+'video/' + self.video_name)
        try:
            for itag in self.itag_list:
                if itag in self.video_mp4_itag:
                    videopath = self.down_path+'video/{}/{}_{}.mp4'.format(self.video_name, self.video_name, itag)
                elif itag in self.video_webm_itag:
                    videopath = self.down_path+'video/{}/{}_{}.webm'.format(self.video_name, self.video_name, itag)
                elif itag in self.audio_mp4_itag:
                    videopath = self.down_path+'video/{}/{}_{}.mp4'.format(self.video_name, self.video_name, itag)
                elif itag in self.audio_webm_itag:
                    videopath = self.down_path+'video/{}/{}_{}.webm'.format(self.video_name, self.video_name, itag)
                else:
                    raise ValueError('Itag Wrong')
                # @add 包括小于4kb的视频要重新下载
                if (os.path.exists(videopath+'.part') and os.path.getsize(videopath+'.part') < 15360) or (not os.path.exists(videopath+'.part') and not os.path.exists(videopath)) : 
                    ###### @add 先删除小于15KB的文件####
                    if os.path.exists(videopath+'.part') and os.path.getsize(videopath+'.part') < 15360:
                        os.remove(videopath+'.part')
                        print(f"#####..delete {itag}..#####")

                    print("\nitag={} is downloading...".format(itag))
                    # @ modify
                    command = 'yt-dlp --limit-rate 15K --cookies {} -f {} {} -o {}'.format(self.cookie_txt, itag, self.url, videopath)
                    command = command.split(' ')

                    # 长度达到8，pop最老的（已6秒)，杀掉itag级别进程，itag下载异常时把video追加在全局video_list
                    if len(down_process_list) == process_count:
                        head_task = down_process_list.pop(0)
                        head_task[0].kill()
                        # kill oldest process时的情况有两种：1.正常 2.异常
                        # 对oldest process异常的情况进行处理

                        if (os.path.exists(head_task[1] +'.part') and os.path.getsize(head_task[1] +'.part') < 15360) or (not os.path.exists(head_task[1] +'.part') and not os.path.exists(head_task[1])):
                            global video_list
                            if not video_list[-1] is head_task[-1]:#同一个video有多个itag，但video_list只需加一次video级别
                                video_list.append(head_task[-1])
                    
                    # 开始处理当前任务
                    process = subprocess.Popen(command) #指定video、指定itag的进程
                    down_process_list.append((process, videopath, self))#（itag级别、itag级别、video级别）
                    time.sleep(sleep_time)# 去队列里排队
                print(" itag={} exits.".format(itag))
        except Exception as e:
            print(e)


if __name__ == '__main__':
    ################################################
    global video_list, process_count, sleep_time, username, run_log_dir

    url_paths = [r'data\yt_crawled_url\funtv_url_202406051751.csv']
    video_list = []
    process_count = 6
    per_down_time = 6 # test param: 8,6 
    sleep_time = per_down_time / process_count
    run_log_dir = 'data/run_log/'

    for url_path in url_paths:
        username = url_path.split('\\')[-1].split('_')[0] # 博主分开下载
        down_path = f'data/yt_download/{username}/'
        yt_fp_path = f'data/yt_fp/yt_fp_{username}.csv'
        ###############################################


        with open(yt_fp_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['ID', 'url', 'itag', 'quality', 'format','vcodec', 'start', 'end', 'contentLength', 'fingerprint', 'duration', 'timeline'])

        # 设置进程列表
        url_df = pd.read_csv(url_path)
        for index, row in url_df.iterrows():
            video_list.append(Video(index, row['url'], down_path, yt_fp_path))
        video_count = video_list.__len__() # 用于写指纹时按顺序且不重复

        # 开始下载
        down_process_list = []
        for video in video_list:
            video.get_websource()
            video.analyse_websource()
            video.download_video(down_process_list) #进程控制

        # 尾部未完成任务的处理
        loop_time = 0
        while down_process_list and loop_time < 10: #
            print("1")
            time.sleep(sleep_time)
            head_task = down_process_list.pop(0)
            head_task[0].kill()
            if not os.path.exists(head_task[1]+'.part') and not os.path.exists(head_task[1]):
                print("2")
                process = subprocess.Popen(head_task[0].args)
                down_process_list.append((process, head_task[1], head_task[-1]))
            loop_time += 1

        print("\n写文件...")
        for video in video_list[:video_count]:
            video.analyse_video()
        print("Done!")


