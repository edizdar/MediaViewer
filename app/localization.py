"""Localization and multi-language engine for Media Viewer Desktop."""

import json
from pathlib import Path
from typing import Callable, Optional

CONFIG_FILE = Path.home() / ".mediaviewer_config.json"

STRINGS = {
    "tr": {
        "open_file_btn": "📁  Dosya Aç",
        "open_file_tip": "Dosya Aç (Ctrl+O)",
        "playlist_tip": "Oynatma Listesi (Ctrl+L)",
        "prev_tip": "Önceki Dosya (←)",
        "next_tip": "Sonraki Dosya (→)",
        "fullscreen_tip": "Tam Ekran (F11)",
        "help_tip": "Kullanım Kılavuzu & Yardım (F1)",
        "lang_tip": "Dili Değiştir (TR / EN)",
        "zoom_out_tip": "Uzaklaştır (Ctrl+-)",
        "zoom_in_tip": "Yakınlaştır (Ctrl++)",
        "fit_tip": "Pencereye Sığdır (Ctrl+F)",
        "original_tip": "Orijinal Boyut (Ctrl+0)",
        "rotate_ccw_tip": "Sola Döndür (Shift+R)",
        "rotate_cw_tip": "Sağa Döndür (R)",
        "crop_tip": "Fotoğrafı Kırp (C)",
        "upscale_tip": "Resmi HD Yap ve Büyüt (2x / 4x Smart Upscale)",
        "delete_tip": "Çöp Kutusuna Gönder (Delete)",
        "adj_tip": "Renk Ayarları (Ctrl+J)",
        "welcome_title": "Media Viewer",
        "welcome_subtitle": "Dosya açmak için Ctrl+O tuşuna basın\nveya bir dosyayı sürükleyip bırakın",
        "fs_exit_btn": "✕  Çıkış",
        "fs_exit_tip": "Tam Ekrandan Çık (Esc veya F11)",
        "open_dialog_title": "Medya Dosyası Aç",
        "delete_confirm_title": "Dosyayı Sil",
        "delete_confirm_msg": "Bu dosyayı çöp kutusuna göndermek istediğinize emin misiniz?\n\n{}",
        "file_deleted": "Dosya çöp kutusuna gönderildi",
        "delete_failed": "Dosya silinemedi:\n{}",
        "copied_clipboard": "Panoya kopyalandı",
        "error_title": "Hata",
        "file_not_found": "Dosya bulunamadı:\n{}",
        "image_load_failed": "Fotoğraf yüklenemedi:\n{}",
        "window_title": "Media Viewer",
        "no_file_open": "Açık Dosya Yok",
        "toast_lang": "Dil: Türkçe 🇹🇷",
        "adj_panel_title": "🎨  Renk Ayarları",
        "adj_brightness": "☀  Parlaklık",
        "adj_contrast": "◑  Kontrast",
        "adj_gamma": "γ  Gamma",
        "adj_sharpness": "🔍  Netlik (Keskinlik)",
        "adj_smart_btn": "✨  Akıllı Ayarla",
        "adj_smart_tip": "İdeal kontrast, parlaklık ve gölge detayını otomatik uygular",
        "adj_reset_btn": "↺  Sıfırla",
        "adj_save_btn": "💾  Kaydet",
        "help_title": "Kullanım Kılavuzu & Yardım",
        "tab_shortcuts": "⌨️ Kısayol Tuşları & Kılavuz",
        "tab_features": "✨ Öne Çıkan Özellikler",
        "tab_faq": "❓ SSS (Sıkça Sorulan Sorular)",
        "tab_about": "ℹ️ Hakkında",
        "check_updates": "🔄  Güncellemeleri Denetle",
        "checking_updates": "Denetleniyor...",
        "update_already_latest": "Tebrikler! Zaten en güncel sürümü (v{}) kullanıyorsunuz.",
        "update_failed": "Güncelleme sunucusuna bağlanılamadı.\nLütfen internet bağlantınızı kontrol edip tekrar deneyin.",
        "close_btn": "Kapat",
    },
    "en": {
        "open_file_btn": "📁  Open File",
        "open_file_tip": "Open File (Ctrl+O)",
        "playlist_tip": "Playlist (Ctrl+L)",
        "prev_tip": "Previous File (←)",
        "next_tip": "Next File (→)",
        "fullscreen_tip": "Fullscreen (F11)",
        "help_tip": "User Guide & Help (F1)",
        "lang_tip": "Switch Language (TR / EN)",
        "zoom_out_tip": "Zoom Out (Ctrl+-)",
        "zoom_in_tip": "Zoom In (Ctrl++)",
        "fit_tip": "Fit to Window (Ctrl+F)",
        "original_tip": "Original Size (Ctrl+0)",
        "rotate_ccw_tip": "Rotate CCW (Shift+R)",
        "rotate_cw_tip": "Rotate CW (R)",
        "crop_tip": "Crop Photo (C)",
        "upscale_tip": "Smart HD Upscale (2x / 4x)",
        "delete_tip": "Move to Recycle Bin (Delete)",
        "adj_tip": "Color Adjustments (Ctrl+J)",
        "welcome_title": "Media Viewer",
        "welcome_subtitle": "Press Ctrl+O to open a file\nor drag & drop a file here",
        "fs_exit_btn": "✕  Exit",
        "fs_exit_tip": "Exit Fullscreen (Esc or F11)",
        "open_dialog_title": "Open Media File",
        "delete_confirm_title": "Delete File",
        "delete_confirm_msg": "Are you sure you want to move this file to the recycle bin?\n\n{}",
        "file_deleted": "File moved to recycle bin",
        "delete_failed": "Failed to delete file:\n{}",
        "copied_clipboard": "Copied to clipboard",
        "error_title": "Error",
        "file_not_found": "File not found:\n{}",
        "image_load_failed": "Failed to load image:\n{}",
        "window_title": "Media Viewer",
        "no_file_open": "No File Open",
        "toast_lang": "Language: English 🇬🇧",
        "adj_panel_title": "🎨  Color Adjustments",
        "adj_brightness": "☀  Brightness",
        "adj_contrast": "◑  Contrast",
        "adj_gamma": "γ  Gamma",
        "adj_sharpness": "🔍  Sharpness",
        "adj_smart_btn": "✨  Smart Enhance",
        "adj_smart_tip": "Automatically applies optimal contrast, brightness, and shadow detail",
        "adj_reset_btn": "↺  Reset",
        "adj_save_btn": "💾  Save",
        "help_title": "User Guide & Help",
        "tab_shortcuts": "⌨️ Shortcuts & Guide",
        "tab_features": "✨ Highlights & Features",
        "tab_faq": "❓ FAQ",
        "tab_about": "ℹ️ About",
        "check_updates": "🔄  Check for Updates",
        "checking_updates": "Checking...",
        "update_already_latest": "Congratulations! You are already using the latest version (v{}).",
        "update_failed": "Could not connect to the update server.\nPlease check your internet connection and try again.",
        "close_btn": "Close",
    }
}


class LocalizationManager:
    _instance: Optional["LocalizationManager"] = None

    def __new__(cls) -> "LocalizationManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._lang = "tr"
            cls._instance._listeners: list[Callable[[str], None]] = []
            cls._instance._load_config()
        return cls._instance

    @property
    def current_language(self) -> str:
        return self._lang

    def _load_config(self) -> None:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._lang = data.get("language", "tr")
        except Exception:
            self._lang = "tr"

    def _save_config(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"language": self._lang}, f, indent=2)
        except Exception:
            pass

    def set_language(self, lang: str) -> None:
        if lang not in ("tr", "en"):
            lang = "tr"
        if self._lang != lang:
            self._lang = lang
            self._save_config()
            for listener in list(self._listeners):
                try:
                    listener(self._lang)
                except Exception:
                    pass

    def toggle_language(self) -> str:
        new_lang = "en" if self._lang == "tr" else "tr"
        self.set_language(new_lang)
        return new_lang

    def add_listener(self, callback: Callable[[str], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get(self, key: str, default: str = "") -> str:
        return STRINGS.get(self._lang, {}).get(key, STRINGS["tr"].get(key, default or key))


_loc = LocalizationManager()


def loc(key: str, default: str = "") -> str:
    """Get localized text for the current language."""
    return _loc.get(key, default)


def get_localization() -> LocalizationManager:
    """Get the singleton localization manager."""
    return _loc
