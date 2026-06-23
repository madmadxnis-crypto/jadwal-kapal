import json
import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

print("🚀 Memulai Master Scraper TEMAS (Versi Filter Direct JS & Headless GitHub)...")

# --- KONFIGURASI CHROME HEADLESS WAJIB UNTUK GITHUB ACTIONS ---
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

# --- JURUS ANTI-TIMEOUT: MATIKAN LOAD GAMBAR BIAR LOADING NGEBUT ---
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)

driver = webdriver.Chrome(options=chrome_options)
driver.set_page_load_timeout(60) # Kasih batas napas load halaman 60 detik
# --------------------------------------------------------------

hari_ini = datetime.now().strftime("%Y-%m-%d")
bulan_depan = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

rute_temas = {
    "Makassar": "IDMKS~MAKASSAR", "Bitung": "IDBIT~BITUNG", "Gorontalo": "IDGTO~GORONTALO",
    "Samarinda": "IDSRI~SAMARINDA", "Balikpapan": "IDBPN~BALIKPAPAN", "Banjarmasin": "IDBDJ~BANJARMASIN",
    "BELAWAN": "IDBLW~BELAWAN", "PALU": "IDPTL~PALU", "Pontianak": "IDPNK~PONTIANAK", "BATAM": "IDBTH~BATAM" 
}

data_jadwal_global = []

for kota_tujuan, kode_port in rute_temas.items():
    print(f"⏳ Ngecek TEMAS: Jakarta -> {kota_tujuan}...")
    url_temas = f"https://kliktemas.com/schedule?routes=IDJKT~JAKARTA~{kode_port}~{hari_ini}~{bulan_depan}"
    
    try:
        driver.get(url_temas)
        time.sleep(6) 
        
        # AKTIVASI FILTER DIRECT DENGAN JAVASCRIPT EXECUTOR
        try:
            checkbox_direct = WebDriverWait(driver, 45).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Direct')]"))
            )
            driver.execute_script("arguments[0].click();", checkbox_direct)
            print("   [FILTER] Berhasil mengaktifkan rute Direct lewat JS.")
            time.sleep(4) 
        except Exception as e_filter:
            print(f"   [FILTER] Tombol Direct tidak ditemukan atau gagal diklik: {type(e_filter).__name__}")

        # Batas tunggu tabel jadwal dinaikin ke 45 detik
        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Est. Departure')]"))
        )
        
        kotak_jadwal = driver.find_elements(By.XPATH, "//div[contains(@class, 'sh-border') and contains(@class, 'bg-white') and .//div[contains(text(), 'Est. Departure')]]")
        jumlah_kapal = 0
        
        for kotak in kotak_jadwal:
            teks_semua = [line.strip() for line in kotak.text.split('\n') if line.strip()]
            if len(teks_semua) < 4: continue
                
            try:
                nama_kapal = "TEMAS VESSEL"
                for baris in teks_semua:
                    if "-" in baris and not any(x in baris for x in ["Est.", "PT TEMAS", "JAKARTA", "MAKASSAR", "SAILING", "ARRIVAL", "DEPARTURE"]):
                        nama_kapal = baris
                        break
                
                if nama_kapal == "TEMAS VESSEL" and len(teks_semua) > 1:
                    nama_kapal = teks_semua[1] if "PT TEMAS" in teks_semua[0] else teks_semua[0]

                etd, eta = "N/A", "N/A"
                for i in range(len(teks_semua)):
                    if "Est. Departure" in teks_semua[i] and i + 1 < len(teks_semua): 
                        etd = teks_semua[i+1]
                    if "Est. Arrival" in teks_semua[i] and i + 1 < len(teks_semua): 
                        eta = teks_semua[i+1]
                
                sudah_ada = any(x['pelayaran'] == 'TEMAS' and x['nama_kapal'] == nama_kapal and x['etd'] == etd and x['rute'] == kota_tujuan for x in data_jadwal_global)
                
                if not sudah_ada and etd != "N/A":
                    data_jadwal_global.append({
                        "rute": kota_tujuan,
                        "pelayaran": "TEMAS",
                        "nama_kapal": nama_kapal,
                        "closing": "N/A",
                        "etd": etd,
                        "eta": eta
                    })
                    jumlah_kapal += 1
            except Exception: pass
            
        print(f"   ✅ Sukses menarik {jumlah_kapal} kapal TEMAS Direct.")
        
    except Exception as e:
        print(f"   ⚠️ GAGAL narik rute {kota_tujuan}. BUKAN KOSONG, tapi ada error.")
        print(f"   🛑 Detail Error: {type(e).__name__} - {str(e)[:200]}")
        
        try:
            nama_file_error = f"error_temas_{kota_tujuan}.png"
            driver.save_screenshot(nama_file_error)
            print(f"   📸 Screenshot disimpan: {nama_file_error}")
        except Exception as screenshot_err:
            print(f"   Gagal mengambil screenshot: {screenshot_err}")

# ==================== LOGIKA PENYIMPANAN AMAN ====================
data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list):
                data_gabungan = []
    except json.JSONDecodeError:
        data_gabungan = []

data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'TEMAS']
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

driver.quit()
print("\n🎉 MASTER TEMAS FILTER DIRECT SELESAI! Data berhasil diperbarui di jadwal.json.")
