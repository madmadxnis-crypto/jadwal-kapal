import subprocess
import os

# Pindah ke folder proyek (uncomment kalau lu jalanin di luar folder)
# os.chdir(r"D:\INSPEKSI MOBIL")

# Daftar script yang mau dijalankan
scripts = [
    "scraper.py",         # Data SPIL
    "scrape_meratus.py",
    "scrape_tanto.py",
    "scrape_icon.py",
    "scrape_samudera.py",
    "scrape_temas.py"
]

print("🚀 Memulai proses update seluruh jadwal kapal...\n" + "="*50)

for script in scripts:
    print(f"🔄 Menjalankan {script}...")
    try:
        # capture_output=True digunakan untuk menangkap logs & error di dalam script
        result = subprocess.run(["python", script], capture_output=True, text=True, check=True)
        
        print(f"✅ {script} SELESAI.")
        # Kalau script lu ada print() di dalamnya, bakal muncul di sini
        if result.stdout:
            print(f"💬 Logs:\n{result.stdout.strip()}")
            
    except subprocess.CalledProcessError as e:
        # Kalau script-nya error/crash, bagian ini bakal nangkep detailnya
        print(f"❌ {script} GAGAL JALAN!")
        print(f"⚠️ Detail Error:\n{e.stderr.strip()}")
        print("-" * 50)
        # Tetap lanjut ke script vendor lain meskipun script ini error
        continue

print("="*50 + "\n🎉 PROSES SINKRONISASI SELESAI!")
