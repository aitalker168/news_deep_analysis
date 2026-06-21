"""
新闻深度分析工具 - 基于Streamlit与GitHub Models API
用户输入新闻文本，AI按照“老记者6大维度”返回分析结果
支持部署到Streamlit Cloud，需在Secrets中设置GITHUB_TOKEN
"""

import streamlit as st
import requests
import json
from typing import Optional

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="新闻深度解构 | 老记者AI助手",
    page_icon="📰",
    layout="centered",
)

# ---------- 从Secrets或侧边栏获取GitHub Token ----------
def get_github_token() -> Optional[str]:
    # 优先从Streamlit secrets读取
    try:
        return st.secrets["GITHUB_TOKEN"]
    except (KeyError, FileNotFoundError):
        pass
    # 其次尝试环境变量
    import os
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    # 最后让用户在侧边栏输入
    return st.sidebar.text_input(
        "🔑 请输入你的 GitHub Token",
        type="password",
        help="在 https://github.com/settings/tokens 创建，无需任何权限",
    )

# ---------- 调用GitHub Models API ----------
def call_ai_model(news_text: str, token: str) -> str:
    """
    使用GitHub Models API中的gpt-4o-mini模型
    API文档: https://docs.github.com/en/github-models
    """
    endpoint = "https://models.inference.ai.azure.com"
    model = "gpt-4o-mini"  # 也可用 "meta-llama-3-8b-instruct"

    system_prompt = """你是一位拥有40年经验的老记者。请你严格按照以下6个维度，对用户提供的新闻进行深度分析。每个维度要给出具体、有洞察力的内容，而不是空洞的套话。使用中文回答。

1. **核心利益冲突 (Core Conflict & Stakeholders)**  
   找出最核心的利益相关方，分析各自的诉求与不可调和的冲突。

2. **前因与历史脉络 (Context & Backstory)**  
   提供简要时间线（过去3-5年），说明哪些长期趋势导致了当前事件。

3. **“没说出来的话” (Hidden Agendas & Omissions)**  
   识别报道中可能的信息盲区、被淡化或缺失的关键声音/数据。

4. **行业/社会宏观背景 (Macro Background)**  
   当前所处的大气候（行业周期、政策法规、技术变革、敏感时期等）。

5. **多方观点与反向论证 (Counter-Perspectives)**  
   提供至少两种针锋相对的专业解读，跳出单一视角。

6. **潜在的多米诺效应 (Secondary Effects & Predictions)**  
   评估短期和长期可能引发的连锁反应，以及对普通人的影响。

格式要求：
- 每个维度标题加粗显示，内容分段清晰。
- 在最后给出一个简短的总体判断（一句话总结）。"""

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下新闻：\n\n{news_text}"},
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
    }

    try:
        response = requests.post(
            f"{endpoint}/openai/deployments/{model}/chat/completions?api-version=2024-12-01-preview",
            headers=headers,
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP错误: {e.response.status_code} - {e.response.text}")
        if "401" in str(e):
            st.error("GitHub Token无效或已过期，请检查后在侧边栏输入正确的Token。")
        return ""
    except Exception as e:
        st.error(f"请求AI失败: {str(e)}")
        return ""

# ---------- 主界面 ----------
def main():
    st.title("📰 新闻深度解构")
    st.markdown(
        "**“新闻的表面是沙子，背后的真相才是金子。”**\n\n"
        "本工具由一位40年经验的老记者设计，通过6个核心维度帮你剥开新闻表象，看清本质。"
    )

    # 获取Token
    token = get_github_token()
    if not token:
        st.warning("⚠️ 请在左侧边栏输入你的 GitHub Token 以启用AI分析。")
        return

    # 新闻输入
    news_text = st.text_area(
        "📝 粘贴新闻报导的全文或摘要",
        height=300,
        placeholder="将新闻内容粘贴到这里...",
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        analyze_btn = st.button("🔍 开始深度分析", type="primary", use_container_width=True)

    # 分析过程
    if analyze_btn and news_text.strip():
        with st.spinner("🕵️ 老记者正在剥洋葱...可能需要30秒"):
            analysis = call_ai_model(news_text, token)

        if analysis:
            st.success("✅ 分析完成！")
            st.markdown("---")
            st.markdown(analysis)
            st.markdown("---")
            st.caption("本分析由AI基于公开模型生成，仅供参考。请独立思考并核实关键信息。")
        else:
            st.error("分析失败，请检查Token或稍后重试。")

    elif analyze_btn and not news_text.strip():
        st.warning("请先输入新闻内容！")

    # 侧边栏说明
    st.sidebar.markdown("## 💡 使用说明")
    st.sidebar.markdown(
        """
1. **在左侧输入你的 GitHub Token**（可在 [GitHub Settings](https://github.com/settings/tokens) 创建，无需任何权限）
2. **粘贴新闻全文或摘要**
3. **点击“开始深度分析”**
4. AI会从6个维度返回深度解读

**部署到Streamlit Cloud后，只需在App的Secrets中添加：**
```toml
GITHUB_TOKEN = "你的token"