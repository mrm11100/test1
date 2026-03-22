import pandas as pd
from snownlp import SnowNLP
import jieba

print("🚀 启动 NLP 情感分析模块...")

# 1. 加载我们刚才生成的数据集
df = pd.read_csv('ecommerce_reviews.csv')

# 2. 定义情感打分函数
def get_sentiment(text):
    try:
        score = SnowNLP(text).sentiments # 计算 0-1 之间的情感概率
        return score
    except:
        return 0.5

print("正在计算每条评论的情感得分（这可能需要几秒钟）...")
df['sentiment_score'] = df['content'].apply(get_sentiment)

# 3. 情感极性划分（正向、负向、中性）
def label_sentiment(score):
    if score >= 0.6: return '正面(Positive)'
    elif score <= 0.4: return '负面(Negative)'
    else: return '中性(Neutral)'

df['sentiment_label'] = df['sentiment_score'].apply(label_sentiment)

# 4. 中文分词（为了后面画词云图做准备）
print("正在使用 Jieba 进行中文分词...")
def cut_words(text):
    words = jieba.cut(text)
    # 过滤掉标点符号和单字
    return ' '.join([w for w in words if len(w) > 1])

df['cut_words'] = df['content'].apply(cut_words)

# 保存处理后的最终数据
df.to_csv('final_analysis_result.csv', index=False, encoding='utf-8-sig')
print("✅ 情感分析与分词全部完成！结果已保存至 [final_analysis_result.csv]")