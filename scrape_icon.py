import json
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

print("🚀 Memulai Master Scraper ICON (Revisi Mapping Rute)...")

# Setup Chrome Options (Biar aman jalan di GitHub Actions)
chrome_options = Options()
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# Tiga baris sakti di bawah ini wajib ditambahin:
chrome_options.add_argument("--window-size=1920,1080") # Biar webnya ngebuka versi Desktop
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36") # Biar ga dikira robot botak
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=chrome_options)

# Mapping rute sesuai ketersediaan di ICON dan revisi kode
rute_icon = {
    "Samarinda": "SRI",
    "Balikpapan": "BPN",
    "Banjarmasin": "BJM", 
    "Batam": "BAT", 
    "Pontianak": "PTK", # Rute Baru ICON
    "Tanjung Pinang": "KID" 
}

data_jadwal_global = []

# Looping HANYA untuk jadwal yang tersedia di rute_icon
for tujuan, kode in rute_icon.items():
    print(f"⏳ Ngecek ICON: Jakarta -> {tujuan} ({kode})...")
    
    # Tembak URL ByPass
    url = f"https://iconlinebooking.co.id/cruise-schedule/JKT/{kode}"
    
    try:
        driver.get(url)
        time.sleep(4) # Tunggu loading halaman beres (Dinaikin jadi 4 detik biar aman)
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Closing Cargo')]"))
            )
        except:
            print(f"   ⚠️ Rute {tujuan} kosong (Data Tidak Ditemukan).")
            continue
            
        # Cari semua card jadwal
        tanda_closing = driver.find_elements(By.XPATH, "//*[contains(text(), 'Closing Cargo')]")
        jumlah_kapal = 0
        
        for el in tanda_closing:
            try:
                # Ambil kotak utuh jadwalnya
                card = el.find_element(By.XPATH, "./ancestor::div[contains(., 'Estimasi Keberangkatan')][1]")
                text_mentah = card.text
                
                # 1. NAMA KAPAL (Revisi: Lebih spesifik ambil baris pertama)
                nama_kapal = "ICON VESSEL"
                baris_teks = text_mentah.split('\n')
                if len(baris_teks) > 0:
                    # Ambil teks sebelum tulisan "Closing Cargo"
                    nama_kapal = baris_teks[0].split('Closing')[0].strip()
                    # Buang tulisan "- Jakarta - Pontianak" di belakang nama kapal
                    nama_kapal = nama_kapal.split('- Jakarta')[0].strip()
                        
                # 2. CLOSING CARGO
                closing_match = re.search(r'Closing Cargo\s*:\s*([\d/]+\s[\d:]+)', text_mentah)
                closing = closing_match.group(1).strip() if closing_match else "N/A"
                
                # 3. ETD
                etd_match = re.search(r'Estimasi Keberangkatan\s*:\s*\n?(.*?\d{4}\s\d{2}:\d{2})', text_mentah)
                etd = etd_match.group(1).strip() if etd_match else "N/A"
                
                # 4. ETA
                eta_match = re.search(r'Estimasi Tiba[\w\s]*:\s*\n?(.*?\d{4}\s\d{2}:\d{2})', text_mentah)
                eta = eta_match.group(1).strip() if eta_match else "N/A"
                
                print(f"   -> [DAPAT] {nama_kapal} | ETD: {etd} | ETA: {eta}")
                
                data_jadwal_global.append({
                    "rute": tujuan,
                    "pelayaran": "ICON",
                    "nama_kapal": nama_kapal,
                    "closing": closing,
                    "etd": etd,
                    "eta": eta,
                    "etb": "N/A",
                    "open_stack": "N/A"
                })
                jumlah_kapal += 1
                    
            except Exception as e:
                pass
                
        if jumlah_kapal > 0:
            print(f"   ✅ Sukses ditarik: {jumlah_kapal} kapal ICON ke {tujuan}.")
        
    except Exception as e:
        print(f"   ❌ Terjadi error di rute {tujuan}: {e}")

# ==================== LOGIKA PENYIMPANAN AMAN ====================
data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list): data_gabungan = []
    except: data_gabungan = []

# Hapus data ICON yang lama
data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'ICON']
# Masukkan data ICON yang baru
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

driver.quit()
print("\n🎉 MASTER ICON SELESAI! Data sudah digabung ke jadwal.json.")
