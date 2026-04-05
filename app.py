from __future__ import annotations

import os
import re
import json
import base64
import random
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st
import yaml
import pandas as pd
import altair as alt
import httpx
from pypdf import PdfReader

# Optional imports
try:
    from docx import Document  # python-docx
except Exception:
    Document = None

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except Exception:
    canvas = None
    letter = None

# LLM SDKs
from openai import OpenAI
import google.generativeai as genai
from anthropic import Anthropic


# =========================
# Constants & configuration
# =========================

APP_TITLE = "Agentic Medical Device Reviewer — WOW Edition"
DEFAULT_MAX_TOKENS = 12000

ALL_MODELS = [
    # OpenAI
    "gpt-4o-mini",
    "gpt-4.1-mini",
    # Gemini
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash-lite",
    "gemini-3-pro-preview",
    # Anthropic
    "claude-3-5-sonnet-2024-10",
    "claude-3-5-haiku-20241022",
    # Grok
    "grok-4-fast-reasoning",
    "grok-3-mini",
]

OPENAI_MODELS = {"gpt-4o-mini", "gpt-4.1-mini"}
GEMINI_MODELS = {"gemini-2.5-flash", "gemini-3-flash-preview", "gemini-2.5-flash-lite", "gemini-3-pro-preview"}
ANTHROPIC_MODELS = {"claude-3-5-sonnet-2024-10", "claude-3-5-haiku-20241022"}
GROK_MODELS = {"grok-4-fast-reasoning", "grok-3-mini"}

# Per user requirement: guidance studio pipeline uses these two only
GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE = ["gemini-2.5-flash", "gemini-3-flash-preview"]

PAINTER_STYLES = [
    "Van Gogh", "Monet", "Picasso", "Da Vinci", "Rembrandt",
    "Matisse", "Kandinsky", "Hokusai", "Yayoi Kusama", "Frida Kahlo",
    "Salvador Dali", "Rothko", "Pollock", "Chagall", "Basquiat",
    "Haring", "Georgia O'Keeffe", "Turner", "Seurat", "Escher",
]

LABELS = {
    "Dashboard": {"English": "Dashboard", "繁體中文": "儀表板"},
    "Guidance Studio": {"English": "Guidance Research & Report Studio", "繁體中文": "指引研究與報告工作室"},
    "TW Premarket": {"English": "TW Premarket Application", "繁體中文": "第二、三等級醫療器材查驗登記"},
    "510k_tab": {"English": "510(k) Intelligence", "繁體中文": "510(k) 智能分析"},
    "PDF → Markdown": {"English": "PDF → Markdown", "繁體中文": "PDF → Markdown"},
    "Checklist & Report": {"English": "510(k) Review Pipeline", "繁體中文": "510(k) 審查全流程"},
    "Note Keeper & Magics": {"English": "Note Keeper & Magics", "繁體中文": "筆記助手與魔法"},
    "Agents Config": {"English": "Agents Config Studio", "繁體中文": "代理設定工作室"},
}

STYLE_CSS = {
    "Van Gogh": "body { background: radial-gradient(circle at top left, #243B55, #141E30); }",
    "Monet": "body { background: linear-gradient(120deg, #a1c4fd, #c2e9fb); }",
    "Picasso": "body { background: linear-gradient(135deg, #ff9a9e, #fecfef); }",
    "Da Vinci": "body { background: radial-gradient(circle, #f9f1c6, #c9a66b); }",
    "Rembrandt": "body { background: radial-gradient(circle, #2c1810, #0b090a); }",
    "Matisse": "body { background: linear-gradient(135deg, #ffecd2, #fcb69f); }",
    "Kandinsky": "body { background: linear-gradient(135deg, #00c6ff, #0072ff); }",
    "Hokusai": "body { background: linear-gradient(135deg, #2b5876, #4e4376); }",
    "Yayoi Kusama": "body { background: radial-gradient(circle, #ffdd00, #ff6a00); }",
    "Frida Kahlo": "body { background: linear-gradient(135deg, #f8b195, #f67280, #c06c84); }",
    "Salvador Dali": "body { background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d); }",
    "Rothko": "body { background: linear-gradient(135deg, #141E30, #243B55); }",
    "Pollock": "body { background: repeating-linear-gradient(45deg,#222,#222 10px,#333 10px,#333 20px); }",
    "Chagall": "body { background: linear-gradient(135deg, #a18cd1, #fbc2eb); }",
    "Basquiat": "body { background: linear-gradient(135deg, #f7971e, #ffd200); }",
    "Haring": "body { background: linear-gradient(135deg, #ff512f, #dd2476); }",
    "Georgia O'Keeffe": "body { background: linear-gradient(135deg, #ffefba, #ffffff); }",
    "Turner": "body { background: linear-gradient(135deg, #f8ffae, #43c6ac); }",
    "Seurat": "body { background: radial-gradient(circle, #e0eafc, #cfdef3); }",
    "Escher": "body { background: linear-gradient(135deg, #232526, #414345); }",
}

DEFAULT_REPORT_TEMPLATE_TW = """# 骨外固定器查驗登記審查指引與審查清單

本文件旨在規範骨外固定器（Orthopedic External Fixators）於醫療器材查驗登記時之臨床前安全與有效性要求，確保產品符合應有之品質標準。

---

## 第一部分：骨外固定器臨床前審查指引 (Review Guidance)

### 1. 產品規格要求 (Product Specifications)
（請填入：用途、組件、工程圖、材質、等同性比較…）

### 2. 生物相容性評估 (Biocompatibility)
（請填入：ISO 10993、豁免條件、測項…）

### 3. 滅菌確效 (Sterilization)
（請填入：SAL 10^-6、ISO 11135/11137/17665…）

### 4. 機械性質評估 (Mechanical Testing)
（請填入：ASTM F1541、剛性、疲勞、鬆脫…）

### 5. 特定風險與額外評估 (Special Risks)
（請填入：MRI、動態機能、特殊宣稱…）

---

## 第二部分：骨外固定器查驗登記審查清單 (Review Checklist)

| 審查項目 | 審查重點 / 具備文件 | 審查結果 (符合/不適用/待補) | 備註說明 |
|---|---|---|---|
| 1.1 用途說明 | 是否包含完整臨床適應症與適應對象？ |  |  |
| 1.2 組件目錄 | 是否列出所有系統組件？ |  |  |
| 2.1 生物相容性 | 是否依 ISO 10993 提供報告？ |  |  |
| 3.1 滅菌 SAL | 是否符合 ≤ 10^-6？ |  |  |
| 4.1 機械性質 | 是否提供符合 ASTM F1541 測試？ |  |  |
| 5.3 MRI 相容性 | 宣稱 MRI 相容者是否提交評估？ |  |  |

---

## 審查結論
- □ 建議核准
- □ 需補件再議（補件項目：）
- □ 不予核准

審查人員簽章：____________________ 日期：YYYY-MM-DD
"""


# =========================
# Localization & style
# =========================

def t(key: str) -> str:
    lang = st.session_state.settings.get("language", "English")
    return LABELS.get(key, {}).get(lang, key)


def apply_style(theme: str, painter_style: str):
    css = STYLE_CSS.get(painter_style, "")
    if theme == "Dark":
        css += """
        body { color: #e5e7eb; }
        .stButton>button { background-color: #111827; color: white; border-radius: 999px; }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
            background-color: #0b1220 !important; color: #e5e7eb !important; border-radius: 0.6rem;
        }
        """
    else:
        css += """
        body { color: #111827; }
        .stButton>button { background-color: #2563eb; color: white; border-radius: 999px; }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
            background-color: #ffffff !important; color: #111827 !important; border-radius: 0.6rem;
        }
        """

    css += """
    .wow-card {
        border-radius: 18px;
        padding: 14px 18px;
        margin-bottom: 0.75rem;
        box-shadow: 0 14px 35px rgba(15,23,42,0.35);
        color: #f9fafb;
    }
    .wow-card-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        opacity: 0.9;
    }
    .wow-card-main { font-size: 1.5rem; font-weight: 800; margin-top: 4px; }
    .wow-badge {
        display:inline-flex; align-items:center;
        padding:2px 10px; border-radius:999px;
        font-size:0.75rem; font-weight:650;
        background:rgba(15,23,42,0.18);
        border:1px solid rgba(148,163,184,0.55);
        margin-right: 6px;
        margin-top: 6px;
    }
    .wow-divider { height: 1px; background: rgba(148,163,184,0.35); margin: 10px 0; }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# =========================
# LLM routing
# =========================

def get_provider(model: str) -> str:
    if model in OPENAI_MODELS:
        return "openai"
    if model in GEMINI_MODELS:
        return "gemini"
    if model in ANTHROPIC_MODELS:
        return "anthropic"
    if model in GROK_MODELS:
        return "grok"

    lower = model.lower()
    if lower.startswith("gpt-") or lower.startswith("o"):
        return "openai"
    if "gemini" in lower:
        return "gemini"
    if "claude" in lower:
        return "anthropic"
    if "grok" in lower:
        return "grok"
    raise ValueError(f"Unknown model: {model}")


def call_llm(
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.2,
    api_keys: Optional[dict] = None,
) -> str:
    provider = get_provider(model)
    api_keys = api_keys or {}

    def get_key(name: str, env_var: str) -> str:
        return (api_keys.get(name) or os.getenv(env_var) or "").strip()

    if provider == "openai":
        key = get_key("openai", "OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Missing OpenAI API key.")
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            max_tokens=int(max_tokens),
            temperature=float(temperature),
        )
        return (resp.choices[0].message.content or "").strip()

    if provider == "gemini":
        key = get_key("gemini", "GEMINI_API_KEY")
        if not key:
            raise RuntimeError("Missing Gemini API key.")
        genai.configure(api_key=key)
        llm = genai.GenerativeModel(model)
        resp = llm.generate_content(
            f"{system_prompt}\n\n{user_prompt}",
            generation_config={
                "max_output_tokens": int(max_tokens),
                "temperature": float(temperature),
            },
        )
        text = getattr(resp, "text", "") or ""
        return text.strip()

    if provider == "anthropic":
        key = get_key("anthropic", "ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("Missing Anthropic API key.")
        client = Anthropic(api_key=key)
        resp = client.messages.create(
            model=model,
            system=system_prompt,
            max_tokens=int(max_tokens),
            temperature=float(temperature),
            messages=[{"role": "user", "content": user_prompt}],
        )
        try:
            parts = resp.content or []
            if parts and hasattr(parts[0], "text"):
                return (parts[0].text or "").strip()
        except Exception:
            pass
        return str(resp).strip()

    if provider == "grok":
        key = get_key("grok", "GROK_API_KEY")
        if not key:
            raise RuntimeError("Missing Grok (xAI) API key.")
        with httpx.Client(base_url="https://api.x.ai/v1", timeout=60) as client:
            r = client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": model,
                    "messages": [{"role": "system", "content": system_prompt},
                                 {"role": "user", "content": user_prompt}],
                    "max_tokens": int(max_tokens),
                    "temperature": float(temperature),
                },
            )
            r.raise_for_status()
            data = r.json()
        return (data["choices"][0]["message"]["content"] or "").strip()

    raise RuntimeError(f"Unsupported provider for model {model}")


# =========================
# Generic helpers
# =========================

def now_utc_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def approx_tokens(text: str) -> int:
    return max(1, int(len(text or "") / 4))


def safe_decode(b: bytes) -> str:
    return (b or b"").decode("utf-8", errors="ignore")


def show_status(step_name: str, status: str):
    color = {
        "pending": "gray",
        "running": "#f59e0b",
        "done": "#10b981",
        "error": "#ef4444",
    }.get(status, "gray")
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;margin-bottom:0.25rem;">
          <div style="width:10px;height:10px;border-radius:50%;background:{color};
                      margin-right:6px;"></div>
          <span style="font-size:0.9rem;">{step_name} – <b>{status}</b></span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def log_event(tab: str, agent: str, model: str, tokens_est: int, extras: Optional[dict] = None):
    st.session_state["history"].append(
        {
            "tab": tab,
            "agent": agent,
            "model": model,
            "tokens_est": int(tokens_est),
            "ts": now_utc_iso(),
            "extras": extras or {},
        }
    )


def record_artifact(name: str, kind: str, content: str, language: str, meta: Optional[dict] = None):
    st.session_state.setdefault("artifacts", [])
    st.session_state["artifacts"].append({
        "name": name,
        "kind": kind,
        "language": language,
        "chars": len(content or ""),
        "ts": now_utc_iso(),
        "meta": meta or {},
    })


def download_block(label: str, filename: str, content: str, mime: str = "text/plain"):
    st.download_button(label, data=(content or "").encode("utf-8"), file_name=filename, mime=mime)


def extract_pdf_pages_to_text(pdf_bytes: bytes, start_page: int, end_page: int) -> str:
    reader = PdfReader(BytesIO(pdf_bytes))
    n = len(reader.pages)
    start = max(0, int(start_page) - 1)
    end = min(n, int(end_page))
    texts: List[str] = []
    for i in range(start, end):
        try:
            texts.append(reader.pages[i].extract_text() or "")
        except Exception:
            texts.append("")
    return "\n\n".join([t for t in texts if t.strip()])


def extract_docx_to_text(docx_bytes: bytes) -> str:
    if Document is None:
        return ""
    try:
        doc = Document(BytesIO(docx_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""


def create_pdf_from_text(text: str) -> bytes:
    if canvas is None or letter is None:
        raise RuntimeError("PDF export needs 'reportlab'. Add it to requirements.txt.")
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    margin = 72
    line_height = 14
    y = height - margin
    for line in (text or "").splitlines():
        if y < margin:
            c.showPage()
            y = height - margin
        c.drawString(margin, y, line[:2000])
        y -= line_height
    c.save()
    buf.seek(0)
    return buf.getvalue()


def strip_html_to_text(html: str) -> str:
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    html = re.sub(r"(?is)<.*?>", " ", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


# =========================
# Lightweight web retrieval (no key)
# =========================

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


def duckduckgo_search(query: str, max_results: int = 8, timeout: int = 25) -> List[SearchResult]:
    q = query.strip()
    if not q:
        return []
    url = "https://duckduckgo.com/html/"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    }
    try:
        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            r = client.post(url, data={"q": q})
            r.raise_for_status()
            html = r.text
    except Exception:
        return []

    results: List[SearchResult] = []
    for m in re.finditer(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html):
        href = m.group(1).strip()
        title_html = m.group(2).strip()
        title = strip_html_to_text(title_html)
        if not href.startswith("http"):
            continue

        snippet = ""
        tail = html[m.end(): m.end() + 1400]
        sn = re.search(r'(?is)class="result__snippet"[^>]*>(.*?)</(?:a|div)>', tail)
        if sn:
            snippet = strip_html_to_text(sn.group(1))

        results.append(SearchResult(title=title[:240], url=href, snippet=snippet[:320]))
        if len(results) >= max_results:
            break
    return results


def fetch_url_text(url: str, timeout: int = 25, max_chars: int = 12000) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
    }
    try:
        with httpx.Client(timeout=timeout, headers=headers, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            txt = strip_html_to_text(r.text or "")
            return txt[:max_chars]
    except Exception:
        return ""


def build_fda_research_pack(guidance_text: str, user_hints: str, max_urls: int = 10) -> Tuple[str, List[dict]]:
    guidance_text = (guidance_text or "").strip()
    hints = (user_hints or "").strip()

    kw = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9\-\(\)\/]{2,}", guidance_text[:5000]):
        if token.lower() in {"and", "the", "for", "with", "this", "that", "from", "into"}:
            continue
        kw.append(token)
    kw = list(dict.fromkeys(kw))[:10]
    keyword_hint = " ".join(kw[:6]) if kw else ""

    queries = []
    if hints:
        queries.append(f"site:fda.gov guidance {hints}")
        queries.append(f"site:fda.gov recognized consensus standards {hints}")
    queries += [
        f"site:fda.gov guidance {keyword_hint}".strip(),
        f"site:fda.gov recognized consensus standards {keyword_hint}".strip(),
        "FDA recognized consensus standards database",
        "FDA guidance medical device performance testing",
        "site:fda.gov 510(k) performance testing guidance",
    ]

    # De-dup and cap
    uniq = []
    for q in queries:
        q = re.sub(r"\s+", " ", q).strip()
        if q and q not in uniq:
            uniq.append(q)
    uniq = uniq[:6]

    sources: List[dict] = []
    blocks: List[str] = []
    for q in uniq:
        results = duckduckgo_search(q, max_results=6)
        if not results:
            continue
        for r in results:
            if "fda.gov" not in r.url:
                continue
            text = fetch_url_text(r.url, max_chars=8000)
            if not text:
                continue
            sources.append({
                "query": q,
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "fetched_text": text,
            })
            blocks.append(
                f"### Source\n- Query: {q}\n- Title: {r.title}\n- URL: {r.url}\n\n"
                f"**Snippet:** {r.snippet}\n\n"
                f"**Fetched text (truncated):**\n{text}\n"
            )
            if len(sources) >= max_urls:
                break
        if len(sources) >= max_urls:
            break

    combined = "# FDA Retrieval Pack (Best-effort)\n\n" + ("\n\n".join(blocks) if blocks else "_No sources retrieved (network blocked or search unavailable)._")
    return combined, sources


# =========================
# Agent UI runner
# =========================

def agent_run_ui(
    agent_id: str,
    tab_key: str,
    default_prompt: str,
    default_input_text: str = "",
    allow_model_override: bool = True,
    tab_label_for_history: Optional[str] = None,
    model_allowlist: Optional[List[str]] = None,
    helper_buttons: bool = True,
):
    agents_cfg = st.session_state.get("agents_cfg", {})
    agents_dict = agents_cfg.get("agents", {}) if isinstance(agents_cfg, dict) else {}

    agent_cfg = agents_dict.get(agent_id, {
        "name": agent_id,
        "model": st.session_state.settings["model"],
        "system_prompt": "",
        "max_tokens": st.session_state.settings["max_tokens"],
    })

    status_key = f"{tab_key}_status"
    if status_key not in st.session_state:
        st.session_state[status_key] = "pending"

    show_status(agent_cfg.get("name", agent_id), st.session_state[status_key])

    allowed_models = model_allowlist or ALL_MODELS
    base_model = st.session_state.get(f"{tab_key}_model", agent_cfg.get("model", st.session_state.settings["model"]))
    if base_model not in allowed_models:
        base_model = allowed_models[0]

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        user_prompt = st.text_area(
            "Prompt",
            value=st.session_state.get(f"{tab_key}_prompt", default_prompt),
            height=160,
            key=f"{tab_key}_prompt",
        )
    with col2:
        model = st.selectbox(
            "Model",
            allowed_models,
            index=allowed_models.index(base_model),
            disabled=not allow_model_override,
            key=f"{tab_key}_model",
        )
    with col3:
        max_tokens = st.number_input(
            "max_tokens",
            min_value=1000,
            max_value=120000,
            value=int(st.session_state.get(f"{tab_key}_max_tokens", agent_cfg.get("max_tokens", st.session_state.settings["max_tokens"]))),
            step=1000,
            key=f"{tab_key}_max_tokens",
        )

    input_text = st.text_area(
        "Input Text / Markdown",
        value=st.session_state.get(f"{tab_key}_input", default_input_text),
        height=260,
        key=f"{tab_key}_input",
    )

    col_run, col_use = st.columns([1, 2])
    with col_run:
        run = st.button("Run Agent", key=f"{tab_key}_run")
    with col_use:
        if helper_buttons:
            if st.button("Use previous output as input", key=f"{tab_key}_use_prev_out"):
                prev = st.session_state.get(f"{tab_key}_output_effective") or st.session_state.get(f"{tab_key}_output") or ""
                st.session_state[f"{tab_key}_input"] = prev
                st.rerun()

    if run:
        st.session_state[status_key] = "running"
        show_status(agent_cfg.get("name", agent_id), "running")

        api_keys = st.session_state.get("api_keys", {})
        system_prompt = agent_cfg.get("system_prompt", "")
        user_full = f"{user_prompt}\n\n---\n\n{input_text}".strip()

        with st.spinner("Running agent..."):
            try:
                out = call_llm(
                    model=model,
                    system_prompt=system_prompt,
                    user_prompt=user_full,
                    max_tokens=int(max_tokens),
                    temperature=float(st.session_state.settings["temperature"]),
                    api_keys=api_keys,
                )
                st.session_state[f"{tab_key}_output"] = out
                st.session_state[status_key] = "done"

                token_est = approx_tokens(user_full + "\n" + out)
                log_event(
                    tab_label_for_history or tab_key,
                    agent_cfg.get("name", agent_id),
                    model,
                    token_est,
                    extras={"agent_id": agent_id},
                )
            except Exception as e:
                st.session_state[status_key] = "error"
                st.error(f"Agent error: {e}")

    output = st.session_state.get(f"{tab_key}_output", "")
    view_mode = st.radio("View mode", ["Markdown", "Plain text"], horizontal=True, key=f"{tab_key}_viewmode")
    edited = st.text_area("Output (editable)", value=output, height=320, key=f"{tab_key}_output_edited")
    st.session_state[f"{tab_key}_output_effective"] = edited


# =========================
# Sidebar
# =========================

def render_sidebar():
    with st.sidebar:
        st.markdown("### Global Settings")

        st.session_state.settings["theme"] = st.radio(
            "Theme", ["Light", "Dark"],
            index=0 if st.session_state.settings["theme"] == "Light" else 1,
        )

        st.session_state.settings["language"] = st.radio(
            "Language", ["English", "繁體中文"],
            index=0 if st.session_state.settings["language"] == "English" else 1,
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            style = st.selectbox(
                "Painter Style",
                PAINTER_STYLES,
                index=PAINTER_STYLES.index(st.session_state.settings["painter_style"]),
            )
        with col2:
            if st.button("Jackpot!"):
                style = random.choice(PAINTER_STYLES)
        st.session_state.settings["painter_style"] = style

        st.session_state.settings["model"] = st.selectbox(
            "Default Model",
            ALL_MODELS,
            index=ALL_MODELS.index(st.session_state.settings["model"]) if st.session_state.settings["model"] in ALL_MODELS else 0,
        )
        st.session_state.settings["max_tokens"] = st.number_input(
            "Default max_tokens",
            min_value=1000,
            max_value=120000,
            value=int(st.session_state.settings["max_tokens"]),
            step=1000,
        )
        st.session_state.settings["temperature"] = st.slider(
            "Temperature",
            0.0, 1.0,
            float(st.session_state.settings["temperature"]),
            0.05,
        )

        st.markdown("---")
        st.markdown("### API Keys")

        keys: Dict[str, str] = {}

        # Do not show key values when env var exists
        if os.getenv("OPENAI_API_KEY"):
            keys["openai"] = os.getenv("OPENAI_API_KEY", "")
            st.caption("OpenAI key from environment.")
        else:
            keys["openai"] = st.text_input("OpenAI API Key", type="password")

        if os.getenv("GEMINI_API_KEY"):
            keys["gemini"] = os.getenv("GEMINI_API_KEY", "")
            st.caption("Gemini key from environment.")
        else:
            keys["gemini"] = st.text_input("Gemini API Key", type="password")

        if os.getenv("ANTHROPIC_API_KEY"):
            keys["anthropic"] = os.getenv("ANTHROPIC_API_KEY", "")
            st.caption("Anthropic key from environment.")
        else:
            keys["anthropic"] = st.text_input("Anthropic API Key", type="password")

        if os.getenv("GROK_API_KEY"):
            keys["grok"] = os.getenv("GROK_API_KEY", "")
            st.caption("Grok key from environment.")
        else:
            keys["grok"] = st.text_input("Grok API Key", type="password")

        st.session_state["api_keys"] = keys

        st.markdown("---")
        st.markdown("### Agents Catalog (agents.yaml)")
        uploaded_agents = st.file_uploader("Upload custom agents.yaml", type=["yaml", "yml"], key="sidebar_agents_yaml")
        if uploaded_agents is not None:
            try:
                cfg = yaml.safe_load(uploaded_agents.getvalue())
                if isinstance(cfg, dict) and "agents" in cfg:
                    st.session_state["agents_cfg"] = cfg
                    st.success("Custom agents.yaml loaded for this session.")
                else:
                    st.warning("Uploaded YAML has no top-level 'agents' key. Keeping current config.")
            except Exception as e:
                st.error(f"Failed to parse uploaded YAML: {e}")


# =========================
# Dashboard (expanded)
# =========================

def render_dashboard():
    st.title(t("Dashboard"))
    hist = st.session_state["history"]
    if not hist:
        st.info("No runs yet.")
        return

    df = pd.DataFrame(hist)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Runs", len(df))
    with col2:
        st.metric("Unique Tabs", int(df["tab"].nunique()))
    with col3:
        st.metric("Approx Tokens", int(df["tokens_est"].sum()))
    with col4:
        st.metric("Artifacts", len(st.session_state.get("artifacts", [])))

    st.markdown("### WOW Status Wall — Latest Activity")
    last = df.sort_values("ts", ascending=False).iloc[0]
    wow_color = "linear-gradient(135deg,#22c55e,#16a34a)"
    if int(last["tokens_est"]) > 40000:
        wow_color = "linear-gradient(135deg,#f97316,#ea580c)"
    if int(last["tokens_est"]) > 80000:
        wow_color = "linear-gradient(135deg,#ef4444,#b91c1c)"

    st.markdown(
        f"""
        <div class="wow-card" style="background:{wow_color};">
          <div class="wow-card-title">LATEST RUN SNAPSHOT</div>
          <div class="wow-card-main">{last['tab']} · {last['agent']}</div>
          <div style="margin-top:6px;font-size:0.9rem;">
            Model: <b>{last['model']}</b> · Tokens ≈ <b>{int(last['tokens_est'])}</b><br>
            Time (UTC): {last['ts']}
          </div>
          <div class="wow-divider"></div>
          <span class="wow-badge">Status: active</span>
          <span class="wow-badge">Theme: {st.session_state.settings.get("theme")}</span>
          <span class="wow-badge">Style: {st.session_state.settings.get("painter_style")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Runs by Tab")
    chart_tab = alt.Chart(df).mark_bar().encode(
        x=alt.X("tab:N", sort="-y"),
        y="count():Q",
        color="tab:N",
        tooltip=["tab", "count()"],
    )
    st.altair_chart(chart_tab, use_container_width=True)

    st.markdown("### Runs by Model")
    chart_model = alt.Chart(df).mark_bar().encode(
        x=alt.X("model:N", sort="-y"),
        y="count():Q",
        color="model:N",
        tooltip=["model", "count()"],
    )
    st.altair_chart(chart_model, use_container_width=True)

    st.markdown("### Model × Tab Usage Heatmap")
    heat_df = df.groupby(["tab", "model"]).size().reset_index(name="count")
    heatmap = alt.Chart(heat_df).mark_rect().encode(
        x=alt.X("model:N", title="Model"),
        y=alt.Y("tab:N", title="Tab"),
        color=alt.Color("count:Q", scale=alt.Scale(scheme="blues"), title="Runs"),
        tooltip=["tab", "model", "count"],
    ).properties(height=260)
    st.altair_chart(heatmap, use_container_width=True)

    st.markdown("### Token Usage Over Time")
    df_time = df.copy()
    df_time["ts"] = pd.to_datetime(df_time["ts"])
    chart_time = alt.Chart(df_time).mark_line(point=True).encode(
        x="ts:T",
        y="tokens_est:Q",
        color="tab:N",
        tooltip=["ts", "tab", "agent", "model", "tokens_est"],
    )
    st.altair_chart(chart_time, use_container_width=True)

    st.markdown("### Download Center (Session Artifacts)")
    artifacts = st.session_state.get("artifacts", [])
    if not artifacts:
        st.caption("No artifacts recorded yet.")
        return
    art_df = pd.DataFrame(artifacts)
    st.dataframe(art_df.sort_values("ts", ascending=False), use_container_width=True, height=260)


# =========================
# TW Premarket helpers (full)
# =========================

TW_APP_FIELDS = [
    "doc_no", "e_no", "apply_date", "case_type", "device_category", "case_kind",
    "origin", "product_class", "similar", "replace_flag", "prior_app_no",
    "name_zh", "name_en", "indications", "spec_comp",
    "main_cat", "item_code", "item_name",
    "uniform_id", "firm_name", "firm_addr",
    "resp_name", "contact_name", "contact_tel", "contact_fax", "contact_email",
    "confirm_match", "cert_raps", "cert_ahwp", "cert_other",
    "manu_type", "manu_name", "manu_country", "manu_addr", "manu_note",
    "auth_applicable", "auth_desc",
    "cfs_applicable", "cfs_desc",
    "qms_applicable", "qms_desc",
    "similar_info", "labeling_info", "tech_file_info",
    "preclinical_info", "preclinical_replace",
    "clinical_just", "clinical_info",
]


def build_tw_app_dict_from_session() -> dict:
    s = st.session_state
    apply_date = s.get("tw_apply_date")
    apply_date_str = apply_date.strftime("%Y-%m-%d") if apply_date else ""
    return {
        "doc_no": s.get("tw_doc_no", ""),
        "e_no": s.get("tw_e_no", ""),
        "apply_date": apply_date_str,
        "case_type": s.get("tw_case_type", ""),
        "device_category": s.get("tw_device_category", ""),
        "case_kind": s.get("tw_case_kind", ""),
        "origin": s.get("tw_origin", ""),
        "product_class": s.get("tw_product_class", ""),
        "similar": s.get("tw_similar", ""),
        "replace_flag": s.get("tw_replace_flag", ""),
        "prior_app_no": s.get("tw_prior_app_no", ""),
        "name_zh": s.get("tw_dev_name_zh", ""),
        "name_en": s.get("tw_dev_name_en", ""),
        "indications": s.get("tw_indications", ""),
        "spec_comp": s.get("tw_spec_comp", ""),
        "main_cat": s.get("tw_main_cat", ""),
        "item_code": s.get("tw_item_code", ""),
        "item_name": s.get("tw_item_name", ""),
        "uniform_id": s.get("tw_uniform_id", ""),
        "firm_name": s.get("tw_firm_name", ""),
        "firm_addr": s.get("tw_firm_addr", ""),
        "resp_name": s.get("tw_resp_name", ""),
        "contact_name": s.get("tw_contact_name", ""),
        "contact_tel": s.get("tw_contact_tel", ""),
        "contact_fax": s.get("tw_contact_fax", ""),
        "contact_email": s.get("tw_contact_email", ""),
        "confirm_match": bool(s.get("tw_confirm_match", False)),
        "cert_raps": bool(s.get("tw_cert_raps", False)),
        "cert_ahwp": bool(s.get("tw_cert_ahwp", False)),
        "cert_other": s.get("tw_cert_other", ""),
        "manu_type": s.get("tw_manu_type", ""),
        "manu_name": s.get("tw_manu_name", ""),
        "manu_country": s.get("tw_manu_country", ""),
        "manu_addr": s.get("tw_manu_addr", ""),
        "manu_note": s.get("tw_manu_note", ""),
        "auth_applicable": s.get("tw_auth_app", ""),
        "auth_desc": s.get("tw_auth_desc", ""),
        "cfs_applicable": s.get("tw_cfs_app", ""),
        "cfs_desc": s.get("tw_cfs_desc", ""),
        "qms_applicable": s.get("tw_qms_app", ""),
        "qms_desc": s.get("tw_qms_desc", ""),
        "similar_info": s.get("tw_similar_info", ""),
        "labeling_info": s.get("tw_labeling_info", ""),
        "tech_file_info": s.get("tw_tech_file_info", ""),
        "preclinical_info": s.get("tw_preclinical_info", ""),
        "preclinical_replace": s.get("tw_preclinical_replace", ""),
        "clinical_just": s.get("tw_clinical_app", ""),
        "clinical_info": s.get("tw_clinical_info", ""),
    }


def apply_tw_app_dict_to_session(data: dict):
    s = st.session_state
    s["tw_doc_no"] = data.get("doc_no", "")
    s["tw_e_no"] = data.get("e_no", "")

    # date parsing
    try:
        from datetime import date
        if data.get("apply_date"):
            y, m, d = map(int, str(data["apply_date"]).split("-"))
            s["tw_apply_date"] = date(y, m, d)
    except Exception:
        pass

    s["tw_case_type"] = data.get("case_type", "")
    s["tw_device_category"] = data.get("device_category", "")
    s["tw_case_kind"] = data.get("case_kind", "")
    s["tw_origin"] = data.get("origin", "")
    s["tw_product_class"] = data.get("product_class", "")
    s["tw_similar"] = data.get("similar", "")
    s["tw_replace_flag"] = data.get("replace_flag", "")
    s["tw_prior_app_no"] = data.get("prior_app_no", "")
    s["tw_dev_name_zh"] = data.get("name_zh", "")
    s["tw_dev_name_en"] = data.get("name_en", "")
    s["tw_indications"] = data.get("indications", "")
    s["tw_spec_comp"] = data.get("spec_comp", "")
    s["tw_main_cat"] = data.get("main_cat", "")
    s["tw_item_code"] = data.get("item_code", "")
    s["tw_item_name"] = data.get("item_name", "")
    s["tw_uniform_id"] = data.get("uniform_id", "")
    s["tw_firm_name"] = data.get("firm_name", "")
    s["tw_firm_addr"] = data.get("firm_addr", "")
    s["tw_resp_name"] = data.get("resp_name", "")
    s["tw_contact_name"] = data.get("contact_name", "")
    s["tw_contact_tel"] = data.get("contact_tel", "")
    s["tw_contact_fax"] = data.get("contact_fax", "")
    s["tw_contact_email"] = data.get("contact_email", "")
    s["tw_confirm_match"] = bool(data.get("confirm_match", False))
    s["tw_cert_raps"] = bool(data.get("cert_raps", False))
    s["tw_cert_ahwp"] = bool(data.get("cert_ahwp", False))
    s["tw_cert_other"] = data.get("cert_other", "")
    s["tw_manu_type"] = data.get("manu_type", "")
    s["tw_manu_name"] = data.get("manu_name", "")
    s["tw_manu_country"] = data.get("manu_country", "")
    s["tw_manu_addr"] = data.get("manu_addr", "")
    s["tw_manu_note"] = data.get("manu_note", "")
    s["tw_auth_app"] = data.get("auth_applicable", "")
    s["tw_auth_desc"] = data.get("auth_desc", "")
    s["tw_cfs_app"] = data.get("cfs_applicable", "")
    s["tw_cfs_desc"] = data.get("cfs_desc", "")
    s["tw_qms_app"] = data.get("qms_applicable", "")
    s["tw_qms_desc"] = data.get("qms_desc", "")
    s["tw_similar_info"] = data.get("similar_info", "")
    s["tw_labeling_info"] = data.get("labeling_info", "")
    s["tw_tech_file_info"] = data.get("tech_file_info", "")
    s["tw_preclinical_info"] = data.get("preclinical_info", "")
    s["tw_preclinical_replace"] = data.get("preclinical_replace", "")
    s["tw_clinical_app"] = data.get("clinical_just", "")
    s["tw_clinical_info"] = data.get("clinical_info", "")


def standardize_tw_app_info_with_llm(raw_obj) -> dict:
    api_keys = st.session_state.get("api_keys", {})
    model = "gemini-2.5-flash"
    if not (api_keys.get("gemini") or os.getenv("GEMINI_API_KEY")):
        raise RuntimeError("No Gemini API key available for standardizing application info.")

    raw_json = json.dumps(raw_obj, ensure_ascii=False, indent=2)
    fields_str = ", ".join(TW_APP_FIELDS)

    system_prompt = f"""
You are a data normalization assistant for a Taiwanese TFDA medical device premarket application.

Goal:
Map arbitrary JSON or CSV-like key/value structures into a STANDARD JSON object
that uses EXACTLY the following top-level keys (all strings except where noted):

{fields_str}

Rules:
- Output MUST be a single JSON object (no markdown, no comments).
- Every key above MUST appear in the JSON.
- If information for a field is clearly not present, set it to an empty string,
  or for boolean-like fields use `false`.
- Do NOT invent new facts; just reorganize/rename what exists.
- `apply_date` should be 'YYYY-MM-DD' if inferable; otherwise empty.
"""

    user_prompt = f"Here is the raw data to normalize:\n\n{raw_json}"

    out = call_llm(
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=4000,
        temperature=0.1,
        api_keys=api_keys,
    )

    # parse JSON (robust)
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        start = out.find("{")
        end = out.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(out[start:end + 1])
        else:
            raise RuntimeError("LLM did not return valid JSON for application info.")

    if not isinstance(data, dict):
        raise RuntimeError("Standardized application info is not a JSON object.")

    for k in TW_APP_FIELDS:
        if k not in data:
            data[k] = "" if k not in ("confirm_match", "cert_raps", "cert_ahwp") else False
    return data


def compute_tw_app_completeness() -> float:
    s = st.session_state
    required_keys = [
        "tw_e_no", "tw_case_type", "tw_device_category",
        "tw_origin", "tw_product_class",
        "tw_dev_name_zh", "tw_dev_name_en",
        "tw_uniform_id", "tw_firm_name", "tw_firm_addr",
        "tw_resp_name", "tw_contact_name", "tw_contact_tel",
        "tw_contact_email",
        "tw_manu_name", "tw_manu_addr",
    ]
    filled = 0
    for k in required_keys:
        v = s.get(k, "")
        if isinstance(v, str):
            if v.strip():
                filled += 1
        else:
            if v:
                filled += 1
    return filled / len(required_keys) if required_keys else 0.0


# =========================
# TW Premarket Tab (full)
# =========================

def render_tw_premarket_tab():
    st.title(t("TW Premarket"))

    st.markdown(
        """
        <div style="background:rgba(238,242,255,0.75);border-radius:12px;padding:10px 14px;
                    border:1px solid rgba(199,210,254,0.8);margin-bottom:0.75rem;">
          <b>Step 1.</b> 線上填寫或由 JSON/CSV 匯入「第二、三等級醫療器材查驗登記申請」主要欄位。<br>
          <b>Step 2.</b> 貼上或上傳「預審/形式審查指引」供 AI 進行完整性檢核。<br>
          <b>Step 3.</b> 產出預審摘要報告 (Markdown)，可在頁面上修改。<br>
          <b>Step 4.</b> AI 協助編修申請書內容，或把輸出串接到下一個 agent。
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Import / Export
    st.markdown("### Application Info 匯入 / 匯出 (JSON / CSV)")

    col_ie1, col_ie2 = st.columns(2)
    with col_ie1:
        st.markdown("**上傳 Application Info**")
        app_file = st.file_uploader("Upload Application Info (JSON / CSV)", type=["json", "csv"], key="tw_app_upload")
        if app_file is not None:
            try:
                if app_file.name.lower().endswith(".json"):
                    raw_data = json.loads(safe_decode(app_file.getvalue()))
                else:
                    df = pd.read_csv(BytesIO(app_file.getvalue()))
                    if len(df) == 0:
                        st.error("CSV 檔案為空。")
                        raw_data = None
                    else:
                        raw_data = df.to_dict(orient="records")[0]
                if raw_data is not None:
                    if isinstance(raw_data, dict) and all(k in raw_data for k in TW_APP_FIELDS):
                        standardized = raw_data
                    else:
                        with st.spinner("使用 LLM 將欄位轉為標準 TFDA 申請書格式..."):
                            standardized = standardize_tw_app_info_with_llm(raw_data)
                    apply_tw_app_dict_to_session(standardized)
                    st.session_state["tw_app_last_loaded"] = standardized
                    st.success("已將上傳資料轉換並套用至申請表單。")
                    st.rerun()
            except Exception as e:
                st.error(f"上傳或標準化失敗：{e}")

    with col_ie2:
        st.markdown("**下載 Application Info**")
        app_dict = build_tw_app_dict_from_session()
        json_bytes = json.dumps(app_dict, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button("Download JSON", data=json_bytes, file_name="tw_premarket_application.json",
                           mime="application/json", key="tw_app_download_json")

        df_app = pd.DataFrame([app_dict])
        csv_bytes = df_app.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", data=csv_bytes, file_name="tw_premarket_application.csv",
                           mime="text/csv", key="tw_app_download_csv")

    if "tw_app_last_loaded" in st.session_state:
        st.markdown("**最近載入/標準化之 Application JSON 預覽**")
        st.json(st.session_state["tw_app_last_loaded"], expanded=False)

    st.markdown("---")

    # WOW completeness
    completeness = compute_tw_app_completeness()
    pct = int(completeness * 100)
    if pct >= 80:
        card_grad = "linear-gradient(135deg,#22c55e,#16a34a)"
        txt = "申請基本欄位完成度高，適合進行預審。"
    elif pct >= 50:
        card_grad = "linear-gradient(135deg,#f97316,#ea580c)"
        txt = "部分關鍵欄位仍待補齊，建議補足後再送預審。"
    else:
        card_grad = "linear-gradient(135deg,#ef4444,#b91c1c)"
        txt = "多數基本欄位尚未填寫，請先充實申請資訊。"

    st.markdown(
        f"""
        <div class="wow-card" style="background:{card_grad};margin-top:0;">
          <div class="wow-card-title">APPLICATION COMPLETENESS</div>
          <div class="wow-card-main">{pct}%</div>
          <div style="margin-top:6px;font-size:0.9rem;">{txt}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(completeness)

    # Step 1 form
    st.markdown("### Step 1 – 線上填寫申請書（草稿）")

    if "tw_app_status" not in st.session_state:
        st.session_state["tw_app_status"] = "pending"
    show_status("申請書填寫", st.session_state["tw_app_status"])

    # 一、案件基本資料
    st.markdown("#### 一、案件基本資料")
    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        doc_no = st.text_input("公文文號", key="tw_doc_no")
        e_no = st.text_input("電子流水號", value=st.session_state.get("tw_e_no", "MDE"), key="tw_e_no")
    with col_a2:
        apply_date = st.date_input("申請日", key="tw_apply_date")
        case_type = st.selectbox(
            "案件類型*",
            ["一般申請案", "同一產品不同品名", "專供外銷", "許可證有效期限屆至後六個月內重新申請"],
            key="tw_case_type",
        )
    with col_a3:
        device_category = st.selectbox("醫療器材類型*", ["一般醫材", "體外診斷器材(IVD)"], key="tw_device_category")
        case_kind = st.selectbox("案件種類*", ["新案", "變更案", "展延案"], index=0, key="tw_case_kind")

    col_a4, col_a5, col_a6 = st.columns(3)
    with col_a4:
        origin = st.selectbox("產地*", ["國產", "輸入", "陸輸"], key="tw_origin")
    with col_a5:
        product_class = st.selectbox("產品等級*", ["第二等級", "第三等級"], key="tw_product_class")
    with col_a6:
        similar = st.selectbox("有無類似品*", ["有", "無", "全球首創"], key="tw_similar")

    col_a7, col_a8 = st.columns(2)
    with col_a7:
        replace_flag = st.radio(
            "是否勾選「替代臨床前測試及原廠品質管制資料」？*",
            ["否", "是"],
            index=0 if st.session_state.get("tw_replace_flag", "否") == "否" else 1,
            key="tw_replace_flag",
        )
    with col_a8:
        prior_app_no = st.text_input("（非首次申請）前次申請案號", key="tw_prior_app_no")

    # 二、醫療器材基本資訊
    st.markdown("#### 二、醫療器材基本資訊")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        name_zh = st.text_input("醫療器材中文名稱*", key="tw_dev_name_zh")
        name_en = st.text_input("醫療器材英文名稱*", key="tw_dev_name_en")
    with col_b2:
        indications = st.text_area("效能、用途或適應症說明", value=st.session_state.get("tw_indications", "詳如核定之中文說明書"), key="tw_indications")
        spec_comp = st.text_area("型號、規格或主要成分說明", value=st.session_state.get("tw_spec_comp", "詳如核定之中文說明書"), key="tw_spec_comp")

    st.markdown("**分類分級品項（依《醫療器材分類分級管理辦法》附表填列）**")
    col_b3, col_b4, col_b5 = st.columns(3)
    with col_b3:
        main_cat = st.selectbox(
            "主類別",
            [
                "", "A.臨床化學及臨床毒理學", "B.血液學及病理學", "C.免疫學及微生物學",
                "D.麻醉學", "E.心臟血管醫學", "F.牙科學", "G.耳鼻喉科學",
                "H.胃腸病科學及泌尿科學", "I.一般及整形外科手術", "J.一般醫院及個人使用裝置",
                "K.神經科學", "L.婦產科學", "M.眼科學", "N.骨科學", "O.物理醫學科學", "P.放射學科學",
            ],
            key="tw_main_cat",
        )
    with col_b4:
        item_code = st.text_input("分級品項代碼（例：A.1225）", key="tw_item_code")
    with col_b5:
        item_name = st.text_input("分級品項名稱（例：肌氨酸酐試驗系統）", key="tw_item_name")

    # 三、醫療器材商資料
    st.markdown("#### 三、醫療器材商資料")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        uniform_id = st.text_input("統一編號*", key="tw_uniform_id")
        firm_name = st.text_input("醫療器材商名稱*", key="tw_firm_name")
        firm_addr = st.text_area("醫療器材商地址*", height=80, key="tw_firm_addr")
    with col_c2:
        resp_name = st.text_input("負責人姓名*", key="tw_resp_name")
        contact_name = st.text_input("聯絡人姓名*", key="tw_contact_name")
        contact_tel = st.text_input("電話*", key="tw_contact_tel")
        contact_fax = st.text_input("聯絡人傳真", key="tw_contact_fax")
        contact_email = st.text_input("電子郵件*", key="tw_contact_email")

    confirm_match = st.checkbox(
        "我已確認上述資料與最新版醫療器材商證照資訊(名稱、地址、負責人)相符",
        key="tw_confirm_match",
    )

    st.markdown("**其它佐證（承辦人訓練證明等）**")
    col_c3, col_c4 = st.columns(2)
    with col_c3:
        cert_raps = st.checkbox("RAPS", key="tw_cert_raps")
        cert_ahwp = st.checkbox("AHWP", key="tw_cert_ahwp")
    with col_c4:
        cert_other = st.text_input("其它，請敘明", key="tw_cert_other")

    # 四、製造廠資訊
    st.markdown("#### 四、製造廠資訊（含委託製造）")
    manu_type = st.radio(
        "製造方式",
        ["單一製造廠", "全部製程委託製造", "委託非全部製程之製造/包裝/貼標/滅菌及最終驗放"],
        index=0,
        key="tw_manu_type",
    )
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        manu_name = st.text_input("製造廠名稱*", key="tw_manu_name")
        manu_country = st.selectbox(
            "製造國別*",
            ["TAIWAN， ROC", "UNITED STATES", "EU (Member State)", "JAPAN", "CHINA", "KOREA， REPUBLIC OF", "OTHER"],
            key="tw_manu_country",
        )
    with col_d2:
        manu_addr = st.text_area("製造廠地址*", height=80, key="tw_manu_addr")
        manu_note = st.text_area("製造廠相關說明（如(O)/(P)製造、委託範圍）", height=80, key="tw_manu_note")

    with st.expander("附件摘要：原廠授權、出產國製售證明、QMS/QSD、技術檔案、臨床資料等", expanded=False):
        auth_applicable = st.selectbox("原廠授權登記書", ["不適用", "適用"], key="tw_auth_app")
        auth_desc = st.text_area("原廠授權登記書資料說明", height=80, key="tw_auth_desc")

        cfs_applicable = st.selectbox("出產國製售證明", ["不適用", "適用"], key="tw_cfs_app")
        cfs_desc = st.text_area("出產國製售證明資料說明", height=80, key="tw_cfs_desc")

        qms_applicable = st.selectbox("QMS/QSD", ["不適用", "適用"], key="tw_qms_app")
        qms_desc = st.text_area("QMS/QSD 資料說明（含案號、登錄狀態）", height=80, key="tw_qms_desc")

        similar_info = st.text_area("類似品與比較表摘要（如無類似品則說明理由）", height=80, key="tw_similar_info")
        labeling_info = st.text_area("標籤、說明書或包裝擬稿重點", height=100, key="tw_labeling_info")
        tech_file_info = st.text_area("產品結構、材料、規格、性能、用途、圖樣等技術檔案摘要", height=120, key="tw_tech_file_info")
        preclinical_info = st.text_area(
            "臨床前測試 & 原廠品質管制檢驗摘要（生物相容性、電氣安全、EMC、滅菌、安定性、功能測試、軟體確效等）",
            height=140,
            key="tw_preclinical_info",
        )
        preclinical_replace = st.text_area("如本案適用「替代臨床前測試及原廠品質管制資料」之說明", height=100, key="tw_preclinical_replace")
        clinical_just = st.selectbox("臨床證據是否適用？", ["不適用", "適用"], key="tw_clinical_app")
        clinical_info = st.text_area("臨床證據摘要（研究報告、臨床評估、臨床試驗、FDA/歐盟核定資料等）", height=140, key="tw_clinical_info")

    # Generate Markdown draft
    if st.button("生成申請書 Markdown 草稿", key="tw_generate_md_btn"):
        missing = []
        def req(field, label):
            if not (field or "").strip():
                missing.append(label)

        req(e_no, "電子流水號")
        req(case_type, "案件類型")
        req(device_category, "醫療器材類型")
        req(origin, "產地")
        req(product_class, "產品等級")
        req(name_zh, "醫療器材中文名稱")
        req(name_en, "醫療器材英文名稱")
        req(uniform_id, "統一編號")
        req(firm_name, "醫療器材商名稱")
        req(firm_addr, "醫療器材商地址")
        req(resp_name, "負責人姓名")
        req(contact_name, "聯絡人姓名")
        req(contact_tel, "電話")
        req(contact_email, "電子郵件")
        req(manu_name, "製造廠名稱")
        req(manu_addr, "製造廠地址")

        if missing:
            st.warning("以下基本欄位尚未填寫完整（形式檢查）：\n- " + "\n- ".join(missing))
            st.session_state["tw_app_status"] = "error"
        else:
            st.session_state["tw_app_status"] = "done"

        apply_date_str = apply_date.strftime("%Y-%m-%d") if apply_date else ""
        app_md = f"""# 第二、三等級醫療器材查驗登記申請書（線上草稿）

## 一、案件基本資料
- 公文文號：{doc_no or "（未填）"}
- 電子流水號：{e_no or "（未填）"}
- 申請日：{apply_date_str or "（未填）"}
- 案件類型：{case_type}
- 醫療器材類型：{device_category}
- 案件種類：{case_kind}
- 產地：{origin}
- 產品等級：{product_class}
- 有無類似品：{similar}
- 是否勾選「替代臨床前測試及原廠品質管制資料」：{replace_flag}
- 前次申請案號（如適用）：{prior_app_no or "不適用"}

## 二、醫療器材基本資訊
- 中文名稱：{name_zh}
- 英文名稱：{name_en}
- 效能、用途或適應症說明：{indications}
- 型號、規格或主要成分：{spec_comp}

### 分類分級品項
- 主類別：{main_cat or "（未填）"}
- 分級品項代碼：{item_code or "（未填）"}
- 分級品項名稱：{item_name or "（未填）"}

## 三、醫療器材商資料
- 統一編號：{uniform_id}
- 醫療器材商名稱：{firm_name}
- 地址：{firm_addr}
- 負責人姓名：{resp_name}
- 聯絡人姓名：{contact_name}
- 電話：{contact_tel}
- 傳真：{contact_fax or "（未填）"}
- 電子郵件：{contact_email}
- 已確認與最新醫療器材商證照資訊相符：{"是" if confirm_match else "否"}

### 其它佐證
- RAPS：{"有" if cert_raps else "無"}
- AHWP：{"有" if cert_ahwp else "無"}
- 其它訓練/證書：{cert_other or "無"}

## 四、製造廠資訊
- 製造方式：{manu_type}
- 製造廠名稱：{manu_name}
- 製造國別：{manu_country}
- 製造廠地址：{manu_addr}
- 製造相關說明：{manu_note or "（未填）"}

## 五～七、原廠授權、出產國製售證明、QMS/QSD
- 原廠授權登記書適用性：{auth_applicable}
- 原廠授權登記書資料說明：{auth_desc or "（未填）"}
- 出產國製售證明適用性：{cfs_applicable}
- 出產國製售證明資料說明：{cfs_desc or "（未填）"}
- QMS/QSD 適用性：{qms_applicable}
- QMS/QSD 資料說明：{qms_desc or "（未填）"}

## 十～十二、類似品、標籤/說明書擬稿、產品技術檔案摘要
### 類似品相關資訊
{similar_info or "（未填）"}

### 標籤／說明書／包裝擬稿重點
{labeling_info or "（未填）"}

### 產品結構、材料、規格、性能、用途、圖樣等技術檔案摘要
{tech_file_info or "（未填）"}

## 十三～十七、特定安全性要求與臨床前測試及品質管制資料
### 臨床前測試與原廠品質管制資料摘要
{preclinical_info or "（未填）"}

### 替代「臨床前測試及原廠品質管制資料」之說明
{preclinical_replace or "（未填）"}

## 十八、臨床證據資料
- 臨床證據適用性：{clinical_just}
- 臨床證據摘要：
{clinical_info or "（未填）"}
"""
        st.session_state["tw_app_markdown"] = app_md

    st.markdown("##### 申請書 Markdown（可編輯）")
    app_md_current = st.session_state.get("tw_app_markdown", "")
    app_view_mode = st.radio("申請書檢視模式", ["Markdown", "純文字"], horizontal=True, key="tw_app_viewmode")
    app_md_edited = st.text_area("申請書內容", value=app_md_current, height=320, key="tw_app_md_edited")
    st.session_state["tw_app_effective_md"] = app_md_edited

    st.markdown("---")

    # Step 2 guidance input
    st.markdown("### Step 2 – 輸入預審/形式審查指引（Screen Review Guidance）")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        guidance_file = st.file_uploader("上傳預審指引 (PDF / TXT / MD)", type=["pdf", "txt", "md"], key="tw_guidance_file")
        guidance_text_from_file = ""
        if guidance_file is not None:
            suffix = guidance_file.name.lower().rsplit(".", 1)[-1]
            data = guidance_file.getvalue()
            if suffix == "pdf":
                guidance_text_from_file = extract_pdf_pages_to_text(data, 1, 9999)
            else:
                guidance_text_from_file = safe_decode(data)
    with col_g2:
        guidance_text_manual = st.text_area("或直接貼上預審/形式審查指引文字或 Markdown", height=200, key="tw_guidance_manual")

    guidance_text = (guidance_text_from_file or guidance_text_manual or "").strip()
    st.session_state["tw_guidance_text"] = guidance_text

    if guidance_text:
        st.success("已載入預審/形式審查指引文字。")
    else:
        st.info("尚未提供預審指引。可先填寫申請書草稿，稍後再補。")

    st.markdown("---")

    # Step 3 screen review agent
    st.markdown("### Step 3 – 形式審查 / 完整性檢核（Agent）")

    base_app_md = st.session_state.get("tw_app_effective_md", "").strip()
    if not base_app_md:
        st.warning("尚未產生申請書 Markdown。請先於 Step 1 填寫並點擊「生成申請書 Markdown 草稿」。")
        return

    base_guidance = st.session_state.get("tw_guidance_text", "")
    combined_input = f"""=== 申請書草稿（Markdown） ===
{base_app_md}

=== 預審 / 形式審查指引（文字/Markdown） ===
{base_guidance or "（尚未提供指引，請依一般法規常規進行形式檢核）"}
"""

    default_screen_prompt = """你是一位熟悉臺灣「第二、三等級醫療器材查驗登記」的形式審查(預審)審查員。

請根據：
1. 上述「申請書草稿（Markdown）」內容
2. 上述「預審 / 形式審查指引」(如有)

執行下列任務，並以 **繁體中文 Markdown** 輸出預審報告：

1. 形式完整性檢核
   - 建立一個表格，逐一列出本案應檢附的主要文件類別（例如：申請書、醫療器材商許可執照、原廠授權登記書、出產國製售證明、QMS/QSD、標籤/說明書擬稿、產品技術檔案、臨床前測試資料、臨床證據資料等）。
   - 對每一項，標示：
     - 「預期應附？」（是/否/不明）
     - 「申請書中是否有提及？」（有/疑似有/未見）
     - 「整體判定」（足夠/可能不足/明顯缺漏）
     - 「備註說明」（請具體指出缺漏內容或需補充重點）。

2. 重要欄位檢核
   - 檢查是否有明顯未填或矛盾之處。
   - 以條列方式說明「問題項目」、「疑慮說明」、「建議補充資料」。

3. 預審評語摘要（300–600 字）
   - 整體完整性評估
   - 必須補件 vs 建議補充

4. 避免臆測；無法判斷請註記。
"""

    agent_run_ui(
        agent_id="tw_screen_review_agent",
        tab_key="tw_screen",
        default_prompt=default_screen_prompt,
        default_input_text=combined_input,
        allow_model_override=True,
        tab_label_for_history="TW Premarket Screen Review",
    )

    screen_out = st.session_state.get("tw_screen_output_effective", "").strip()
    if screen_out:
        record_artifact("tw_screen_review.md", "markdown", screen_out, "繁體中文")

    st.markdown("---")

    # Step 4 doc helper agent
    st.markdown("### Step 4 – AI 協助編修申請書內容")

    helper_default_prompt = """你是一位協助臺灣醫療器材查驗登記申請人的文件撰寫助手。

請在 **不改變實際技術與法規內容** 的前提下，針對以下「申請書草稿（Markdown）」：

1. 優化段落結構與標題層級，使其更符合主管機關常見文件格式。
2. 修正文句中的明顯語病或不通順處，但不得自行新增未出現在原文的重要資訊。
3. 如有明顯資訊不足之處，以「※待補：...」標註提醒。
4. 保持輸出為 Markdown。
"""

    agent_run_ui(
        agent_id="tw_app_doc_helper",
        tab_key="tw_app_helper",
        default_prompt=helper_default_prompt,
        default_input_text=base_app_md,
        allow_model_override=True,
        tab_label_for_history="TW Application Doc Helper",
    )

    helper_out = st.session_state.get("tw_app_helper_output_effective", "").strip()
    if helper_out:
        record_artifact("tw_application_doc_helper.md", "markdown", helper_out, "繁體中文")


# =========================
# 510(k) Intelligence Tab
# =========================

def render_510k_tab():
    st.title(t("510k_tab"))
    col1, col2 = st.columns(2)
    with col1:
        device_name = st.text_input("Device Name")
        k_number = st.text_input("510(k) Number (e.g., K123456)")
    with col2:
        sponsor = st.text_input("Sponsor / Manufacturer (optional)")
        product_code = st.text_input("Product Code (optional)")
    extra_info = st.text_area("Additional context (indications, technology, etc.)")

    default_prompt = f"""
You are assisting an FDA 510(k) reviewer.

Task:
1. Summarize publicly available information (do not fabricate identifiers).
2. Produce a detailed, review-oriented summary (about 2000–3000 words).
3. Provide markdown tables: device overview, indications, testing, risks.

Language: {st.session_state.settings["language"]}.
"""
    combined_input = f"""
=== Device Inputs ===
Device name: {device_name}
510(k) number: {k_number}
Sponsor: {sponsor}
Product code: {product_code}

Additional context:
{extra_info}
""".strip()

    agent_run_ui(
        agent_id="fda_510k_intel_agent",
        tab_key="510k",
        default_prompt=default_prompt,
        default_input_text=combined_input,
        tab_label_for_history="510(k) Intelligence",
    )


# =========================
# PDF → Markdown Tab
# =========================

def render_pdf_to_md_tab():
    st.title(t("PDF → Markdown"))

    uploaded = st.file_uploader("Upload PDF to convert selected pages to Markdown", type=["pdf"], key="pdf_to_md_uploader")
    if uploaded:
        col1, col2 = st.columns(2)
        with col1:
            num_start = st.number_input("From page", min_value=1, value=1, key="pdf_to_md_from")
        with col2:
            num_end = st.number_input("To page", min_value=1, value=5, key="pdf_to_md_to")

        if st.button("Extract Text", key="pdf_to_md_extract_btn"):
            try:
                text = extract_pdf_pages_to_text(uploaded.getvalue(), int(num_start), int(num_end))
            except Exception as e:
                st.error(f"PDF extraction failed: {e}")
                text = ""
            st.session_state["pdf_raw_text"] = text

    raw_text = st.session_state.get("pdf_raw_text", "")
    if raw_text:
        default_prompt = f"""
You are converting part of a regulatory PDF into markdown.

- Preserve headings, lists, tables as much as possible.
- Do not hallucinate content not present.
- Output language: {st.session_state.settings["language"]}.
"""
        agent_run_ui(
            agent_id="pdf_to_markdown_agent",
            tab_key="pdf_to_md",
            default_prompt=default_prompt,
            default_input_text=raw_text,
            tab_label_for_history="PDF → Markdown",
        )
    else:
        st.info("Upload a PDF and click 'Extract Text' to begin.")


# =========================
# 510(k) Review Pipeline (agentic, editable)
# =========================

def render_510k_review_pipeline_tab():
    st.title(t("Checklist & Report"))

    st.markdown("### Step 1 — Paste submission material → Structured Markdown (Agent)")
    raw_subm = st.text_area("Paste 510(k) submission material (text/markdown)", height=200, key="subm_paste")

    struct_prompt = """You are a 510(k) submission organizer.

Restructure the content into organized markdown with sections:
- Device & submitter info
- Device description and technology
- Indications for use
- Predicate/comparator
- Performance testing
- Risks and risk controls

Do not invent facts; only reorganize and clarify.
"""
    agent_run_ui(
        agent_id="submission_structurer_agent",
        tab_key="subm_struct",
        default_prompt=struct_prompt,
        default_input_text=raw_subm,
        tab_label_for_history="510(k) Submission Structurer",
    )
    subm_structured = st.session_state.get("subm_struct_output_effective", "").strip()
    if subm_structured:
        record_artifact("510k_structured_submission.md", "markdown", subm_structured, st.session_state.settings.get("language", "English"))

    st.markdown("---")
    st.markdown("### Step 2 — Paste checklist (or build your own)")

    chk_md = st.text_area("Paste checklist (markdown or text)", height=200, key="chk_md")
    st.markdown("---")

    st.markdown("### Step 3 — Build Review Report (Agent)")
    rep_prompt = """You are drafting an internal FDA 510(k) review memo.

Using the checklist and structured submission, write a review report with:
- Introduction & scope
- Device and submission overview
- Differences vs predicate(s)
- Checklist-based assessment (tables encouraged)
- Overall conclusion and recommendations

Do not fabricate missing data; mark TBD where needed.
"""
    combined = f"=== CHECKLIST ===\n{chk_md}\n\n=== STRUCTURED SUBMISSION ===\n{subm_structured or ''}".strip()
    agent_run_ui(
        agent_id="review_memo_builder_agent",
        tab_key="review_memo",
        default_prompt=rep_prompt,
        default_input_text=combined,
        tab_label_for_history="510(k) Review Memo Builder",
    )

    memo_out = st.session_state.get("review_memo_output_effective", "").strip()
    if memo_out:
        record_artifact("510k_review_memo.md", "markdown", memo_out, st.session_state.settings.get("language", "English"))


# =========================
# Note Keeper & Magics (6+)
# =========================

def highlight_keywords(text: str, keywords: List[str], color: str) -> str:
    if not text or not keywords:
        return text
    out = text
    for kw in sorted(set([k.strip() for k in keywords if k.strip()]), key=len, reverse=True):
        span = f'<span style="color:{color};font-weight:700;">{kw}</span>'
        out = out.replace(kw, span)
    return out


def render_note_keeper_tab():
    st.title(t("Note Keeper & Magics"))

    st.markdown("### Step 1 — Paste Notes & Transform to Structured Markdown")
    raw_notes = st.text_area("Paste your notes (text or markdown)", height=220, key="notes_raw")

    col_n1, col_n2 = st.columns(2)
    with col_n1:
        note_model = st.selectbox("Model for Note → Markdown", ALL_MODELS,
                                  index=ALL_MODELS.index(st.session_state.settings["model"]),
                                  key="note_model")
    with col_n2:
        note_max_tokens = st.number_input("max_tokens", min_value=2000, max_value=120000, value=12000, step=1000, key="note_max_tokens")

    default_note_prompt = """你是一位協助醫療器材/510(k)/TFDA 審查員整理個人筆記的助手。

請將下列雜亂或半結構化的筆記整理成：
1) 清晰的 Markdown 結構（標題、子標題、條列）
2) 保留所有重點，不要憑空新增內容
3) 顯示：關鍵技術要點、主要風險與疑問、待釐清/追問事項
"""
    note_struct_prompt = st.text_area("Prompt for Note → Markdown", value=default_note_prompt, height=160, key="note_struct_prompt")

    if st.button("Transform notes to structured Markdown", key="note_run_btn"):
        if not raw_notes.strip():
            st.warning("Please paste notes first.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = note_struct_prompt + "\n\n=== RAW NOTES ===\n" + raw_notes
            try:
                out = call_llm(
                    model=note_model,
                    system_prompt="You organize reviewer's notes into clean markdown.",
                    user_prompt=user_prompt,
                    max_tokens=int(note_max_tokens),
                    temperature=0.15,
                    api_keys=api_keys,
                )
                st.session_state["note_md"] = out
                log_event("Note Keeper", "Note Structurer", note_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")

    base_note = st.text_area("Structured Note (editable)", value=st.session_state.get("note_md", raw_notes), height=280, key="note_md_edited")

    # Magic 1 — AI Formatting
    st.markdown("---\n### Magic 1 — AI Formatting")
    fmt_model = st.selectbox("Model (Formatting)", ALL_MODELS, index=ALL_MODELS.index(st.session_state.settings["model"]), key="fmt_model")
    fmt_prompt = st.text_area("Prompt", value="請在不改變內容的前提下，統一標題層級與條列格式，讓此筆記更易讀（輸出 Markdown）。",
                              height=120, key="fmt_prompt")
    if st.button("Run AI Formatting", key="fmt_run_btn"):
        if not base_note.strip():
            st.warning("No base note available.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = fmt_prompt + "\n\n=== NOTE ===\n" + base_note
            try:
                out = call_llm(fmt_model, "You format markdown without changing meaning.", user_prompt,
                               max_tokens=12000, temperature=0.1, api_keys=api_keys)
                st.session_state["fmt_note"] = out
                log_event("Note Keeper", "AI Formatting", fmt_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")
    if st.session_state.get("fmt_note"):
        st.text_area("Formatted Note (editable)", value=st.session_state["fmt_note"], height=220, key="fmt_note_edit")

    # Magic 2 — AI Keywords (manual highlight, coral default)
    st.markdown("---\n### Magic 2 — AI Keywords (Manual highlight)")
    kw_input = st.text_input("Keywords (comma-separated)", key="kw_input", value="510(k), TFDA, QMS, biocompatibility")
    kw_color = st.color_picker("Color for keywords", "#FF7F50", key="kw_color")
    if st.button("Apply Keyword Highlighting", key="kw_run_btn"):
        if not base_note.strip():
            st.warning("No base note available.")
        else:
            keywords = [k.strip() for k in kw_input.split(",") if k.strip()]
            st.session_state["kw_note"] = highlight_keywords(base_note, keywords, kw_color)
    if st.session_state.get("kw_note"):
        st.markdown(st.session_state["kw_note"], unsafe_allow_html=True)

    # Magic 3 — AI Summary
    st.markdown("---\n### Magic 3 — AI Summary")
    sum_model = st.selectbox("Model (Summary)", ALL_MODELS, index=ALL_MODELS.index("gpt-4o-mini"), key="note_sum_model")
    sum_prompt = st.text_area("Prompt", value="請將以下審查筆記摘要為 5–10 個重點 bullet，並附上一段 3–5 句的整體摘要（使用繁體中文）。",
                              height=140, key="note_sum_prompt")
    if st.button("Run AI Summary", key="note_sum_run_btn"):
        if not base_note.strip():
            st.warning("No base note available.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = sum_prompt + "\n\n=== NOTE ===\n" + base_note
            try:
                out = call_llm(sum_model, "You write executive summaries for regulatory notes.", user_prompt,
                               max_tokens=12000, temperature=0.2, api_keys=api_keys)
                st.session_state["note_summary"] = out
                log_event("Note Keeper", "AI Summary", sum_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")
    if st.session_state.get("note_summary"):
        st.text_area("Summary (editable)", value=st.session_state["note_summary"], height=200, key="note_summary_edit")

    # Magic 4 — AI Action Items
    st.markdown("---\n### Magic 4 — AI Action Items")
    act_model = st.selectbox("Model (Action Items)", ALL_MODELS, index=ALL_MODELS.index(st.session_state.settings["model"]), key="note_act_model")
    act_prompt = st.text_area("Prompt",
                              value="請從以下筆記中萃取需要後續行動的事項（補件、澄清、內部會議等），並以 Markdown 表格輸出：項目、負責人(可留空)、優先順序、說明。",
                              height=140, key="note_act_prompt")
    if st.button("Run AI Action Items", key="note_act_run_btn"):
        if not base_note.strip():
            st.warning("No base note available.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = act_prompt + "\n\n=== NOTE ===\n" + base_note
            try:
                out = call_llm(act_model, "You extract action items from review notes.", user_prompt,
                               max_tokens=12000, temperature=0.2, api_keys=api_keys)
                st.session_state["note_actions"] = out
                log_event("Note Keeper", "AI Action Items", act_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")
    if st.session_state.get("note_actions"):
        st.text_area("Action Items (editable)", value=st.session_state["note_actions"], height=220, key="note_actions_edit")

    # Magic 5 — AI Glossary
    st.markdown("---\n### Magic 5 — AI Glossary (術語表)")
    glo_model = st.selectbox("Model (Glossary)", ALL_MODELS, index=ALL_MODELS.index("gemini-2.5-flash"), key="note_glo_model")
    glo_prompt = st.text_area("Prompt",
                              value="請從以下筆記中找出重要專有名詞 (英文縮寫、標準、指引文件名稱、專業術語)，製作 Markdown 表格：Term, Full Name/Chinese, Explanation。",
                              height=140, key="note_glo_prompt")
    if st.button("Run AI Glossary", key="note_glo_run_btn"):
        if not base_note.strip():
            st.warning("No base note available.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = glo_prompt + "\n\n=== NOTE ===\n" + base_note
            try:
                out = call_llm(glo_model, "You build glossaries for regulatory notes.", user_prompt,
                               max_tokens=12000, temperature=0.2, api_keys=api_keys)
                st.session_state["note_glossary"] = out
                log_event("Note Keeper", "AI Glossary", glo_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")
    if st.session_state.get("note_glossary"):
        st.text_area("Glossary (editable)", value=st.session_state["note_glossary"], height=220, key="note_glossary_edit")

    # Magic 6 — Contradiction & Consistency Check (WOW)
    st.markdown("---\n### Magic 6 — Contradiction & Consistency Check (WOW)")
    cc_model = st.selectbox("Model (Consistency)", ALL_MODELS, index=ALL_MODELS.index(st.session_state.settings["model"]), key="cc_model")
    cc_prompt = st.text_area(
        "Prompt",
        value="請檢查以下筆記是否存在矛盾、版本不一致、名詞混用或推論過度，並輸出：矛盾點、影響、建議修正、需要追問的問題清單（Markdown）。",
        height=120,
        key="cc_prompt",
    )
    if st.button("Run Consistency Check", key="cc_run_btn"):
        if not base_note.strip():
            st.warning("No note content to check.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = cc_prompt + "\n\n=== NOTE ===\n" + base_note
            try:
                out = call_llm(cc_model, "You detect contradictions in regulatory notes.", user_prompt,
                               max_tokens=12000, temperature=0.2, api_keys=api_keys)
                st.session_state["cc_out"] = out
                log_event("Note Keeper", "Consistency Check", cc_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")
    if st.session_state.get("cc_out"):
        st.text_area("Consistency Output (editable)", value=st.session_state["cc_out"], height=240, key="cc_out_edit")


# =========================
# Agents Config Studio
# =========================

def render_agents_config_tab():
    st.title(t("Agents Config"))

    cfg = st.session_state.get("agents_cfg", {"agents": {}})
    agents_dict = cfg.get("agents", {}) if isinstance(cfg, dict) else {}

    st.subheader("1) Current Agents Overview")
    if not agents_dict:
        st.warning("No agents found in current agents.yaml.")
    else:
        df = pd.DataFrame([{
            "agent_id": aid,
            "name": acfg.get("name", ""),
            "model": acfg.get("model", ""),
            "category": acfg.get("category", ""),
        } for aid, acfg in agents_dict.items()])
        st.dataframe(df, use_container_width=True, height=260)

    st.markdown("---")
    st.subheader("2) Edit Full agents.yaml (raw text)")
    yaml_str_current = yaml.dump(cfg, allow_unicode=True, sort_keys=False)
    edited_yaml_text = st.text_area("agents.yaml (editable)", value=yaml_str_current, height=360, key="agents_yaml_text_editor")

    col_a1, col_a2, col_a3 = st.columns(3)
    with col_a1:
        if st.button("Apply edited YAML to session", key="apply_edited_yaml"):
            try:
                new_cfg = yaml.safe_load(edited_yaml_text)
                if not isinstance(new_cfg, dict) or "agents" not in new_cfg:
                    st.error("Parsed YAML does not contain top-level key 'agents'. No changes applied.")
                else:
                    st.session_state["agents_cfg"] = new_cfg
                    st.success("Updated agents.yaml in current session.")
            except Exception as e:
                st.error(f"Failed to parse edited YAML: {e}")

    with col_a2:
        uploaded_agents_tab = st.file_uploader("Upload agents.yaml file", type=["yaml", "yml"], key="agents_yaml_tab_uploader")
        if uploaded_agents_tab is not None:
            try:
                new_cfg = yaml.safe_load(uploaded_agents_tab.getvalue())
                if isinstance(new_cfg, dict) and "agents" in new_cfg:
                    st.session_state["agents_cfg"] = new_cfg
                    st.success("Uploaded agents.yaml applied to this session.")
                else:
                    st.warning("Uploaded file has no top-level 'agents' key. Ignoring.")
            except Exception as e:
                st.error(f"Failed to parse uploaded YAML: {e}")

    with col_a3:
        st.download_button(
            "Download current agents.yaml",
            data=yaml_str_current.encode("utf-8"),
            file_name="agents.yaml",
            mime="text/yaml",
            key="download_agents_yaml_current",
        )


# =========================
# Guidance Research & Report Studio (new pipeline + WOW tools)
# =========================

def render_guidance_studio_tab():
    st.title(t("Guidance Studio"))

    st.markdown(
        """
        <div style="background:rgba(99,102,241,0.14);border-radius:12px;padding:10px 14px;
                    border:1px solid rgba(99,102,241,0.35);margin-bottom:0.75rem;">
          <b>Pipeline:</b> Guidance Input → Structuring → FDA Research (grounded) → Comprehensive Report (2000–3000 words)
          → Template Report → Generate <code>skill.md</code><br>
          <span style="opacity:0.9;">All steps support editable prompts, Gemini model selection, and editable outputs.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Output language selector (separate from UI language)
    out_lang = st.radio(
        "Output language for reports",
        ["繁體中文", "English"],
        index=0,
        horizontal=True,
        key="guidance_out_lang",
    )

    st.markdown("## Step A — Paste or Upload Published Guidance (txt / markdown / pdf)")

    colA1, colA2 = st.columns([1, 1])
    with colA1:
        up = st.file_uploader("Upload guidance", type=["txt", "md", "pdf"], key="guidance_upload")
        if up is not None:
            name = up.name.lower()
            data = up.getvalue()
            if name.endswith(".pdf"):
                p1, p2 = st.columns(2)
                with p1:
                    from_p = st.number_input("PDF from page", min_value=1, value=1, key="guid_pdf_from")
                with p2:
                    to_p = st.number_input("PDF to page", min_value=1, value=20, key="guid_pdf_to")
                if st.button("Extract PDF text", key="guid_pdf_extract_btn"):
                    with st.spinner("Extracting PDF text..."):
                        try:
                            st.session_state["guidance_raw"] = extract_pdf_pages_to_text(data, int(from_p), int(to_p))
                        except Exception as e:
                            st.error(f"PDF extract failed: {e}")
            else:
                st.session_state["guidance_raw"] = safe_decode(data)

    with colA2:
        pasted = st.text_area("Or paste guidance text/markdown", height=220, key="guidance_paste")
        if st.button("Use pasted text", key="guidance_use_paste_btn"):
            st.session_state["guidance_raw"] = pasted or ""

    guidance_raw = (st.session_state.get("guidance_raw") or "").strip()
    if guidance_raw:
        st.success(f"Guidance loaded. Length: {len(guidance_raw)} chars.")
        record_artifact("guidance_raw", "input", guidance_raw, out_lang, meta={"source": "upload_or_paste"})
    else:
        st.info("Provide guidance content to continue.")

    st.markdown("## Step B — Guidance Structuring (Agent)")
    default_struct_prompt = f"""You are a regulatory documentation analyst.

Task:
- Transform the provided published guidance into highly organized Markdown.
- Preserve content; do not invent facts.
- Create:
  1) Clean section outline
  2) Table of extracted requirements (requirement | rationale | expected evidence)
  3) Glossary
  4) Open questions / ambiguities

Output language: {out_lang}.
"""
    agent_run_ui(
        agent_id="guidance_structuring_agent",
        tab_key="guid_struct",
        default_prompt=default_struct_prompt,
        default_input_text=guidance_raw,
        tab_label_for_history="Guidance Structuring",
    )
    guidance_structured = (st.session_state.get("guid_struct_output_effective") or "").strip()
    if guidance_structured:
        record_artifact("guidance_structured.md", "markdown", guidance_structured, out_lang)

    st.markdown("## Step C — FDA Related Research (Grounded Retrieval + Gemini Agent)")
    st.caption("Best-effort retrieval using public search; then Gemini synthesizes an Evidence Table with URLs (no fabrication).")

    user_hints = st.text_input("Optional hints (device type, intended use, product code, keywords)", key="guid_hints")

    colC1, colC2 = st.columns([1, 1])
    with colC1:
        research_model = st.selectbox("Gemini model (research)", GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE, index=0, key="fda_research_model")
    with colC2:
        research_max_tokens = st.number_input("max_tokens (research)", min_value=2000, max_value=120000, value=16000, step=1000, key="fda_research_max_tokens")

    default_research_prompt = f"""You are an FDA-focused regulatory researcher.

You will receive:
1) The user's guidance content (raw + structured)
2) A retrieval pack containing FDA URLs and truncated page text (best-effort)

Tasks:
- Identify FDA-related information relevant to the guidance topic:
  - FDA Guidance documents (final/draft)
  - FDA Recognized Consensus Standards
  - Any relevant FDA pages related to 510(k) expectations
- Create an "Evidence Table" in Markdown with columns:
  Source Type | Title | Organization | URL | Relevance (1-5) | Key extracted points | Notes/limits
- Then provide a short "How to use these sources" section.

Hard rules:
- Do NOT fabricate URLs, titles, standard numbers, or guidance names.
- If you cannot verify, label as "unverified" and explain.

Output language: {out_lang}.
"""
    research_prompt = st.text_area("Prompt (research agent)", value=default_research_prompt, height=170, key="fda_research_prompt")

    if st.button("Run grounded retrieval + research agent", key="fda_research_run_btn"):
        if not guidance_raw:
            st.warning("No guidance input.")
        else:
            with st.spinner("Retrieving FDA sources (best-effort)..."):
                retrieval_md, sources = build_fda_research_pack(guidance_raw, user_hints, max_urls=10)
                st.session_state["fda_retrieval_md"] = retrieval_md
                st.session_state["fda_sources_raw"] = sources

            combined_input = f"""=== GUIDANCE (RAW) ===
{guidance_raw}

=== GUIDANCE (STRUCTURED, if available) ===
{guidance_structured or "(not provided)"}

=== RETRIEVAL PACK ===
{st.session_state.get("fda_retrieval_md","")}
"""
            try:
                api_keys = st.session_state.get("api_keys", {})
                out = call_llm(
                    model=research_model,
                    system_prompt="You synthesize FDA evidence with citations and strict non-fabrication rules.",
                    user_prompt=f"{research_prompt}\n\n---\n\n{combined_input}",
                    max_tokens=int(research_max_tokens),
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["fda_evidence_md"] = out
                log_event("Guidance Studio", "FDA Research Agent", research_model, approx_tokens(combined_input + out))
            except Exception as e:
                st.error(f"Research agent failed: {e}")

    if st.session_state.get("fda_retrieval_md"):
        with st.expander("Retrieved sources pack (transparency)", expanded=False):
            st.text_area("Retrieval pack (read-only)", value=st.session_state["fda_retrieval_md"], height=240)

    evidence_md = st.text_area("Evidence Table & Research Notes (editable)", value=st.session_state.get("fda_evidence_md", ""), height=260, key="fda_evidence_edit")
    if evidence_md.strip():
        record_artifact("evidence_table.md", "markdown", evidence_md, out_lang)

    st.markdown("## Step D — Comprehensive Report (2000–3000 words, grounded)")
    colD1, colD2 = st.columns([1, 1])
    with colD1:
        report_model = st.selectbox("Gemini model (comprehensive report)", GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE, index=0, key="comp_report_model")
    with colD2:
        report_max_tokens = st.number_input("max_tokens (report)", min_value=4000, max_value=120000, value=24000, step=1000, key="comp_report_max_tokens")

    default_report_prompt = f"""You are a senior medical device regulatory analyst.

Write a comprehensive Markdown report (target 2000–3000 words) grounded in:
- The provided published guidance (user input)
- The evidence table and retrieved FDA sources

Requirements:
- Do not fabricate titles, URLs, standard numbers, or regulatory clauses.
- Include: Executive Summary, Requirement Extraction Table, FDA Landscape, International Regulatory/Standards Mapping,
  Evidence & Testing Matrix, Gaps/Risks/Open Questions, and References.
- Add confidence labels (High/Med/Low) for major claims with brief rationale.

Output language: {out_lang}.
"""
    report_prompt = st.text_area("Prompt (comprehensive report)", value=default_report_prompt, height=170, key="comp_report_prompt")

    if st.button("Generate comprehensive report", key="comp_report_run_btn"):
        if not guidance_raw:
            st.warning("No guidance input.")
        elif not evidence_md.strip():
            st.warning("Evidence table is empty. Run Step C first (or paste evidence).")
        else:
            api_keys = st.session_state.get("api_keys", {})
            combined_input = f"""=== GUIDANCE (RAW) ===
{guidance_raw}

=== GUIDANCE (STRUCTURED) ===
{guidance_structured or "(not provided)"}

=== FDA EVIDENCE TABLE & NOTES ===
{evidence_md}
"""
            try:
                out = call_llm(
                    model=report_model,
                    system_prompt="You write grounded regulatory reports with citations.",
                    user_prompt=f"{report_prompt}\n\n---\n\n{combined_input}",
                    max_tokens=int(report_max_tokens),
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["comprehensive_report_md"] = out
                log_event("Guidance Studio", "Comprehensive Report Agent", report_model, approx_tokens(combined_input + out))
            except Exception as e:
                st.error(f"Report generation failed: {e}")

    comp_md = st.text_area("Comprehensive report (editable)", value=st.session_state.get("comprehensive_report_md", ""), height=320, key="comp_report_edit")
    if comp_md.strip():
        record_artifact("comprehensive_report.md", "markdown", comp_md, out_lang)
        c1, c2 = st.columns(2)
        with c1:
            download_block("Download report (.md)", "comprehensive_report.md", comp_md, mime="text/markdown")
        with c2:
            download_block("Download report (.txt)", "comprehensive_report.txt", comp_md, mime="text/plain")

    st.markdown("## Step E — Template-based Report (user template or default)")
    template_mode = st.radio("Template source", ["Default template", "Paste/upload template"], index=0, horizontal=True, key="tmpl_mode")

    template_text = ""
    if template_mode == "Default template":
        template_text = DEFAULT_REPORT_TEMPLATE_TW
        st.text_area("Default template (read-only)", value=template_text, height=220, key="default_template_ro")
    else:
        tmpl_up = st.file_uploader("Upload template (txt/md)", type=["txt", "md"], key="tmpl_upload")
        tmpl_paste = st.text_area("Or paste template", height=180, key="tmpl_paste")
        if tmpl_up is not None:
            template_text = safe_decode(tmpl_up.getvalue())
        else:
            template_text = tmpl_paste or ""

    colE1, colE2 = st.columns([1, 1])
    with colE1:
        tmpl_model = st.selectbox("Gemini model (template stage)", GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE, index=0, key="tmpl_model")
    with colE2:
        tmpl_max_tokens = st.number_input("max_tokens (template)", min_value=4000, max_value=120000, value=24000, step=1000, key="tmpl_max_tokens")

    default_tmpl_prompt = f"""You are a regulatory report editor.

Input:
- A comprehensive regulatory report (grounded)
- A report template (structure/checklist format)

Task:
- Rewrite the report so it conforms to the template structure.
- Preserve grounding and references. Do not invent missing information.
- If template asks for content not present, add a clear marker like "※待補" (or "TBD") and list what is missing.

Output language: {out_lang}.
"""
    tmpl_prompt = st.text_area("Prompt (template applier)", value=default_tmpl_prompt, height=150, key="tmpl_prompt")

    if st.button("Generate template-based report", key="tmpl_run_btn"):
        if not comp_md.strip():
            st.warning("Comprehensive report is empty. Run Step D first.")
        elif not template_text.strip():
            st.warning("Template is empty. Provide template or use default.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            combined_input = f"""=== COMPREHENSIVE REPORT ===
{comp_md}

=== TEMPLATE ===
{template_text}
"""
            try:
                out = call_llm(
                    model=tmpl_model,
                    system_prompt="You apply regulatory templates without fabricating details.",
                    user_prompt=f"{tmpl_prompt}\n\n---\n\n{combined_input}",
                    max_tokens=int(tmpl_max_tokens),
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["templated_report_md"] = out
                log_event("Guidance Studio", "Template Report Agent", tmpl_model, approx_tokens(combined_input + out))
            except Exception as e:
                st.error(f"Template report failed: {e}")

    templated_md = st.text_area("Template-based report (editable)", value=st.session_state.get("templated_report_md", ""), height=320, key="templated_report_edit")
    if templated_md.strip():
        record_artifact("templated_report.md", "markdown", templated_md, out_lang)
        c1, c2 = st.columns(2)
        with c1:
            download_block("Download templated report (.md)", "templated_report.md", templated_md, mime="text/markdown")
        with c2:
            download_block("Download templated report (.txt)", "templated_report.txt", templated_md, mime="text/plain")

    st.markdown("## Step F — Generate skill.md (Skill Creator format, with 3 WOW features in the skill)")
    colF1, colF2 = st.columns([1, 1])
    with colF1:
        skill_model = st.selectbox("Gemini model (skill.md)", GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE, index=0, key="skill_model")
    with colF2:
        skill_max_tokens = st.number_input("max_tokens (skill.md)", min_value=3000, max_value=120000, value=16000, step=1000, key="skill_max_tokens")

    default_skill_prompt = f"""Use the Skill Creator format to produce the entire content for a single file named skill.md.

Goal of the skill:
- Generate comprehensive medical device guidance grounded in a provided published guidance input.
- Mimic the structure and information density of the provided guidance.
- Include a review checklist and evidence mapping.
- Include 3 WOW features inside the skill:
  1) Auto-Structure Mimicry (learn and mimic the input guidance structure)
  2) Citation-Confidence Heat Labels (High/Med/Low for key claims, with rationale)
  3) Checklist Autopilot + Gap Flags (auto checklist with missing-evidence flags)

Hard rules:
- The entire skill.md content MUST be written in: {out_lang}.
- The frontmatter description must be "pushy" to trigger on: guidance, regulatory report, standards mapping, checklist, 510(k), templates.
- Include clear output templates and steps.

Input will include guidance, structured guidance, evidence table, and reports.

Now generate skill.md content only (no extra commentary).
"""
    skill_prompt = st.text_area("Prompt (skill.md generator)", value=default_skill_prompt, height=170, key="skill_prompt")

    if st.button("Generate skill.md", key="skill_run_btn"):
        if not comp_md.strip():
            st.warning("Comprehensive report empty. Run Step D first.")
        else:
            api_keys = st.session_state.get("api_keys", {})
            combined_input = f"""=== GUIDANCE (RAW) ===
{guidance_raw}

=== GUIDANCE (STRUCTURED) ===
{guidance_structured or "(not provided)"}

=== EVIDENCE TABLE ===
{evidence_md}

=== COMPREHENSIVE REPORT ===
{comp_md}

=== TEMPLATE-BASED REPORT (optional) ===
{templated_md or "(not provided)"}
"""
            try:
                out = call_llm(
                    model=skill_model,
                    system_prompt="You write skills in standard SKILL.md format.",
                    user_prompt=f"{skill_prompt}\n\n---\n\n{combined_input}",
                    max_tokens=int(skill_max_tokens),
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["skill_md"] = out
                log_event("Guidance Studio", "Skill.md Generator", skill_model, approx_tokens(combined_input + out))
            except Exception as e:
                st.error(f"skill.md generation failed: {e}")

    skill_md = st.text_area("skill.md (editable)", value=st.session_state.get("skill_md", ""), height=340, key="skill_md_edit")
    if skill_md.strip():
        record_artifact("skill.md", "skill", skill_md, out_lang)
        download_block("Download skill.md", "skill.md", skill_md, mime="text/markdown")

    st.markdown("## WOW AI Tools (Optional) — 3 additional WOW AI features")
    st.caption("Delta Radar, Evidence Traceability Table, Smart Checklist Builder (all allow prompt/model changes).")

    with st.expander("WOW #1 — Regulatory Delta Radar", expanded=False):
        d_model = st.selectbox("Model (Delta Radar)", ALL_MODELS, index=ALL_MODELS.index(st.session_state.settings["model"]), key="delta_model")
        d_prompt = st.text_area(
            "Prompt (Delta Radar)",
            value=f"Compare the two texts and produce a regulatory delta report in {out_lang}: additions, removals, changed requirements/standards, impact, recommended actions. Use markdown tables.",
            height=120,
            key="delta_prompt",
        )
        old_text = st.text_area("Old version", height=160, key="delta_old")
        new_text = st.text_area("New version", height=160, key="delta_new")
        if st.button("Run Delta Radar", key="delta_run"):
            api_keys = st.session_state.get("api_keys", {})
            combined = f"=== OLD ===\n{old_text}\n\n=== NEW ===\n{new_text}"
            try:
                out = call_llm(
                    model=d_model,
                    system_prompt="You generate delta analysis for regulatory documents.",
                    user_prompt=f"{d_prompt}\n\n---\n\n{combined}",
                    max_tokens=16000,
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["delta_out"] = out
                log_event("Guidance Studio", "Delta Radar", d_model, approx_tokens(combined + out))
            except Exception as e:
                st.error(f"Delta Radar failed: {e}")
        st.text_area("Delta report (editable)", value=st.session_state.get("delta_out", ""), height=240, key="delta_out_edit")

    with st.expander("WOW #2 — Evidence Traceability Table", expanded=False):
        tr_model = st.selectbox("Model (Traceability)", ALL_MODELS, index=ALL_MODELS.index("gpt-4o-mini"), key="trace_model")
        tr_prompt = st.text_area(
            "Prompt (Traceability)",
            value=f"From the report text and evidence table, create a traceability table: Claim ID | Claim | Source URLs | Confidence | Notes. Output in {out_lang}.",
            height=120,
            key="trace_prompt",
        )
        base_for_trace = st.text_area("Input (report + evidence)", value=(comp_md + "\n\n" + evidence_md).strip(), height=220, key="trace_input")
        if st.button("Generate traceability table", key="trace_run"):
            api_keys = st.session_state.get("api_keys", {})
            try:
                out = call_llm(
                    model=tr_model,
                    system_prompt="You create evidence traceability tables for audit.",
                    user_prompt=f"{tr_prompt}\n\n---\n\n{base_for_trace}",
                    max_tokens=16000,
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["trace_out"] = out
                log_event("Guidance Studio", "Traceability", tr_model, approx_tokens(base_for_trace + out))
            except Exception as e:
                st.error(f"Traceability failed: {e}")
        trace_out = st.text_area("Traceability output (editable)", value=st.session_state.get("trace_out", ""), height=260, key="trace_out_edit")
        if trace_out.strip():
            record_artifact("traceability_table.md", "markdown", trace_out, out_lang)

    with st.expander("WOW #3 — Smart Checklist Builder", expanded=False):
        ck_model = st.selectbox("Model (Checklist Builder)", ALL_MODELS, index=ALL_MODELS.index(st.session_state.settings["model"]), key="ck_model")
        ck_prompt = st.text_area(
            "Prompt (Checklist Builder)",
            value=f"Create a review checklist from the input. Output markdown table with columns: Item | What to check | Expected evidence | Status (blank) | Notes. Language: {out_lang}.",
            height=120,
            key="ck_prompt",
        )
        ck_input = st.text_area("Input (any report)", value=(templated_md or comp_md).strip(), height=220, key="ck_input")
        if st.button("Generate checklist", key="ck_run"):
            api_keys = st.session_state.get("api_keys", {})
            try:
                out = call_llm(
                    model=ck_model,
                    system_prompt="You generate practical regulatory checklists.",
                    user_prompt=f"{ck_prompt}\n\n---\n\n{ck_input}",
                    max_tokens=16000,
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["ck_out"] = out
                log_event("Guidance Studio", "Checklist Builder", ck_model, approx_tokens(ck_input + out))
            except Exception as e:
                st.error(f"Checklist Builder failed: {e}")
        ck_out = st.text_area("Checklist (editable)", value=st.session_state.get("ck_out", ""), height=260, key="ck_out_edit")
        if ck_out.strip():
            record_artifact("smart_checklist.md", "markdown", ck_out, out_lang)


# =========================
# Main
# =========================

st.set_page_config(page_title=APP_TITLE, layout="wide")

if "settings" not in st.session_state:
    st.session_state["settings"] = {
        "theme": "Light",
        "language": "繁體中文",
        "painter_style": "Van Gogh",
        "model": "gpt-4o-mini",
        "max_tokens": DEFAULT_MAX_TOKENS,
        "temperature": 0.2,
    }
if "history" not in st.session_state:
    st.session_state["history"] = []
if "artifacts" not in st.session_state:
    st.session_state["artifacts"] = []

# Load agents.yaml or fallback
if "agents_cfg" not in st.session_state:
    try:
        with open("agents.yaml", "r", encoding="utf-8") as f:
            st.session_state["agents_cfg"] = yaml.safe_load(f)
    except Exception:
        st.session_state["agents_cfg"] = {
            "agents": {
                "fda_510k_intel_agent": {
                    "name": "510(k) Intelligence Agent",
                    "model": "gpt-4o-mini",
                    "system_prompt": "You are an FDA 510(k) analyst.",
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "category": "FDA 510(k)",
                },
                "pdf_to_markdown_agent": {
                    "name": "PDF to Markdown Agent",
                    "model": "gemini-2.5-flash",
                    "system_prompt": "You convert PDF-extracted text into clean markdown.",
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "category": "Document Preprocessing",
                },
                "guidance_structuring_agent": {
                    "name": "Guidance Structuring Agent",
                    "model": "gemini-2.5-flash",
                    "system_prompt": "You structure published guidance into clean markdown and requirement tables.",
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "category": "Guidance Studio",
                },
                "tw_screen_review_agent": {
                    "name": "TFDA 預審形式審查代理",
                    "model": "gemini-2.5-flash",
                    "system_prompt": "You are a TFDA premarket screen reviewer.",
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "category": "TFDA Premarket",
                },
                "tw_app_doc_helper": {
                    "name": "TFDA 申請書撰寫助手",
                    "model": "gpt-4o-mini",
                    "system_prompt": "You help improve TFDA application documents.",
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "category": "TFDA Premarket",
                },
                "submission_structurer_agent": {
                    "name": "510(k) Submission Structurer",
                    "model": "gpt-4o-mini",
                    "system_prompt": "You structure a 510(k) submission into organized markdown.",
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "category": "FDA 510(k)",
                },
                "review_memo_builder_agent": {
                    "name": "510(k) Review Memo Builder",
                    "model": "gpt-4o-mini",
                    "system_prompt": "You draft review memos based on checklists and structured submissions.",
                    "max_tokens": DEFAULT_MAX_TOKENS,
                    "category": "FDA 510(k)",
                },
            }
        }

render_sidebar()
apply_style(st.session_state.settings["theme"], st.session_state.settings["painter_style"])

tab_labels = [
    t("Dashboard"),
    t("Guidance Studio"),
    t("TW Premarket"),
    t("510k_tab"),
    t("PDF → Markdown"),
    t("Checklist & Report"),
    t("Note Keeper & Magics"),
    t("Agents Config"),
]
tabs = st.tabs(tab_labels)

with tabs[0]:
    render_dashboard()
with tabs[1]:
    render_guidance_studio_tab()
with tabs[2]:
    render_tw_premarket_tab()
with tabs[3]:
    render_510k_tab()
with tabs[4]:
    render_pdf_to_md_tab()
with tabs[5]:
    render_510k_review_pipeline_tab()
with tabs[6]:
    render_note_keeper_tab()
with tabs[7]:
    render_agents_config_tab()
