
import csv

def modify_csv(input_file, output_file, url_info_path):
    
    url_info = []
    with open(url_info_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            url_info.append(row)

    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        rows = list(reader) 

    new_rows = []
    for idx, row in enumerate(rows):
        duration = 0
        for info_row in url_info:
            if info_row['url'] == row[0]:
                duration = int(info_row['duration'])//1000
                break
        if duration <= 60 or duration >= 1800: # 滤掉小于2分钟，大于30分钟的url
            print(f'=-=【{idx}: {row[0]} duration={duration}~】=-=')
            continue
        new_rows.append(row)

    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(new_rows)

    print(len(rows), len(new_rows))


input_file = r'data\yt_crawled_url\DJYNews_url_20240611162957.csv'
output_file = r'data\yt_crawled_url\final_DJYNews_url_20240611162957.csv'
url_info_path = r'data\url_info\DJYNews_url_info.csv'

modify_csv(input_file, output_file, url_info_path)