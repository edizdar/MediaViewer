import sys
import shutil
import subprocess
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from app import __version__

def build_windows():
    print("\n" + "=" * 60)
    print(f"[WINDOWS] MediaViewer v{__version__} derleniyor...")
    print("=" * 60)

    spec_file = ROOT_DIR / "MediaViewer.spec"
    if not spec_file.exists():
        print(f"[HATA] {spec_file} bulunamadı!")
        return False

    cmd = [sys.executable, "-m", "PyInstaller", "--clean", str(spec_file)]
    res = subprocess.run(cmd, cwd=str(ROOT_DIR))
    if res.returncode != 0:
        print("[HATA] Windows derlemesi başarısız oldu!")
        return False

    built_exe = ROOT_DIR / "dist" / "MediaViewer.exe"
    if not built_exe.exists():
        print(f"[HATA] {built_exe} bulunamadı!")
        return False

    # 1. Ana sabit isim: MediaViewer.exe
    target_fixed = ROOT_DIR / "MediaViewer.exe"
    shutil.copy2(built_exe, target_fixed)

    # 2. Sürüm numaralı dosya: MediaViewer_vX.X.X.exe
    target_versioned = ROOT_DIR / f"MediaViewer_v{__version__}.exe"
    shutil.copy2(built_exe, target_versioned)

    # 3. versions/ klasörüne de yedek kopya
    versions_dir = ROOT_DIR / "versions"
    versions_dir.mkdir(exist_ok=True)
    shutil.copy2(built_exe, versions_dir / f"MediaViewer_v{__version__}.exe")

    size_mb = target_fixed.stat().st_size / (1024 * 1024)
    print(f"\n[OK] Windows Derlemesi Tamamlandı ({size_mb:.2f} MB)")
    print(f" -> {target_fixed.name}")
    print(f" -> {target_versioned.name}")
    return True

def build_android():
    print("\n" + "=" * 60)
    print(f"[ANDROID] MediaViewer v{__version__} APK derleniyor...")
    print("=" * 60)

    android_dir = ROOT_DIR / "android"
    gradlew_bat = android_dir / "gradlew.bat"
    if not gradlew_bat.exists():
        print(f"[HATA] {gradlew_bat} bulunamadı!")
        return False

    # Sync version in android/app/build.gradle.kts if needed
    build_gradle = android_dir / "app" / "build.gradle.kts"
    if build_gradle.exists():
        content = build_gradle.read_text(encoding="utf-8")
        import re
        content_updated = re.sub(r'versionName\s*=\s*"[^"]*"', f'versionName = "{__version__}"', content)
        if content_updated != content:
            build_gradle.write_text(content_updated, encoding="utf-8")
            print(f"[BİLGİ] Android versionName '{__version__}' olarak güncellendi.")

    cmd = ["cmd.exe", "/c", str(gradlew_bat), "assembleDebug"]
    res = subprocess.run(cmd, cwd=str(android_dir))
    if res.returncode != 0:
        print("[HATA] Android derlemesi başarısız oldu!")
        return False

    built_apk = android_dir / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    if not built_apk.exists():
        print(f"[HATA] {built_apk} bulunamadı!")
        return False

    # 1. Ana sabit isim: MediaViewer.apk
    target_apk_fixed = ROOT_DIR / "MediaViewer.apk"
    shutil.copy2(built_apk, target_apk_fixed)

    # 2. Sürüm numaralı dosya: MediaViewer_vX.X.X.apk
    target_apk_versioned = ROOT_DIR / f"MediaViewer_v{__version__}.apk"
    shutil.copy2(built_apk, target_apk_versioned)

    # 3. android/ klasörüne de kopya
    shutil.copy2(built_apk, android_dir / f"MediaViewer_v{__version__}.apk")
    shutil.copy2(built_apk, android_dir / "MediaViewer.apk")

    size_mb = target_apk_fixed.stat().st_size / (1024 * 1024)
    print(f"\n[OK] Android Derlemesi Tamamlandı ({size_mb:.2f} MB)")
    print(f" -> {target_apk_fixed.name}")
    print(f" -> {target_apk_versioned.name}")
    return True

def main():
    args = sys.argv[1:]
    do_all = "--all" in args or "-a" in args
    do_android = "--android" in args or do_all
    do_win = "--windows" in args or not do_android or do_all

    success_win = True
    success_android = True

    if do_win:
        success_win = build_windows()

    if do_android:
        success_android = build_android()

    print("\n" + "=" * 60)
    if success_win and success_android:
        print(f"BÜTÜN İŞLEMLER BAŞARIYLA TAMAMLANDI! (Sürüm: v{__version__})")
        print(f"Dosyalar {ROOT_DIR} dizininde hazır:")
        if do_win:
            print(f" - MediaViewer.exe")
            print(f" - MediaViewer_v{__version__}.exe")
        if do_android:
            print(f" - MediaViewer.apk")
            print(f" - MediaViewer_v{__version__}.apk")
    else:
        print("BİR VEYA DAHA FAZLA DERLEME HATA VERDİ!")
    print("=" * 60)

if __name__ == "__main__":
    main()
