import streamlit as st
import pandas as pd
from openai import OpenAI
from datetime import datetime
import os

st.set_page_config(page_title="AI Pazar Analizi", layout="wide")
st.title("🤖 AI Pazar Analiz Agenti")

# Groq API Client
client = OpenAI(
   client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

st.sidebar.header("⚙️ Ayarlar")
country = st.sidebar.selectbox("🌍 Ülke", ["TR", "US", "GB", "DE", "FR"])
topic = st.sidebar.text_input("📊 Analiz Konusu", "Yapay Zeka")
competitors = st.sidebar.text_area("🎯 Rakipler (virgülle ayır)", "")

def ai_analyze(topic, country, competitors):
    try:
        prompt = f"""Sen uzman bir pazar analistisin.

KONU: {topic}
ÜLKE: {country}
RAKİPLER: {competitors if competitors else 'Belirtilmemiş'}

Aşağıdaki başlıklarda DETAYLI analiz yap:
1. 📊 PAZAR DURUMU
2. 🎯 HEDEF KİTLE
3. 🔥 REKABET ANALİZİ
4. 💡 FIRSATLAR
5. ⚠️ RİSKLER
6. 📈 STRATEJİK ÖNERİLER

Türkçe, net öneriler ver. Madde madde yaz."""

        with st.spinner('🤖 AI düşünüyor... (10-30 saniye)...'):
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"Hata: {str(e)}"

def save_analysis(topic, country, analysis):
    file = 'gecmis.csv'
    df = pd.DataFrame([{
        'Tarih': datetime.now().strftime("%Y-%m-%d %H:%M"),
        'Konu': topic,
        'Ulke': country,
        'Analiz': analysis[:300]
    }])
    if not os.path.exists(file):
        df.to_csv(file, index=False, encoding='utf-8-sig')
    else:
        df.to_csv(file, mode='a', header=False, index=False, encoding='utf-8-sig')

col1, col2 = st.columns(2)
with col1:
    st.metric("🌍 Ülke", country)
with col2:
    st.metric("🔍 Konu", topic)

if st.button("🚀 ANALİZİ BAŞLAT", type="primary", use_container_width=True):
    with st.spinner('Bekleyin...'):
        analysis = ai_analyze(topic, country, competitors)
        if analysis and "Hata" not in analysis:
            st.markdown(analysis)
            save_analysis(topic, country, analysis)
            st.success("✅ Kaydedildi!")
        else:
            st.error(f"❌ {analysis}")

st.markdown("---")
st.subheader("📁 Geçmiş Analizler")
file = 'gecmis.csv'
if os.path.exists(file):
    st.dataframe(pd.read_csv(file).tail(10), use_container_width=True)
else:
    st.info("Henüz geçmiş analiz yok.")
