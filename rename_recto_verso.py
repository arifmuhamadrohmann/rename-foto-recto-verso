#!/usr/bin/env python3
"""Tambahkan penanda R/V pada nama berkas hasil digitalisasi.

Copyright © 2026 Aip - arif.muhamadrohman@gmail.com
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Sequence


VERSION = "1.0.3"
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
class RenameItem:
    side: str
    source: Path
    destination: Path | None
    state: str
    detail: str
    code: str
    has_pair: bool = False

    @property
    def ready(self) -> bool:
        return self.state == "ready" and self.destination is not None


@dataclass(frozen=True)
class Analysis:
    items: tuple[RenameItem, ...]
    ignored_count: int

    @property
    def ready_count(self) -> int:
        return sum(item.ready for item in self.items)

    @property
    def already_count(self) -> int:
        return sum(item.state == "already" for item in self.items)

    @property
    def conflict_count(self) -> int:
        return sum(item.state == "conflict" for item in self.items)

    @property
    def unpaired_count(self) -> int:
        return sum(not item.has_pair for item in self.items)


def _path_key(path: Path) -> str:
    """Kunci konservatif untuk mendeteksi benturan di filesystem umum."""
    return os.path.abspath(os.fspath(path)).casefold()


def _same_existing_file(first: Path, second: Path) -> bool:
    try:
        return first.exists() and second.exists() and os.path.samefile(first, second)
    except OSError:
        return False


def _iter_files(folder: Path, recursive: bool) -> Iterable[Path]:
    candidates = folder.rglob("*") if recursive else folder.iterdir()
    return sorted(
        (path for path in candidates if path.is_file() and not path.name.startswith(".")),
        key=lambda path: os.fspath(path.relative_to(folder)).casefold(),
    )


def _analyze_one_folder(
    folder: Path,
    side: str,
    marker: str,
    recursive: bool,
    all_files: bool,
) -> tuple[list[RenameItem], int]:
    items: list[RenameItem] = []
    ignored = 0
    marker_folded = marker.casefold()

    for source in _iter_files(folder, recursive):
        if not all_files and source.suffix.casefold() not in PHOTO_EXTENSIONS:
            ignored += 1
            continue

        stem = source.stem
        already_marked = bool(marker) and stem.endswith(marker)
        different_case = (
            bool(marker)
            and not already_marked
            and stem.casefold().endswith(marker_folded)
        )
        code = stem[: -len(marker)] if already_marked or different_case else stem

        if already_marked:
            items.append(
                RenameItem(
                    side=side,
                    source=source,
                    destination=None,
                    state="already",
                    detail=f"Sudah berakhiran {marker}",
                    code=code,
                )
            )
            continue

        new_stem = f"{code}{marker}" if different_case else f"{stem}{marker}"
        destination = source.with_name(f"{new_stem}{source.suffix}")
        if destination.exists() and not _same_existing_file(source, destination):
            state = "conflict"
            detail = f"Tujuan sudah ada: {destination.name}"
        else:
            state = "ready"
            detail = "Ubah penanda menjadi huruf kecil" if different_case else "Siap"

        items.append(
            RenameItem(
                side=side,
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
    *,
    recursive: bool = False,
    all_files: bool = False,
    separator: str = "",
) -> Analysis:
    separators = tuple(value for value in (os.sep, os.altsep) if value)
    if any(value in separator for value in separators):
        raise ValueError("Pemisah tidak boleh mengandung tanda pemisah folder.")

    recto = recto.expanduser().resolve()
    verso = verso.expanduser().resolve()

    for label, folder in (("RECTO", recto), ("VERSO", verso)):
        if not folder.exists():
            raise ValueError(f"Folder {label} tidak ditemukan: {folder}")
        if not folder.is_dir():
            raise ValueError(f"Lokasi {label} bukan folder: {folder}")

    if _path_key(recto) == _path_key(verso):
        raise ValueError("Folder RECTO dan VERSO harus berbeda.")

    recto_items, recto_ignored = _analyze_one_folder(
        recto, "RECTO", f"{separator}r", recursive, all_files
    )
    verso_items, verso_ignored = _analyze_one_folder(
        verso, "VERSO", f"{separator}v", recursive, all_files
    )
    items = recto_items + verso_items

    # Tandai kode yang memiliki pasangan pada sisi seberangnya. Perbedaan
    # ekstensi tidak menjadi masalah selama kode nama berkas sama.
    recto_codes = {item.code.casefold() for item in recto_items}
    verso_codes = {item.code.casefold() for item in verso_items}
    paired_items = [
        replace(
            item,
            has_pair=(
                item.code.casefold() in (verso_codes if item.side == "RECTO" else recto_codes)
            ),
        )
        for item in items
    ]

    # Pemeriksaan tambahan apabila dua rencana secara tidak sengaja menuju
    # path yang sama.
    destination_counts: dict[str, int] = {}
    for item in paired_items:
        if item.destination is not None:
            key = _path_key(item.destination)
            destination_counts[key] = destination_counts.get(key, 0) + 1

    final_items: list[RenameItem] = []
    for item in paired_items:
        if (
            item.destination is not None
            and destination_counts[_path_key(item.destination)] > 1
        ):
            final_items.append(
                replace(item, state="conflict", detail="Dua file menuju nama yang sama")
            )
        else:
            final_items.append(item)

    return Analysis(tuple(final_items), recto_ignored + verso_ignored)


def execute(analysis: Analysis) -> list[tuple[Path, Path]]:
    """Jalankan rencana; batalkan perubahan yang sudah terjadi jika ada kegagalan."""
    ready_items = [item for item in analysis.items if item.ready]

    for item in ready_items:
        assert item.destination is not None
        if not item.source.exists():
            raise RuntimeError(f"File sumber sudah tidak ada: {item.source}")
        if item.destination.exists() and not _same_existing_file(
            item.source, item.destination
        ):
            raise RuntimeError(f"Nama tujuan muncul setelah analisis: {item.destination}")

    completed: list[tuple[Path, Path]] = []
    try:
        for item in ready_items:
            assert item.destination is not None
            if _same_existing_file(item.source, item.destination):
                item.source.replace(item.destination)
            else:
                item.source.rename(item.destination)
            completed.append((item.source, item.destination))
    except Exception as exc:
        rollback_errors: list[str] = []
        for source, destination in reversed(completed):
            try:
                if destination.exists() and (
                    not source.exists() or _same_existing_file(source, destination)
                ):
                    destination.replace(source)
                elif destination.exists() and source.exists():
                    rollback_errors.append(f"Nama sumber sudah dipakai: {source}")
            except Exception as rollback_exc:  # pragma: no cover - sangat jarang
                rollback_errors.append(str(rollback_exc))
        extra = ""
        if rollback_errors:
            extra = " Rollback tidak lengkap: " + "; ".join(rollback_errors)
        raise RuntimeError(f"Rename gagal: {exc}.{extra}") from exc

    return completed


def _status_text(item: RenameItem) -> str:
    labels = {
        "ready": "SIAP",
        "already": "SUDAH",
        "conflict": "KONFLIK",
    }
    pair = "pasangan ada" if item.has_pair else "tanpa pasangan"
    return f"{labels[item.state]} - {item.detail}; {pair}"


def _print_analysis(analysis: Analysis) -> None:
    print("SISI\tNAMA LAMA\tNAMA BARU\tSTATUS")
    for item in analysis.items:
        new_name = item.destination.name if item.destination else "-"
        print(f"{item.side}\t{item.source.name}\t{new_name}\t{_status_text(item)}")
    print(
        "\nRingkasan: "
        f"{analysis.ready_count} siap, "
        f"{analysis.already_count} sudah sesuai, "
        f"{analysis.conflict_count} konflik, "
        f"{analysis.unpaired_count} tanpa pasangan, "
        f"{analysis.ignored_count} file nonfoto diabaikan."
    )


def run_gui() -> int:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, ttk
    except ImportError:
        print(
            "Tkinter tidak tersedia. Jalankan dengan --recto dan --verso melalui terminal.",
            file=sys.stderr,
        )
        return 2

    class RenameApp:
        def __init__(self, root: "tk.Tk") -> None:
            self.root = root
            self.root.title("Rename Foto RECTO / VERSO")
            self.root.minsize(820, 560)
            self.analysis: Analysis | None = None

            self.recto_var = tk.StringVar()
            self.verso_var = tk.StringVar()
            self.separator_var = tk.StringVar()
            self.recursive_var = tk.BooleanVar(value=False)
            self.all_files_var = tk.BooleanVar(value=False)
            self.summary_var = tk.StringVar(
                value="Pilih folder RECTO dan VERSO, lalu klik Analisis."
            )

            outer = ttk.Frame(root, padding=14)
            outer.pack(fill="both", expand=True)
            outer.columnconfigure(1, weight=1)
            outer.rowconfigure(7, weight=1)

            ttk.Label(
                outer,
                text="Penambah Akhiran Foto Digitalisasi",
                font=("TkDefaultFont", 15, "bold"),
            ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

            self._folder_row(outer, 1, "Folder RECTO", self.recto_var)
            self._folder_row(outer, 2, "Folder VERSO", self.verso_var)

            ttk.Label(outer, text="Pemisah (opsional)").grid(
                row=3, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Entry(outer, textvariable=self.separator_var, width=8).grid(
                row=3, column=1, sticky="w", pady=4
            )
            ttk.Label(outer, text="Kosong: KODE1r.jpg  •  Isi _: KODE1_r.jpg").grid(
                row=3, column=1, sticky="w", padx=(80, 0), pady=4
            )

            options = ttk.Frame(outer)
            options.grid(row=4, column=0, columnspan=3, sticky="w", pady=(5, 8))
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
            buttons.grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))
            ttk.Button(buttons, text="Analisis & Pratinjau", command=self.analyze).pack(
                side="left"
            )
            self.rename_button = ttk.Button(
                buttons,
                text="Rename File",
                command=self.rename,
                state="disabled",
            )
            self.rename_button.pack(side="left", padx=8)

            ttk.Label(outer, textvariable=self.summary_var, wraplength=780).grid(
                row=6, column=0, columnspan=3, sticky="w", pady=(0, 8)
            )

            table_frame = ttk.Frame(outer)
            table_frame.grid(row=7, column=0, columnspan=3, sticky="nsew")
            table_frame.columnconfigure(0, weight=1)
            table_frame.rowconfigure(0, weight=1)

            columns = ("side", "old", "new", "status")
            self.table = ttk.Treeview(table_frame, columns=columns, show="headings")
            headings = {
                "side": "Sisi",
                "old": "Nama Lama",
                "new": "Nama Baru",
                "status": "Status",
            }
            widths = {"side": 75, "old": 210, "new": 210, "status": 300}
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
                row=8, column=0, columnspan=3, sticky="e", pady=(10, 0)
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
                self.rename_button.configure(state="disabled")

        def analyze(self) -> None:
            if not self.recto_var.get().strip() or not self.verso_var.get().strip():
                messagebox.showwarning(
                    "Folder belum lengkap", "Pilih folder RECTO dan VERSO terlebih dahulu."
                )
                return
            try:
                self.analysis = analyze(
                    Path(self.recto_var.get().strip()),
                    Path(self.verso_var.get().strip()),
                    recursive=self.recursive_var.get(),
                    all_files=self.all_files_var.get(),
                    separator=self.separator_var.get(),
                )
            except Exception as exc:
                self.analysis = None
                self.rename_button.configure(state="disabled")
                messagebox.showerror("Analisis gagal", str(exc))
                return

            for row in self.table.get_children():
                self.table.delete(row)
            for item in self.analysis.items:
                self.table.insert(
                    "",
                    "end",
                    values=(
                        item.side,
                        item.source.name,
                        item.destination.name if item.destination else "-",
                        _status_text(item),
                    ),
                )

            self.summary_var.set(
                f"{self.analysis.ready_count} siap di-rename • "
                f"{self.analysis.already_count} sudah sesuai • "
                f"{self.analysis.conflict_count} konflik (akan dilewati) • "
                f"{self.analysis.unpaired_count} tanpa pasangan • "
                f"{self.analysis.ignored_count} file nonfoto diabaikan"
            )
            self.rename_button.configure(
                state="normal" if self.analysis.ready_count else "disabled"
            )

        def rename(self) -> None:
            if self.analysis is None or not self.analysis.ready_count:
                return
            if not messagebox.askyesno(
                "Konfirmasi rename",
                f"Rename {self.analysis.ready_count} file sesuai pratinjau?\n\n"
                "File berstatus konflik atau sudah sesuai tidak akan diubah.",
            ):
                return
            try:
                completed = execute(self.analysis)
            except Exception as exc:
                messagebox.showerror("Rename gagal", str(exc))
                return

            messagebox.showinfo(
                "Selesai", f"Berhasil me-rename {len(completed)} file."
            )
            self.analyze()

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Antarmuka grafis tidak dapat dibuka: {exc}", file=sys.stderr)
        return 2
    RenameApp(root)
    root.mainloop()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rename_recto_verso.py",
        description=(
            "Tambahkan r pada nama foto di folder RECTO dan v pada nama foto "
            "di folder VERSO. Tanpa argumen, aplikasi grafis akan dibuka."
        ),
        epilog=COPYRIGHT,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}\n{COPYRIGHT}",
    )
    parser.add_argument("--recto", type=Path, help="Path folder RECTO")
    parser.add_argument("--verso", type=Path, help="Path folder VERSO")
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
        help="Terapkan rename; tanpa opsi ini hanya menampilkan pratinjau",
    )
    parser.add_argument(
        "--gui", action="store_true", help="Buka antarmuka grafis"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.gui or (args.recto is None and args.verso is None):
        return run_gui()
    if args.recto is None or args.verso is None:
        parser.error("--recto dan --verso harus diberikan bersama-sama")

    try:
        result = analyze(
            args.recto,
            args.verso,
            recursive=args.recursive,
            all_files=args.all_files,
            separator=args.separator,
        )
        _print_analysis(result)
        if args.apply:
            completed = execute(result)
            print(f"\nSelesai: {len(completed)} file berhasil di-rename.")
        else:
            print("\nMode pratinjau: belum ada file yang diubah. Tambahkan --apply untuk menerapkan.")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
