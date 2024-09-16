import json
import csv
from datetime import datetime 
import re
import os
import itertools

def get_chunk_info(har_file_path, result_path):
    filename = har_file_path.split('\\')[-1]
    
    with open(result_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        quality = filename.split('--')[1]
        date = filename.split('--')[2].split('.')[0]
        video_url = "https://www.youtube.com/watch?v=" + filename.split('--')[0]
        with open(har_file_path, "r", encoding='utf-8') as f:
            har_data = json.load(f)
        # 响应体变量
        headers_size = []
        body_size = []
        tansfer_size = []
        
        
        for entry in har_data['log']['entries']:
            url = entry['request']['url']
            if 'videoplayback?' in url :
                if entry['response']['content']['size'] > 0:
                    headers_size.append(entry['response']['headersSize'])
                    body_size.append(entry['response']['content']['size'])
                    tansfer_size.append(entry['response']['_transferSize'])
        
        #写入
        writer = csv.writer(file)
        writer.writerow([video_url, quality, date, '/'.join(map(str, body_size))])

# def traverse_files_in_matching_subfolders(directory):
#     for root, dirs, files in os.walk(directory):
#         for dir_name in dirs:
#             if "--PCAP" not in dir_name:
#                 subfolder_path = os.path.join(root, dir_name)
#                 print(f'遍历文件夹: {subfolder_path}')
#                 for sub_root, _, sub_files in os.walk(subfolder_path):
#                     for file in sub_files:
#                         print(f'文件: {os.path.join(sub_root, file)}')

if __name__ == '__main__':
    har_path = r'data\720_quic_traffic_result4'
    result_path = r'data\quic_body\final_DJYNews_720_quic_body_log_33.csv'

    with open(result_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['url', 'quality', 'date', 'body_list'])

    for root, dirs, files in os.walk(har_path):
        for dir_name in dirs:
            if "--PCAP" not in dir_name:
                subfolder_path = os.path.join(root, dir_name)
                print(f'遍历文件夹: {subfolder_path}')
                for sub_root, _, sub_files in os.walk(subfolder_path):
                    for file in sub_files:
                        print(f'文件: {os.path.join(sub_root, file)}')
                        get_chunk_info(os.path.join(sub_root, file), result_path)

    

