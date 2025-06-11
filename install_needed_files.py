import subprocess
import sys

def install(package):
    subprocess.call([sys.executable, "-m", "pip", "install", package])

install("httpx")
install("lxml")
install("Html2Image")

