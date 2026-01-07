# main.py (FULL FIXED) — Linux-only + title ellipsis + i18n + audio quality dropdown FIX
from __future__ import annotations

import os
import re
import shutil
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QApplication, QMessageBox, QListWidgetItem, QListWidget

import yt_dlp
from ui import MediaDownloaderUI


# ----------------------------
# Host / deps (LINUX ONLY)
# ----------------------------

@dataclass(frozen=True)
class HostInfo:
    pkg: str  # pacman | apt | dnf | zypper | apk | unknown


def detect_host() -> HostInfo:
    if shutil.which("pacman"):
        return HostInfo("pacman")
    if shutil.which("apt"):
        return HostInfo("apt")
    if shutil.which("dnf"):
        return HostInfo("dnf")
    if shutil.which("zypper"):
        return HostInfo("zypper")
    if shutil.which("apk"):
        return HostInfo("apk")
    return HostInfo("unknown")


def which_ffmpeg() -> Optional[str]:
    return shutil.which("ffmpeg")


def linux_install_hint(pkg_mgr: str) -> str:
    return {
        "pacman": "sudo pacman -S --needed ffmpeg",
        "apt": "sudo apt update && sudo apt install -y ffmpeg",
        "dnf": "sudo dnf install -y ffmpeg",
        "zypper": "sudo zypper install -y ffmpeg",
        "apk": "sudo apk add ffmpeg",
    }.get(pkg_mgr, "ffmpeg kur (paket yöneticin bilinmiyor).")


def human_mb(n: Optional[int]) -> str:
    if not n:
        return "0 MB"
    return f"{n/(1024*1024):.1f} MB"


def safe_percent(p: str) -> int:
    s = (p or "").strip()
    s = re.sub(r"\x1b\[[0-9;]*m", "", s)  # ANSI escape temizle
    s = s.replace("%", "").strip()
    try:
        v = int(float(s))
    except Exception:
        v = 0
    return max(0, min(100, v))


def pct_from_bytes(done_b: int, total_b: int) -> Optional[int]:
    if not total_b or total_b <= 0:
        return None
    try:
        v = int((done_b / total_b) * 100)
        return max(0, min(100, v))
    except Exception:
        return None


def elide(text: str, max_chars: int = 70) -> str:
    s = (text or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


# ----------------------------
# i18n
# ----------------------------

def norm_lang(code: str) -> str:
    code = (code or "en").lower()
    return code.split("_")[0].split("-")[0][:2]


TR_BASE = {
    "title_error": "Hata",
    "title_warn": "Uyarı",
    "title_ok": "Tamam",
    "title_deps": "Gereksinimler",

    "ready": "Hazır",
    "analyzing": "Analiz ediliyor...",
    "found": "{n} video bulundu",
    "downloading": "İndiriliyor…",
    "stopping": "Durduruluyor...",
    "converting": "Dönüştürülüyor...",

    "btn_start": "İndirmeye Başla",
    "btn_stop": "Durdur",

    "no_url": "Lütfen bir URL girin!",
    "select_one": "Lütfen en az bir video seçin!",
    "select_folder": "Lütfen indirme klasörü seçin!",

    "ffmpeg_missing": "FFmpeg bulunamadı.",
    "install_hint": "Kurulum komutu:\n{cmd}",
    "install_now": "Şimdi kur/indir",
    "later": "Sonra",

    "done": "İndirme tamamlandı.",
    "dl_error": "İndirme hatası:\n{msg}",
    "an_error": "Bağlantı analiz edilemedi:\n{msg}",

    "format_lbl": "Format:",
    "quality_lbl": "Kalite:",
    "audio_quality_lbl": "Ses Kalitesi:",
    "playlist_lbl": "Playlist / Videolar",
    "select_all": "Hepsini Seç",
    "check_btn": "Kontrol",
    "folder_btn": "Klasör Seç",
    "lang_lbl": "Dil:",
    "url_ph": "YouTube, Instagram, TikTok, X/Twitter vb. bağlantı yapıştır...",
    "search_ph": "Listede ara...",
    "folder_lbl": "Klasör: {path}",
}

T: Dict[str, Dict[str, str]] = {
    "tr": TR_BASE,
    "en": {
        "title_error": "Error",
        "title_warn": "Warning",
        "title_ok": "OK",
        "title_deps": "Requirements",
        "ready": "Ready",
        "analyzing": "Analyzing...",
        "found": "Found {n} videos",
        "downloading": "Downloading…",
        "stopping": "Stopping...",
        "converting": "Converting...",
        "btn_start": "Start Download",
        "btn_stop": "Stop",
        "no_url": "Please enter a URL!",
        "select_one": "Select at least one video!",
        "select_folder": "Please select a download folder!",
        "ffmpeg_missing": "FFmpeg not found.",
        "install_hint": "Install command:\n{cmd}",
        "install_now": "Install/Download now",
        "later": "Later",
        "done": "Download finished.",
        "dl_error": "Download error:\n{msg}",
        "an_error": "Could not analyze link:\n{msg}",
        "format_lbl": "Format:",
        "quality_lbl": "Quality:",
        "audio_quality_lbl": "Audio Quality:",
        "playlist_lbl": "Playlist / Videos",
        "select_all": "Select All",
        "check_btn": "Check",
        "folder_btn": "Choose Folder",
        "lang_lbl": "Language:",
        "url_ph": "Paste a link (YouTube, Instagram, TikTok, X/Twitter etc.)...",
        "search_ph": "Search in list...",
        "folder_lbl": "Folder: {path}",
    },
    "de": {
        "title_error": "Fehler",
        "title_warn": "Warnung",
        "title_ok": "OK",
        "title_deps": "Voraussetzungen",
        "ready": "Bereit",
        "analyzing": "Analysiere...",
        "found": "{n} Videos gefunden",
        "downloading": "Wird heruntergeladen…",
        "stopping": "Wird angehalten...",
        "converting": "Wird konvertiert...",
        "btn_start": "Download starten",
        "btn_stop": "Stopp",
        "no_url": "Bitte eine URL eingeben!",
        "select_one": "Bitte mindestens ein Video auswählen!",
        "select_folder": "Bitte einen Download-Ordner wählen!",
        "ffmpeg_missing": "FFmpeg nicht gefunden.",
        "install_hint": "Installationsbefehl:\n{cmd}",
        "install_now": "Jetzt installieren",
        "later": "Später",
        "done": "Download abgeschlossen.",
        "dl_error": "Download-Fehler:\n{msg}",
        "an_error": "Link konnte nicht analysiert werden:\n{msg}",
        "format_lbl": "Format:",
        "quality_lbl": "Qualität:",
        "audio_quality_lbl": "Audioqualität:",
        "playlist_lbl": "Playlist / Videos",
        "select_all": "Alle auswählen",
        "check_btn": "Prüfen",
        "folder_btn": "Ordner wählen",
        "lang_lbl": "Sprache:",
        "url_ph": "Link einfügen (YouTube, Instagram, TikTok, X usw.)...",
        "search_ph": "In Liste suchen...",
        "folder_lbl": "Ordner: {path}",
    },
    "es": {
        "title_error": "Error",
        "title_warn": "Aviso",
        "title_ok": "OK",
        "title_deps": "Requisitos",
        "ready": "Listo",
        "analyzing": "Analizando...",
        "found": "Se encontraron {n} vídeos",
        "downloading": "Descargando…",
        "stopping": "Deteniendo...",
        "converting": "Convirtiendo...",
        "btn_start": "Iniciar descarga",
        "btn_stop": "Detener",
        "no_url": "¡Introduce una URL!",
        "select_one": "¡Selecciona al menos un vídeo!",
        "select_folder": "¡Selecciona una carpeta de descarga!",
        "ffmpeg_missing": "No se encontró FFmpeg.",
        "install_hint": "Comando de instalación:\n{cmd}",
        "install_now": "Instalar/descargar ahora",
        "later": "Más tarde",
        "done": "Descarga finalizada.",
        "dl_error": "Error de descarga:\n{msg}",
        "an_error": "No se pudo analizar el enlace:\n{msg}",
        "format_lbl": "Formato:",
        "quality_lbl": "Calidad:",
        "audio_quality_lbl": "Calidad de audio:",
        "playlist_lbl": "Lista / Vídeos",
        "select_all": "Seleccionar todo",
        "check_btn": "Comprobar",
        "folder_btn": "Elegir carpeta",
        "lang_lbl": "Idioma:",
        "url_ph": "Pega un enlace (YouTube, Instagram, TikTok, X, etc.)...",
        "search_ph": "Buscar en la lista...",
        "folder_lbl": "Carpeta: {path}",
    },
    "fr": {
        "title_error": "Erreur",
        "title_warn": "Avertissement",
        "title_ok": "OK",
        "title_deps": "Prérequis",
        "ready": "Prêt",
        "analyzing": "Analyse...",
        "found": "{n} vidéos trouvées",
        "downloading": "Téléchargement…",
        "stopping": "Arrêt...",
        "converting": "Conversion...",
        "btn_start": "Démarrer",
        "btn_stop": "Arrêter",
        "no_url": "Entrez une URL !",
        "select_one": "Sélectionnez au moins une vidéo !",
        "select_folder": "Choisissez un dossier de téléchargement !",
        "ffmpeg_missing": "FFmpeg introuvable.",
        "install_hint": "Commande d’installation :\n{cmd}",
        "install_now": "Installer / télécharger",
        "later": "Plus tard",
        "done": "Téléchargement terminé.",
        "dl_error": "Erreur de téléchargement :\n{msg}",
        "an_error": "Impossible d’analyser le lien :\n{msg}",
        "format_lbl": "Format :",
        "quality_lbl": "Qualité :",
        "audio_quality_lbl": "Qualité audio :",
        "playlist_lbl": "Playlist / Vidéos",
        "select_all": "Tout sélectionner",
        "check_btn": "Vérifier",
        "folder_btn": "Choisir dossier",
        "lang_lbl": "Langue :",
        "url_ph": "Collez un lien (YouTube, Instagram, TikTok, X, etc.)...",
        "search_ph": "Rechercher dans la liste...",
        "folder_lbl": "Dossier : {path}",
    },
    "it": {
        "title_error": "Errore",
        "title_warn": "Avviso",
        "title_ok": "OK",
        "title_deps": "Requisiti",
        "ready": "Pronto",
        "analyzing": "Analisi...",
        "found": "Trovati {n} video",
        "downloading": "Download…",
        "stopping": "Interruzione...",
        "converting": "Conversione...",
        "btn_start": "Avvia download",
        "btn_stop": "Stop",
        "no_url": "Inserisci un URL!",
        "select_one": "Seleziona almeno un video!",
        "select_folder": "Seleziona una cartella di download!",
        "ffmpeg_missing": "FFmpeg non trovato.",
        "install_hint": "Comando di installazione:\n{cmd}",
        "install_now": "Installa / scarica",
        "later": "Più tardi",
        "done": "Download completato.",
        "dl_error": "Errore di download:\n{msg}",
        "an_error": "Impossibile analizzare il link:\n{msg}",
        "format_lbl": "Formato:",
        "quality_lbl": "Qualità:",
        "audio_quality_lbl": "Qualità audio:",
        "playlist_lbl": "Playlist / Video",
        "select_all": "Seleziona tutto",
        "check_btn": "Controlla",
        "folder_btn": "Scegli cartella",
        "lang_lbl": "Lingua:",
        "url_ph": "Incolla un link (YouTube, Instagram, TikTok, X, ecc.)...",
        "search_ph": "Cerca nella lista...",
        "folder_lbl": "Cartella: {path}",
    },
    "ja": {
        "title_error": "エラー",
        "title_warn": "警告",
        "title_ok": "OK",
        "title_deps": "要件",
        "ready": "準備完了",
        "analyzing": "解析中...",
        "found": "{n} 件の動画",
        "downloading": "ダウンロード中…",
        "stopping": "停止中...",
        "converting": "変換中...",
        "btn_start": "ダウンロード開始",
        "btn_stop": "停止",
        "no_url": "URLを入力して！",
        "select_one": "少なくとも1つ選んで！",
        "select_folder": "保存フォルダを選んで！",
        "ffmpeg_missing": "FFmpeg が見つかりません。",
        "install_hint": "インストール:\n{cmd}",
        "install_now": "今すぐ導入",
        "later": "後で",
        "done": "完了しました。",
        "dl_error": "エラー:\n{msg}",
        "an_error": "リンクを解析できません:\n{msg}",
        "format_lbl": "形式:",
        "quality_lbl": "品質:",
        "audio_quality_lbl": "音質:",
        "playlist_lbl": "プレイリスト / 動画",
        "select_all": "すべて選択",
        "check_btn": "確認",
        "folder_btn": "フォルダ選択",
        "lang_lbl": "言語:",
        "url_ph": "リンクを貼り付け（YouTube/Instagram/TikTok/Xなど）...",
        "search_ph": "リスト内検索...",
        "folder_lbl": "フォルダ: {path}",
    },
    "zh": {
        "title_error": "错误",
        "title_warn": "警告",
        "title_ok": "好",
        "title_deps": "依赖",
        "ready": "就绪",
        "analyzing": "正在解析...",
        "found": "找到 {n} 个视频",
        "downloading": "下载中…",
        "stopping": "正在停止...",
        "converting": "转换中...",
        "btn_start": "开始下载",
        "btn_stop": "停止",
        "no_url": "请输入 URL！",
        "select_one": "请至少选择一个视频！",
        "select_folder": "请选择下载文件夹！",
        "ffmpeg_missing": "未找到 FFmpeg。",
        "install_hint": "安装命令：\n{cmd}",
        "install_now": "立即安装/下载",
        "later": "稍后",
        "done": "下载完成。",
        "dl_error": "下载错误:\n{msg}",
        "an_error": "无法解析链接:\n{msg}",
        "format_lbl": "格式:",
        "quality_lbl": "清晰度:",
        "audio_quality_lbl": "音频质量:",
        "playlist_lbl": "播放列表 / 视频",
        "select_all": "全选",
        "check_btn": "检查",
        "folder_btn": "选择文件夹",
        "lang_lbl": "语言:",
        "url_ph": "粘贴链接（YouTube/Instagram/TikTok/X 等）...",
        "search_ph": "列表内搜索...",
        "folder_lbl": "文件夹: {path}",
    },
    "ru": {
        "title_error": "Ошибка",
        "title_warn": "Предупреждение",
        "title_ok": "ОК",
        "title_deps": "Требования",
        "ready": "Готово",
        "analyzing": "Анализ...",
        "found": "Найдено видео: {n}",
        "downloading": "Загрузка…",
        "stopping": "Остановка...",
        "converting": "Конвертация...",
        "btn_start": "Начать загрузку",
        "btn_stop": "Стоп",
        "no_url": "Введите URL!",
        "select_one": "Выберите хотя бы одно видео!",
        "select_folder": "Выберите папку для загрузки!",
        "ffmpeg_missing": "FFmpeg не найден.",
        "install_hint": "Команда установки:\n{cmd}",
        "install_now": "Установить/скачать",
        "later": "Позже",
        "done": "Загрузка завершена.",
        "dl_error": "Ошибка загрузки:\n{msg}",
        "an_error": "Не удалось проанализировать ссылку:\n{msg}",
        "format_lbl": "Формат:",
        "quality_lbl": "Качество:",
        "audio_quality_lbl": "Качество аудио:",
        "playlist_lbl": "Плейлист / Видео",
        "select_all": "Выбрать все",
        "check_btn": "Проверить",
        "folder_btn": "Выбрать папку",
        "lang_lbl": "Язык:",
        "url_ph": "Вставьте ссылку (YouTube, Instagram, TikTok, X и т. д.)...",
        "search_ph": "Поиск по списку...",
        "folder_lbl": "Папка: {path}",
    },
}

def tr(lang: str, key: str, **kwargs) -> str:
    lang = norm_lang(lang)
    if lang in T and key in T[lang]:
        return T[lang][key].format(**kwargs)
    if key in TR_BASE:
        return TR_BASE[key].format(**kwargs)
    return (T.get("en", {}).get(key) or key).format(**kwargs)


# ----------------------------
# Workers
# ----------------------------

class AnalyzeWorker(QObject):
    sig_entries = pyqtSignal(list)
    sig_error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": "in_playlist",
                "skip_download": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)

            if isinstance(info, dict) and info.get("entries"):
                entries = [e for e in info["entries"] if e]
            else:
                entries = [info]

            for e in entries:
                if isinstance(e, dict) and not e.get("webpage_url"):
                    u = e.get("url")
                    if isinstance(u, str) and u.startswith("http"):
                        e["webpage_url"] = u

            self.sig_entries.emit(entries)
        except Exception as ex:
            self.sig_error.emit(str(ex))


class DownloadWorker(QObject):
    sig_progress = pyqtSignal(int, str)  # percent: -1 => indeterminate
    sig_done = pyqtSignal()
    sig_error = pyqtSignal(str)

    def __init__(
        self,
        urls: List[str],
        out_dir: str,
        fmt_text: str,
        q_text: str,
        ffmpeg_bin: Optional[str],
        lang: str,
    ):
        super().__init__()
        self.urls = urls
        self.out_dir = out_dir
        self.fmt_text = fmt_text
        self.q_text = q_text
        self.ffmpeg_bin = ffmpeg_bin
        self.lang = lang
        self._stop = False

    def stop(self):
        self._stop = True

    def _build(self) -> Tuple[str, List[dict], Dict[str, Any]]:
        post: List[dict] = []
        extra: Dict[str, Any] = {}

        t = (self.fmt_text or "").upper().strip()
        q = (self.q_text or "").strip()

        # ---- AUDIO ----
        if t in ("MP3", "WAV", "FLAC"):
            fmt = "bestaudio/best"

            if t == "MP3":
                # "320 kbps" -> "320"
                m = re.search(r"(\d+)", q)
                br = m.group(1) if m else "320"
                post = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": br,  # yt-dlp: 0(best) .. 9(worst) OR bitrate string; pratikte "320" çalışıyor
                }]
            elif t == "WAV":
                post = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "0",
                }]
            else:  # FLAC
                post = [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "flac",
                    "preferredquality": "0",
                }]

            return fmt, post, extra

        # ---- VIDEO ----
        if "2160" in q:
            fmt = "bestvideo[height<=2160]+bestaudio/best"
        elif "1440" in q:
            fmt = "bestvideo[height<=1440]+bestaudio/best"
        elif "1080" in q:
            fmt = "bestvideo[height<=1080]+bestaudio/best"
        elif "720" in q:
            fmt = "bestvideo[height<=720]+bestaudio/best"
        elif "480" in q:
            fmt = "bestvideo[height<=480]+bestaudio/best"
        elif "360" in q:
            fmt = "bestvideo[height<=360]+bestaudio/best"
        else:
            fmt = "bestvideo+bestaudio/best"

        if t == "MP4":
            extra["merge_output_format"] = "mp4"
        elif t == "WEBM":
            extra["merge_output_format"] = "webm"

        return fmt, post, extra

    def run(self):
        try:
            fmt, post, extra = self._build()

            def hook(d: Dict[str, Any]):
                if self._stop:
                    raise Exception("USER_STOP")

                st = d.get("status")

                if st == "downloading":
                    done_b = int(d.get("downloaded_bytes") or 0)
                    total_b = int(d.get("total_bytes") or d.get("total_bytes_estimate") or 0)

                    pct = None
                    if d.get("_percent_str"):
                        pct = safe_percent(d.get("_percent_str", "0"))

                    if pct is None:
                        pct = pct_from_bytes(done_b, total_b)

                    if pct is None:
                        self.sig_progress.emit(-1, f"{human_mb(done_b)} / ? | ETA: ?")
                        return

                    speed = d.get("speed")
                    eta = d.get("eta")
                    speed_s = f"{(speed/(1024*1024)):.2f} MB/s" if speed else "?"
                    eta_s = f"{eta}s" if isinstance(eta, int) else "?"
                    self.sig_progress.emit(
                        pct,
                        f"{human_mb(done_b)} / {human_mb(total_b)} | {speed_s} | ETA: {eta_s}",
                    )

                elif st == "finished":
                    self.sig_progress.emit(100, tr(self.lang, "converting"))

            ydl_opts: Dict[str, Any] = {
                "format": fmt,
                "outtmpl": os.path.join(self.out_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [hook],
                "postprocessors": post,
                "noplaylist": False,
                "quiet": True,
                "no_warnings": True,
                "nocolor": True,
            }
            ydl_opts.update(extra)
            if self.ffmpeg_bin:
                ydl_opts["ffmpeg_location"] = self.ffmpeg_bin

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download(self.urls)

            self.sig_done.emit()
        except Exception as ex:
            if "USER_STOP" in str(ex):
                self.sig_error.emit("USER_STOP")
            else:
                self.sig_error.emit(str(ex))


# ----------------------------
# App
# ----------------------------

class MediaDownloader(MediaDownloaderUI):
    def __init__(self):
        super().__init__()

        self.host = detect_host()
        self.ffmpeg_bin_dir: Optional[str] = None

        self.is_downloading = False
        self.an_thread: Optional[QThread] = None
        self.an_worker: Optional[AnalyzeWorker] = None
        self.dl_thread: Optional[QThread] = None
        self.dl_worker: Optional[DownloadWorker] = None

        # ---- Quality options (video+audio) ----
        self._video_qualities = ["2160p", "1440p", "1080p", "720p", "480p", "360p"]
        self._mp3_qualities = ["320 kbps", "256 kbps", "192 kbps", "160 kbps", "128 kbps", "96 kbps"]
        self._flac_qualities = ["Lossless (FLAC)"]
        self._wav_qualities = ["PCM (WAV)"]

        # ---- LIST UI FIXES ----
        self.playlist_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.playlist_list.setIconSize(QSize(96, 96))
        self.playlist_list.itemClicked.connect(self.on_item_clicked_toggle_check)

        self.lang = norm_lang(str(self.lang_combo.currentData() or "tr"))

        if self.download_folder == "İndirilenler":
            self.download_folder = str(Path.home() / "Downloads")
            Path(self.download_folder).mkdir(parents=True, exist_ok=True)

        # Signals
        self.check_button.clicked.connect(self.analyze_link)
        self.url_input.returnPressed.connect(self.analyze_link)
        self.download_button.clicked.connect(self.start_or_stop_download)
        self.select_all_cb.stateChanged.connect(self.toggle_select_all)
        self.playlist_search.textChanged.connect(self.filter_playlist)
        self.folder_selected.connect(self.update_save_path)
        self.format_combo.currentIndexChanged.connect(self.update_quality_options)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)

        self.apply_language_ui(force_info_ready=True)
        self.update_quality_options()
        self.startup_check_requirements()

    def on_item_clicked_toggle_check(self, item: QListWidgetItem):
        cur = item.checkState()
        item.setCheckState(
            Qt.CheckState.Unchecked if cur == Qt.CheckState.Checked else Qt.CheckState.Checked
        )

    def on_language_changed(self):
        self.lang = norm_lang(str(self.lang_combo.currentData() or "tr"))
        self.apply_language_ui(force_info_ready=False)
        self.update_quality_options()  # dil değişince label + seçenekler tekrar

    def apply_language_ui(self, force_info_ready: bool = False):
        self.url_input.setPlaceholderText(tr(self.lang, "url_ph"))
        self.playlist_search.setPlaceholderText(tr(self.lang, "search_ph"))
        self.select_all_cb.setText(tr(self.lang, "select_all"))

        self.check_button.setText(tr(self.lang, "check_btn"))
        self.folder_button.setText(tr(self.lang, "folder_btn"))
        self.download_button.setText(
            tr(self.lang, "btn_stop") if self.is_downloading else tr(self.lang, "btn_start")
        )

        self.format_label.setText(tr(self.lang, "format_lbl"))
        # quality label update_quality_options içinde format'a göre set edilecek
        self.playlist_label.setText(tr(self.lang, "playlist_lbl"))
        self.lang_label.setText(tr(self.lang, "lang_lbl"))

        self.folder_label.setText(tr(self.lang, "folder_lbl", path=self.download_folder))

        if force_info_ready:
            self.info_label.setText(tr(self.lang, "ready"))
        else:
            current = (self.info_label.text() or "").strip()
            ready_set = {v.get("ready", "") for v in T.values() if isinstance(v, dict)}
            ready_set.add(TR_BASE.get("ready", ""))
            if current in ready_set:
                self.info_label.setText(tr(self.lang, "ready"))

    def startup_check_requirements(self):
        if which_ffmpeg() or self.ffmpeg_bin_dir:
            return

        cmd = linux_install_hint(self.host.pkg)

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(tr(self.lang, "title_deps"))
        box.setText(f"{tr(self.lang,'ffmpeg_missing')}\n\n{tr(self.lang,'install_hint', cmd=cmd)}")
        btn_install = box.addButton(tr(self.lang, "install_now"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(tr(self.lang, "later"), QMessageBox.ButtonRole.RejectRole)
        box.exec()

        if box.clickedButton() == btn_install:
            QApplication.clipboard().setText(cmd)

    def update_save_path(self, path: str):
        self.download_folder = path
        self.folder_label.setText(tr(self.lang, "folder_lbl", path=path))

    def update_quality_options(self):
        fmt = (self.format_combo.currentText() or "").upper().strip()

        # preserve current choice when possible
        prev = self.quality_combo.currentText() if self.quality_combo.count() else ""

        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()

        if fmt in ("MP4", "WEBM"):
            self.quality_label.setText(tr(self.lang, "quality_lbl"))
            self.quality_combo.addItems(self._video_qualities)
            self.quality_combo.setEnabled(True)
            # default 1080p
            idx = self.quality_combo.findText(prev) if prev else self.quality_combo.findText("1080p")
            self.quality_combo.setCurrentIndex(idx if idx >= 0 else self.quality_combo.findText("1080p"))

        elif fmt == "MP3":
            self.quality_label.setText(tr(self.lang, "audio_quality_lbl"))
            self.quality_combo.addItems(self._mp3_qualities)
            self.quality_combo.setEnabled(True)
            idx = self.quality_combo.findText(prev) if prev else self.quality_combo.findText("320 kbps")
            self.quality_combo.setCurrentIndex(idx if idx >= 0 else self.quality_combo.findText("320 kbps"))

        elif fmt == "FLAC":
            self.quality_label.setText(tr(self.lang, "audio_quality_lbl"))
            self.quality_combo.addItems(self._flac_qualities)
            self.quality_combo.setEnabled(True)
            self.quality_combo.setCurrentIndex(0)

        elif fmt == "WAV":
            self.quality_label.setText(tr(self.lang, "audio_quality_lbl"))
            self.quality_combo.addItems(self._wav_qualities)
            self.quality_combo.setEnabled(True)
            self.quality_combo.setCurrentIndex(0)

        else:
            # fallback
            self.quality_label.setText(tr(self.lang, "quality_lbl"))
            self.quality_combo.addItems(self._video_qualities)
            self.quality_combo.setEnabled(True)
            self.quality_combo.setCurrentIndex(self.quality_combo.findText("1080p"))

        self.quality_combo.blockSignals(False)

    def toggle_select_all(self, state: int):
        checked = (state == Qt.CheckState.Checked.value)
        for i in range(self.playlist_list.count()):
            self.playlist_list.item(i).setCheckState(
                Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )

    def filter_playlist(self, text: str):
        text = (text or "").lower().strip()
        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            item.setHidden(text not in item.text().lower())

    def analyze_link(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, tr(self.lang, "title_warn"), tr(self.lang, "no_url"))
            return

        self.info_label.setText(tr(self.lang, "analyzing"))
        self.playlist_list.clear()

        self.an_thread = QThread(self)
        self.an_worker = AnalyzeWorker(url)
        self.an_worker.moveToThread(self.an_thread)

        self.an_thread.started.connect(self.an_worker.run)
        self.an_worker.sig_entries.connect(self.on_entries_ready, Qt.ConnectionType.QueuedConnection)
        self.an_worker.sig_error.connect(self.on_analyze_error, Qt.ConnectionType.QueuedConnection)

        self.an_worker.sig_entries.connect(self.an_thread.quit)
        self.an_worker.sig_error.connect(self.an_thread.quit)
        self.an_thread.finished.connect(self.an_worker.deleteLater)
        self.an_thread.finished.connect(self.an_thread.deleteLater)

        self.an_thread.start()

    def on_analyze_error(self, msg: str):
        QMessageBox.critical(self, tr(self.lang, "title_error"), tr(self.lang, "an_error", msg=msg))
        self.info_label.setText(tr(self.lang, "ready"))

    def on_entries_ready(self, entries: List[Dict[str, Any]]):
        self.playlist_list.clear()

        for e in entries:
            if not isinstance(e, dict):
                continue

            title = elide(e.get("title") or "Unknown", 70)
            dur = e.get("duration_string") or e.get("duration") or "?"
            if isinstance(dur, (int, float)):
                dur = f"{int(dur)}s"

            it = QListWidgetItem(f"{title} [{dur}]")
            it.setData(Qt.ItemDataRole.UserRole, e)

            it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            it.setCheckState(Qt.CheckState.Checked)

            it.setSizeHint(QSize(0, 106))

            thumb = e.get("thumbnail")
            if thumb:
                try:
                    data = urllib.request.urlopen(thumb, timeout=4).read()
                    pix = QPixmap()
                    pix.loadFromData(data)
                    if not pix.isNull():
                        scaled = pix.scaled(
                            96, 96,
                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                        it.setIcon(QIcon(scaled))
                except Exception:
                    pass

            self.playlist_list.addItem(it)

        self.select_all_cb.setChecked(True)
        self.info_label.setText(tr(self.lang, "found", n=len(entries)))

    def selected_urls(self) -> List[str]:
        urls: List[str] = []
        base_url = self.url_input.text().strip()

        for i in range(self.playlist_list.count()):
            item = self.playlist_list.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                continue

            e = item.data(Qt.ItemDataRole.UserRole) or {}
            if not isinstance(e, dict):
                continue

            u = e.get("webpage_url")
            if isinstance(u, str) and u.startswith("http"):
                urls.append(u)
                continue

            u2 = e.get("url")
            if isinstance(u2, str):
                if u2.startswith("http"):
                    urls.append(u2)
                    continue
                if re.fullmatch(r"[A-Za-z0-9_-]{8,}", u2):
                    urls.append(f"https://www.youtube.com/watch?v={u2}")
                    continue

            urls.append(base_url)

        return urls

    def start_or_stop_download(self):
        if self.is_downloading:
            self.is_downloading = False
            if self.dl_worker:
                self.dl_worker.stop()
            self.info_label.setText(tr(self.lang, "stopping"))
            self.download_button.setText(tr(self.lang, "btn_start"))
            return

        if self.playlist_list.count() == 0:
            self.analyze_link()
            return

        urls = self.selected_urls()
        if not urls:
            QMessageBox.warning(self, tr(self.lang, "title_warn"), tr(self.lang, "select_one"))
            return

        if not self.download_folder or not os.path.isdir(self.download_folder):
            QMessageBox.warning(self, tr(self.lang, "title_warn"), tr(self.lang, "select_folder"))
            return

        if not which_ffmpeg() and not self.ffmpeg_bin_dir:
            self.startup_check_requirements()

        self.is_downloading = True
        self.download_button.setText(tr(self.lang, "btn_stop"))

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.info_label.setText(tr(self.lang, "downloading"))

        self.dl_thread = QThread(self)
        self.dl_worker = DownloadWorker(
            urls=urls,
            out_dir=self.download_folder,
            fmt_text=self.format_combo.currentText(),
            q_text=self.quality_combo.currentText(),
            ffmpeg_bin=self.ffmpeg_bin_dir,
            lang=self.lang,
        )
        self.dl_worker.moveToThread(self.dl_thread)

        self.dl_thread.started.connect(self.dl_worker.run)
        self.dl_worker.sig_progress.connect(self.on_dl_progress, Qt.ConnectionType.QueuedConnection)
        self.dl_worker.sig_done.connect(self.on_dl_done, Qt.ConnectionType.QueuedConnection)
        self.dl_worker.sig_error.connect(self.on_dl_error, Qt.ConnectionType.QueuedConnection)

        self.dl_worker.sig_done.connect(self.dl_thread.quit)
        self.dl_worker.sig_error.connect(self.dl_thread.quit)
        self.dl_thread.finished.connect(self.dl_worker.deleteLater)
        self.dl_thread.finished.connect(self.dl_thread.deleteLater)

        self.dl_thread.start()

    def on_dl_progress(self, percent: int, text: str):
        if percent < 0:
            self.progress_bar.setRange(0, 0)
        else:
            if self.progress_bar.minimum() == 0 and self.progress_bar.maximum() == 0:
                self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(percent)
        self.info_label.setText(text)

    def finish_download_ui(self):
        self.is_downloading = False
        self.download_button.setText(tr(self.lang, "btn_start"))
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.info_label.setText(tr(self.lang, "ready"))
        self.dl_worker = None
        self.dl_thread = None

    def on_dl_done(self):
        QMessageBox.information(self, tr(self.lang, "title_ok"), tr(self.lang, "done"))
        self.finish_download_ui()

    def on_dl_error(self, msg: str):
        if msg == "USER_STOP":
            self.finish_download_ui()
            return
        QMessageBox.critical(self, tr(self.lang, "title_error"), tr(self.lang, "dl_error", msg=msg))
        self.finish_download_ui()


if __name__ == "__main__":
    app = QApplication([])
    app.setStyle("Fusion")
    win = MediaDownloader()
    win.show()
    app.exec()
