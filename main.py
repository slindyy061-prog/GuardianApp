import os
import hashlib
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread
from kivy.core.window import Window

# Try to import Android-specific modules.
# These only exist when running on an actual Android device via Buildozer.
try:
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    ANDROID = True
except ImportError:
    ANDROID = False


# ==========================
# SETTINGS
# ==========================

TRUSTED_NAMES = [
    "termux",
    "whatsapp",
    "telegram",
    "google",
    "chrome",
    "youtube",
    "instagram",
    "facebook",
    "spotify",
    "snapchat",
    "tiktok"
]

SUSPICIOUS_WORDS = [
    "hack",
    "mod",
    "crack",
    "injector",
    "cheat",
    "premium unlocked",
    "free money",
    "bypass",
    "vip hack",
    "unlimited money",
    "generator"
]


# ==========================
# HELPER FUNCTIONS
# ==========================

def sha256_hash(filepath):
    try:
        hash_object = hashlib.sha256()
        with open(filepath, "rb") as file:
            while True:
                chunk = file.read(4096)
                if not chunk:
                    break
                hash_object.update(chunk)
        return hash_object.hexdigest()
    except Exception:
        return None


def format_size(size_bytes):
    mb = size_bytes / (1024 * 1024)
    return round(mb, 2)


# ==========================
# SECURITY SCANNER
# (now sends output to a callback instead of print)
# ==========================

def scan_folder(folder_path, log):

    log("")
    log("GUARDIAN SECURITY SCAN")
    log("=" * 50)
    log(f"Scanning Folder: {folder_path}")
    log("=" * 50)

    if not os.path.exists(folder_path):
        log("Folder not found: " + folder_path)
        return

    total_files = 0
    safe_files = 0
    suspicious_files = []

    for root, dirs, files in os.walk(folder_path):
        for file in files:

            total_files += 1
            filepath = os.path.join(root, file)
            filename = file.lower()

            risk_score = 0
            reasons = []

            # Hidden file check
            if file.startswith("."):
                risk_score += 1
                reasons.append("Hidden file")

            # Suspicious keyword scan
            for word in SUSPICIOUS_WORDS:
                if word in filename:
                    risk_score += 4
                    reasons.append(f"Suspicious keyword found: '{word}'")

            # APK analysis
            extension = os.path.splitext(file)[1].lower()

            if extension == ".apk":
                trusted = False
                for trusted_name in TRUSTED_NAMES:
                    if trusted_name in filename:
                        trusted = True
                        break

                if trusted:
                    reasons.append("Trusted app name")
                else:
                    risk_score += 2
                    reasons.append("Unknown APK")

            # File size check
            try:
                size_mb = format_size(os.path.getsize(filepath))
                if extension == ".apk" and size_mb > 500:
                    risk_score += 2
                    reasons.append("Very large APK file")
            except Exception:
                size_mb = 0

            # Hash
            file_hash = sha256_hash(filepath)

            # Risk level
            if risk_score >= 5:
                risk_level = "HIGH"
            elif risk_score >= 3:
                risk_level = "MEDIUM"
            elif risk_score >= 1:
                risk_level = "LOW"
            else:
                risk_level = "SAFE"

            if risk_score > 0:
                suspicious_files.append({
                    "file": filepath,
                    "risk": risk_level,
                    "reasons": reasons,
                    "hash": file_hash,
                    "size": size_mb
                })
            else:
                safe_files += 1

    # FINAL REPORT
    log("")
    log("Scan Complete")
    log("=" * 50)
    log(f"Total Files: {total_files}")
    log(f"Safe Files: {safe_files}")
    log(f"Findings: {len(suspicious_files)}")

    if total_files > 0:
        score = int((safe_files / total_files) * 100)
    else:
        score = 100

    log(f"Security Score: {score}%")
    log("")
    log("SECURITY REPORT")
    log("=" * 50)

    if suspicious_files:
        for item in suspicious_files:
            log("")
            log("FILE: " + item["file"])
            log("Risk Level: " + item["risk"])
            log(f"Size: {item['size']} MB")

            if item["hash"]:
                log(f"SHA256: {item['hash'][:30]}...")

            log("Reasons:")
            for reason in item["reasons"]:
                log("  - " + reason)
            log("-" * 50)
    else:
        log("No suspicious files found!")

    log("")
    log("Guardian Scan Finished")


# ==========================
# KIVY APP
# ==========================

class GuardianApp(App):

    def build(self):
        Window.clearcolor = (0.04, 0.05, 0.08, 1)

        root = BoxLayout(orientation="vertical", padding=16, spacing=12)

        title = Label(
            text="Guardian Security Scanner",
            font_size="22sp",
            size_hint=(1, 0.1),
            bold=True
        )
        root.add_widget(title)

        self.scan_button = Button(
            text="Start Scan",
            size_hint=(1, 0.1),
            background_color=(0, 0.7, 0.8, 1)
        )
        self.scan_button.bind(on_press=self.start_scan)
        root.add_widget(self.scan_button)

        scroll = ScrollView(size_hint=(1, 0.8))
        self.output_label = Label(
            text="Tap 'Start Scan' to check your Downloads folder.",
            size_hint_y=None,
            text_size=(Window.width - 32, None),
            halign="left",
            valign="top"
        )
        self.output_label.bind(
            texture_size=lambda instance, value: setattr(
                self.output_label, "height", value[1]
            )
        )
        scroll.add_widget(self.output_label)
        root.add_widget(scroll)

        return root

    def start_scan(self, instance):
        self.output_label.text = "Scanning... please wait.\n"
        self.scan_button.disabled = True
        threading.Thread(target=self.run_scan, daemon=True).start()

    def run_scan(self):
        if ANDROID:
            try:
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ])
            except Exception:
                pass

            base = primary_external_storage_path()
            folder = os.path.join(base, "Download")
        else:
            # Desktop testing: scans your normal Downloads folder
            folder = os.path.join(os.path.expanduser("~"), "Downloads")

        # Clear "Scanning..." message before writing results
        self.clear_output()

        scan_folder(folder, self.log)

        self.enable_button()

    @mainthread
    def clear_output(self):
        self.output_label.text = ""

    @mainthread
    def log(self, text):
        self.output_label.text += text + "\n"

    @mainthread
    def enable_button(self):
        self.scan_button.disabled = False


if __name__ == "__main__":
    GuardianApp().run()