
prosessed_url_file = r'data\quic_chunk\online_chunk_quic_train.csv'
line1=[]
with open(prosessed_url_file, 'r', encoding='utf-8') as infile:
    for line in infile:
        line1.append(line)

chunk_url_file = r'data\quic_chunk\online_chunk_quic.csv'
line2 = []
with open(chunk_url_file, 'r', encoding='utf-8') as infile2:
    for line in infile2:
        line2.append(line)

train_url = r'data\quic_chunk\train_url.csv'
with open(train_url, 'r', encoding='utf-8') as file:
    with open(r'data\quic_chunk\test_chunk.csv', 'w', encoding='utf-8') as f1, open(r'data\quic_chunk\train_chunk.csv', 'w', encoding='utf-8') as f2:
        for url in file:
            for l1 in line1:
                if l1.strip().split(',')[0] == url.strip():
                    f2.write(l1)
            for l2 in line2:
                if l2.strip().split(',')[0] == url.strip():
                    f1.write(l2)

