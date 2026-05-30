import requests
import json
import os
from datetime import datetime, timedelta

print("🚀 Memulai Master Scraper SAMUDERA (Mode API FULL SPEED)...")

# Logika Tanggal
tanggal_mulai = datetime.now()
tanggal_akhir = tanggal_mulai + timedelta(days=30)
start_date_str = tanggal_mulai.strftime("%Y-%m-%d") 
end_date_str = tanggal_akhir.strftime("%Y-%m-%d")

print(f"📅 Rentang Pencarian: {start_date_str} s/d {end_date_str}")

rute_samudera = {
    "Medan": "BELAWAN",          
    "Tanjung Pinang": "TANJUNG PINANG", 
    "Batam": "BATAM", 
    "Pontianak": "PONTIANAK", 
    "Samarinda": "SAMARINDA", 
    "Banjarmasin": "BANJARMASIN", 
    "Balikpapan": "BALIKPAPAN", 
    "Makassar": "MAKASSAR", 
    "Palu": "PANTOLOAN",       
    "Manado": "BITUNG",         
    "Gorontalo": "GORONTALO"
}

url_api_direct = "https://connect.samudera.id/api/iqauth/api/glossys_vessel_direct_samudera_id"
url_api_transit = "https://connect.samudera.id/api/iqauth/api/glossys_vessel_direct_transhipment_samudera_id"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*"
})

data_jadwal_global = []

# Fungsi perapih tanggal: 2026-06-01 15:00:00 -> 01 Jun 2026
def rapihin_tanggal(text_tanggal):
    if not text_tanggal or text_tanggal == "N/A": return "N/A"
    try:
        tgl_saja = text_tanggal.split(' ')[0]
        dt = datetime.strptime(tgl_saja, "%Y-%m-%d")
        return dt.strftime("%d %b %Y")
    except:
        return text_tanggal

for tujuan, kota_tujuan in rute_samudera.items():
    print(f"\n⏳ Tembak API SAMUDERA: JAKARTA -> {kota_tujuan}...")
    
    params = {
        "port1": "JAKARTA",
        "port2": kota_tujuan,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "page": 1,
        "limit": 100
    }
    
    jumlah_dapat = 0

    # 1. TARIK DATA DIRECT (KAPAL LANGSUNG)
    try:
        res_direct = session.get(url_api_direct, params=params)
        if res_direct.status_code == 200:
            hasil = res_direct.json()
            if hasil.get("success") and isinstance(hasil.get("data"), list):
                for kapal in hasil["data"]:
                    v_name = kapal.get("vessel_name", "SAMUDERA VESSEL")
                    v_voy = kapal.get("voyage", "")
                    nama_kapal = f"{v_name} V.{v_voy}" if v_voy else v_name
                    
                    # Ambil key dari asumsi bedah JSON
                    etd = rapihin_tanggal(kapal.get("etd_source", "N/A"))
                    eta = rapihin_tanggal(kapal.get("eta_destination", "N/A"))
                    
                    print(f"   -> [DIRECT] {nama_kapal} | ETD: {etd} | ETA: {eta}")
                    data_jadwal_global.append({
                        "rute": tujuan,
                        "pelayaran": "SAMUDERA",
                        "nama_kapal": nama_kapal,
                        "closing": "N/A",
                        "etd": etd,
                        "eta": eta,
                        "etb": "N/A",
                        "open_stack": "N/A"
                    })
                    jumlah_dapat += 1
    except Exception as e:
        pass

    # 2. TARIK DATA TRANSIT (Berdasarkan Screenshot Lu)
    try:
        res_transit = session.get(url_api_transit, params=params)
        if res_transit.status_code == 200:
            hasil = res_transit.json()
            if hasil.get("success") and isinstance(hasil.get("data"), list):
                for kapal in hasil["data"]:
                    
                    # Kapal 1
                    v1_name = kapal.get("vessel_name", "KAPAL 1")
                    v1_voy = kapal.get("voyage", "")
                    kapal1 = f"{v1_name} V.{v1_voy}" if v1_voy else v1_name
                    
                    # Kapal 2 (Transit)
                    v2_name = kapal.get("next_vessel_name", "KAPAL 2")
                    v2_voy = kapal.get("next_vessel_voyage", "")
                    kapal2 = f"{v2_name} V.{v2_voy}" if v2_voy else v2_name
                    
                    nama_kapal = f"{kapal1} -> {kapal2}"
                    
                    # ETD keberangkatan awal, ETA kedatangan akhir
                    etd = rapihin_tanggal(kapal.get("etd_source", "N/A"))
                    eta = rapihin_tanggal(kapal.get("next_eta_destination", "N/A"))
                    
                    print(f"   -> [TRANSIT] {nama_kapal} | ETD: {etd} | ETA: {eta}")
                    data_jadwal_global.append({
                        "rute": tujuan,
                        "pelayaran": "SAMUDERA",
                        "nama_kapal": nama_kapal,
                        "closing": "N/A",
                        "etd": etd,
                        "eta": eta,
                        "etb": "N/A",
                        "open_stack": "N/A"
                    })
                    jumlah_dapat += 1
    except Exception as e:
        pass

    if jumlah_dapat == 0:
        print(f"   ⚠️ Rute {tujuan} kosong (Ga ada kapal).")
    else:
        print(f"   ✅ Sukses ditarik: {jumlah_dapat} kapal ke {tujuan}.")


# ==================== SIMPAN KE JSON ====================
print("\n💾 Menyimpan ke jadwal.json...")
data_gabungan = []

if os.path.exists('jadwal.json') and os.path.getsize('jadwal.json') > 0:
    try:
        with open('jadwal.json', 'r') as f:
            data_gabungan = json.load(f)
            if not isinstance(data_gabungan, list): data_gabungan = []
    except: data_gabungan = []

# Buang jadwal Samudera lama biar gak dobel
data_gabungan = [j for j in data_gabungan if j.get('pelayaran') != 'SAMUDERA']
# Masukin jadwal baru
data_gabungan.extend(data_jadwal_global)

with open('jadwal.json', 'w') as f:
    json.dump(data_gabungan, f, indent=4)

print("🎉 API MASTER SAMUDERA SELESAI & SUDAH TERSIMPAN!")