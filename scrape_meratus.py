import json
import os
import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

print("🚀 Memulai Master Scraper MERATUS (Versi UNDETECTED-CHROMEDRIVER - Super Stealth)...")

# --- KONFIGURASI UNDETECTED CHROMEDRIVER ---
options = uc.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

# TAMBAHAN SENJATA ANTI-BOT:
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# FIX: version_main=150 wajib untuk GitHub Actions
driver = uc.Chrome(options=options, version_main=150)
# -------------------------------------------

rute_meratus = {
    "Makassar": "IDMAK", "Bitung": "IDBIT", "Gorontalo": "IDGTO",
    "Samarinda": "IDSRI", "Balikpapan": "IDBPN", "Pontianak": "IDPNK", "Batam": "IDBTH", "Banjarmasin": "IDBDJ",
    "Belawan": "IDBLW", "Palu": "IDPTN"
}

data_jadwal_global = []

for kota_tujuan, kode_port in rute_meratus.items():
    print(f"⏳ Ngecek MERATUS: Jakarta -> {kota_tujuan}...")
    timestamp_sekarang = int(time.time() * 1000)
    url_meratus = f"https://meratus-one.com/product/sea-freight?nodeFrom=IDJKT&nodeTo={kode_port}&effectiveDate={timestamp_sekarang}"

    try:
        driver.get(url_meratus)
        print("   -> Menunggu loading awal (bypassing sistem keamanan jika ada)...")
        time.sleep(10) # Waktu tunggu dilebihin biar Cloudflare kelar loading

        try:
            btn_direct = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Direct')]"))
            )
            btn_direct.click()
            time.sleep(3)
        except Exception: 
            pass 

        print("   -> Mencari data Route Detail...")
        WebDriverWait(driver, 35).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Route Detail')]"))
        )

        tombol_detail = driver.find_elements(By.XPATH, "//*[contains(text(), 'Route Detail')]")
        jumlah_kapal = 0

        for btn in tombol_detail:
            try:
                card = btn.find_element(By.XPATH, "./ancestor::div[contains(., 'MERATUS')][1]")
                flat_text = " ".join([line.strip() for line in card.text.split('\n') if line.strip()])

                nama_kapal = "MERATUS VESSEL"
                for idx, line in enumerate(card.text.split('\n')):
                    if "MERATUS" in line:
                        voyage = card.text.split('\n')[idx+1].strip() if idx+1 < len(card.text.split('\n')) else ""
                        nama_kapal = f"{line.strip()} - {voyage}" if voyage else line.strip()
                        break

                etd_match = re.search(r'ETD\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})', flat_text)
                etd = etd_match.group(1).strip() if etd_match else "N/A"

                eta_match = re.search(r'ETA\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})', flat_text)
                eta = eta_match.group(1).strip() if eta_match else "N/A"

                closing_match = re.search(r'Close CY Dry\s*:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4}(?:\s+\d{2}:\d{2})?)', flat_text)
                closing = closing_match.group(1).strip() if closing_match else "N/A"

                etb_match = re.search(r'ETB\s+(\d{1,2}\s+[A-Za-z]+\s+\d{4})', flat_text)
                etb = etb_match.group(1).strip() if etb_match else "N/A"

                open_stack_match = re.search(r'Open Stack\s*:\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4}(?:\s+\d{2}:\d{2})?)', flat_text)
                open_stack = open_stack_match.group(1).strip() if open_stack_match else "N/A"

                print(f"   -> [DAPAT] {nama_kapal} | ETB: {etb} | Open Stack: {open_stack}")

                if not any(x['pelayaran'] == 'MERATUS' and x['nama_kapal'] == nama_kapal and x['etd'] == etd and x['rute'] == kota_tujuan for x in data_jadwal_global):
                    data_jadwal_global.append({
                        "rute": kota_tujuan,
                        "pelayaran": "MERATUS",
                        "nama_kapal": nama_kapal,
                        "closing": closing,
                        "etd": etd,
                        "eta": eta,
                        "etb": etb,
                        "open_stack": open_stack
                    })
                    jumlah_kapal += 1
            except Exception: 
                pass
                
        if jumlah_kapal > 0:
            print(f"   ✅ Sukses ditarik: {jumlah_kapal} kapal.")
        else:
            print(f"   ⚠️ Halaman berhasil dimuat tapi tabel jadwal kosong.")

    except Exception as e:
        print(f"   ⚠️ GAGAL narik rute {kota_tujuan}. BUKAN KOSONG, tapi ada error.")
        print(f"   🛑 Detail Error: {type(e).__name__} - Halaman Timeout/Diblokir Server")
        
        try:
            nama_file_error = f"error_meratus_{kota_tujuan}.png"
            driver.save_screenshot(nama_file_error)
            print(f"   📸 Screenshot disimpan: {nama_file_error}")
        except Exception as screenshot_err:
            print(f"   Gagal mengambil screenshot: {screenshot_err}")

# Simpan ke JSON
data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list): data_gabungan = []
    except Exception: 
        data_gabungan = []

data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'MERATUS']
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

driver.quit()
print("\n🎉 MERATUS SELESAI! Data Open Stack & ETB sudah ditulis ke jadwal.json.")
