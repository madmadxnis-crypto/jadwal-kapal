import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

print("🚀 Memulai Master Scraper SPIL (Fokus ETB & Open Stack)...")
driver = webdriver.Chrome()

daftar_tujuan = ["Makassar", "Bitung", "Gorontalo", "Samarinda", "Balikpapan", "Banjarmasin", "Belawan", "Palu", "Batam", "Pontianak"]
data_jadwal_global = []

for tujuan in daftar_tujuan:
    print(f"⏳ Ngecek SPIL: Jakarta -> {tujuan}...")
    url = f"https://myspil.com/myspilcom/port/select?portfrom=Jakarta&portto={tujuan}&etd=&vesselname=&vesselid="

    try:
        driver.get(url)
        WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.XPATH, "//table/tbody/tr"))
        )

        baris_tabel = driver.find_elements(By.XPATH, "//table/tbody/tr")
        for baris in baris_tabel:
            kolom = baris.find_elements(By.TAG_NAME, "td")

            if len(kolom) >= 7 and "IMO" in kolom[1].text:
                teks_kapal = kolom[1].text.split('\n')
                nama_kapal = f"{teks_kapal[0].strip()} - {teks_kapal[1].strip()}" if len(teks_kapal) > 1 else teks_kapal[0].strip()

                closing = kolom[2].text.replace('\n', ' ').split('Reefer')[0].strip() or "N/A"
                etd = kolom[3].text.replace('\n', ' ').split('Reefer')[0].strip()
                eta = kolom[4].text.replace('\n', ' ').split('Reefer')[0].strip()

                # Ekstrak ETB (Kolom 5)
                try:
                    etb = kolom[5].text.replace('\n', ' ').split('Reefer')[0].strip()
                except:
                    etb = "N/A"
                if not etb: etb = "N/A"

                # Ekstrak Open Stack (Kolom 6)
                try:
                    open_stack = kolom[6].text.replace('\n', ' ').strip()
                except:
                    open_stack = "N/A"
                if not open_stack: open_stack = "N/A"

                print(f"   -> [DAPAT] Kapal: {nama_kapal} | ETB: {etb} | Open Stack: {open_stack}")

                data_jadwal_global.append({
                    "rute": tujuan,
                    "pelayaran": "SPIL",
                    "nama_kapal": nama_kapal,
                    "closing": closing,
                    "etd": etd,
                    "eta": eta,
                    "etb": etb,
                    "open_stack": open_stack
                })
    except Exception as e:
        print(f"   ❌ Rute {tujuan} kosong/error.")

# Simpan ke JSON
data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list): data_gabungan = []
    except:
        data_gabungan = []

data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'SPIL']
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

driver.quit()
print("\n🎉 SPIL SELESAI! Data Open Stack & ETB sudah ditulis ke jadwal.json.")