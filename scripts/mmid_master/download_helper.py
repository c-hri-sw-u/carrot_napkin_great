'''
python3 mmid-master/download_helper.py --help

python3 mmid-master/download_helper.py --list

python3 mmid-master/download_helper.py --lang spanish --limit 3
python3 mmid-master/download_helper.py --lang french --limit 1
python3 mmid-master/download_helper.py --lang french --limit 100
'''


import re
import os
import argparse
import subprocess
import sys
import tarfile
import shutil

def parse_downloads_md(file_path):
    """Parses the downloads.md file to extract download links."""
    downloads = {}
    
    # Try to find downloads.md in current directory if default path fails
    if not os.path.exists(file_path):
        # Check relative to script location
        base_dir = os.path.dirname(os.path.abspath(__file__))
        alt_path = os.path.join(base_dir, 'downloads.md')
        
        # Check relative to current working directory
        cwd_path = os.path.join(os.getcwd(), 'mmid-master', 'downloads.md')
        
        if os.path.exists(alt_path):
            file_path = alt_path
        elif os.path.exists(cwd_path):
            file_path = cwd_path
        elif os.path.exists('downloads.md'):
            file_path = 'downloads.md'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: Could not find {file_path}")
        return {}

    # Regex to match the markdown table rows
    # | language | 100 images | 1 image | metadata | dictionary | web text |
    # Matches: | name | [link](url) | ...
    link_pattern = re.compile(r'\[link\]\((https?://[^)]+)\)')
    
    for line in lines:
        line = line.strip()
        if not line.startswith('|') or '---' in line:
            continue
            
        parts = [p.strip() for p in line.split('|')]
        # parts[0] is empty because line starts with |
        # Some lines might have different number of columns or empty columns
        # The structure is | language | 100 images | 1 image | metadata | dictionary | web text |
        # So we expect at least 7 parts (including empty first and last)
        
        if len(parts) < 3:
            continue
            
        language = parts[1].lower()
        if not language or language == 'language' or '---' in language or '**' in language:
            continue
        
        # Extract links
        links = {}
        # 100 images -> index 2
        if len(parts) > 2:
            m = link_pattern.search(parts[2])
            if m: links['full'] = m.group(1)
        
        # 1 image -> index 3
        if len(parts) > 3:
            m = link_pattern.search(parts[3])
            if m: links['mini'] = m.group(1)
        
        # metadata -> index 4
        if len(parts) > 4:
            m = link_pattern.search(parts[4])
            if m: links['metadata'] = m.group(1)
        
        # dictionary -> index 5
        if len(parts) > 5:
            m = link_pattern.search(parts[5])
            if m: links['dictionary'] = m.group(1)
        
        # web text -> index 6
        if len(parts) > 6:
            m = link_pattern.search(parts[6])
            if m: links['text'] = m.group(1)
        
        if links:
            downloads[language] = links
            
    return downloads

def download_file(url, dest_folder):
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    filename = url.split('/')[-1]
    dest_path = os.path.join(dest_folder, filename)
    
    if os.path.exists(dest_path):
        print(f"File {filename} already exists. Skipping download.")
        return

    print(f"Downloading {url} to {dest_path}...")
    try:
        # Use curl for downloading
        subprocess.run(['curl', '-O', url], cwd=dest_folder, check=True)
        print("Download complete.")
    except subprocess.CalledProcessError:
        print("Error downloading file.")
    except FileNotFoundError:
        print("Error: curl is not installed or not found.")

def filter_inner_tar(tar_path, limit):
    """
    Reads a tar.gz file (inner word package), keeps only 'limit' images,
    and rewrites the tar.gz file.
    """
    temp_path = tar_path + ".tmp"
    try:
        with tarfile.open(tar_path, "r:gz") as source, tarfile.open(temp_path, "w:gz") as dest:
            members = source.getmembers()
            images = [m for m in members if m.name.lower().endswith(('.png', '.jpg', '.jpeg'))]
            others = [m for m in members if m not in images]
            
            # Sort images to keep the first ones (usually numbered 01.png, 02.png...)
            images.sort(key=lambda x: x.name)
            keep_images = images[:limit]
            
            for m in others:
                f = source.extractfile(m)
                if f:
                    dest.addfile(m, f)
                    
            for m in keep_images:
                f = source.extractfile(m)
                if f:
                    dest.addfile(m, f)
        
        os.replace(temp_path, tar_path)
        return True
    except Exception as e:
        print(f"Error filtering {tar_path}: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False

def process_full_package(filename, limit):
    print(f"\nSmart Mode: Processing {filename} to keep {limit} images per word...")
    
    extract_dir = filename.replace('.tgz', '').replace('.tar.gz', '')
    
    # 1. Extract the main package
    if not os.path.exists(extract_dir):
        print(f"Extracting main package to {extract_dir}...")
        try:
            with tarfile.open(filename, "r:gz") as tar:
                tar.extractall(path=extract_dir)
        except Exception as e:
            print(f"Failed to extract {filename}: {e}")
            return
    else:
        print(f"Directory {extract_dir} already exists. Using existing content.")

    # 2. Iterate over extracted files
    print(f"Filtering images (keeping top {limit} per word)...")
    count = 0
    filtered_count = 0
    
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.tar.gz'):
                full_path = os.path.join(root, file)
                if filter_inner_tar(full_path, limit):
                    filtered_count += 1
                count += 1
                if count % 100 == 0:
                    print(f"Processed {count} words...", end='\r')
                    
    print(f"\nFinished processing {filtered_count} word packages.")
    print(f"You can now find the dataset in: {extract_dir}")
    print("Note: The original large package file was kept. You can delete it manually if satisfied.")

def main():
    parser = argparse.ArgumentParser(description="Download MMID dataset packages.")
    parser.add_argument('--list', action='store_true', help="List all available languages")
    parser.add_argument('--lang', type=str, help="Language to download (e.g., 'french', 'english-01')")
    parser.add_argument('--type', type=str, default='mini', choices=['full', 'mini', 'metadata', 'dictionary', 'text'], 
                        help="Type of package to download (default: mini)")
    parser.add_argument('--limit', type=int, help="Smart Mode: Number of images per word. If specified (e.g. 3), downloads full package and filters it.")
    parser.add_argument('--md_path', type=str, default='mmid-master/downloads.md', help="Path to downloads.md")
    
    args = parser.parse_args()
    
    data = parse_downloads_md(args.md_path)
    
    if not data:
        print("No download data found. Check the path to downloads.md.")
        return

    if args.list:
        print("Available languages:")
        for lang in sorted(data.keys()):
            print(f"- {lang}")
        return

    if args.lang:
        lang = args.lang.lower()
        if lang not in data:
            print(f"Language '{lang}' not found. Use --list to see available languages.")
            return
        
        # Determine package type and filtering based on limit
        should_filter = False
        package_type = args.type
        
        if args.limit:
            if args.limit == 1:
                package_type = 'mini'
                print(f"Smart Mode: Limit is 1, using 'mini' package.")
            elif args.limit >= 100:
                package_type = 'full'
                print(f"Smart Mode: Limit is >= 100, using 'full' package without filtering.")
            else:
                package_type = 'full'
                should_filter = True
                print(f"Smart Mode: Limit is {args.limit}, will download 'full' package and filter.")
        
        if package_type not in data[lang]:
            print(f"Type '{package_type}' not available for {lang}.")
            return
            
        url = data[lang][package_type]
        download_file(url, ".")
        
        if should_filter:
            filename = url.split('/')[-1]
            if os.path.exists(filename):
                process_full_package(filename, args.limit)
            else:
                print("Error: Package file not found after download attempt.")
                
    else:
        print("Please specify a language with --lang or list languages with --list")

if __name__ == "__main__":
    main()
