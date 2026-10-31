"""Localization and multi-language engine for Media Viewer Desktop."""

import json
from pathlib import Path
from typing import Callable, Optional

CONFIG_FILE = Path.home() / ".mediaviewer_config.json"


def detect_system_language() -> str:
    """Detect Windows system language. Returns 'tr' if Turkish, else 'en'."""
    # 1. Direct Windows Win32 API check via ctypes
    try:
        import ctypes
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        # Primary language ID is lower 10 bits: 0x1F is LANG_TURKISH
        if (lang_id & 0x3FF) == 0x1F:
            return "tr"
        return "en"
    except Exception:
        pass

    # 2. Python locale fallback
    try:
        import locale
        loc_val = locale.getdefaultlocale()
        if loc_val and loc_val[0] and loc_val[0].lower().startswith("tr"):
            return "tr"
    except Exception:
        pass

    return "en"


STRINGS = {
    "tr": {
        "open_file_btn": "📁  Dosya Aç",
        "open_file_tip": "Dosya Aç (Ctrl+O)",
        "playlist_tip": "Oynatma Listesi (Ctrl+L)",
        "prev_tip": "Önceki Dosya (←)",
        "next_tip": "Sonraki Dosya (→)",
        "fullscreen_tip": "Tam Ekran (F11)",
        "help_tip": "Kullanım Kılavuzu & Yardım (F1)",
        "lang_tip": "Dili Değiştir (Otomatik / TR / EN)",
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
        "toast_lang_tr": "Dil: Türkçe (TR)",
        "toast_lang_en": "Dil: English (EN)",
        "toast_lang_auto": "Dil: Otomatik (Sistem: {})",
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
        "update_banner_msg": "🎉  <b>Media Viewer {} yayınlandı!</b>  (Mevcut: v{})",
        "update_banner_details": "📋 Yenilikleri Gör",
        "update_banner_download": "📥 Hemen İndir",
        "update_dialog_title": "Yeni Sürüm Mevcut!",
        "update_dialog_header": "Yeni Bir Sürüm Yayınlandı: {}",
        "update_dialog_sub": "Mevcut Sürüm: v{}  →  <b>Yeni Sürüm: {}</b>",
        "update_dialog_notes": "<b>Yenilikler ve İyileştirmeler:</b>",
        "update_dialog_later": "Daha Sonra",
        "update_dialog_dl_btn": "📥  Yeni Sürümü İndir",
        "update_dialog_no_notes": "<i>Bu sürüm için detaylı not belirtilmemiş.</i>",
    },
    "en": {
        "open_file_btn": "📁  Open File",
        "open_file_tip": "Open File (Ctrl+O)",
        "playlist_tip": "Playlist (Ctrl+L)",
        "prev_tip": "Previous File (←)",
        "next_tip": "Next File (→)",
        "fullscreen_tip": "Fullscreen (F11)",
        "help_tip": "User Guide & Help (F1)",
        "lang_tip": "Switch Language (Auto / TR / EN)",
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
        "toast_lang_tr": "Language: Turkish (TR)",
        "toast_lang_en": "Language: English (EN)",
        "toast_lang_auto": "Language: Auto (System: {})",
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
        "update_banner_msg": "🎉  <b>Media Viewer {} is available!</b>  (Current: v{})",
        "update_banner_details": "📋 View Details",
        "update_banner_download": "📥 Download Now",
        "update_dialog_title": "New Version Available!",
        "update_dialog_header": "A New Version Has Been Released: {}",
        "update_dialog_sub": "Current Version: v{}  →  <b>New Version: {}</b>",
        "update_dialog_notes": "<b>What's New & Improvements:</b>",
        "update_dialog_later": "Later",
        "update_dialog_dl_btn": "📥  Download New Version",
        "update_dialog_no_notes": "<i>No detailed release notes provided for this version.</i>",
    }
}


class LocalizationManager:
    _instance: Optional["LocalizationManager"] = None

    def __new__(cls) -> "LocalizationManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mode = "auto"  # "auto", "tr", "en"
            cls._instance._listeners: list[Callable[[str], None]] = []
            cls._instance._load_config()
        return cls._instance

    @property
    def mode(self) -> str:
        """Configured mode: 'auto', 'tr', or 'en'."""
        return self._mode

    @property
    def current_language(self) -> str:
        """Active language code: 'tr' or 'en'."""
        if self._mode == "auto":
            return detect_system_language()
        return self._mode

    def _load_config(self) -> None:
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._mode = data.get("language", "auto")
                    if self._mode not in ("auto", "tr", "en"):
                        self._mode = "auto"
        except Exception:
            self._mode = "auto"

    def _save_config(self) -> None:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"language": self._mode}, f, indent=2)
        except Exception:
            pass

    def set_mode(self, mode: str) -> None:
        if mode not in ("auto", "tr", "en"):
            mode = "auto"
        if self._mode != mode:
            self._mode = mode
            self._save_config()
            for listener in list(self._listeners):
                try:
                    listener(self.current_language)
                except Exception:
                    pass

    def toggle_language(self) -> str:
        """Cycle between Auto -> EN -> TR -> Auto."""
        cur_lang = self.current_language
        if self._mode == "auto":
            # If auto currently picked tr, switch to explicit en; if en, switch to explicit tr
            new_mode = "en" if cur_lang == "tr" else "tr"
        elif self._mode == "en":
            new_mode = "tr"
        elif self._mode == "tr":
            new_mode = "auto"
        else:
            new_mode = "auto"

        self.set_mode(new_mode)
        return self.current_language

    def get_toast_message(self) -> str:
        cur = self.current_language.upper()
        if self._mode == "auto":
            return self.get("toast_lang_auto").format(cur)
        elif self._mode == "tr":
            return self.get("toast_lang_tr")
        else:
            return self.get("toast_lang_en")

    def add_listener(self, callback: Callable[[str], None]) -> None:
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def get(self, key: str, default: str = "") -> str:
        lang = self.current_language
        return STRINGS.get(lang, {}).get(key, STRINGS["tr"].get(key, default or key))


_loc = LocalizationManager()


def loc(key: str, default: str = "") -> str:
    """Get localized text for the active language."""
    return _loc.get(key, default)


def get_localization() -> LocalizationManager:
    """Get the singleton localization manager."""
    return _loc
