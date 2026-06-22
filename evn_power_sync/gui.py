from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, ttk
from types import SimpleNamespace
from typing import Any

from .area_index import load_area_index, refresh_area_index
from .cli import _events_for_location
from .locations_store import (
    add_tracked_location,
    load_cached_locations,
    load_tracked_locations,
    refresh_locations_cache,
    search_cached_locations,
)
from .models import render_schedule, search_locations


def _location_label(location: dict[str, Any]) -> str:
    if location.get("area"):
        province = f" - {location.get('province')}" if location.get("province") else ""
        return f"[area:{location.get('source')}] {location.get('area')} -> {location.get('power_company') or location.get('name')} ({location.get('code')}){province}"
    province = f" - {location.get('province')}" if location.get("province") else ""
    return f"[{location.get('source')}] {location.get('name')} ({location.get('code')}){province}"


class EvnPowerSyncApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("EVN Power Sync")
        self.geometry("980x680")
        self.cached_locations: list[dict[str, Any]] = []
        self.area_entries: list[dict[str, Any]] = []
        self.tracked_locations: list[dict[str, Any]] = []
        self.visible_locations: list[dict[str, Any]] = []

        self.search_var = tk.StringVar()
        self.from_date_var = tk.StringVar(value="22-06-2026")
        self.to_date_var = tk.StringVar(value="02-07-2026")
        self.area_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Sẵn sàng")

        self._build_ui()
        self._load_local_locations()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Search vị trí").grid(row=0, column=0, sticky=tk.W)
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=45)
        search_entry.grid(row=0, column=1, padx=6, sticky=tk.W)
        search_entry.bind("<KeyRelease>", lambda _event: self._apply_search())

        ttk.Button(top, text="Tải lại vị trí online", command=self._refresh_online_async).grid(row=0, column=2, padx=6)
        ttk.Button(top, text="Lưu vị trí theo dõi", command=self._save_selected_location).grid(row=0, column=3, padx=6)

        ttk.Label(top, text="Từ ngày").grid(row=1, column=0, sticky=tk.W, pady=(8, 0))
        ttk.Entry(top, textvariable=self.from_date_var, width=16).grid(row=1, column=1, sticky=tk.W, padx=6, pady=(8, 0))
        ttk.Label(top, text="Đến ngày").grid(row=1, column=1, sticky=tk.W, padx=(150, 0), pady=(8, 0))
        ttk.Entry(top, textvariable=self.to_date_var, width=16).grid(row=1, column=1, sticky=tk.W, padx=(220, 0), pady=(8, 0))
        ttk.Label(top, text="Khu vực EVNSPC").grid(row=1, column=2, sticky=tk.W, pady=(8, 0))
        ttk.Entry(top, textvariable=self.area_var, width=28).grid(row=1, column=3, sticky=tk.W, padx=6, pady=(8, 0))

        body = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        left = ttk.Frame(body)
        body.add(left, weight=1)
        ttk.Label(left, text="Vị trí").pack(anchor=tk.W)
        self.locations_list = tk.Listbox(left, height=24, exportselection=False)
        self.locations_list.pack(fill=tk.BOTH, expand=True)

        right = ttk.Frame(body)
        body.add(right, weight=2)
        ttk.Button(right, text="Lấy lịch", command=self._load_schedule_async).pack(anchor=tk.W, pady=(0, 6))
        self.output = tk.Text(right, wrap=tk.WORD)
        self.output.pack(fill=tk.BOTH, expand=True)

        status = ttk.Label(self, textvariable=self.status_var, padding=(10, 4))
        status.pack(fill=tk.X)

    def _load_local_locations(self) -> None:
        self.cached_locations = load_cached_locations()
        self.area_entries = load_area_index()
        self.tracked_locations = load_tracked_locations()
        self.visible_locations = (self.cached_locations + self.area_entries) or self.tracked_locations
        self._render_locations(self.visible_locations)
        self.status_var.set(
            f"Cache: {len(self.cached_locations)} vị trí | Khu vực: {len(self.area_entries)} | Theo dõi: {len(self.tracked_locations)} vị trí"
        )

    def _render_locations(self, locations: list[dict[str, Any]]) -> None:
        self.locations_list.delete(0, tk.END)
        self.visible_locations = locations
        for location in locations:
            self.locations_list.insert(tk.END, _location_label(location))

    def _selected_location(self) -> dict[str, Any] | None:
        selection = self.locations_list.curselection()
        if not selection:
            return None
        return self.visible_locations[selection[0]]

    def _apply_search(self) -> None:
        query = self.search_var.get().strip()
        source = (self.cached_locations + self.area_entries) or self.tracked_locations
        self._render_locations(search_locations(source, query, limit=100) if query else source)

    def _set_output(self, text: str) -> None:
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)

    def _run_background(self, label: str, worker, on_success) -> None:
        self.status_var.set(label)

        def run() -> None:
            try:
                result = worker()
            except Exception as exc:  # noqa: BLE001 - GUI must show any fetch error.
                self.after(0, lambda: messagebox.showerror("Lỗi", str(exc)))
                self.after(0, lambda: self.status_var.set("Có lỗi"))
                return
            self.after(0, lambda: on_success(result))

        threading.Thread(target=run, daemon=True).start()

    def _refresh_online_async(self) -> None:
        from_date = self.from_date_var.get().strip()
        to_date = self.to_date_var.get().strip()

        def worker() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
            locations = refresh_locations_cache()
            area_entries = refresh_area_index(locations, from_date, to_date)
            return locations, area_entries

        def done(result: tuple[list[dict[str, Any]], list[dict[str, Any]]]) -> None:
            locations, area_entries = result
            self.cached_locations = locations
            self.area_entries = area_entries
            self._apply_search()
            self.status_var.set(f"Đã tải {len(locations)} vị trí và quét {len(area_entries)} khu vực")

        self._run_background("Đang tải vị trí online và quét khu vực...", worker, done)

    def _save_selected_location(self) -> None:
        location = self._selected_location()
        if not location:
            messagebox.showinfo("Chưa chọn", "Chọn một vị trí trước.")
            return
        self.tracked_locations = add_tracked_location(location)
        self.status_var.set(f"Đã lưu: {_location_label(location)}")

    def _load_schedule_async(self) -> None:
        location = self._selected_location()
        if not location:
            messagebox.showinfo("Chưa chọn", "Chọn một vị trí trước.")
            return

        args = SimpleNamespace(
            from_date=self.from_date_var.get().strip(),
            to_date=self.to_date_var.get().strip(),
            area=self.area_var.get().strip() or location.get("area") or None,
        )

        def worker() -> str:
            return render_schedule(_events_for_location(location, args))

        def done(text: str) -> None:
            self._set_output(text)
            self.status_var.set("Đã lấy lịch")

        self._run_background("Đang lấy lịch...", worker, done)


def main() -> None:
    app = EvnPowerSyncApp()
    app.mainloop()


if __name__ == "__main__":
    main()
