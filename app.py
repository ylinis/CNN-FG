# app.py

import streamlit as st
import pandas as pd
from datetime import datetime, date

# Selenium importai
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

@st.cache_data
def gauti_duomenis_su_selenium(pradzios_data: date, pabaigos_data: date):
    """
    Nuskaito Fear & Greed indekso duomenis iš finhacker.cz,
    naudojant Selenium naršyklės automatizavimui.
    """
    try:
        # --- Selenium konfigūracija Streamlit Cloud ---
        options = Options()
        options.add_argument("--disable-gpu")
        options.add_argument("--headless") # Būtina serverio aplinkai
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Automatiškai įdiegia ir paleidžia tinkamą chromedriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        url = "https://finhacker.cz/fear-and-greed-index-historical-data/"
        driver.get(url)

        # --- Laukimas, kol lentelė atsiras ---
        # Laukiame iki 20 sekundžių, kol elementas su ID 'tablepress-2' bus matomas
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "tablepress-2")))

        # Kai lentelė yra, perduodame puslapio kodą į pandas
        page_source = driver.page_source
        lenteles = pd.read_html(page_source, header=0)
        df = lenteles[0] # Dabar lentelė greičiausiai bus pirma

    except Exception as e:
        st.error(f"Selenium klaida: Nepavyko gauti duomenų. Klaida: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit() # Būtinai uždarome naršyklę

    # --- Duomenų valymas (lieka beveik nepakitęs) ---
    try:
        df.rename(columns={
            'Date': 'data',
            'F&G Value': 'reiksme',
            'F&G Rating': 'ivertinimas'
        }, inplace=True)
        
        df['data'] = pd.to_datetime(df['data'], format='%B %d, %Y')
        df.set_index('data', inplace=True)
        
        filtruotas_df = df.loc[pradzios_data.strftime('%Y-%m-%d'):pabaigos_data.strftime('%Y-%m-%d')]
        
        if filtruotas_df.empty:
            return pd.DataFrame()

        galutinis_df = filtruotas_df.reset_index().sort_values(by='data', ascending=False)
        return galutinis_df[['data', 'reiksme', 'ivertinimas']]

    except (IndexError, KeyError) as e:
        st.error(f"Pandas klaida: Nepavyko apdoroti duomenų lentelės. Gali būti, kad svetainės struktūra pasikeitė. Klaida: {e}")
        return None


# --- Streamlit Vartotojo Sąsaja (lieka nepakitusi) ---
st.set_page_config(page_title="F&G Index Scraper", layout="centered")
st.title("📊 Fear & Greed Index Scraper (finhacker.cz)")
st.markdown("Pasirinkite norimą datų intervalą ir atsisiųskite istorinius duomenis `.csv` formatu.")
st.header("1. Pasirinkite datas")
col1, col2 = st.columns(2)
with col1:
    pradzios_data = st.date_input("Pradžios data", date(2023, 1, 1))
with col2:
    pabaigos_data = st.date_input("Pabaigos data", datetime.now())

st.header("2. Generuokite failą")
if st.button("Gauti duomenis ir paruošti atsisiuntimui"):
    if pradzios_data > pabaigos_data:
        st.error("Klaida: Pradžios data negali būti vėlesnė už pabaigos datą.")
    else:
        with st.spinner('Paleidžiama naršyklė serveryje ir laukiama duomenų... Tai gali užtrukti ilgiau.'):
            df = gauti_duomenis_su_selenium(pradzios_data, pabaigos_data)

        if df is not None:
            if not df.empty:
                st.success(f"✅ Duomenys sėkmingai gauti! Iš viso eilučių: {len(df)}")
                st.header("3. Peržiūra ir atsisiuntimas")
                st.dataframe(df.head())
                df['data'] = df['data'].dt.strftime('%Y-%m-%d')
                csv_duomenys = df.to_csv(index=False).encode('utf-8')
                failo_pavadinimas = f"finhacker_fg_index_{pradzios_data}_{pabaigos_data}.csv"
                st.download_button(
                   label="Atsisiųsti CSV failą",
                   data=csv_duomenys,
                   file_name=failo_pavadinimas,
                   mime='text/csv',
                )
            else:
                st.warning("Pasirinktame datų intervale duomenų nerasta.")
