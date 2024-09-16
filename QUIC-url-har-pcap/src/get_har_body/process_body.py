import csv

def modify_csv(input_file, output_file, filtered_url_path):
    url_list = []
    # with open(filtered_url_path, 'r', newline='', encoding='utf-8') as file:
    #     reader = csv.reader(file)
    #     header = next(reader)
    #     for line in  list(reader):
    #         url_list.append(line[0])

    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        rows = list(reader)  
    

    new_rows = []
    for row in rows:
        if row:  # 确保行不为空
            # 不在指纹库中的在线播放要滤掉、或者说视频<1min >30min的要滤掉
            if row[0]  in url_list:
                continue 
            body_list = list(map(int, row[-1].split('/')))   
            new_body_list = [x for x in body_list if x > 5000] # quic一开始会传一些1000~2000B左右的块， 类似于指纹信息
            row[-1] = '/'.join(list(map(str, new_body_list)))
            if len(new_body_list) <= 5: # 取长度大于10的chunk list
                continue
            
            new_rows.append(row)

    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(new_rows)


input_file = r'data\quic_body\DJYNews_720_quic_body_log_33.csv'
output_file = r'data\quic_body\final_720_quic_body_log_33.csv'
filtered_url_path = r'data\url\funtv8964_url_202406051751.csv'

modify_csv(input_file, output_file, filtered_url_path)
