# Sortir Foto RECTO, VERSO, dan IDENTITY

Program ini menyortir dan memindahkan foto digitalisasi dari tiga folder sumber ke folder hasil berdasarkan sisi dan format file.

## Aturan nama

- RECTO mendapat akhiran huruf kecil `r`.
- VERSO mendapat akhiran huruf kecil `v`.
- Nama file IDENTITY tetap persis seperti sumber.
- JPG dan CR dengan kode sama diproses sebagai file terpisah.
- File versi lama dengan `R` atau `V` kapital dikoreksi menjadi `r` atau `v`.

Contoh:

```text
RECTO/ABC001.jpg       → HASIL/RECTO JPG/ABC001r.jpg
RECTO/ABC001.cr3       → HASIL/RECTO CR3/ABC001r.cr3
VERSO/ABC001.jpg       → HASIL/VERSO JPG/ABC001v.jpg
VERSO/ABC001.cr3       → HASIL/VERSO CR3/ABC001v.cr3
IDENTITY/Identitas.jpg → HASIL/IDENTITY JPG/Identitas.jpg
IDENTITY/Identitas.cr3 → HASIL/IDENTITY CR3/Identitas.cr3
```

Nama folder RAW mengikuti ekstensi yang benar-benar ditemukan. Sebagai contoh, CR2 menghasilkan folder `RECTO CR2`, sedangkan CR3 menghasilkan `RECTO CR3`. Format foto lain yang didukung juga mendapat foldernya sendiri, seperti `TIF`, `PNG`, atau `DNG`.

File tidak pernah ditimpa. Konflik nama ditandai pada pratinjau dan dilewati.

## Menggunakan antarmuka grafis

1. Jalankan program.
2. Pilih folder sumber **RECTO**.
3. Pilih folder sumber **VERSO**.
4. Pilih folder sumber **IDENTITY**.
5. Pilih satu folder **HASIL**.
6. Klik **Analisis & Pratinjau**.
7. Periksa folder tujuan dan nama baru.
8. Klik **Sortir & Pindahkan**, lalu konfirmasi.

Kolom **Pemisah r/v** boleh dikosongkan untuk hasil `ABC001r.jpg`. Isi dengan `_` jika menginginkan `ABC001_r.jpg`. Pengaturan ini tidak mengubah nama IDENTITY.

## Menjalankan di Windows

### Dengan Python

1. Instal Python 3 dan aktifkan **Add Python to PATH** ketika melakukan instalasi.
2. Pastikan `rename_recto_verso.py` dan `Jalankan di Windows.bat` berada dalam folder yang sama.
3. Klik dua kali `Jalankan di Windows.bat`.

### Membuat EXE portabel

1. Gunakan komputer Windows yang terhubung ke internet.
2. Klik dua kali `Buat EXE Windows.bat`.
3. Setelah selesai, Windows Explorer otomatis menyorot `dist\RenameFotoRectoVerso.exe`.

EXE dapat dijalankan pada komputer Windows lain tanpa memasang Python.

### Membuat installer Windows

1. Instal Python 3 dan Inno Setup 6.
2. Klik dua kali `Buat Installer Windows.bat`.
3. Setelah selesai, Windows Explorer otomatis menyorot `installer\Setup-RenameFotoRectoVerso-2.0.0.exe`.

## Menjalankan di macOS

Klik dua kali `Jalankan Rename Foto.command`, atau jalankan:

```bash
python3 rename_recto_verso.py
```

## Penggunaan terminal

Pratinjau saja:

```bash
python3 rename_recto_verso.py \
  --recto "/path/RECTO" \
  --verso "/path/VERSO" \
  --identity "/path/IDENTITY" \
  --output "/path/HASIL"
```

Pindahkan file sesuai pratinjau:

```bash
python3 rename_recto_verso.py \
  --recto "/path/RECTO" \
  --verso "/path/VERSO" \
  --identity "/path/IDENTITY" \
  --output "/path/HASIL" \
  --apply
```

Pilihan tambahan:

- `--recursive`: sertakan foto dalam subfolder.
- `--separator _`: gunakan akhiran `_r` dan `_v`.
- `--all-files`: proses semua jenis file, bukan hanya format foto umum.
- `--help`: tampilkan petunjuk terminal.
- `--version`: tampilkan versi dan copyright.

## Catatan keamanan

- Program selalu menampilkan pratinjau sebelum pemindahan melalui GUI.
- File tujuan yang sudah ada tidak akan ditimpa.
- Jika pemindahan gagal di tengah proses, program mencoba mengembalikan file yang sudah dipindahkan ke lokasi sumber.
- Folder HASIL tidak boleh berada di dalam folder sumber agar hasil tidak dianalisis ulang.

---

Copyright © 2026 Aip - arif.muhamadrohman@gmail.com
