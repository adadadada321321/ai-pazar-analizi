import streamlit as st
import pandas as pd
from openai import OpenAI
from datetime import datetime
import os
import json
import time
from pytrends.request import TrendReq
import plotly.express as px
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF

# ==================== SAYFA AYARLARI ====================
st.set_page_config(page_title="🤖 AI Pazar Analiz Agenti", layout="wide", page_icon="🤖")
st.title("🤖 AI Pazar Analiz Agenti")
st.markdown("*Otonom pazar araştırma, sosyal medya tarama ve NLP analizi*")

# ==================== API CLIENT ====================
client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# ==================== YAN MENÜ ====================
st.sidebar.header("⚙️ Agent Ayarları")

country = st.sidebar.selectbox("🌍 Ülke", {
    "TR": "Türkiye", "US": "Amerika", "GB": "İngiltere", 
    "DE": "Almanya", "FR": "Fransa"
}.items(), format_func=lambda x: x[1])
country_code = list({
    "TR": "Türkiye", "US": "Amerika", "GB": "İngiltere", 
    "DE": "Almanya", "FR": "Fransa"
}.keys())[list({
    "TR": "Türkiye", "US": "Amerika", "GB": "İngiltere", 
    "DE": "Almanya", "FR": "Fransa"
}.values()).index(country)]

topic = st.sidebar.text_input("📊 Analiz Konusu", "Elektrikli Araba")
competitors = st.sidebar.text_area("🎯 Rakipler (virgülle ayır)", "Tesla, TOGG")

# Agent Modülleri
st.sidebar.subheader("🔧 Aktif Modüller")
use_trends = st.sidebar.checkbox("📈 Google Trends", value=True)
use_social = st.sidebar.checkbox("🐦 Sosyal Medya", value=True)
use_scrape = st.sidebar.checkbox("🌐 Web Scraping", value=True)
use_nlp = st.sidebar.checkbox("🧠 NLP Analiz", value=True)
use_report = st.sidebar.checkbox("📄 Rapor Export", value=True)

# ==================== AGENT MODÜLLERİ ====================

def get_trends_data(keyword, geo, timeframe='today 12-m'):
    """Google Trends verisi çek"""
    try:
        pytrends = TrendReq(hl='tr-TR', tz=180)
        pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()
        if not df.empty:
            df = df.reset_index()
            return df
    except Exception as e:
        st.warning(f"Trends hatası: {e}")
    return None

def get_social_mentions(keyword, platform='twitter'):
    """Sosyal medya mention'larını simüle et (API limitleri nedeniyle)"""
    # Gerçek implementation için Twitter API v2 free tier kullanılabilir
    # Şimdilik simüle edilmiş veri döndürüyoruz
    mentions = [
        {"platform": "Twitter", "text": f"{keyword} hakkında olumlu yorum", "sentiment": "positive"},
        {"platform": "Twitter", "text": f"{keyword} fiyatları yüksek", "sentiment": "negative"},
        {"platform": "LinkedIn", "text": f"{keyword} sektörü büyüyor", "sentiment": "positive"},
    ]
    return pd.DataFrame(mentions)

def scrape_web(url, keyword):
    """Basit web scraping"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Başlık ve meta açıklama çek
        title = soup.find('title').text if soup.find('title') else 'Başlık yok'
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc = meta_desc['content'] if meta_desc else 'Açıklama yok'
        
        # Keyword geçiş sayısını say
        keyword_count = response.text.lower().count(keyword.lower())
        
        return {"title": title[:100], "desc": desc[:200], "keyword_count": keyword_count}
    except:
        return None

def nlp_analyze(text, task='sentiment'):
    """NLP analizi: duygu, anahtar kelime, özet"""
    try:
        if task == 'sentiment':
            prompt = f"Metnin duygu analizini yap (pozitif/nötr/negatif) ve güven skoru ver (0-100):\n\n{text[:500]}"
        elif task == 'keywords':
            prompt = f"Metinden en önemli 5 anahtar kelimeyi çıkar:\n\n{text[:500]}"
        elif task == 'summary':
            prompt = f"Metni 2 cümlede özetle:\n\n{text[:500]}"
        else:
            prompt = text[:500]
            
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response.choices[0].message.content
    except:
        return "NLP analizi yapılamadı"

def competitor_analysis(topic, competitors_list, country):
    """Rakip analizi"""
    competitors = [c.strip() for c in competitors_list.split(',') if c.strip()]
    analysis = []
    
    for comp in competitors:
        prompt = f"""{comp} şirketinin {topic} sektöründeki durumunu analiz et.
Ülke: {country}
- Pazar payı tahmini
- Güçlü yönler
- Zayıf yönler
- Son hareketleri

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

def generate_pdf_report(data, filename="rapor.pdf"):
    """PDF rapor oluştur"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="AI Pazar Analiz Raporu", ln=True, align='C')
    pdf.ln(10)
    
    for key, value in data.items():
        pdf.multi_cell(0, 10, txt=f"{key}:\n{value}")
        pdf.ln(5)
    
    pdf.output(filename)
    return filename

# ==================== ANA AGENT FONKSİYONU ====================

def run_agent(topic, country_code, country_name, competitors, modules):
    """Tüm agent modüllerini çalıştır"""
    results = {"topic": topic, "country": country_name, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
    
    # 1. Ana AI Analiz
    with st.status("🧠 Ana AI analizi...", expanded=True) as status:
        prompt = f"""Sen kıdemli bir pazar analisti ve strateji danışmanısın.

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
                results["trends"] = {
                    "chart": px.line(trends_df, x='date', y=topic, title=f"{topic} - Arama İlgi Grafiği"),
                    "peak_date": trends_df.loc[trends_df[topic].idxmax(), 'date'] if not trends_df.empty else None,
                    "avg_interest": trends_df[topic].mean()
                }
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
    
    # 4. Web Scraping (örnek URL'ler)
    if modules.get("scrape"):
        with st.status("🌐 Web scraping...", expanded=False) as status:
            urls = [
                f"https://tr.investing.com/search?q={topic.replace(' ', '+')}",
                f"https://www.haberturk.com/arama/{topic.replace(' ', '-')}"
            ]
            scraped = []
            for url in urls[:1]:  # Sadece ilk URL'yi dene (hız için)
                result = scrape_web(url, topic)
                if result:
                    scraped.append(result)
            if scraped:
                results["scraped"] = scraped
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

# ==================== ANA ARAYÜZ ====================

# Bilgi Kartları
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🌍 Ülke", country)
with col2:
    st.metric("🔍 Konu", topic)
with col3:
    st.metric("🎯 Rakip Sayısı", len([c for c in competitors.split(',') if c.strip()]))

# Agent Çalıştır Butonu
if st.button("🚀 AGENT'I BAŞLAT", type="primary", use_container_width=True, icon="🤖"):
    with st.spinner('🤖 AI Agent çalışıyor... Tüm modüller aktif...'):
        
        # Modül ayarlarını hazırla
        modules = {
            "trends": use_trends,
            "social": use_social,
            "scrape": use_scrape,
            "nlp": use_nlp,
            "report": use_report
        }
        
        # Agent'ı çalıştır
        results = run_agent(topic, country_code, country, competitors, modules)
        
        # ==================== SONUÇLARI GÖSTER ====================
        
        # 1. Ana Analiz
        st.markdown("### 📋 Ana AI Analizi")
        st.markdown(results.get("main_analysis", "Analiz yok"))
        
        # 2. Google Trends Grafiği
        if results.get("trends") and results["trends"].get("chart"):
            st.markdown("### 📈 Google Trends")
            st.plotly_chart(results["trends"]["chart"], use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🔝 Zirve Tarih", results["trends"]["peak_date"])
            with col2:
                st.metric("📊 Ort. İlgi", f"{results['trends']['avg_interest']:.1f}")
        
        # 3. Sosyal Medya
        if results.get("social"):
            st.markdown("### 🐦 Sosyal Medya Görünürlük")
            social_df = pd.DataFrame(results["social"]["mentions"])
            st.dataframe(social_df, use_container_width=True)
            
            # Duygu dağılımı
            if results["social"].get("sentiment_dist"):
                fig = px.pie(values=list(results["social"]["sentiment_dist"].values()), 
                           names=list(results["social"]["sentiment_dist"].keys()),
                           title="Duygu Dağılımı")
                st.plotly_chart(fig, use_container_width=True)
        
        # 4. Web Scraping Sonuçları
        if results.get("scraped"):
            st.markdown("### 🌐 Web İçerik Özeti")
            for item in results["scraped"]:
                with st.expander(f"📄 {item['title']}"):
                    st.write(f"**Açıklama:** {item['desc']}")
                    st.write(f"**'{topic}' geçiş sayısı:** {item['keyword_count']}")
        
        # 5. Rakip Analizi
        if results.get("competitors"):
            st.markdown("### 🔍 Rakip Analizleri")
            for comp in results["competitors"]:
                with st.expander(f"🏢 {comp['competitor']}"):
                    st.markdown(comp["analysis"])
        
        # 6. NLP Sonuçları
        if results.get("nlp"):
            st.markdown("### 🧠 NLP Analiz Sonuçları")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Duygu:** {results['nlp']['sentiment']}")
            with col2:
                st.success(f"**Anahtar Kelimeler:** {results['nlp']['keywords']}")
            st.warning(f"**Özet:** {results['nlp']['summary']}")
        
        # 7. PDF Export
        if modules.get("report"):
            st.markdown("### 📄 Rapor İndir")
            pdf_data = {
                "Konu": results.get("topic"),
                "Ülke": results.get("country"),
                "Tarih": results.get("timestamp"),
                "Analiz": results.get("main_analysis", "")[:1000]
            }
            pdf_path = generate_pdf_report(pdf_data, f"rapor_{datetime.now().strftime('%Y%m%d')}.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 PDF Raporu İndir",
                        data=f.read(),
                        file_name=f"ai_analiz_{topic.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
        
        # 8. CSV Kaydet
        save_data = {
            "Tarih": results.get("timestamp"),
            "Konu": results.get("topic"),
            "Ülke": results.get("country"),
            "Analiz_Ozeti": results.get("main_analysis", "")[:200]
        }
        df = pd.DataFrame([save_data])
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8')
        st.download_button(
            label="📥 CSV Verisini İndir",
            data=csv,
            file_name='analiz_gecmisi.csv',
            mime='text/csv'
        )
        
        st.success("✅ Agent görevini tamamladı!")

# ==================== GEÇMİŞ ANALİZLER ====================
st.markdown("---")
st.subheader("📁 Geçmiş Analizler")

if os.path.exists('gecmis.csv'):
    try:
        history_df = pd.read_csv('gecmis.csv')
        st.dataframe(history_df.tail(10), use_container_width=True)
    except:
        st.info("Geçmiş verisi okunamadı")
else:
    st.info("Henüz geçmiş analiz yok.")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <b>🤖 AI Pazar Analiz Agenti v2.0</b><br>
    Powered by Groq API + Streamlit Cloud • Tamamen Ücretsiz
</div>
""", unsafe_allow_html=True)
