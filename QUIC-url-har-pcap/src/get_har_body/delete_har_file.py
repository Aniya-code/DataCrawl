import os
import shutil

def delete_folders(base_path):
    # 遍历给定路径下的所有文件夹
    for root, dirs, files in os.walk(base_path, topdown=False):
        for dir_name in dirs:
            folder_path = os.path.join(root, dir_name)
            # 如果文件夹名称不是以'--PCAP'结尾，则删除
            if not dir_name.endswith("--PCAP"):
                print(f"Deleting folder: {folder_path}")
                shutil.rmtree(folder_path)

# 使用示例：删除当前目录中所有名称不以'--PCAP'结尾的文件夹:HAR FILE
base_path = r"data\720_quic_traffic_result"
delete_folders(base_path)
