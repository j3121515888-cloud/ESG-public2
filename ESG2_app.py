import io

import pandas as pd
import requests
import streamlit as st
import urllib3

# verify=False 會產生警告，這裡先關閉警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="公開資訊觀測站資料", page_icon="📊", layout="wide")
st.title("📊 公開資訊觀測站 開放資料")

# ------------------------------------------------------------------
# 側邊欄：設定
# ------------------------------------------------------------------
DEFAULT_URL = "https://mopsfin.twse.com.tw/opendata/t187ap46_L_1.csv"  # 換連結

with st.sidebar:
    st.header("設定")
    url = st.text_input("CSV 連結", value=DEFAULT_URL)
    verify_ssl = st.checkbox("驗證 SSL 憑證", value=False)
    drop_na = st.checkbox("刪除含有空值的列 (dropna)", value=True)
    if st.button("🔄 重新抓取資料"):
        st.cache_data.clear()


# ------------------------------------------------------------------
# 抓取資料（快取 10 分鐘，避免每次互動都重新下載）
# ------------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner="資料下載中...")
def load_data(url: str, verify: bool) -> pd.DataFrame:
    response = requests.get(url, verify=verify, timeout=30)
    response.raise_for_status()
    # 直接從記憶體讀取，不需要先存成 data01.csv
    return pd.read_csv(io.BytesIO(response.content), encoding="utf-8-sig")  # 繁體中文


try:
    df = load_data(url, verify_ssl)
except Exception as e:
    st.error(f"資料抓取失敗：{e}")
    st.stop()

if drop_na:
    df = df.dropna()

# ------------------------------------------------------------------
# 主畫面
# ------------------------------------------------------------------
col1, col2 = st.columns(2)
col1.metric("資料筆數", f"{len(df):,}")
col2.metric("欄位數", len(df.columns))

keyword = st.text_input("🔍 關鍵字搜尋（搜尋所有欄位）")
if keyword:
    mask = df.astype(str).apply(lambda col: col.str.contains(keyword, case=False, na=False))
    df = df[mask.any(axis=1)]
    st.caption(f"符合 {len(df):,} 筆")

st.dataframe(df, use_container_width=True)

st.download_button(
    label="⬇️ 下載 CSV",
    data=df.to_csv(index=False).encode("utf-8-sig"),
    file_name="data01.csv",
    mime="text/csv",
)
