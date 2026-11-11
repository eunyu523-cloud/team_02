import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET

# --- 1. 기본 설정 및 제목 ---
st.set_page_config(page_title="부동산 실거래가 분석", page_icon="🏢", layout="wide")
st.title("🏢 서울 지역 아파트 실거래가 및 자산 트렌드 분석")
st.markdown("국토교통부 공공데이터 API를 활용하여 아파트 매매 실거래가 추이와 가격 격차를 분석합니다.")

# --- 2. 사이드바 (검색 조건 설정) ---
st.sidebar.header("🔍 검색 조건 설정")
api_key = st.sidebar.text_input("공공데이터포털 API 인증키 (일반 인증키)", type="password")

# 서울 지역 코드 (종로구, 강남구, 서초구, 송파구)
gu_dict = {"종로구": "11110", "강남구": "11680", "서초구": "11650", "송파구": "11710"}
selected_gu_name = st.sidebar.selectbox("서울 자치구 선택", list(gu_dict.keys()))
lawd_cd = gu_dict[selected_gu_name]

deal_ymd = st.sidebar.text_input("조회 연월 (YYYYMM)", value="202310")

# --- 3. 데이터 수집 함수 (API 호출) ---
@st.cache_data
def get_apt_trade_data(api_key, lawd_cd, deal_ymd):
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    params = {
        "serviceKey": api_key,
        "pageNo": "1",
        "numOfRows": "100",
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd
    }

    try:
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)

        items = root.findall(".//item")
        if not items:
            return pd.DataFrame()

        data = []
        for item in items:
            data.append({
                "아파트": item.findtext("aptNm"),
                "법정동": item.findtext("umdNm"),
                "전용면적(㎡)": float(item.findtext("excluUseAr")),
                "거래금액(만원)": int(item.findtext("dealAmount").replace(",", "").strip()),
                "층": item.findtext("floor"),
                "건축년도": item.findtext("buildYear")
            })
        return pd.DataFrame(data)
    except Exception as e:
        return None

# --- 4. 화면 출력 (데이터 확인) ---
st.subheader(f"📊 {selected_gu_name} 아파트 실거래가 수집 데이터")

if st.sidebar.button("데이터 불러오기"):
    if api_key:
        with st.spinner("공공데이터 API에서 실거래가를 불러오는 중입니다..."):
            df = get_apt_trade_data(api_key, lawd_cd, deal_ymd)
            if df is not None and not df.empty:
                st.success("데이터 수집 완료!")
                st.dataframe(df, use_container_width=True)
                st.metric(label="총 거래 건수", value=f"{len(df)} 건")
            else:
                st.warning("해당 조건에 일치하는 거래 내역이 없거나 API 키가 아직 승인 반영 전일 수 있습니다.")
    else:
        st.error("좌측 사이드바에 API 인증키를 입력해주세요.")
else:
    st.info("API 키를 입력하고 데이터를 불러오기 전까지 샘플 데이터가 표시됩니다.")
    sample_data = pd.DataFrame({
        "아파트": ["경희궁자이", "은마아파트", "반포자이", "잠실엘스"],
        "법정동": ["홍파동", "대치동", "반포동", "잠실동"],
        "전용면적(㎡)": [84.8, 76.7, 84.9, 84.8],
        "거래금액(만원)": [205000, 230000, 350000, 240000],
        "층": ["12", "5", "21", "15"]
    })
    st.dataframe(sample_data, use_container_width=True)
