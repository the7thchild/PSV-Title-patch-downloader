import sys
import os
import subprocess
import hashlib
import hmac
import re

def find_wget():
    """Find wget.exe in current directory or bin/ folder"""
    # Check current directory first
    if os.path.exists("wget.exe"):
        return "wget.exe"
    
    # Check bin/ folder
    if os.path.exists(os.path.join("bin", "wget.exe")):
        return os.path.join("bin", "wget.exe")
    
    return None

def hmac_sha256(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def build_xml_url(titleid, env="np"):
    key = bytes([
        0xE5,0xE2,0x78,0xAA,0x1E,0xE3,0x40,0x82,0xA0,0x88,0x27,0x9C,
        0x83,0xF9,0xBB,0xC8,0x06,0x82,0x1C,0x52,0xF2,0xAB,0x5D,0x2B,
        0x4A,0xBD,0x99,0x54,0x50,0x35,0x51,0x14
    ])
    
    titleid = titleid.upper()
    data = "{}_{}".format(env, titleid)
    digest = hmac_sha256(key, data)
    hash_hex = digest.hex()
    
    return "http://gs-sec.ww.{}.dl.playstation.net/pl/{}/{}/{}/{}-ver.xml".format(
        env, env, titleid, hash_hex, titleid)

def run_wget(wget_path, url, output_path, show_progress=True):
    if not wget_path:
        print("Error: wget.exe not found! Please place it in the current folder or in bin\\")
        return False
    
    cmd = [wget_path]
    
    if show_progress:
        cmd.extend(['--show-progress', '--progress=bar:force'])
    else:
        cmd.append('-q')
    
    cmd.extend(['-O', output_path, url])
    
    try:
        print("Downloading: {}".format(os.path.basename(output_path)))
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        print("Download failed: {}".format(url))
        return False
    except Exception as e:
        print("Error running wget: {}".format(e))
        return False

def download_all_packages(xml_content, out_dir, wget_path):
    urls = re.findall(r'url="(http[^"]+)"', xml_content)
    if not urls:
        print("No update packages found in the XML.")
        return 0
    
    pkg_count = 0
    success_count = 0
    skipped_count = 0
    
    print("\nFound {} potential download link(s). Filtering for .pkg only...\n".format(len(urls)))
    
    for url in urls:
        if not url.lower().endswith('.pkg'):
            continue
            
        pkg_count += 1
        filename = url.split('/')[-1]
        save_path = os.path.join(out_dir, filename)
        
        if os.path.exists(save_path):
            print("[{}] {} - Already exists, skipping.".format(pkg_count, filename))
            skipped_count += 1
            continue
        
        print("[{}] {}".format(pkg_count, filename))
        if run_wget(wget_path, url, save_path):
            success_count += 1
            print("   OK\n")
        else:
            print("   Failed\n")
    
    if pkg_count == 0:
        print("No .pkg files found in the update manifest.")
    else:
        print("Summary: {} downloaded, {} already existed.".format(success_count, skipped_count))
    
    return success_count

def main():
    wget_path = find_wget()
    if not wget_path:
        print("Error: wget.exe was not found.")
        print("Please place wget.exe in the same folder as this script or in a 'bin' subfolder.")
        return

    print("Using wget: {}".format(wget_path))
    
    if len(sys.argv) < 2:
        print("Usage: python VitaUpdateDownloader.py <TITLEID> [output_folder] [env]")
        print("Example: python VitaUpdateDownloader.py PCSE00001 D:\\Updates")
        return

    titleid = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    env = sys.argv[3] if len(sys.argv) > 3 else "np"

    os.makedirs(out_dir, exist_ok=True)

    xml_url = build_xml_url(titleid, env)
    xml_path = os.path.join(out_dir, "{}-ver.xml".format(titleid.upper()))

    print("==================================================")
    print("PS Vita Title Update Downloader")
    print("==================================================")
    print("Title ID : {}".format(titleid.upper()))
    print("Env      : {}".format(env))
    print("Output   : {}".format(out_dir))
    print("")

    print("Downloading version manifest (XML)...")
    if not run_wget(wget_path, xml_url, xml_path):
        print("Failed to download XML manifest.")
        return

    print("\nReading XML and filtering packages...")
    with open(xml_path, "r", encoding="utf-8", errors="ignore") as f:
        xml = f.read()

    downloaded = download_all_packages(xml, out_dir, wget_path)

    # Clean up XML file
    try:
        if os.path.exists(xml_path):
            os.remove(xml_path)
            print("Temporary XML file deleted.")
    except:
        pass

    print("==================================================")
    print("Finished! {} .pkg file(s) downloaded.".format(downloaded))
    print("==================================================")

if __name__ == "__main__":
    main()
