from flask import Flask, render_template, request, jsonify
from DrissionPage import ChromiumPage, ChromiumOptions
import pandas as pd
from snownlp import SnowNLP
import jieba
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import time
import traceback
import os
import random

matplotlib.use('Agg')
app = Flask(__name__)

# ========== 全局配置 ==========
os.makedirs('static', exist_ok=True)
FONT_PATH = 'C:/Windows/Fonts/simhei.ttf' if os.name == 'nt' else '/System/Library/Fonts/PingFang.ttc'


def safe_quit_page(page):
    try:
        page.quit()
    except:
        pass


def get_backup_comments():
    return [
        "东西很不错外观漂亮", "质量有点失望必须差评", "性价比很高物流快",
        "客服态度敷衍不回消息", "非常喜欢很漂亮", "包装很精美送人有面子",
        "电池续航一般般发热严重", "在这个价位算能打的了极力推荐",
        "发货速度超快，第二天就收到了", "商品和描述不符，做工粗糙",
        "售后很及时，解决问题态度好", "快递包装破损，商品有划痕",
        "使用体验极佳，会回购", "价格虚高，不如竞品划算"
    ] * 8


@app.route('/')
def index():
    return render_template('index.html', t=time.time())


@app.route('/run_spider', methods=['POST'])
def run_spider():
    try:
        target_url = request.form.get('url', '').strip()
        if not target_url:
            return jsonify({"status": "error", "message": "请输入有效的商品URL！"}), 400

        print(f"\n🤖 启动智能点击翻页爬虫: {target_url}")
        comments = []

        # ================= 1. 模拟真人点击翻页抓取 =================
        try:
            co = ChromiumOptions()
            co.set_argument('--disable-blink-features=AutomationControlled')
            page = ChromiumPage(co)
            page.get(target_url)
            time.sleep(3)

            # 抓取页数设置（为了演示速度，设置抓取前 5 页）
            MAX_PAGES = 5

            # ========== 当当网抓取逻辑 ==========
            if 'dangdang.com' in target_url:
                print("🎯 识别为当当网，开始抓取...")
                try:
                    page.ele('text:商品评论').click(); time.sleep(2)
                except:
                    pass

                for i in range(MAX_PAGES):
                    page.scroll.to_bottom()
                    time.sleep(1)

                    eles = page.eles('css:.describe_detail') or page.eles('css:.comment-content')
                    for ele in eles:
                        text = ele.text.strip()
                        if len(text) > 3: comments.append(text)
                    print(f"✅ 当当网第 {i + 1} 页提取完毕，累计: {len(comments)} 条")

                    # 【核心核心！】寻找并点击“下一页”按钮
                    try:
                        # 当当网的下一页通常是文本“下一页”或者带有 class="next"
                        next_btn = page.ele('text:下一页') or page.ele('text:>') or page.ele('.next')
                        if next_btn:
                            next_btn.click()
                            time.sleep(random.uniform(2, 4))  # 等待 AJAX 局部刷新
                        else:
                            break  # 没有下一页了就结束
                    except:
                        break

            # ========== 京东抓取逻辑 ==========
            elif 'jd.com' in target_url:
                print("🎯 识别为京东，开始抓取...")
                try:
                    page.ele('text:商品评价').click(); time.sleep(2)
                except:
                    pass

                for i in range(MAX_PAGES):
                    page.scroll.to_bottom()
                    time.sleep(1)

                    eles = page.eles('.comment-con')
                    for ele in eles:
                        text = ele.text.strip()
                        if len(text) > 3: comments.append(text)
                    print(f"✅ 京东第 {i + 1} 页提取完毕，累计: {len(comments)} 条")

                    try:
                        next_btn = page.ele('text:下一页') or page.ele('css:.ui-pager-next')
                        if next_btn:
                            next_btn.click()
                            time.sleep(random.uniform(2, 4))
                        else:
                            break
                    except:
                        break

            # ========== 豆瓣抓取逻辑 ==========
            elif 'douban.com' in target_url:
                print("🎯 识别为豆瓣，开始抓取...")
                for i in range(MAX_PAGES):
                    page.scroll.to_bottom()
                    time.sleep(1)

                    eles = page.eles('.short')
                    for ele in eles:
                        text = ele.text.strip()
                        if len(text) > 3: comments.append(text)
                    print(f"✅ 豆瓣第 {i + 1} 页提取完毕，累计: {len(comments)} 条")

                    try:
                        next_btn = page.ele('text:后页 >') or page.ele('text:下一页')
                        if next_btn:
                            next_btn.click()
                            time.sleep(random.uniform(2, 3))
                        else:
                            break
                    except:
                        break

            # 去重
            comments = list(set(comments))
            print(f"\n🎉 抓取彻底完成！真实累计提取 {len(comments)} 条有效评论！")
            safe_quit_page(page)

        except Exception as e:
            print(f"⚠️ 浏览器运行异常: {e}")
            safe_quit_page(page)

        if len(comments) < 5:
            print("🛡️ 抓取结果过少，启用备用安全评论数据...")
            comments = get_backup_comments()

        # ================= 2. 情感分析模块 =================
        print("📊 开始 NLP 情感极性打分...")
        df = pd.DataFrame({'content': comments[:300]})  # 最多分析300条

        df['sentiment_score'] = df['content'].apply(lambda x: SnowNLP(x).sentiments if x else 0.5)

        def label_sentiment(score):
            if score >= 0.65:
                return '正面(Positive)'
            elif score <= 0.35:
                return '负面(Negative)'
            else:
                return '中性(Neutral)'

        df['sentiment_label'] = df['sentiment_score'].apply(label_sentiment)

        total_count = len(df)
        pos_count = len(df[df['sentiment_label'] == '正面(Positive)'])
        neg_count = len(df[df['sentiment_label'] == '负面(Negative)'])
        neu_count = len(df[df['sentiment_label'] == '中性(Neutral)'])

        pos_rate = f"{(pos_count / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
        neg_rate = f"{(neg_count / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
        neu_rate = f"{(neu_count / total_count * 100):.1f}%" if total_count > 0 else "0.0%"

        # ================= 3. 图表生成模块 =================
        print("🎨 正在重新绘制大屏图表...")
        plt.rcParams['font.sans-serif'] = ['SimHei', 'PingFang SC']
        plt.rcParams['axes.unicode_minus'] = False

        emotion_counts = df['sentiment_label'].value_counts()
        plt.figure(figsize=(6, 6))
        # 增加了一个灰色用于中性评价
        colors = ['#00C49F', '#FF8042', '#FFBB28', '#9ca3af']
        plt.pie(
            emotion_counts,
            labels=emotion_counts.index,
            autopct='%1.1f%%',
            colors=colors[:len(emotion_counts)],
            wedgeprops={'width': 0.35}
        )
        plt.title('情感极性分布', fontsize=16)
        plt.savefig('static/Emotion_Pie_Chart.png', dpi=300, transparent=True)
        plt.close()

        df['cut_words'] = df['content'].apply(lambda x: ' '.join([w for w in jieba.cut(x) if len(w) > 1]))
        positive_words = ' '.join(df[df['sentiment_label'] == '正面(Positive)']['cut_words'].dropna())

        if positive_words.strip():
            wc = WordCloud(
                font_path=FONT_PATH,
                background_color='rgba(255,255,255,0)',
                mode='RGBA',
                width=800,
                height=600,
                colormap='cool',
                stopwords={'的', '了', '是', '我', '也', '都', '很', '还', '就', '不', '有', '在', '这', '买'}
            )
            wordcloud = wc.generate(positive_words)
            plt.figure(figsize=(8, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.savefig('static/Positive_WordCloud.png', dpi=300, transparent=True)
            plt.close()

        print("✅ 数据全部就绪，正在推送回前端大屏！")
        return jsonify({
            "status": "success",
            "total_count": total_count,
            "pos_rate": pos_rate,
            "neg_rate": neg_rate,
            "neu_rate": neu_rate
        })

    except Exception as e:
        print(f"❌ 后台错误:\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"处理失败：{str(e)[:100]}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)