import subprocess
import os

# Pindah ke folder proyek
# os.chdir(r"D:\INSPEKSI MOBIL")

# Daftar script yang mau dijalankan
scripts = ["scraper.py", "scrape_meratus.py", "scrape_tanto.py", "scrape_icon.py", "scrape_samudera.py", "scrape_temas.py]

for script in scripts:
    print(f"🚀 Menjalankan {script}...")
    subprocess.run(["python", script])
    print(f"✅ {script} selesai.")

print("\n🎉 SEMUA JADWAL BERHASIL DIUPDATE!")
