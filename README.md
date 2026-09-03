# Rename Foto RECTO dan VERSO

Program ini menambahkan penanda pada akhir nama file, tepat sebelum ekstensi:

- `ABC001.jpg` di folder RECTO menjadi `ABC001r.jpg`
- `ABC001.jpg` di folder VERSO menjadi `ABC001v.jpg`

Jika satu foto tersedia dalam format JPG dan CR3, keduanya diproses:

- `ABC001.jpg` menjadi `ABC001r.jpg`
- `ABC001.cr3` menjadi `ABC001r.cr3`

File tidak pernah ditimpa. Program akan melewati file yang sudah memiliki penanda yang benar atau memiliki konflik nama.

## Cara termudah (antarmuka grafis)

1. Pastikan Python 3 sudah tersedia.
2. Pada macOS, klik dua kali `Jalankan Rename Foto.command`. Alternatifnya, jalankan dari terminal:

   ```bash
   python3 rename_recto_verso.py
   ```

3. Klik **Pilih…** untuk menentukan folder RECTO dan VERSO.
4. Klik **Analisis & Pratinjau**.
5. Periksa nama lama, nama baru, status, dan informasi pasangan.
6. Klik **Rename File**, lalu konfirmasi.

Kolom **Pemisah** boleh dikosongkan untuk hasil `ABC001r.jpg`. Isi dengan `_` jika menginginkan `ABC001_r.jpg`.

## Menjalankan di Windows

Ada tiga pilihan:

### 1. Menjalankan dengan Python

1. Instal Python 3 dari situs resmi Python. Saat instalasi, aktifkan **Add Python to PATH**.
2. Pastikan `rename_recto_verso.py` dan `Jalankan di Windows.bat` berada dalam folder yang sama.
3. Klik dua kali `Jalankan di Windows.bat`.

### 2. Membuat EXE portabel

1. Buka paket ini di komputer Windows yang terhubung ke internet.
2. Klik dua kali `Buat EXE Windows.bat`.
3. Tunggu hingga selesai. Windows Explorer akan terbuka otomatis dan menyorot hasil `dist\RenameFotoRectoVerso.exe`.

EXE tersebut dapat disalin dan dijalankan di komputer Windows lain tanpa memasang Python.

### 3. Membuat installer Windows

1. Instal Python 3 dan Inno Setup 6.
2. Klik dua kali `Buat Installer Windows.bat`.
3. Windows Explorer akan terbuka otomatis dan menyorot hasil `installer\Setup-RenameFotoRectoVerso-1.0.3.exe`.

Installer memasang aplikasi untuk pengguna Windows saat ini, membuat pintasan menu Start, menawarkan pintasan Desktop, dan menyediakan proses uninstall.

## Penggunaan melalui terminal

Pratinjau saja (belum mengubah file):

```bash
python3 rename_recto_verso.py --recto "/path/RECTO" --verso "/path/VERSO"
```

Terapkan rename:

```bash
python3 rename_recto_verso.py --recto "/path/RECTO" --verso "/path/VERSO" --apply
```

Pilihan tambahan:

- `--recursive`: sertakan foto dalam subfolder.
- `--separator _`: menghasilkan akhiran `_r` dan `_v`.
- `--all-files`: proses semua tipe file, bukan hanya format foto umum.
- `--help`: tampilkan seluruh petunjuk terminal.
- `--version`: tampilkan versi program.

## Catatan analisis

Program membandingkan kode nama antara RECTO dan VERSO. Status **pasangan ada** berarti kode yang sama ditemukan pada kedua sisi. Status **tanpa pasangan** hanya merupakan peringatan dan tidak menghalangi rename.

File versi lama yang berakhiran huruf kapital, seperti `ABC001R.jpg`, akan dianalisis sebagai perubahan kapitalisasi menjadi `ABC001r.jpg`.

---

Copyright © 2026 Aip - arif.muhamadrohman@gmail.com
