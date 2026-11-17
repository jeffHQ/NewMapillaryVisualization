"""
Genera el QR del póster y convierte las fuentes HTML (paper, póster, presentación) a PDF con Chrome/Edge sin interfaz.

Uso (desde deliveries/week15/code):
    pip install -r ../../../requirements.txt
    python build_pdfs.py

Salidas:
    ../poster/qr.svg
    ../FinalPaper.pdf · ../FinalPoster.pdf · ../PresentationFinal.pdf
    y una copia de cada PDF en ../app/files/ (los enlaces de la página del proyecto apuntan allí).

Variable opcional: CHROME_PATH para indicar el ejecutable de Chrome, Edge o Chromium.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import qrcode
import qrcode.image.svg

ROOT = Path(__file__).resolve().parent.parent
APP_URL = "https://jeffhq.github.io/NewMapillaryVisualization/"

JOBS = [
    (ROOT / "paper" / "paper.html", ROOT / "FinalPaper.pdf"),
    (ROOT / "poster" / "poster.html", ROOT / "FinalPoster.pdf"),
    (ROOT / "presentation" / "PresentationFinal.html", ROOT / "PresentationFinal.pdf"),
]


def find_browser():
    cands = [os.environ.get("CHROME_PATH"),
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for c in cands:
        if c and Path(c).exists():
            return c
    sys.exit("No se encontró Chrome/Edge/Chromium. Define CHROME_PATH.")


def make_qr():
    img = qrcode.make(APP_URL, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=1)
    out = ROOT / "poster" / "qr.svg"
    img.save(str(out))
    print("QR ->", out)


def to_pdf(browser, src, dst):
    profile = tempfile.mkdtemp(prefix="pdf_profile_")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--user-data-dir={profile}", f"--print-to-pdf={dst}", src.as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    shutil.rmtree(profile, ignore_errors=True)
    print("PDF ->", dst)


if __name__ == "__main__":
    make_qr()
    browser = find_browser()
    (ROOT / "app" / "files").mkdir(exist_ok=True)
    for src, dst in JOBS:
        to_pdf(browser, src, dst)
        shutil.copy(dst, ROOT / "app" / "files" / dst.name)
