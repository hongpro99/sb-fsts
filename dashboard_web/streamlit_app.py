# streamlit_app.py

import streamlit as st
import feedparser
import openai
import re
from datetime import datetime, date
from collections import Counter


# ✅ OpenAI 설정
from openai import OpenAI
# 🔑 OpenAI API 키 설정
client = OpenAI(api_key = "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")

# ✅ 뉴스 수집 함수
def get_stock_news(query, max_results=10, only_today=False):
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    news_items = []

    for entry in feed.entries:
        summary_cleaned = re.sub('<[^<]+?>', '', entry.summary)

        try:
            published_dt = datetime(*entry.published_parsed[:6])
            published_str = published_dt.strftime("%Y-%m-%d %H:%M")
        except:
            published_dt = None
            published_str = "날짜 정보 없음"

        news_items.append({
            "title": entry.title,
            "link": entry.link,
            "summary": summary_cleaned,
            "published": published_str,
            "published_dt": published_dt
        })

    # ✅ 오늘 뉴스만 필터링
    if only_today:
        today = date.today()
        news_items = [item for item in news_items
                    if item["published_dt"] and item["published_dt"].date() == today]

    # ✅ 최신순 정렬
    news_items.sort(key=lambda x: x["published_dt"] or datetime.min, reverse=True)

    return news_items[:max_results]

# ✅ 감성 추출 함수
def extract_sentiment(text):
    match = re.search(r"\[감성\]\s*(긍정|부정|중립)", text)
    return match.group(1) if match else "분류 실패"

# ✅ GPT 요약 및 감성 분석 함수
def summarize_news_with_gpt(title, content):
    prompt = f"""
다음은 주식 관련 뉴스입니다:

제목: {title}
내용: {content}

1.이 뉴스를 한 문단으로 요약해 주세요.
2.또한 이 뉴스가 투자자 입장에서 긍정적인지, 부정적인지, 중립적인지 판단해 주세요. (긍정/부정/중립 중 하나만 선택)
3.그렇게 판단한 이유를 간단히 설명해 주세요.

결과는 아래 형식으로 반환해 주세요:

[요약]
...

[감성]
긍정 / 부정 / 중립

[이유]
(감성 판단 이유 요약)
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 주식 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content

# ✅ 투자 의견 요약 함수
def generate_investment_opinion(news_summaries, stock_name):
    prompt = f"""
당신은 투자 전문가입니다. 아래는 '{stock_name}'에 대한 최근 뉴스 요약입니다:

{news_summaries}

이 종목의 최근의 뉴스 흐름과 감성을 기반으로 투자자에게 조언을 해 주세요.
'매수 고려 / 관망 / 리스크 주의' 중 하나로 판단하고, 그 이유를 간단히 설명해 주세요.

[투자 의견]
매수 고려 / 관망 / 리스크 주의 중 택 1

[이유]
(간단한 설명)
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 주식 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    return response.choices[0].message.content

# ✅ Streamlit UI
st.title("📈 종목 뉴스 요약 & 감성 분석")
query = st.text_input("종목명을 입력하세요 (예: 삼성전자)")
only_today = st.checkbox("📅 오늘 뉴스만 보기")

if query:
    st.info(f'"{query}" 관련 뉴스를 수집하고 요약 중입니다...')
    news_list = get_stock_news(query, only_today=only_today)

    if not news_list:
        st.warning("오늘 날짜의 뉴스가 없습니다.")
    else:
        sentiment_counter = Counter()
        summarized_texts = []
        results = []

        for i, news in enumerate(news_list):
            with st.spinner("요약 및 분석 중..."):
                result = summarize_news_with_gpt(news["title"], news["summary"])
            sentiment = extract_sentiment(result)
            sentiment_counter[sentiment] += 1
            summarized_texts.append(f"- {news['title']}: {result}")
            results.append((news, result))

        # ✅ 감성 요약 표시
        st.markdown("## 📊 감성 분석 요약")
        st.write(f"👍 긍정: {sentiment_counter['긍정']}건")
        st.write(f"😐 중립: {sentiment_counter['중립']}건")
        st.write(f"👎 부정: {sentiment_counter['부정']}건")
        st.markdown("---")

        # ✅ GPT 투자 의견 표시
        with st.spinner("GPT가 투자 의견을 분석 중..."):
            opinion_result = generate_investment_opinion("\n".join(summarized_texts), query)

        st.markdown("## 🧠 GPT 투자 의견")
        st.success(opinion_result)
        st.markdown("---")

        # ✅ 뉴스 출력
        for i, (news, result) in enumerate(results):
            st.subheader(f"📰 뉴스 {i+1}: {news['title']}")
            st.caption(f"🗓 날짜: {news['published']}")
            st.write(f"[원문 링크]({news['link']})")
            st.write(result)
