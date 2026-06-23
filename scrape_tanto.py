import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print("🚀 Memulai Master Scraper TANTO (Mode Headless Standar & Fix Loading)...")

# --- KONFIGURASI HEADLESS CHROME STANDAR ---
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)
# -----------------------------------

daftar_tujuan = ["MAKASSAR", "Bitung", "Gorontalo", "Samarinda", "Balikpapan", "Banjarmasin", "Medan", "Tangkian", "Pontianak", "Batam"]
data_jadwal_global = []

for tujuan in daftar_tujuan:
    tujuan_tanto = tujuan
    if tujuan.lower() == "belawan":
        tujuan_tanto = "MEDAN"
    elif tujuan.lower() == "palu":
        tujuan_tanto = "TANGKIAN"

    print(f"⏳ Ngecek TANTO: Jakarta -> {tujuan_tanto} (Standar: {tujuan})...")
    
    try:
        driver.get("https://www.tantonet.com/schedule.php")
        
        # 1. ISI PORT OF LOAD (JAKARTA) - KUNCI FIX LOADING ADA DI SINI
        try:
            pol_container = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.ID, "select2-pol-container"))
            )
            if "JAKARTA" not in pol_container.text.upper(): 
                pol_container.click()
                time.sleep(1)
                driver.switch_to.active_element.send_keys("JAKARTA")
                time.sleep(1)
                driver.switch_to.active_element.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"   ⚠️ Gagal set POL JAKARTA: {type(e).__name__}")

        # 2. ISI PORT OF DISCHARGE
        try:
            pod_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Select Port of Discharge']"))
            )
            pod_input.send_keys(tujuan_tanto.upper())
            time.sleep(1.5)
            pod_input.send_keys(Keys.ENTER)
        except Exception:
            continue

        # 3. KLIK TOMBOL SEARCH
        time.sleep(1)
        tombol_search = driver.find_element(By.XPATH, "//*[contains(text(), 'Search') or @value='Search']")
        driver.execute_script("arguments[0].click();", tombol_search) 

        print("   ⏳ Menunggu data ditarik dari server Tanto...")
        
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table//tr[td]"))
            )
        except Exception:
            pass 
        
        # 4. EKSTRAK DATA DARI TABEL
        baris_tabel = driver.find_elements(By.XPATH, "//table//tr[td]")
        jumlah_kapal = 0
        
        for baris in baris_tabel:
            kolom = baris.find_elements(By.TAG_NAME, "td")
            
            if len(kolom) >= 5:
                nama_kapal = kolom[0].text.strip()
                if nama_kapal == "" or "No data" in nama_kapal:
                    continue
                
                closing = kolom[2].text.strip()
                etd = kolom[3].text.strip()
                eta = kolom[4].text.strip()
                
                if eta == "-": eta = "N/A"
                if closing == "-": closing = "N/A"
                
                print(f"   -> [DAPAT] {nama_kapal} | Closing: {closing} | ETD: {etd} | ETA: {eta}")
                
                data_jadwal_global.append({
                    "rute": tujuan,
                    "pelayaran": "TANTO",
                    "nama_kapal": nama_kapal,
                    "closing": closing,
                    "etd": etd,
                    "eta": eta,
                    "etb": "N/A",
                    "open_stack": "N/A"
                })
                jumlah_kapal += 1
                
        if jumlah_kapal > 0:
            print(f"   ✅ Sukses ditarik: {jumlah_kapal} kapal TANTO.")
        else:
            print(f"   ⚠️ Rute {tujuan_tanto} kosong (Tidak ada kapal).")

    except Exception as e:
        print(f"   ❌ Terjadi error di rute {tujuan_tanto}: {type(e).__name__} - {str(e)[:150]}")

data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list): data_gabungan = []
    except: data_gabungan = []

data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'TANTO']
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

driver.quit()
print("\n🎉 MASTER TANTO SELESAI! Data sudah diamankan ke jadwal.json.")
