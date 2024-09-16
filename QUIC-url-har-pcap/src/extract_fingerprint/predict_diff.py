import matplotlib.pyplot as plt

# 读取文件中的数据
file_path = r"data\quic_chunk\aligned_chunk_body.csv"
chunk_values = []
body_values = []

with open(file_path, 'r') as file:
    for line in file:
        columns = line.strip().split(',')
        chunk_values.extend(map(int, columns[1].split('/')))
        body_values.extend(map(float, columns[2].split('/')))

# 计算truebody的值
truebody_values = [int(0.9733666 * chunk - 292.334483) for chunk in chunk_values]
print(f"共{len(truebody_values)}个数据")

# 计算body和truebody之间的差值
differences = [body - truebody for body, truebody in zip(body_values, truebody_values)]






# 定义不同范围的区间
bins = [i * 200 for i in range(-6, 7)]

# 统计各区间内差值的数量
count_in_intervals = [sum((b <= diff < b + 200) for diff in differences) for b in bins]

total_count = sum(count_in_intervals)

# 计算各区间占比
percentages = [count / len(differences) * 100 if total_count != 0 else 0 for count in count_in_intervals] # 100不变，求%

# 绘制占比直方图
plt.figure(figsize=(15, 6))
bars = plt.bar([f"{b}-{b+200}" for b in bins[:-1]], count_in_intervals[:-1], color='skyblue', edgecolor='black')

for bar, percent in zip(bars, percentages):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2, height, f'{percent:.1f}%', ha='center', va='bottom')

plt.xlabel('Difference Range between body and truebody')
plt.ylabel('Frequency')
plt.title('Distribution of Differences between body and truebody in Intervals')
plt.grid(axis='y')
plt.show()


# 打印总占比
print(f"Total percentage of the bars: {sum(percentages):.2f}%")