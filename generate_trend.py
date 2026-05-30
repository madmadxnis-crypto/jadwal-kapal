import pandas as pd
import json

print("🚀 Membaca data Excel untuk dianalisa (Revisi tambah Rute/Tujuan)...")

file_excel = "Copy of AKTIFITAS VIA LAUT 2026 (3).xlsx"
sheet_utama = "DATABASE" 

try:
    # Tambahin 'F' untuk ngambil kolom CABANG/Tujuan
    df = pd.read_excel(file_excel, sheet_name=sheet_utama, usecols="F,O,AD,AG")
    
    # Rename kolom biar rapi
    df.columns = ['Tujuan', 'Pelayaran', 'Vendor', 'ODN']
    
    # 1. Bersihin data kosong
    df = df.dropna(subset=['Tujuan', 'Pelayaran', 'Vendor', 'ODN'])
    
    # 2. LOGIKA UTAMA: 1 Nomor ODN = 1 Trip (Hapus duplikat ODN)
    df_unique = df.drop_duplicates(subset=['ODN'])
    
    # 3. Hitung trend: Rute -> Vendor -> Pelayaran
    trend_data = df_unique.groupby(['Tujuan', 'Vendor', 'Pelayaran']).size().reset_index(name='Jumlah')
    
    # 4. Susun ulang ke format JSON (Dictionary Bertingkat)
    hasil_json = {}
    for index, row in trend_data.iterrows():
        tujuan = str(row['Tujuan']).strip().upper()
        vendor = str(row['Vendor']).strip().upper()
        pelayaran = str(row['Pelayaran']).strip().upper()
        jumlah = int(row['Jumlah'])
        
        # Bikin hirarki: TUJUAN -> VENDOR -> PELAYARAN = JUMLAH
        if tujuan not in hasil_json:
            hasil_json[tujuan] = {}
            
        if vendor not in hasil_json[tujuan]:
            hasil_json[tujuan][vendor] = {}
            
        hasil_json[tujuan][vendor][pelayaran] = jumlah

    # 5. Export ke JSON
    with open('trend_vendor_rute.json', 'w') as f:
        json.dump(hasil_json, f, indent=4)
        
    print("✅ BERHASIL! File 'trend_vendor_rute.json' sudah tercetak di folder lu.")

except Exception as e:
    print(f"❌ ERROR: {e}")