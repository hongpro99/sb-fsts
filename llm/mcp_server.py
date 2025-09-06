# weather_server.py
from typing import List
from mcp.server.fastmcp import FastMCP
import pytz
from datetime import datetime, date
import argparse
from collections import Counter
import re
import feedparser
from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import StrOutputParser


parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8005, help="Port number for MCP server")
args = parser.parse_args()

# mcp = FastMCP("Mcp", port=8005)
mcp = FastMCP("Mcp", port=args.port)


@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    return "It's always sunny in New York"

@mcp.tool()
async def get_current_time() -> str:
    """Get current time."""
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    return now.strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
async def get_stock_news_sentiment(stock_name: str, only_today: bool) -> str:
    """주식 관련 뉴스를 조회한 후, 감성 분석 결과를 제공하는 tool 입니다."""

    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        azure_endpoint="https://sb-azure-openai-studio.openai.azure.com/",
        api_version="2024-10-21",
        verbose=True,
        temperature=0  # 창의성 조정,
    )

    news_list = get_stock_news(stock_name, only_today=only_today)

    sentiment_counter = Counter()
    summarized_texts = []
    results = []

    for i, news in enumerate(news_list):
        result = summarize_news_with_gpt(llm, news["title"], news["summary"])
        sentiment = extract_sentiment(result)
        sentiment_counter[sentiment] += 1
        summarized_texts.append(f"- {news['title']}: {result}")
        results.append((news, result))

    # ✅ GPT 투자 의견 표시
    opinion_result = generate_investment_opinion(llm, "\n".join(summarized_texts), stock_name)

    return opinion_result


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

def summarize_news_with_gpt(llm, title, content):
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
    llm_chain = llm | StrOutputParser()

    messages = [
        ("system", "당신은 주식 분석 전문가입니다."),
        ("human", prompt),
    ]

    response = llm_chain.invoke(messages)

    return response

def extract_sentiment(text):
    match = re.search(r"\[감성\]\s*(긍정|부정|중립)", text)
    return match.group(1) if match else "분류 실패"

def generate_investment_opinion(llm, news_summaries, stock_name):
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
    llm_chain = llm | StrOutputParser()

    messages = [
        ("system", "당신은 주식 분석 전문가입니다."),
        ("human", prompt),
    ]

    response = llm_chain.invoke(messages)

    return response


if __name__ == "__main__":
    # mcp.run(transport="sse")
    mcp.run(transport="sse")