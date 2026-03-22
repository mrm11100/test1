import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

print("📊 启动数据可视化模块，正在生成图表...")

# 解决图片上中文字体显示为方块的问题 (Windows 自带黑体)
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv('final_analysis_result.csv')

# ==================== 图表 1：情感分布饼图 ====================
emotion_counts = df['sentiment_label'].value_counts()
plt.figure(figsize=(8, 6))
# 画饼图，设置漂亮的颜色
colors =['#ff9999','#66b3ff','#99ff99']
plt.pie(emotion_counts, labels=emotion_counts.index, autopct='%1.1f%%',
        colors=colors, startangle=140, shadow=True, textprops={'fontsize': 12})
plt.title('电商商品评论情感倾向分布图', fontsize=16)
plt.savefig('Emotion_Pie_Chart.png', dpi=300) # 高清保存用于插进论文
print("✅ 情感分布饼图已保存为：Emotion_Pie_Chart.png")


# ==================== 图表 2：好评词云图 ====================
# 提取所有正面评论的分词结果
positive_words = ' '.join(df[df['sentiment_label'] == '正面(Positive)']['cut_words'].dropna())

# 注意：Windows 系统的字体通常在 C:/Windows/Fonts/simhei.ttf
wc = WordCloud(
    font_path='C:/Windows/Fonts/simhei.ttf', # 指定中文字体
    background_color='white',                # 背景颜色
    width=800, height=600,
    colormap='summer'                        # 词云颜色主题
)
wordcloud = wc.generate(positive_words)

plt.figure(figsize=(10, 8))
plt.imshow(wordcloud, interpolation='bilinear')
plt.axis('off') # 不显示坐标轴
plt.title('用户正面评价(好评)词云图', fontsize=18)
plt.savefig('Positive_WordCloud.png', dpi=300)
print("✅ 正面词云图已保存为：Positive_WordCloud.png")
print("🎉 全部大功告成！快去文件夹里看你生成的两张高清大图吧！这是你论文最好的素材！")