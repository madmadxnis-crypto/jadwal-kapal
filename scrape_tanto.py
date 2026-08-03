import json
import os
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("🚀 Memulai Master Scraper TANTO (Versi UNDETECTED-CHROMEDRIVER - Fix Dropdown Headless)...")

# --- KONFIGURASI UNDETECTED CHROMEDRIVER ---
options = uc.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# FIX: Gunakan uc.Chrome dan version_main=150 khusus untuk GitHub Actions
driver = uc.Chrome(options=options, version_main=150)
# -------------------------------------------

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
        time.sleep(3) # Tunggu web stabil
        
        # 1. ISI PORT OF LOAD (JAKARTA) - FIX MAXIMAL
        try:
            pol_container = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "select2-pol-container"))
            )
            if "JAKARTA" not in pol_container.text.upper(): 
                # Paksa klik pakai JS biar gak meleset
                driver.execute_script("arguments[0].click();", pol_container)
                time.sleep(1.5)
                
                # Pastikan kotak ketik (search field) benar-benar terlihat di layar
                search_box = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, "//input[@class='select2-search__field']"))
                )
                search_box.clear()
                search_box.send_keys("JAKARTA")
                time.sleep(1.5)
                search_box.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"   ⚠️ Gagal set POL JAKARTA: {type(e).__name__}")
            continue # Kalau POL gagal, mending skip rute ini daripada narik data ngawur

        # 2. ISI PORT OF DISCHARGE (TUJUAN)
        try:
            pod_input = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Select Port of Discharge']"))
            )
            # Paksa scroll ke elemen biar kelihatan jelas di mode headless
            driver.execute_script("arguments[0].scrollIntoView(true);", pod_input)
            time.sleep(1)

            pod_input.clear()
            time.sleep(0.5)
            pod_input.send_keys(tujuan_tanto.upper())
            time.sleep(2)
            pod_input.send_keys(Keys.ENTER)
        except Exception as e:
            print(f"   ⚠️ Halaman Tanto gagal loading di form POD: {type(e).__name__}")
            try:
                driver.save_screenshot(f"error_tanto_form_{tujuan_tanto}.png")
            except: pass
            continue

        # 3. KLIK TOMBOL SEARCH
        time.sleep(1)
        try:
            tombol_search = driver.find_element(By.XPATH, "//button[contains(text(), 'Search')] | //input[@value='Search']")
            driver.execute_script("arguments[0].click();", tombol_search) 
        except Exception as e:
            print(f"   ⚠️ Gagal klik tombol search: {type(e).__name__}")

        print("   ⏳ Menunggu data ditarik dari server Tanto...")
        
        # 4. TUNGGU TABEL MUNCUL & EKSTRAK
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//table//tr[td]"))
            )
        except Exception:
            pass # Tetap lanjut baca tabel, siapa tau emang kosong (No Data)
        
        baris_tabel = driver.find_elements(By.XPATH, "//table//tr[td]")
        jumlah_kapal = 0
        
        for baris in baris_tabel:
            kolom = baris.find_elements(By.TAG_NAME, "td")
            
            if len(kolom) >= 5:
                nama_kapal = kolom[0].text.strip()
                if nama_kapal == "" or "No data" in nama_kapal or "No Schedule" in nama_kapal:
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
            print(f"   ⚠️ Rute {tujuan_tanto} kosong. Ambil foto TKP...")
            try:
                driver.save_screenshot(f"debug_tanto_kosong_{tujuan_tanto}.png")
            except Exception:
                pass

    except Exception as e:
        print(f"   ❌ Terjadi error sistem di rute {tujuan_tanto}: {type(e).__name__}")
        try:
            driver.save_screenshot(f"error_tanto_fatal_{tujuan_tanto}.png")
        except: pass

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
