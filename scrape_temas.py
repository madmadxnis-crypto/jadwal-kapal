import json
import os
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

print("🚀 Memulai Master Scraper TEMAS (Versi Filter Direct & Headless GitHub)...")

# --- KONFIGURASI CHROME HEADLESS WAJIB UNTUK GITHUB ACTIONS ---
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=chrome_options)
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
        time.sleep(4) # Waktu tunggu dilebihin sedikit buat server GitHub
        
        # AKTIVASI FILTER DIRECT: Cari teks 'Direct' lalu klik checkbox/labelnya
        try:
            checkbox_direct = driver.find_element(By.XPATH, "//*[contains(text(), 'Direct')]")
            checkbox_direct.click()
            print("   [FILTER] Berhasil mengaktifkan rute Direct.")
            time.sleep(3) # Tunggu tabel refresh otomatis setelah diklik
        except Exception:
            print("   [FILTER] Tombol Direct tidak ditemukan atau sudah aktif.")

        WebDriverWait(driver, 10).until(
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
                    # Logika deteksi Vessel Voyage (mencari tanda strip "-" pemisah nomor voyage)
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
                        "closing": "N/A", # Sesuai request, dikunci N/A karena TEMAS direct tidak ada kolom closing manual di modul ini
                        "etd": etd,
                        "eta": eta
                    })
                    jumlah_kapal += 1
            except: pass
        print(f"   ✅ Sukses menarik {jumlah_kapal} kapal TEMAS Direct.")
    except Exception:
        print(f"   ⚠️ Rute {kota_tujuan} kosong/tidak ada jadwal.")

# ==================== LOGIKA PENYIMPANAN AMAN (ANTI TIMPA) ====================
data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list):
                data_gabungan = []
    except json.JSONDecodeError:
        data_gabungan = []

# Bersihkan data TEMAS lama saja, data pelayaran lain (SPIL, dll) tetap aman
data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'TEMAS']
# Gabungkan data TEMAS yang baru didapat
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)
# ==============================================================================

driver.quit()
print("\n🎉 MASTER TEMAS FILTER DIRECT SELESAI! Data berhasil diperbarui di jadwal.json.")
