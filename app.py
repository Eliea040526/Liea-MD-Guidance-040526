from __future__ import annotations

import os
import re
import json
import time
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
    # Anthropic (examples; allow via agents.yaml too)
    "claude-3-5-sonnet-2024-10",
    "claude-3-5-haiku-20241022",
    # Grok
    "grok-4-fast-reasoning",
    "grok-3-mini",
]

OPENAI_MODELS = {"gpt-4o-mini", "gpt-4.1-mini"}
GEMINI_MODELS = {
    "gemini-2.5-flash",
    "gemini-3-flash-preview",
    "gemini-2.5-flash-lite",
    "gemini-3-pro-preview",
}
ANTHROPIC_MODELS = {"claude-3-5-sonnet-2024-10", "claude-3-5-haiku-20241022"}
GROK_MODELS = {"grok-4-fast-reasoning", "grok-3-mini"}

GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE = {"gemini-2.5-flash", "gemini-3-flash-preview"}

PAINTER_STYLES = [
    "Van Gogh", "Monet", "Picasso", "Da Vinci", "Rembrandt",
    "Matisse", "Kandinsky", "Hokusai", "Yayoi Kusama", "Frida Kahlo",
    "Salvador Dali", "Rothko", "Pollock", "Chagall", "Basquiat",
    "Haring", "Georgia O'Keeffe", "Turner", "Seurat", "Escher",
]

LABELS = {
    "Dashboard": {"English": "Dashboard", "繁體中文": "儀表板"},
    "TW Premarket": {"English": "TW Premarket Application", "繁體中文": "第二、三等級醫療器材查驗登記"},
    "510k_tab": {"English": "510(k) Intelligence", "繁體中文": "510(k) 智能分析"},
    "PDF → Markdown": {"English": "PDF → Markdown", "繁體中文": "PDF → Markdown"},
    "Checklist & Report": {"English": "510(k) Review Pipeline", "繁體中文": "510(k) 審查全流程"},
    "Note Keeper & Magics": {"English": "Note Keeper & Magics", "繁體中文": "筆記助手與魔法"},
    "Agents Config": {"English": "Agents Config Studio", "繁體中文": "代理設定工作室"},
    "Guidance Studio": {"English": "Guidance Research & Report Studio", "繁體中文": "指引研究與報告工作室"},
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
# Helpers: localization & style
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
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
            background-color: #0b1220 !important; color: #e5e7eb !important; border-radius: 0.6rem;
        }
        """
    else:
        css += """
        body { color: #111827; }
        .stButton>button { background-color: #2563eb; color: white; border-radius: 999px; }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
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
    # allow models defined in agents.yaml; infer by prefix
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
        # Keep prompts simple to reduce SDK incompatibilities across Gemini model variants
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
        # Defensive parsing
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


def approx_tokens(text: str) -> int:
    # Rough estimate; avoids SDK tokenizers
    return max(1, int(len(text) / 4))


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
    for line in text.splitlines():
        if y < margin:
            c.showPage()
            y = height - margin
        c.drawString(margin, y, line[:2000])
        y -= line_height
    c.save()
    buf.seek(0)
    return buf.getvalue()


def show_pdf(pdf_bytes: bytes, height: int = 600):
    if not pdf_bytes:
        return
    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="{height}"></iframe>',
        unsafe_allow_html=True,
    )


def strip_html_to_text(html: str) -> str:
    # Minimal HTML -> text; avoids bs4 dependency
    html = re.sub(r"(?is)<script.*?>.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?>.*?</style>", " ", html)
    html = re.sub(r"(?is)<.*?>", " ", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


# =========================
# Lightweight web search (no key)
# =========================

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


def duckduckgo_search(query: str, max_results: int = 8, timeout: int = 25) -> List[SearchResult]:
    """
    DuckDuckGo HTML endpoint (no key). Best-effort. If blocked, returns empty list.
    """
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

    # Parse results without BeautifulSoup
    # DDG result blocks typically contain: <a class="result__a" href="...">Title</a>
    results: List[SearchResult] = []
    for m in re.finditer(r'(?is)<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html):
        href = m.group(1).strip()
        title_html = m.group(2).strip()
        title = strip_html_to_text(title_html)
        if not href.startswith("http"):
            continue

        # Snippet nearby: <a ...> ... </a> ... <a class="result__snippet"> or <div class="result__snippet">
        # Fallback: empty snippet
        snippet = ""
        tail = html[m.end(): m.end() + 1200]
        sn = re.search(r'(?is)class="result__snippet"[^>]*>(.*?)</(?:a|div)>', tail)
        if sn:
            snippet = strip_html_to_text(sn.group(1))

        results.append(SearchResult(title=title[:200], url=href, snippet=snippet[:300]))
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
            content_type = r.headers.get("content-type", "")
            text = r.text if "text" in content_type or "html" in content_type or not content_type else r.text
            txt = strip_html_to_text(text)
            return txt[:max_chars]
    except Exception:
        return ""


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

    run = st.button("Run Agent", key=f"{tab_key}_run")

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
    edited = st.text_area(
        "Output (editable)",
        value=output,
        height=320,
        key=f"{tab_key}_output_edited",
    )
    st.session_state[f"{tab_key}_output_effective"] = edited


# =========================
# Sidebar
# =========================

def render_sidebar():
    with st.sidebar:
        st.markdown("### Global Settings")

        st.session_state.settings["theme"] = st.radio(
            "Theme",
            ["Light", "Dark"],
            index=0 if st.session_state.settings["theme"] == "Light" else 1,
        )
        st.session_state.settings["language"] = st.radio(
            "Language",
            ["English", "繁體中文"],
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
            0.0,
            1.0,
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
                cfg = yaml.safe_load(uploaded_agents.read())
                if isinstance(cfg, dict) and "agents" in cfg:
                    st.session_state["agents_cfg"] = cfg
                    st.success("Custom agents.yaml loaded for this session.")
                else:
                    st.warning("Uploaded YAML has no top-level 'agents' key. Keeping current config.")
            except Exception as e:
                st.error(f"Failed to parse uploaded YAML: {e}")


# =========================
# Awesome Dashboard (expanded)
# =========================

def render_dashboard():
    st.title(t("Dashboard"))
    hist = st.session_state["history"]
    if not hist:
        st.info("No runs yet.")
        return

    df = pd.DataFrame(hist)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Runs", len(df))
    with col2:
        st.metric("Unique Tabs", int(df["tab"].nunique()))
    with col3:
        st.metric("Approx Tokens", int(df["tokens_est"].sum()))

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
          <span class="wow-badge">Session artifacts: {len(st.session_state.get("artifacts", []))}</span>
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

    # Download Center (artifacts)
    st.markdown("### Download Center (Session Artifacts)")
    artifacts = st.session_state.get("artifacts", [])
    if not artifacts:
        st.caption("No artifacts recorded yet.")
    else:
        art_df = pd.DataFrame(artifacts)
        st.dataframe(art_df.sort_values("ts", ascending=False), use_container_width=True, height=260)


# =========================
# Minimal stubs for existing tabs
# (Preserved: 510(k), PDF->MD, Note Keeper, Agents Config)
# For TW Premarket, you can paste your existing implementation; here we keep a light placeholder.
# =========================

def render_tw_premarket_tab():
    st.title(t("TW Premarket"))
    st.info("TW Premarket tab is preserved. Integrate your full existing TW Premarket implementation here.")


def render_510k_tab():
    st.title(t("510k_tab"))
    device_name = st.text_input("Device Name")
    k_number = st.text_input("510(k) Number (e.g., K123456)")
    sponsor = st.text_input("Sponsor / Manufacturer (optional)")
    product_code = st.text_input("Product Code (optional)")
    extra_info = st.text_area("Additional context (indications, technology, etc.)")

    default_prompt = f"""
You are assisting an FDA 510(k) reviewer.

Task:
1. Summarize publicly available information to support review context (do not fabricate identifiers).
2. Produce a detailed, review-oriented summary (about 2000–3000 words).
3. Provide several markdown tables (device overview, indications, performance testing, risks).

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
        allow_model_override=True,
    )


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

- Goal: produce clean, structured markdown preserving headings, lists, and tables.
- Do not hallucinate content that is not in the text.

Language: {st.session_state.settings["language"]}.
"""
        agent_run_ui(
            agent_id="pdf_to_markdown_agent",
            tab_key="pdf_to_md",
            default_prompt=default_prompt,
            default_input_text=raw_text,
            tab_label_for_history="PDF → Markdown",
            allow_model_override=True,
        )
    else:
        st.info("Upload a PDF and click 'Extract Text' to begin.")


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
    raw_notes = st.text_area("Paste your notes (text or markdown)", height=220, key="notes_raw")

    note_model = st.selectbox("Model for Note → Markdown", ALL_MODELS, index=ALL_MODELS.index(st.session_state.settings["model"]), key="note_model")
    note_max_tokens = st.number_input("max_tokens", min_value=2000, max_value=120000, value=12000, step=1000, key="note_max_tokens")

    default_note_prompt = """你是一位協助醫療器材/510(k)/TFDA 審查員整理個人筆記的助手。

請將下列雜亂或半結構化的筆記整理成清晰的 Markdown：
1) 標題階層與條列清楚
2) 保留原意，不新增未出現的關鍵事實
3) 顯示：關鍵技術要點、主要風險與疑問、待釐清事項
"""
    note_struct_prompt = st.text_area("Prompt for Note → Markdown", value=default_note_prompt, height=160, key="note_struct_prompt")

    if st.button("Transform notes to structured Markdown", key="note_run_btn"):
        if raw_notes.strip():
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = f"{note_struct_prompt}\n\n=== RAW NOTES ===\n{raw_notes}"
            try:
                out = call_llm(
                    model=note_model,
                    system_prompt="You organize review notes into clean markdown.",
                    user_prompt=user_prompt,
                    max_tokens=int(note_max_tokens),
                    temperature=0.15,
                    api_keys=api_keys,
                )
                st.session_state["note_md"] = out
                log_event("Note Keeper", "Note Structurer", note_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please paste notes first.")

    base_note = st.text_area("Structured Note (editable)", value=st.session_state.get("note_md", raw_notes), height=280, key="note_md_edited")

    st.markdown("### Magic — AI Keywords (Coral default)")
    kw_input = st.text_input("Keywords (comma-separated)", value="510(k), TFDA, QMS, biocompatibility", key="kw_input")
    kw_color = st.color_picker("Color for keywords", "#FF7F50", key="kw_color")
    if st.button("Apply Keyword Highlighting", key="kw_apply_btn"):
        kws = [k.strip() for k in kw_input.split(",") if k.strip()]
        st.session_state["kw_note"] = highlight_keywords(base_note, kws, kw_color)

    if st.session_state.get("kw_note"):
        st.markdown(st.session_state["kw_note"], unsafe_allow_html=True)

    st.markdown("### Magic — Contradiction & Consistency Check (WOW)")
    cc_model = st.selectbox("Model (Consistency)", ALL_MODELS, index=ALL_MODELS.index(st.session_state.settings["model"]), key="cc_model")
    cc_prompt = st.text_area(
        "Prompt (Consistency)",
        value="請檢查以下筆記是否存在矛盾、版本不一致、名詞混用或推論過度，並輸出：矛盾點、影響、建議修正、需要向作者追問的問題清單（Markdown）。",
        height=120,
        key="cc_prompt",
    )
    if st.button("Run Consistency Check", key="cc_run_btn"):
        if base_note.strip():
            api_keys = st.session_state.get("api_keys", {})
            user_prompt = f"{cc_prompt}\n\n=== NOTE ===\n{base_note}"
            try:
                out = call_llm(
                    model=cc_model,
                    system_prompt="You detect contradictions and consistency issues in regulatory notes.",
                    user_prompt=user_prompt,
                    max_tokens=12000,
                    temperature=0.2,
                    api_keys=api_keys,
                )
                st.session_state["cc_out"] = out
                log_event("Note Keeper", "Consistency Check", cc_model, approx_tokens(user_prompt + out))
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("No note content to check.")

    if st.session_state.get("cc_out"):
        st.text_area("Consistency Output (editable)", value=st.session_state["cc_out"], height=240, key="cc_out_edit")


def render_agents_config_tab():
    st.title(t("Agents Config"))
    cfg = st.session_state.get("agents_cfg", {"agents": {}})
    agents_dict = cfg.get("agents", {}) if isinstance(cfg, dict) else {}

    st.subheader("Current Agents Overview")
    if not agents_dict:
        st.warning("No agents found in current agents.yaml.")
    else:
        df = pd.DataFrame([{
            "agent_id": aid,
            "name": ac.get("name", ""),
            "model": ac.get("model", ""),
            "category": ac.get("category", ""),
        } for aid, ac in agents_dict.items()])
        st.dataframe(df, use_container_width=True, height=260)

    st.markdown("---")
    st.subheader("Edit Full agents.yaml (raw text)")
    yaml_str_current = yaml.dump(cfg, allow_unicode=True, sort_keys=False)
    edited = st.text_area("agents.yaml (editable)", value=yaml_str_current, height=360, key="agents_yaml_editor")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Apply YAML to session", key="agents_apply_yaml"):
            try:
                new_cfg = yaml.safe_load(edited)
                if isinstance(new_cfg, dict) and "agents" in new_cfg:
                    st.session_state["agents_cfg"] = new_cfg
                    st.success("Updated agents.yaml in session.")
                else:
                    st.error("YAML must contain top-level 'agents' key.")
            except Exception as e:
                st.error(f"Parse error: {e}")
    with col2:
        st.download_button(
            "Download current agents.yaml",
            data=yaml_str_current.encode("utf-8"),
            file_name="agents.yaml",
            mime="text/yaml",
            key="agents_download_yaml",
        )


# =========================
# New: Guidance Research & Report Studio
# =========================

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


def build_fda_research_pack(guidance_text: str, user_hints: str, max_urls: int = 10) -> Tuple[str, List[dict]]:
    """
    Creates a best-effort retrieval pack:
    - Proposes search queries (rule-based + hints)
    - Uses DuckDuckGo to find FDA-related pages
    - Fetches text snippets for grounding
    Returns:
      - combined_retrieval_md
      - raw_sources list (dicts)
    """
    guidance_text = (guidance_text or "").strip()
    hints = (user_hints or "").strip()

    # Rule-based query seeds (kept short to avoid overfetch)
    seeds = []
    if hints:
        seeds.append(hints)
    # Use early part of guidance as signal
    first = re.sub(r"\s+", " ", guidance_text[:800])
    if first:
        seeds.append(first)

    # Extract some candidate keywords
    kw = []
    for token in re.findall(r"[A-Za-z][A-Za-z0-9\-\(\)\/]{2,}", guidance_text[:4000]):
        if token.lower() in {"and", "the", "for", "with", "this", "that"}:
            continue
        kw.append(token)
    kw = list(dict.fromkeys(kw))[:10]

    keyword_hint = " ".join(kw[:6]) if kw else ""
    query_candidates = [
        f"site:fda.gov guidance {keyword_hint}",
        f"site:fda.gov recognized consensus standards {keyword_hint}",
        f"FDA 510(k) performance testing {keyword_hint}",
        "FDA recognized consensus standards database",
        "FDA guidance medical device performance testing",
    ]
    # Add a device-specific seed if we detected something like "external fixator"
    if re.search(r"external\s+fix", guidance_text[:5000], re.I):
        query_candidates.insert(0, "site:fda.gov orthopedic external fixator guidance")
        query_candidates.insert(1, "site:fda.gov recognized consensus standards orthopedic external fixator")

    # De-duplicate and cap
    queries = []
    for q in query_candidates:
        q = q.strip()
        if q and q not in queries:
            queries.append(q)
    queries = queries[:5]

    sources: List[dict] = []
    retrieval_blocks: List[str] = []
    for q in queries:
        results = duckduckgo_search(q, max_results=6)
        if not results:
            continue
        for r in results:
            # Prefer FDA domains; still allow accessdata / fda.gov subdomains
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
            retrieval_blocks.append(
                f"### Source\n- Query: {q}\n- Title: {r.title}\n- URL: {r.url}\n\n"
                f"**Snippet:** {r.snippet}\n\n"
                f"**Fetched text (truncated):**\n{text}\n"
            )
            if len(sources) >= max_urls:
                break
        if len(sources) >= max_urls:
            break

    combined = "# FDA Retrieval Pack (Best-effort)\n\n" + ("\n\n".join(retrieval_blocks) if retrieval_blocks else "_No sources retrieved (network blocked or search unavailable)._")
    return combined, sources


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
        pdf_pages = None
        guidance_from_file = ""
        if up is not None:
            name = up.name.lower()
            try:
                data = up.getvalue()
            except Exception:
                data = up.read()

            if name.endswith(".pdf"):
                p1, p2 = st.columns(2)
                with p1:
                    from_p = st.number_input("PDF from page", min_value=1, value=1, key="guid_pdf_from")
                with p2:
                    to_p = st.number_input("PDF to page", min_value=1, value=20, key="guid_pdf_to")
                if st.button("Extract PDF text", key="guid_pdf_extract_btn"):
                    with st.spinner("Extracting PDF text..."):
                        try:
                            guidance_from_file = extract_pdf_pages_to_text(data, int(from_p), int(to_p))
                            st.session_state["guidance_raw"] = guidance_from_file
                        except Exception as e:
                            st.error(f"PDF extract failed: {e}")
            else:
                guidance_from_file = safe_decode(data)
                st.session_state["guidance_raw"] = guidance_from_file

    with colA2:
        pasted = st.text_area("Or paste guidance text/markdown", height=220, key="guidance_paste")
        if st.button("Use pasted text", key="guidance_use_paste_btn"):
            st.session_state["guidance_raw"] = pasted or ""

    guidance_raw = st.session_state.get("guidance_raw", "").strip()
    if guidance_raw:
        st.success(f"Guidance loaded. Length: {len(guidance_raw)} chars.")
        record_artifact("guidance_raw", "input", guidance_raw, out_lang, meta={"source": "upload_or_paste"})
    else:
        st.info("Provide guidance content to continue.")

    st.markdown("## Step B — Guidance Structuring (Agent)")
    default_struct_prompt = f"""You are a regulatory documentation analyst.

Task:
- Transform the provided published guidance into highly organized Markdown.
- Preserve all content; do not invent facts.
- Create:
  1) A clean section outline (headings/subheadings)
  2) A table of extracted requirements (requirement, rationale, evidence expected)
  3) Glossary (acronyms/terms)
  4) Open questions / ambiguities

Output language: {out_lang}.
"""
    agent_run_ui(
        agent_id="guidance_structuring_agent",
        tab_key="guid_struct",
        default_prompt=default_struct_prompt,
        default_input_text=guidance_raw,
        tab_label_for_history="Guidance Structuring",
        allow_model_override=True,
        model_allowlist=list(GEMINI_MODELS.union(OPENAI_MODELS, ANTHROPIC_MODELS, GROK_MODELS)),
    )
    guidance_structured = st.session_state.get("guid_struct_output_effective", "").strip()
    if guidance_structured:
        record_artifact("guidance_structured.md", "markdown", guidance_structured, out_lang)

    st.markdown("## Step C — FDA Related Research (Grounded Search + Agent)")
    st.caption("This step uses best-effort web retrieval and then Gemini synthesizes an evidence table with URLs.")
    user_hints = st.text_input("Optional hints (device type, intended use, product code, keywords)", key="guid_hints")

    colC1, colC2 = st.columns([1, 1])
    with colC1:
        research_model = st.selectbox(
            "Gemini model (research)",
            list(GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE),
            index=0,
            key="fda_research_model",
        )
    with colC2:
        research_max_tokens = st.number_input("max_tokens (research)", min_value=2000, max_value=120000, value=16000, step=1000, key="fda_research_max_tokens")

    default_research_prompt = f"""You are an FDA-focused regulatory researcher.

You will receive:
1) The user's guidance content (structured or raw)
2) A retrieval pack containing FDA URLs and truncated page text (best-effort)

Tasks:
- Identify FDA-related information relevant to the guidance topic:
  - FDA Guidance documents (final/draft)
  - FDA Recognized Consensus Standards (ISO/IEC/ASTM/AAMI, etc.)
  - Any relevant FDA pages about 510(k) summaries or performance testing expectations
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
                    system_prompt="You synthesize FDA regulatory evidence with citations.",
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
        with st.expander("Retrieved sources pack (debug / transparency)", expanded=False):
            st.text_area("Retrieval pack (read-only)", value=st.session_state["fda_retrieval_md"], height=240)

    evidence_md = st.text_area("Evidence Table & Research Notes (editable)", value=st.session_state.get("fda_evidence_md", ""), height=260, key="fda_evidence_edit")
    if evidence_md.strip():
        record_artifact("evidence_table.md", "markdown", evidence_md, out_lang)

    st.markdown("## Step D — Comprehensive Report (2000–3000 words, grounded)")
    colD1, colD2 = st.columns([1, 1])
    with colD1:
        report_model = st.selectbox(
            "Gemini model (comprehensive report)",
            list(GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE),
            index=0,
            key="comp_report_model",
        )
    with colD2:
        report_max_tokens = st.number_input("max_tokens (report)", min_value=4000, max_value=120000, value=24000, step=1000, key="comp_report_max_tokens")

    default_report_prompt = f"""You are a senior medical device regulatory analyst.

Write a comprehensive Markdown report (target 2000–3000 words) grounded in:
- The provided published guidance (user input)
- The evidence table and retrieved FDA sources

Requirements:
- Do not fabricate titles, URLs, standard numbers, or regulatory clauses.
- Include an Executive Summary, Requirement Extraction Table, FDA Landscape, International Regulatory/Standards Mapping,
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
        template_text = DEFAULT_REPORT_TEMPLATE_TW if out_lang == "繁體中文" else DEFAULT_REPORT_TEMPLATE_TW
        st.text_area("Default template (read-only)", value=template_text, height=220, key="default_template_ro")
    else:
        tmpl_up = st.file_uploader("Upload template (txt/md)", type=["txt", "md"], key="tmpl_upload")
        tmpl_paste = st.text_area("Or paste template", height=180, key="tmpl_paste")
        if tmpl_up is not None:
            template_text = safe_decode(tmpl_up.getvalue())
        else:
            template_text = tmpl_paste

    colE1, colE2 = st.columns([1, 1])
    with colE1:
        tmpl_model = st.selectbox(
            "Gemini model (template stage)",
            list(GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE),
            index=0,
            key="tmpl_model",
        )
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
        skill_model = st.selectbox(
            "Gemini model (skill.md)",
            list(GEMINI_REQUIRED_FOR_GUIDANCE_PIPELINE),
            index=0,
            key="skill_model",
        )
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
- The frontmatter description must be "pushy" so it triggers whenever user mentions guidance, regulatory report, standards mapping, checklist, 510(k), or template-based report writing.
- Include output format templates in the skill so an agent can follow reliably.

Input you will receive includes:
- Original guidance
- Structured guidance
- Evidence table
- Comprehensive report
- Template report (optional)

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

    st.markdown("## WOW AI Tools (Optional)")
    st.caption("These are extra AI features: Delta Radar, Traceability Table, Smart Checklist Builder.")

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
        tr_model = st.selectbox("Model (Traceability)", ALL_MODELS, index=ALL_MODELS.index("gpt-4o-mini") if "gpt-4o-mini" in ALL_MODELS else 0, key="trace_model")
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
# App initialization
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

# Load agents.yaml (fallback default)
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
    render_note_keeper_tab()
with tabs[6]:
    render_agents_config_tab()
