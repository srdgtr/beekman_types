import subprocess
import sys

def install():
    subprocess.call([sys.executable, "-m", "pip", "install", "requests-html"])

install()