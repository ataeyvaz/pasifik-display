import subprocess
import sys

def run(cmd: list[str]):
    print("\n>>", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    py = sys.executable
    run([py, "tools/scrape/scrape_zeroteknik.py"])
    run([py, "tools/scrape/scrape_solobu.py"])
    print("\nBitti. data/raw altını kontrol et.")

if __name__ == "__main__":
    main()
