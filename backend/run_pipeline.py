
import subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
scripts = [
    "01_clean_data.py",
    "02_build_master.py",
    "03_eda_and_statistics.py",
    "04_train_models.py",
    "05_score_and_recommend.py",
]

for script in scripts:
    print("\n" + "="*70)
    print("RUNNING:", script)
    print("="*70)
    subprocess.run([sys.executable, str(BASE/"src"/script)], check=True)

print("\nSTOCKSENSE BACKEND PIPELINE COMPLETE.")
