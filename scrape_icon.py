import json
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

print("🚀 Memulai Master Scraper ICON (Revisi Mapping Rute)...")
driver = webdriver.Chrome()

# Mapping rute sesuai ketersediaan di ICON dan revisi kode
rute_icon = {
    "Samarinda": "SRI",
    "Balikpapan": "BPN",
    "Banjarmasin": "BJM", # Revisi
    "Batam": "BAT", # Rute Baru ICON
    "Pontianak": "PTK", # Rute Baru ICON
    "Tanjung Pinang": "KID" # Rute Baru ICON
}

data_jadwal_global = []

# Looping HANYA untuk jadwal yang tersedia di rute_icon
for tujuan, kode in rute_icon.items():
    print(f"⏳ Ngecek ICON: Jakarta -> {tujuan} ({kode})...")
    
    # Tembak URL ByPass
    url = f"https://iconlinebooking.co.id/cruise-schedule/JKT/{kode}"
    
    try:
        driver.get(url)
        time.sleep(3) # Tunggu loading halaman beres
        
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Closing Cargo')]"))
            )
        except:
            print(f"   ⚠️ Rute {tujuan} kosong (Data Tidak Ditemukan).")
            continue
            
        tanda_closing = driver.find_elements(By.XPATH, "//*[contains(text(), 'Closing Cargo :')]")
        jumlah_kapal = 0
        
        for el in tanda_closing:
            try:
                card = el.find_element(By.XPATH, "./ancestor::div[contains(., 'Estimasi Keberangkatan')][1]")
                text_mentah = card.text
                
                # 1. NAMA KAPAL
                nama_kapal = "ICON VESSEL"
                baris_teks = text_mentah.split('\n')
                for baris in baris_teks:
                    if "ICON" in baris or "IE" in baris or "V." in baris:
                        nama_kapal = baris.split('Closing')[0].strip()
                        break
                        
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
            print(f"   ✅ Sukses ditarik: {jumlah_kapal} kapal ICON.")
        
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

data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'ICON']
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

driver.quit()
print("\n🎉 MASTER ICON SELESAI! Data sudah digabung ke jadwal.json.")