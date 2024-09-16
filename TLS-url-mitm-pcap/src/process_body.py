import csv

def modify_csv(input_file, output_file):
    with open(input_file, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        header = next(reader)
        rows = list(reader)  

    
    for row in rows:
        if row:  # 确保行不为空
            body_list = list(map(int, row[-1].split('/')))   
            new_body_list = [x for x in body_list if x > 2000]
            row[-1] = '/'.join(list(map(str, new_body_list)))

    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(rows)


input_file = r'data\tls_body_log.csv'
output_file = r'data\final_tls_body_log.csv'

modify_csv(input_file, output_file)
