import json
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

print("🚀 Memulai Master Scraper TANTO (Mapping Rute Khusus & Fix Closing)...")
driver = webdriver.Chrome()

# Rute Standar Dashboard Kita
daftar_tujuan = ["Makassar", "Bitung", "Gorontalo", "Samarinda", "Balikpapan", "Banjarmasin", "Medan", "Tangkian", "Pontianak", "Batam"]
data_jadwal_global = []

for tujuan in daftar_tujuan:
    # MAPPING KHUSUS TANTO: Sesuaikan dengan nama port di web Tanto
    tujuan_tanto = tujuan
    if tujuan.lower() == "belawan":
        tujuan_tanto = "MEDAN"
    elif tujuan.lower() == "palu":
        tujuan_tanto = "TANGKIAN"

    print(f"⏳ Ngecek TANTO: Jakarta -> {tujuan_tanto} (Standar: {tujuan})...")
    
    try:
        driver.get("https://www.tantonet.com/schedule.php")
        time.sleep(4) 
        
        # 1. ISI PORT OF LOAD (JAKARTA)
        try:
            pol_container = driver.find_element(By.ID, "select2-pol-container")
            if "JAKARTA" not in pol_container.text: 
                pol_container.click()
                time.sleep(1)
                driver.switch_to.active_element.send_keys("JAKARTA")
                time.sleep(1)
                driver.switch_to.active_element.send_keys(Keys.ENTER)
        except Exception:
            pass

        # 2. ISI PORT OF DISCHARGE (PAKAI NAMA KOTA KHUSUS TANTO)
        try:
            pod_input = driver.find_element(By.XPATH, "//input[@placeholder='Select Port of Discharge']")
            pod_input.send_keys(tujuan_tanto.upper())
            time.sleep(1.5)
            pod_input.send_keys(Keys.ENTER)
        except Exception:
            print(f"   ❌ Gagal menemukan kolom Port of Discharge untuk {tujuan_tanto}.")
            continue

        # 3. KLIK TOMBOL SEARCH
        time.sleep(1)
        tombol_search = driver.find_element(By.XPATH, "//*[contains(text(), 'Search') or @value='Search']")
        driver.execute_script("arguments[0].click();", tombol_search) 

        print("   ⏳ Menunggu data ditarik dari server Tanto...")
        time.sleep(4) 
        
        # 4. EKSTRAK DATA DARI TABEL
        baris_tabel = driver.find_elements(By.XPATH, "//table//tr[td]")
        jumlah_kapal = 0
        
        for baris in baris_tabel:
            kolom = baris.find_elements(By.TAG_NAME, "td")
            
            if len(kolom) >= 5:
                nama_kapal = kolom[0].text.strip()
                
                # Abaikan kalau barisnya kosong atau tulisan "No data available"
                if nama_kapal == "" or "No data" in nama_kapal:
                    continue
                
                # Kolom ke-3 (index 2) adalah Closing
                closing = kolom[2].text.strip()
                etd = kolom[3].text.strip()
                eta = kolom[4].text.strip()
                
                # Bersihkan tanda strip '-' dari web Tanto
                if eta == "-": eta = "N/A"
                if closing == "-": closing = "N/A"
                
                # Cetak ke layar beserta nilai Closing-nya biar yakin
                print(f"   -> [DAPAT] {nama_kapal} | Closing: {closing} | ETD: {etd} | ETA: {eta}")
                
                data_jadwal_global.append({
                    "rute": tujuan,  # Tetap simpan nama rute STANDAR agar dashboard tidak error
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
        print(f"   ❌ Terjadi error di rute {tujuan_tanto}: {e}")

# ==================== LOGIKA PENYIMPANAN ====================
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
print("\n🎉 MASTER TANTO SELESAI! Silakan refresh dashboard Chrome kamu.")