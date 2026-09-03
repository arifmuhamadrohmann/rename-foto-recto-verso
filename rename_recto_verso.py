#!/usr/bin/env python3
"""Sortir dan pindahkan foto digitalisasi RECTO, VERSO, dan IDENTITY.

Copyright © 2026 Aip - arif.muhamadrohman@gmail.com
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Sequence


VERSION = "2.0.0"
AUTHOR = "Aip"
AUTHOR_EMAIL = "arif.muhamadrohman@gmail.com"
COPYRIGHT = f"Copyright © 2026 {AUTHOR} - {AUTHOR_EMAIL}"
PHOTO_EXTENSIONS = {
    ".avif",
    ".bmp",
    ".cr2",
    ".cr3",
    ".dng",
    ".gif",
    ".heic",
    ".heif",
    ".jpeg",
    ".jpg",
    ".nef",
    ".png",
    ".raw",
    ".tif",
    ".tiff",
    ".webp",
}


@dataclass(frozen=True)
class MoveItem:
    side: str
    file_type: str
    source: Path
    destination: Path
    state: str
    detail: str
    code: str
    has_pair: bool = False

    @property
    def ready(self) -> bool:
        return self.state == "ready"


@dataclass(frozen=True)
class Analysis:
    items: tuple[MoveItem, ...]
    ignored_count: int
    output_root: Path

    @property
    def ready_count(self) -> int:
        return sum(item.ready for item in self.items)

    @property
    def conflict_count(self) -> int:
        return sum(item.state == "conflict" for item in self.items)

    @property
    def unpaired_count(self) -> int:
        return sum(
            item.side in {"RECTO", "VERSO"} and not item.has_pair
            for item in self.items
        )

    @property
    def output_folder_count(self) -> int:
        return len({item.destination.parent for item in self.items if item.ready})


def _path_key(path: Path) -> str:
    """Kunci konservatif untuk mendeteksi benturan di filesystem umum."""
    return os.path.abspath(os.fspath(path)).casefold()


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _iter_files(folder: Path, recursive: bool) -> Iterable[Path]:
    candidates = folder.rglob("*") if recursive else folder.iterdir()
    return sorted(
        (path for path in candidates if path.is_file() and not path.name.startswith(".")),
        key=lambda path: os.fspath(path.relative_to(folder)).casefold(),
    )


def _format_group(path: Path) -> str:
    extension = path.suffix.casefold()
    if extension in {".jpg", ".jpeg"}:
        return "JPG"
    if extension:
        return extension[1:].upper()
    return "TANPA EKSTENSI"


def _new_name(stem: str, extension: str, marker: str) -> tuple[str, str, str]:
    """Kembalikan nama baru, kode dasar, dan keterangan perubahan."""
    if not marker:  # IDENTITY: nama wajib tetap seperti sumber.
        return f"{stem}{extension}", stem, "Nama IDENTITY tetap"

    if stem.endswith(marker):
        return f"{stem}{extension}", stem[: -len(marker)], "Penanda sudah sesuai"

    if stem.casefold().endswith(marker.casefold()):
        code = stem[: -len(marker)]
        return (
            f"{code}{marker}{extension}",
            code,
            "Ubah penanda menjadi huruf kecil",
        )

    return f"{stem}{marker}{extension}", stem, f"Tambahkan penanda {marker}"


def _analyze_one_folder(
    folder: Path,
    side: str,
    marker: str,
    output_root: Path,
    recursive: bool,
    all_files: bool,
) -> tuple[list[MoveItem], int]:
    items: list[MoveItem] = []
    ignored = 0

    for source in _iter_files(folder, recursive):
        if not all_files and source.suffix.casefold() not in PHOTO_EXTENSIONS:
            ignored += 1
            continue

        file_type = _format_group(source)
        destination_folder = output_root / f"{side} {file_type}"
        new_name, code, change_detail = _new_name(source.stem, source.suffix, marker)
        destination = destination_folder / new_name

        if _path_key(source) == _path_key(destination):
            state = "conflict"
            detail = "Folder sumber dan tujuan sama"
        elif destination.exists():
            state = "conflict"
            detail = f"Tujuan sudah ada: {destination}"
        else:
            state = "ready"
            detail = f"{change_detail}; pindahkan ke {destination_folder.name}"

        items.append(
            MoveItem(
                side=side,
                file_type=file_type,
                source=source,
                destination=destination,
                state=state,
                detail=detail,
                code=code,
            )
        )

    return items, ignored


def analyze(
    recto: Path,
    verso: Path,
    identity: Path,
    output: Path,
    *,
    recursive: bool = False,
    all_files: bool = False,
    separator: str = "",
) -> Analysis:
    separators = tuple(value for value in (os.sep, os.altsep) if value)
    if any(value in separator for value in separators):
        raise ValueError("Pemisah tidak boleh mengandung tanda pemisah folder.")

    source_folders = {
        "RECTO": recto.expanduser().resolve(),
        "VERSO": verso.expanduser().resolve(),
        "IDENTITY": identity.expanduser().resolve(),
    }
    output_root = output.expanduser().resolve()

    for label, folder in source_folders.items():
        if not folder.exists():
            raise ValueError(f"Folder {label} tidak ditemukan: {folder}")
        if not folder.is_dir():
            raise ValueError(f"Lokasi {label} bukan folder: {folder}")

    source_keys = {_path_key(folder) for folder in source_folders.values()}
    if len(source_keys) != len(source_folders):
        raise ValueError("Folder RECTO, VERSO, dan IDENTITY harus berbeda.")

    for label, folder in source_folders.items():
        if _is_within(output_root, folder):
            raise ValueError(
                f"Folder hasil tidak boleh berada di dalam folder sumber {label}."
            )

    specs = (
        ("RECTO", f"{separator}r"),
        ("VERSO", f"{separator}v"),
        ("IDENTITY", ""),
    )
    items: list[MoveItem] = []
    ignored_count = 0
    side_items: dict[str, list[MoveItem]] = {}

    for side, marker in specs:
        found, ignored = _analyze_one_folder(
            source_folders[side],
            side,
            marker,
            output_root,
            recursive,
            all_files,
        )
        side_items[side] = found
        items.extend(found)
        ignored_count += ignored

    recto_codes = {item.code.casefold() for item in side_items["RECTO"]}
    verso_codes = {item.code.casefold() for item in side_items["VERSO"]}
    paired_items = [
        replace(
            item,
            has_pair=(
                True
                if item.side == "IDENTITY"
                else item.code.casefold()
                in (verso_codes if item.side == "RECTO" else recto_codes)
            ),
        )
        for item in items
    ]

    destination_counts: dict[str, int] = {}
    for item in paired_items:
        key = _path_key(item.destination)
        destination_counts[key] = destination_counts.get(key, 0) + 1

    final_items: list[MoveItem] = []
    for item in paired_items:
        if destination_counts[_path_key(item.destination)] > 1:
            final_items.append(
                replace(item, state="conflict", detail="Dua file menuju nama yang sama")
            )
        else:
            final_items.append(item)

    return Analysis(tuple(final_items), ignored_count, output_root)


def execute(analysis: Analysis) -> list[tuple[Path, Path]]:
    """Pindahkan rencana; kembalikan file yang sudah berpindah jika terjadi gagal."""
    ready_items = [item for item in analysis.items if item.ready]

    for item in ready_items:
        if not item.source.exists():
            raise RuntimeError(f"File sumber sudah tidak ada: {item.source}")
        if item.destination.exists():
            raise RuntimeError(f"Nama tujuan muncul setelah analisis: {item.destination}")

    completed: list[tuple[Path, Path]] = []
    created_folders: set[Path] = set()
    try:
        for item in ready_items:
            if not item.destination.parent.exists():
                item.destination.parent.mkdir(parents=True, exist_ok=True)
                created_folders.add(item.destination.parent)
            shutil.move(os.fspath(item.source), os.fspath(item.destination))
            completed.append((item.source, item.destination))
    except Exception as exc:
        rollback_errors: list[str] = []
        for source, destination in reversed(completed):
            try:
                if destination.exists() and not source.exists():
                    source.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(os.fspath(destination), os.fspath(source))
                elif destination.exists() and source.exists():
                    rollback_errors.append(f"Nama sumber sudah dipakai: {source}")
            except Exception as rollback_exc:  # pragma: no cover - sangat jarang
                rollback_errors.append(str(rollback_exc))

        for folder in sorted(created_folders, key=lambda value: len(value.parts), reverse=True):
            try:
                folder.rmdir()
            except OSError:
                pass

        extra = ""
        if rollback_errors:
            extra = " Rollback tidak lengkap: " + "; ".join(rollback_errors)
        raise RuntimeError(f"Pemindahan gagal: {exc}.{extra}") from exc

    return completed


def _status_text(item: MoveItem) -> str:
    labels = {"ready": "SIAP", "conflict": "KONFLIK"}
    if item.side == "IDENTITY":
        note = "nama asli dipertahankan"
    else:
        note = "pasangan ada" if item.has_pair else "tanpa pasangan"
    return f"{labels[item.state]} - {item.detail}; {note}"


def _print_analysis(analysis: Analysis) -> None:
    print("SISI\tFORMAT\tNAMA SUMBER\tTUJUAN\tSTATUS")
    for item in analysis.items:
        try:
            destination = item.destination.relative_to(analysis.output_root)
        except ValueError:
            destination = item.destination
        print(
            f"{item.side}\t{item.file_type}\t{item.source.name}\t"
            f"{destination}\t{_status_text(item)}"
        )
    print(
        "\nRingkasan: "
        f"{analysis.ready_count} siap dipindahkan, "
        f"{analysis.output_folder_count} folder hasil, "
        f"{analysis.conflict_count} konflik, "
        f"{analysis.unpaired_count} RECTO/VERSO tanpa pasangan, "
        f"{analysis.ignored_count} file nonfoto diabaikan."
    )


def run_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError:
        print(
            "Tkinter tidak tersedia. Gunakan --recto, --verso, --identity, "
            "dan --output melalui terminal.",
            file=sys.stderr,
        )
        return 2

    class SortPhotoApp:
        def __init__(self, root: "tk.Tk") -> None:
            self.root = root
            self.root.title("Sortir Foto RECTO / VERSO / IDENTITY")
            self.root.minsize(980, 650)
            self.analysis: Analysis | None = None

            self.recto_var = tk.StringVar()
            self.verso_var = tk.StringVar()
            self.identity_var = tk.StringVar()
            self.output_var = tk.StringVar()
            self.separator_var = tk.StringVar()
            self.recursive_var = tk.BooleanVar(value=False)
            self.all_files_var = tk.BooleanVar(value=False)
            self.summary_var = tk.StringVar(
                value="Pilih tiga folder sumber dan satu folder hasil."
            )

            outer = ttk.Frame(root, padding=14)
            outer.pack(fill="both", expand=True)
            outer.columnconfigure(1, weight=1)
            outer.rowconfigure(9, weight=1)

            ttk.Label(
                outer,
                text="Sortir Foto Digitalisasi",
                font=("TkDefaultFont", 15, "bold"),
            ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

            self._folder_row(outer, 1, "Folder RECTO", self.recto_var)
            self._folder_row(outer, 2, "Folder VERSO", self.verso_var)
            self._folder_row(outer, 3, "Folder IDENTITY", self.identity_var)
            self._folder_row(outer, 4, "Folder HASIL", self.output_var)

            ttk.Label(outer, text="Pemisah r/v (opsional)").grid(
                row=5, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(outer, textvariable=self.separator_var, width=8).grid(
                row=5, column=1, sticky="w", pady=4
            )
            ttk.Label(
                outer,
                text="Kosong: KODE1r.jpg  •  Isi _: KODE1_r.jpg  •  IDENTITY tetap",
            ).grid(row=5, column=1, sticky="w", padx=(80, 0), pady=4)

            options = ttk.Frame(outer)
            options.grid(row=6, column=0, columnspan=3, sticky="w", pady=(5, 8))
            ttk.Checkbutton(
                options,
                text="Sertakan subfolder",
                variable=self.recursive_var,
            ).pack(side="left", padx=(0, 18))
            ttk.Checkbutton(
                options,
                text="Sertakan semua jenis file",
                variable=self.all_files_var,
            ).pack(side="left")

            buttons = ttk.Frame(outer)
            buttons.grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 8))
            ttk.Button(buttons, text="Analisis & Pratinjau", command=self.analyze).pack(
                side="left"
            )
            self.move_button = ttk.Button(
                buttons,
                text="Sortir & Pindahkan",
                command=self.move,
                state="disabled",
            )
            self.move_button.pack(side="left", padx=8)

            ttk.Label(outer, textvariable=self.summary_var, wraplength=920).grid(
                row=8, column=0, columnspan=3, sticky="w", pady=(0, 8)
            )

            table_frame = ttk.Frame(outer)
            table_frame.grid(row=9, column=0, columnspan=3, sticky="nsew")
            table_frame.columnconfigure(0, weight=1)
            table_frame.rowconfigure(0, weight=1)

            columns = ("side", "format", "old", "destination", "status")
            self.table = ttk.Treeview(table_frame, columns=columns, show="headings")
            headings = {
                "side": "Sisi",
                "format": "Format",
                "old": "Nama Sumber",
                "destination": "Folder / Nama Tujuan",
                "status": "Status",
            }
            widths = {
                "side": 80,
                "format": 70,
                "old": 190,
                "destination": 270,
                "status": 330,
            }
            for column in columns:
                self.table.heading(column, text=headings[column])
                self.table.column(column, width=widths[column], anchor="w")
            scrollbar = ttk.Scrollbar(
                table_frame, orient="vertical", command=self.table.yview
            )
            self.table.configure(yscrollcommand=scrollbar.set)
            self.table.grid(row=0, column=0, sticky="nsew")
            scrollbar.grid(row=0, column=1, sticky="ns")

            ttk.Label(outer, text=COPYRIGHT).grid(
                row=10, column=0, columnspan=3, sticky="e", pady=(10, 0)
            )

        def _folder_row(
            self, parent: "ttk.Frame", row: int, label: str, variable: "tk.StringVar"
        ) -> None:
            ttk.Label(parent, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(parent, textvariable=variable).grid(
                row=row, column=1, sticky="ew", pady=4
            )
            ttk.Button(
                parent,
                text="Pilih…",
                command=lambda: self._choose_folder(variable),
            ).grid(row=row, column=2, padx=(8, 0), pady=4)

        def _choose_folder(self, variable: "tk.StringVar") -> None:
            selected = filedialog.askdirectory(
                title="Pilih folder",
                initialdir=variable.get() or str(Path.home()),
            )
            if selected:
                variable.set(selected)
                self.analysis = None
                self.move_button.configure(state="disabled")

        def analyze(self) -> None:
            paths = (
                self.recto_var.get().strip(),
                self.verso_var.get().strip(),
                self.identity_var.get().strip(),
                self.output_var.get().strip(),
            )
            if not all(paths):
                messagebox.showwarning(
                    "Folder belum lengkap",
                    "Pilih folder RECTO, VERSO, IDENTITY, dan HASIL terlebih dahulu.",
                )
                return
            try:
                self.analysis = analyze(
                    Path(paths[0]),
                    Path(paths[1]),
                    Path(paths[2]),
                    Path(paths[3]),
                    recursive=self.recursive_var.get(),
                    all_files=self.all_files_var.get(),
                    separator=self.separator_var.get(),
                )
            except Exception as exc:
                self.analysis = None
                self.move_button.configure(state="disabled")
                messagebox.showerror("Analisis gagal", str(exc))
                return

            for row in self.table.get_children():
                self.table.delete(row)
            for item in self.analysis.items:
                relative_destination = item.destination.relative_to(
                    self.analysis.output_root
                )
                self.table.insert(
                    "",
                    "end",
                    values=(
                        item.side,
                        item.file_type,
                        item.source.name,
                        os.fspath(relative_destination),
                        _status_text(item),
                    ),
                )

            self.summary_var.set(
                f"{self.analysis.ready_count} siap dipindahkan • "
                f"{self.analysis.output_folder_count} folder hasil • "
                f"{self.analysis.conflict_count} konflik (akan dilewati) • "
                f"{self.analysis.unpaired_count} RECTO/VERSO tanpa pasangan • "
                f"{self.analysis.ignored_count} file nonfoto diabaikan"
            )
            self.move_button.configure(
                state="normal" if self.analysis.ready_count else "disabled"
            )

        def move(self) -> None:
            if self.analysis is None or not self.analysis.ready_count:
                return
            if not messagebox.askyesno(
                "Konfirmasi pemindahan",
                f"Pindahkan {self.analysis.ready_count} file ke "
                f"{self.analysis.output_folder_count} folder hasil?\n\n"
                "RECTO diberi akhiran r, VERSO diberi akhiran v, dan nama "
                "IDENTITY tetap. File konflik tidak akan dipindahkan.",
            ):
                return
            try:
                completed = execute(self.analysis)
            except Exception as exc:
                messagebox.showerror("Pemindahan gagal", str(exc))
                return

            messagebox.showinfo(
                "Selesai", f"Berhasil menyortir dan memindahkan {len(completed)} file."
            )
            self.analyze()

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Antarmuka grafis tidak dapat dibuka: {exc}", file=sys.stderr)
        return 2
    SortPhotoApp(root)
    root.mainloop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rename_recto_verso.py",
        description=(
            "Sortir dan pindahkan foto RECTO, VERSO, dan IDENTITY berdasarkan "
            "format. RECTO diberi r, VERSO diberi v, dan nama IDENTITY tetap. "
            "Tanpa argumen, aplikasi grafis akan dibuka."
        ),
        epilog=COPYRIGHT,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}\n{COPYRIGHT}",
    )
    parser.add_argument("--recto", type=Path, help="Path folder sumber RECTO")
    parser.add_argument("--verso", type=Path, help="Path folder sumber VERSO")
    parser.add_argument("--identity", type=Path, help="Path folder sumber IDENTITY")
    parser.add_argument("--output", type=Path, help="Path folder hasil")
    parser.add_argument(
        "--separator",
        default="",
        help="Teks sebelum r/v, misalnya '_' untuk KODE_r.jpg (default: kosong)",
    )
    parser.add_argument(
        "--recursive", action="store_true", help="Sertakan file di dalam subfolder"
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Proses semua jenis file, bukan hanya format foto",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Pindahkan file; tanpa opsi ini hanya menampilkan pratinjau",
    )
    parser.add_argument("--gui", action="store_true", help="Buka antarmuka grafis")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    folder_args = (args.recto, args.verso, args.identity, args.output)
    if args.gui or all(value is None for value in folder_args):
        return run_gui()
    if any(value is None for value in folder_args):
        parser.error("--recto, --verso, --identity, dan --output harus diberikan bersama")

    try:
        result = analyze(
            args.recto,
            args.verso,
            args.identity,
            args.output,
            recursive=args.recursive,
            all_files=args.all_files,
            separator=args.separator,
        )
        _print_analysis(result)
        if args.apply:
            completed = execute(result)
            print(f"\nSelesai: {len(completed)} file berhasil dipindahkan.")
        else:
            print(
                "\nMode pratinjau: belum ada file yang dipindahkan. "
                "Tambahkan --apply untuk menerapkan."
            )
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
