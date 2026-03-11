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

# Ülke seçimi (DÜZELTİLMİŞ)
country_options = {
    "Türkiye": "TR", 
    "Amerika": "US", 
    "İngiltere": "GB", 
    "Almanya": "DE", 
    "Fransa": "FR"
}
country_name = st.sidebar.selectbox("🌍 Ülke", list(country_options.keys()))
country_code = country_options[country_name]

topic = st.sidebar.text_input("📊 Analiz Konusu", "Elektrikli Araba")
competitors = st.sidebar.text_area("🎯 Rakipler (virgülle ayır)", "Tesla, TOGG")

# Agent Modülleri
st.sidebar.subheader("🔧 Aktif Modüller")
use_trends = st.sidebar.checkbox("📈 Google Trends", value=True)
use_social = st.sidebar.checkbox("🐦 Sosyal Medya", value=True)
use_scrape = st.sidebar.checkbox("🌐 Web Scraping", value=True)
use_nlp = st.sidebar.checkbox("🧠 NLP Analiz", value=True)
use_report = st.sidebar.checkbox("📄 Rapor Export", value=True)

# ... (gerisi aynı, sadece country yerine country_name kullan)
