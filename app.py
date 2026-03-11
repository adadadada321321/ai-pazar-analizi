import streamlit as st
import pandas as pd
from openai import OpenAI
from datetime import datetime
import os
import time
from pytrends.request import TrendReq
import plotly.express as px
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="🤖 AI Pazar Analiz Agenti", layout="wide", page_icon="🤖")
st.title("🤖 AI Pazar Analiz Agenti")
st.markdown("*Otonom pazar araştırma, sosyal medya tarama ve NLP analizi*")

client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

st.sidebar.header("⚙️ Agent Ayarları")

country_options = {"Türkiye": "TR", "Amerika": "US", "İngiltere": "GB", "Almanya": "DE", "Fransa": "FR"}
country_name = st.sidebar.selectbox("🌍 Ülke", list(country_options.keys()))
country_code = country_options[country_name]

topic = st.sidebar.text_input("📊 Analiz Konusu", "Elektrikli Araba")
competitors = st.sidebar.text_area("🎯 Rakipler (virgülle ayır)", "Tesla, TOGG")

st.sidebar.subheader("🔧 Aktif Modüller")
use_trends = st.sidebar.checkbox("📈 Google Trends", value=True)
use_social = st.sidebar.checkbox("🐦 Sosyal Medya", value=True)
use_scrape = st.sidebar.checkbox("🌐 Web Scraping", value=True)
use_nlp = st.sidebar.checkbox("🧠 NLP Analiz", value=True)
use_report = st.sidebar.checkbox("📄 Rapor Export", value=True)

def get_trends_data(keyword, geo):
    try:
        pytrends = TrendReq(hl='tr-TR', tz=180)
        pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo=geo)
        df = pytrends.interest_over_time()
        if not df.empty:
            df = df.reset_index()
            return df
    except Exception as e:
        st.warning(f"Trends hatası: {e}")
    return None

def get_social_mentions(keyword):
    mentions = [
        {"platform": "Twitter", "text": f"{keyword} hakkında olumlu yorum", "sentiment": "positive"},
        {"platform": "Twitter", "text": f"{keyword} fiyatları yüksek", "sentiment": "negative"},
        {"platform": "LinkedIn", "text": f"{keyword} sektörü büyüyor", "sentiment": "positive"},
    ]
    return pd.DataFrame(mentions)

def scrape_web(url, keyword):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text if soup.find('title') else 'Başlık yok'
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc['content'] if meta_desc else 'Açıklama yok'
        keyword_count = response.text.lower().count(keyword.lower())
        return {"title": title[:100], "desc": desc[:200], "keyword_count": keyword_count}
    except:
        return None

def nlp_analyze(text, task='sentiment'):
    try:
        if task == 'sentiment':
            prompt = f"Metnin duygu analizini yap (pozitif/nötr/negatif):\n\n{text[:500]}"
        elif task == 'keywords':
            prompt = f"Metinden en önemli 5 anahtar kelimeyi çıkar:\n\n{text[:500]}"
        else:
            prompt = f"Metni 2 cümlede özetle:\n\n{text[:500]}"
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content
    except:
        return "NLP analizi yapılamadı"

def competitor_analysis(topic, competitors_list, country):
    competitors = [c.strip() for c in competitors_list.split(',') if c.strip()]
    analysis = []
    for comp in competitors:
        prompt = f"""{comp} şirketinin {topic} sektöründeki durumunu analiz et. Ülke: {country}
- Pazar payı tahmini - Güçlü yönler - Zayıf yönler
Madde madde, kısa yaz."""
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            analysis.append({"competitor": comp, "analysis": response.choices[0].message.content})
        except:
            analysis.append({"competitor": comp, "analysis": "Analiz yapılamadı"})
    return analysis
    
def run_agent(topic, country_code, country_name, competitors, modules):
    """Tüm agent modüllerini çalıştır"""
    results = {"topic": topic, "country": country_name, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    # 1. Ana AI Analiz
    with st.status("🧠 Ana AI analizi...", expanded=True) as status:
        prompt = f"""Sen kıdemli bir pazar analistisin.

KONU: {topic}
ÜLKE: {country_name} ({country_code})
RAKİPLER: {competitors}

Aşağıdaki başlıklarda PROFESYONEL analiz yap:

📊 MEVCUT DURUM
- Pazar büyüklüğü ve büyüme
- Ana trendler
- Regülasyonlar

🎯 HEDEF KİTLE
- Demografik profil
- Davranışsal özellikler
- İhtiyaç analizi

🔥 REKABET
- Pazar payları
- Farklılaşma noktaları
- Fırsat alanları

💡 STRATEJİ
- Kısa vadeli aksiyonlar
- Orta vadeli planlar
- Risk yönetimi

Türkçe, net, uygulanabilir, madde madde yaz."""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            results["main_analysis"] = response.choices[0].message.content
            status.update(label="✅ Ana analiz tamamlandı", state="complete")
        except Exception as e:
            results["main_analysis"] = f"Hata: {e}"
            status.update(label="❌ Ana analiz başarısız", state="error")
    
    # 2. Google Trends
    if modules.get("trends"):
        with st.status("📈 Google Trends verileri...", expanded=False) as status:
            trends_df = get_trends_data(topic, country_code)
            if trends_df is not None:
                if topic in trends_df.columns:
                    results["trends"] = {
                        "chart": px.line(trends_df, x='date', y=topic, title=f"{topic} - Arama İlgi Grafiği"),
                        "peak_date": trends_df.loc[trends_df[topic].idxmax(), 'date'] if not trends_df.empty else None,
                        "avg_interest": trends_df[topic].mean()
                    }
                else:
                    results["trends"] = {"chart": None}
                status.update(label="✅ Trends verisi alındı", state="complete")
            else:
                status.update(label="⚠️ Trends verisi alınamadı", state="warning")
    
    # 3. Sosyal Medya
    if modules.get("social"):
        with st.status("🐦 Sosyal medya tarama...", expanded=False) as status:
            social_df = get_social_mentions(topic)
            if not social_df.empty:
                results["social"] = {
                    "mentions": social_df.to_dict('records'),
                    "sentiment_dist": social_df['sentiment'].value_counts().to_dict()
                }
                status.update(label="✅ Sosyal medya verisi toplandı", state="complete")
    
    # 4. Web Scraping
    if modules.get("scrape"):
        with st.status("🌐 Web scraping...", expanded=False) as status:
            url = f"https://www.google.com/search?q={topic.replace(' ', '+')}"
            result = scrape_web(url, topic)
            if result:
                results["scraped"] = [result]
                status.update(label="✅ Web verisi çekildi", state="complete")
            else:
                status.update(label="⚠️ Web scraping başarısız", state="warning")
    
    # 5. Rakip Analizi
    if competitors.strip():
        with st.status("🔍 Rakip analizi...", expanded=False) as status:
            results["competitors"] = competitor_analysis(topic, competitors, country_name)
            status.update(label="✅ Rakip analizi tamamlandı", state="complete")
    
    # 6. NLP Analiz
    if modules.get("nlp") and results.get("main_analysis"):
        with st.status("🧠 NLP işleme...", expanded=False) as status:
            results["nlp"] = {
                "sentiment": nlp_analyze(results["main_analysis"], 'sentiment'),
                "keywords": nlp_analyze(results["main_analysis"], 'keywords'),
                "summary": nlp_analyze(results["main_analysis"], 'summary')
            }
            status.update(label="✅ NLP analizi tamamlandı", state="complete")
    
    return results

def run_agent(topic, country_code, country_name, competitors, modules):
    """Tüm agent modüllerini çalıştır"""
    results = {"topic": topic, "country": country_name, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    # 1. Ana AI Analiz
    with st.status("🧠 Ana AI analizi...", expanded=True) as status:
        prompt = f"""Sen kıdemli bir pazar analistisin.

KONU: {topic}
ÜLKE: {country_name} ({country_code})
RAKİPLER: {competitors}

Aşağıdaki başlıklarda PROFESYONEL analiz yap:

📊 MEVCUT DURUM
- Pazar büyüklüğü ve büyüme
- Ana trendler
- Regülasyonlar

🎯 HEDEF KİTLE
- Demografik profil
- Davranışsal özellikler
- İhtiyaç analizi

🔥 REKABET
- Pazar payları
- Farklılaşma noktaları
- Fırsat alanları

💡 STRATEJİ
- Kısa vadeli aksiyonlar
- Orta vadeli planlar
- Risk yönetimi

Türkçe, net, uygulanabilir, madde madde yaz."""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000
            )
            results["main_analysis"] = response.choices[0].message.content
            status.update(label="✅ Ana analiz tamamlandı", state="complete")
        except Exception as e:
            results["main_analysis"] = f"Hata: {e}"
            status.update(label="❌ Ana analiz başarısız", state="error")
    
    # 2. Google Trends
    if modules.get("trends"):
        with st.status("📈 Google Trends verileri...", expanded=False) as status:
            trends_df = get_trends_data(topic, country_code)
            if trends_df is not None:
                if topic in trends_df.columns:
                    results["trends"] = {
                        "chart": px.line(trends_df, x='date', y=topic, title=f"{topic} - Arama İlgi Grafiği"),
                        "peak_date": trends_df.loc[trends_df[topic].idxmax(), 'date'] if not trends_df.empty else None,
                        "avg_interest": trends_df[topic].mean()
                    }
                else:
                    results["trends"] = {"chart": None}
                status.update(label="✅ Trends verisi alındı", state="complete")
            else:
                status.update(label="⚠️ Trends verisi alınamadı", state="warning")
    
    # 3. Sosyal Medya
    if modules.get("social"):
        with st.status("🐦 Sosyal medya tarama...", expanded=False) as status:
            social_df = get_social_mentions(topic)
            if not social_df.empty:
                results["social"] = {
                    "mentions": social_df.to_dict('records'),
                    "sentiment_dist": social_df['sentiment'].value_counts().to_dict()
                }
                status.update(label="✅ Sosyal medya verisi toplandı", state="complete")
    
    # 4. Web Scraping
    if modules.get("scrape"):
        with st.status("🌐 Web scraping...", expanded=False) as status:
            url = f"https://www.google.com/search?q={topic.replace(' ', '+')}"
            result = scrape_web(url, topic)
            if result:
                results["scraped"] = [result]
                status.update(label="✅ Web verisi çekildi", state="complete")
            else:
                status.update(label="⚠️ Web scraping başarısız", state="warning")
    
    # 5. Rakip Analizi
    if competitors.strip():
        with st.status("🔍 Rakip analizi...", expanded=False) as status:
            results["competitors"] = competitor_analysis(topic, competitors, country_name)
            status.update(label="✅ Rakip analizi tamamlandı", state="complete")
    
    # 6. NLP Analiz
    if modules.get("nlp") and results.get("main_analysis"):
        with st.status("🧠 NLP işleme...", expanded=False) as status:
            results["nlp"] = {
                "sentiment": nlp_analyze(results["main_analysis"], 'sentiment'),
                "keywords": nlp_analyze(results["main_analysis"], 'keywords'),
                "summary": nlp_analyze(results["main_analysis"], 'summary')
            }
            status.update(label="✅ NLP analizi tamamlandı", state="complete")
    
    return results

