import json
import os
import requests
from datetime import datetime

print("🚀 Memulai Master Scraper MERATUS (Versi JALUR NINJA API - Anti 403 & Super Kilat)...")

rute_meratus = {
    "Makassar": "IDMAK", "Bitung": "IDBIT", "Gorontalo": "IDGTO",
    "Samarinda": "IDSRI", "Balikpapan": "IDBPN", "Pontianak": "IDPNK",
    "Batam": "IDBTH", "Banjarmasin": "IDBDJ", "Belawan": "IDBLW", "Palu": "IDPTN"
}

data_jadwal_global = []

# Ambil tanggal hari ini untuk parameter pencarian (Format: YYYY-MM-DD)
tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")

# Header penyamaran biar API ngira ini request dari browser asli
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://meratus-one.com",
    "Referer": "https://meratus-one.com/"
}

# Fungsi untuk merapikan format tanggal dari API (contoh: 2026-08-04T18:00:00 -> 04 Aug 2026 18:00)
def format_tanggal(date_str):
    if not date_str: 
        return "N/A"
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
        if dt.hour == 0 and dt.minute == 0:
            return dt.strftime("%d %b %Y") # Kalau jam 00:00, tampilkan tanggal saja
        else:
            return dt.strftime("%d %b %Y %H:%M")
    except Exception:
        return str(date_str).replace("T", " ")

for kota_tujuan, kode_port in rute_meratus.items():
    print(f"⏳ Menembak API MERATUS: Jakarta -> {kota_tujuan}...")
    url_api = f"https://api.meratus-one.com/schedules?por=IDJKT&del={kode_port}&etd={tanggal_hari_ini}"

    try:
        # Request langsung ke API (Tanpa buka browser, hitungan detik kelar!)
        response = requests.get(url_api, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            if not items:
                print(f"   ⚠️ Rute {kota_tujuan} kosong (tidak ada jadwal di server).")
                continue

            jumlah_kapal = 0
            for item in items:
                # 1. Ambil Nama Kapal & Voyage
                vessel_name = item.get("modeName", "MERATUS VESSEL")
                voyage = item.get("modeCode", "")
                nama_kapal = f"{vessel_name} - {voyage}" if voyage else vessel_name

                # 2. Ambil Tanggal Sesuai Kunci JSON Asli
                etd = format_tanggal(item.get("etd"))
                eta = format_tanggal(item.get("eta"))
                etb = format_tanggal(item.get("etb"))
                closing = format_tanggal(item.get("closingDateDry"))
                
                # Coba ambil open stack (kalau ada di data tersembunyinya)
                open_stack = format_tanggal(item.get("openStackDate", item.get("openStack")))

                print(f"   -> [DAPAT] {nama_kapal} | ETD: {etd} | Closing: {closing}")

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

            print(f"   ✅ Sukses ditarik: {jumlah_kapal} kapal.")
        else:
            print(f"   ❌ Gagal narik API {kota_tujuan}. HTTP Status: {response.status_code}")

    except Exception as e:
        print(f"   🛑 Error sistem saat narik API {kota_tujuan}: {e}")

# Simpan ke jadwal.json
data_gabungan = []
if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list): data_gabungan = []
    except Exception:
        data_gabungan = []

# Buang data Meratus yang lama, masukin hasil API yang baru
data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'MERATUS']
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

print("\n🎉 MERATUS API SELESAI! Data sudah diamankan ke jadwal.json super cepat.")
