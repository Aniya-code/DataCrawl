prosessed_url_file = r'data\quic_chunk\online_chunk_quic_train.csv'
processed_url=set()
with open(prosessed_url_file, 'r', encoding='utf-8') as infile:
    processed_url.update([line.strip().split(',')[0] for line in infile])

chunk_url_file = r'data\quic_chunk\online_chunk_quic.csv'
chunk_url=set()
with open(chunk_url_file, 'r', encoding='utf-8') as infile2:
    chunk_url.update([line.strip().split(',')[0] for line in infile2])

train_url = r'data\quic_chunk\train_url.csv'
with open(train_url, 'w', encoding='utf-8') as file:
    for url in processed_url :
        if url in chunk_url:
            file.write(url+'\n')
