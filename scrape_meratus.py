import json
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

print("🚀 Memulai Master Scraper MERATUS (Fokus ETB & Open Stack)...")
driver = webdriver.Chrome()

rute_meratus = {
    "Makassar": "IDMAK", "Bitung": "IDBIT", "Gorontalo": "IDGTO",
    "Samarinda": "IDSRI", "Balikpapan": "IDBPN", "Pontianak": "IDPNK", "Batam": "IDBTH", "Banjarmasin": "IDBDJ",
    "Belawan": "IDBLW", "Palu": "IDPTN,"
}

data_jadwal_global = []

for kota_tujuan, kode_port in rute_meratus.items():
    print(f"⏳ Ngecek MERATUS: Jakarta -> {kota_tujuan}...")
    timestamp_sekarang = int(time.time() * 1000)
    url_meratus = f"https://meratus-one.com/product/sea-freight?nodeFrom=IDJKT&nodeTo={kode_port}&effectiveDate={timestamp_sekarang}"

    try:
        driver.get(url_meratus)
        time.sleep(4)

        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'Direct')]").click()
            time.sleep(2)
        except: pass

        WebDriverWait(driver, 10).until(
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

                # PENCARIAN ETB DAN OPEN STACK MERATUS
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
            except: pass
        print(f"   ✅ Sukses ditarik: {jumlah_kapal} kapal.")
    except: print(f"   ⚠️ Rute {kota_tujuan} kosong.")

# Simpan ke JSON
data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list): data_gabungan = []
    except: data_gabungan = []

data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'MERATUS']
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

driver.quit()
print("\n🎉 MERATUS SELESAI! Data Open Stack & ETB sudah ditulis ke jadwal.json.")
