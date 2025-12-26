#!/usr/bin/env python3

'''
python3 scripts/mmid_master/mmid_manager.py --list
python3 scripts/mmid_master/mmid_manager.py --lang japanese --download --limit 3
python3 scripts/mmid_master/mmid_manager.py --extract --source scale-japanese-package.tgz --limit 3
'''



import os
import sys
import argparse
import re
import subprocess
import tarfile
import shutil
import json
from tqdm import tqdm

class MMIDManager:
    def __init__(self, downloads_md_path=None):
        self.downloads_md_path = downloads_md_path
        self.data = {}
        
    def resolve_downloads_md_path(self):
        """Finds the downloads.md file."""
        if self.downloads_md_path and os.path.exists(self.downloads_md_path):
            return self.downloads_md_path
            
        # Search common locations
        candidates = [
            os.path.join(os.getcwd(), 'mmid-master', 'downloads.md'),
            os.path.join(os.getcwd(), '..', '..', 'mmid-master', 'downloads.md'), # If running from scripts/mmid_master/
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'mmid-master', 'downloads.md'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads.md'),
            'downloads.md'
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def parse_downloads_md(self):
        """Parses the downloads.md file to extract download links."""
        file_path = self.resolve_downloads_md_path()
        if not file_path:
            print("Error: Could not find downloads.md.")
            print("Please run this script from the project root or ensure 'mmid-master/downloads.md' exists.")
            return False

        print(f"Reading data from: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading file: {e}")
            return False

        # Regex to extract URL from [link](url)
        link_pattern = re.compile(r'\((https?://[^)]+)\)')
        
        for line in lines:
            line = line.strip()
            if not line.startswith('|') or '---' in line:
                continue
                
            parts = [p.strip() for p in line.split('|')]
            
            # | language | 100 images | 1 image | metadata | dictionary | web text |
            # split gives: ['', 'lang', '100', '1', 'meta', 'dict', 'text', '']
            
            if len(parts) < 3:
                continue
                
            language = parts[1].lower()
            if not language or language == 'language' or '**' in language:
                continue
            
            links = {}
            
            # Helper to extract link from column index
            def get_link(index):
                if index < len(parts):
                    m = link_pattern.search(parts[index])
                    return m.group(1) if m else None
                return None

            links['full'] = get_link(2)       # 100 images
            links['mini'] = get_link(3)       # 1 image
            links['metadata'] = get_link(4)   # metadata
            links['dictionary'] = get_link(5) # dictionary
            links['text'] = get_link(6)       # web text
            
            # Only add if we have at least one link
            if any(links.values()):
                self.data[language] = links
                
        return True

    def list_languages(self):
        if not self.data:
            if not self.parse_downloads_md():
                return
        
        print(f"\nAvailable languages ({len(self.data)}):")
        
        # Group by first letter for better readability
        sorted_langs = sorted(self.data.keys())
        current_char = ''
        for lang in sorted_langs:
            first_char = lang[0].upper()
            if first_char != current_char:
                print(f"\n--- {first_char} ---")
                current_char = first_char
            print(f"  {lang}")
        print()

    def download_file(self, url, dest_folder):
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        
        filename = url.split('/')[-1]
        dest_path = os.path.join(dest_folder, filename)
        
        if os.path.exists(dest_path):
            print(f"File {filename} already exists in {dest_folder}. Skipping download.")
            return dest_path

        print(f"Downloading {url} to {dest_path}...")
        try:
            # Use curl for downloading, it's reliable and shows progress
            subprocess.run(['curl', '-L', '-O', url], cwd=dest_folder, check=True)
            print("Download complete.")
            return dest_path
        except subprocess.CalledProcessError:
            print("Error downloading file.")
            return None
        except FileNotFoundError:
            print("Error: curl is not installed or not found.")
            return None

    def _handle_dictionary(self, source_path, dest_dir):
        """
        Attempts to download the dictionary for the language and create a words.json mapping.
        """
        # 1. Guess language from filename
        filename = os.path.basename(source_path)
        # Patterns: scale-lang-package.tgz, mini-lang-package.tgz
        match = re.search(r'(scale|mini)-(.+)-package\.tgz', filename)
        if not match:
            return
            
        lang = match.group(2)
        
        # 2. Check if we have the link
        if not self.data:
            self.parse_downloads_md()
            
        if lang not in self.data or 'dictionary' not in self.data[lang]:
            # Try to refresh data if missing
            self.parse_downloads_md()
            if lang not in self.data or 'dictionary' not in self.data[lang]:
                print(f"Warning: No dictionary link found for language '{lang}' in downloads.md")
                return
            
        dict_url = self.data[lang]['dictionary']
        if not dict_url:
            return

        # 3. Download dictionary
        dict_filename = os.path.basename(dict_url)
        dict_path = os.path.join(dest_dir, dict_filename)
        
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        try:
            if not os.path.exists(dict_path):
                print(f"Downloading dictionary for {lang}...")
                subprocess.run(['curl', '-L', '-o', dict_path, dict_url], check=True)
                
            # 4. Process TSV to JSON
            json_path = os.path.join(dest_dir, 'words.json')
            if not os.path.exists(json_path):
                print("Generating words.json from dictionary...")
                word_map = {}
                with open(dict_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            word = parts[0]
                            word_id = parts[1]
                            word_map[word_id] = word
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(word_map, f, ensure_ascii=False, indent=2)
                    
                print(f"Created words.json with {len(word_map)} entries.")
            
        except Exception as e:
            print(f"Error handling dictionary: {e}")

    def extract_top_k(self, source_path, dest_dir, k):
        """
        Extracts top k images from source_path (tarball or directory) to dest_dir.
        """
        if not os.path.exists(source_path):
            print(f"Error: Source not found: {source_path}")
            return

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            print(f"Created destination directory: {dest_dir}")

        # Try to handle dictionary/mapping automatically
        self._handle_dictionary(source_path, dest_dir)

        if os.path.isdir(source_path):
            print(f"Processing directory: {source_path}")
            self._process_directory_source(source_path, dest_dir, k)
        elif tarfile.is_tarfile(source_path):
            print(f"Processing tarball: {source_path}")
            self._process_tarball_source(source_path, dest_dir, k)
        else:
            print(f"Error: Source is neither a directory nor a tar file: {source_path}")

    def _process_directory_source(self, source_dir, dest_dir, k):
        # Find word folders (or tarballs inside)
        items = os.listdir(source_dir)
        # Assuming structure: source_dir/word_id/images...
        # Or source_dir might contain word_id.tar.gz
        
        # We need to detect if source_dir is the package root (containing numbered folders)
        # or if it's already inside a word folder (unlikely for batch processing)
        
        word_items = [i for i in items if i.replace('.tar.gz', '').isdigit()]
        
        if not word_items:
            # Maybe the source_dir IS the extracted package folder which contains the word folders
            # Let's check one level deeper if needed, or just assume the provided path is correct
            print(f"Found {len(word_items)} word items in {source_dir}.")
        
        for item in tqdm(word_items, desc="Processing words"):
            src_item_path = os.path.join(source_dir, item)
            word_id = item.replace('.tar.gz', '')
            dest_word_dir = os.path.join(dest_dir, word_id)
            
            if os.path.isdir(src_item_path):
                self._copy_top_k_from_dir(src_item_path, dest_word_dir, k)
            elif tarfile.is_tarfile(src_item_path):
                self._extract_top_k_from_tar(src_item_path, dest_word_dir, k)

    def _process_tarball_source(self, tar_path, dest_dir, k):
        # If it's a main package tarball (e.g., scale-spanish-package.tgz), 
        # it contains many .tar.gz files (one per word) inside.
        # We can extract them on the fly without extracting the whole big package first.
        
        print(f"Reading main package stream from {tar_path}...")
        print("Note: This is a large file (19GB+), scanning may take a moment to start...")
        
        try:
            # Use 'r|gz' for streaming access which avoids reading the whole file structure first
            with tarfile.open(tar_path, "r|gz") as main_tar:
                count = 0
                word_counts = {} # word_id -> number of images extracted
                
                # Wrap main_tar in tqdm to show progress of iterating through members
                # Since we don't know the total number of files, it will show iterations/sec
                pbar = tqdm(main_tar, desc="Scanning & Extracting", unit="file")
                
                for member in pbar:
                    if not member.isfile():
                        continue
                        
                    # CASE A: Nested tarball (e.g. scale-spanish-package/1234.tar.gz)
                    if member.name.endswith('.tar.gz') and member.name.split('/')[-1].replace('.tar.gz', '').isdigit():
                        word_id = member.name.split('/')[-1].replace('.tar.gz', '')
                        dest_word_dir = os.path.join(dest_dir, word_id)
                        
                        # Extract the inner tar to memory/temp file to process it
                        f = main_tar.extractfile(member)
                        if f:
                            try:
                                with tarfile.open(fileobj=f, mode="r:gz") as inner_tar:
                                    self._extract_from_tar_object(inner_tar, dest_word_dir, k)
                                count += 1
                                if count % 100 == 0:
                                    pbar.set_description(f"Extracted {count} words")
                            except Exception as e:
                                pbar.write(f"Warning: Failed to process inner tar {member.name}: {e}")
                    
                    # CASE B: Flat directory structure (e.g. scale-japanese-package/5418/01.jpg)
                    else:
                        parts = member.name.split('/')
                        # Expect: root_dir/word_id/filename
                        if len(parts) >= 3 and parts[-2].isdigit():
                            word_id = parts[-2]
                            filename = parts[-1]
                            dest_word_dir = os.path.join(dest_dir, word_id)
                            
                            is_image = filename.lower().endswith(('.png', '.jpg', '.jpeg'))
                            is_meta = filename in ['word.txt', 'metadata.json', 'errors.json']
                            
                            if is_image:
                                current_word_count = word_counts.get(word_id, 0)
                                if current_word_count < k:
                                    self._extract_direct_file(main_tar, member, dest_word_dir)
                                    word_counts[word_id] = current_word_count + 1
                                    
                                    # Just for progress update roughly
                                    if current_word_count == 0:
                                        count += 1
                                        if count % 100 == 0:
                                            pbar.set_description(f"Extracted {count} words")
                            
                            elif is_meta:
                                self._extract_direct_file(main_tar, member, dest_word_dir)

                print(f"\nFinished processing {count} word packages.")

        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            return
        except Exception as e:
            print(f"Error processing main tarball: {e}")

    def _extract_direct_file(self, tar_obj, member, dest_path):
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
            
        f = tar_obj.extractfile(member)
        if f:
            out_filename = os.path.basename(member.name)
            out_path = os.path.join(dest_path, out_filename)
            with open(out_path, 'wb') as out_f:
                shutil.copyfileobj(f, out_f)

    def _copy_top_k_from_dir(self, src_path, dest_path, k):
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
            
        files = [f for f in os.listdir(src_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        files.sort()
        
        to_copy = files[:k]
        
        for f in to_copy:
            shutil.copy2(os.path.join(src_path, f), os.path.join(dest_path, f))
            
        for meta_file in ['word.txt', 'metadata.json', 'errors.json']:
            if os.path.exists(os.path.join(src_path, meta_file)):
                shutil.copy2(os.path.join(src_path, meta_file), os.path.join(dest_path, meta_file))

    def _extract_top_k_from_tar(self, tar_path, dest_path, k):
        try:
            with tarfile.open(tar_path, "r:gz") as tar:
                self._extract_from_tar_object(tar, dest_path, k)
        except Exception as e:
            print(f"Error reading tar {tar_path}: {e}")

    def _extract_from_tar_object(self, tar_obj, dest_path, k):
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
            
        members = tar_obj.getmembers()
        images = [m for m in members if m.name.lower().endswith(('.png', '.jpg', '.jpeg'))]
        images.sort(key=lambda x: x.name)
        
        to_extract = images[:k]
        
        meta_files = [m for m in members if os.path.basename(m.name) in ['word.txt', 'metadata.json', 'errors.json']]
        
        for member in to_extract + meta_files:
            f = tar_obj.extractfile(member)
            if f:
                out_filename = os.path.basename(member.name)
                out_path = os.path.join(dest_path, out_filename)
                with open(out_path, 'wb') as out_f:
                    shutil.copyfileobj(f, out_f)

    def run(self):
        parser = argparse.ArgumentParser(description="MMID Dataset Manager: Download and Extract")
        parser.add_argument('--list', action='store_true', help="List available languages")
        parser.add_argument('--lang', type=str, help="Language to process")
        parser.add_argument('--download', action='store_true', help="Download the package")
        parser.add_argument('--extract', action='store_true', help="Extract images from package")
        parser.add_argument('--source', type=str, help="Source path for extraction (existing file or folder)")
        parser.add_argument('--limit', type=int, default=None, help="Number of images per word to keep (e.g. 3)")
        parser.add_argument('--dest', type=str, default='.', help="Destination folder for downloads/extraction")
        parser.add_argument('--keep_full', action='store_true', help="Keep the full downloaded package after extraction")
        
        args = parser.parse_args()
        
        # 1. List Languages
        if args.list:
            self.list_languages()
            return

        # 2. Extract from local source
        if args.extract and args.source:
            if not args.limit:
                print("Warning: No --limit specified. Extracting ALL images.")
                # We can handle this, or default to all. For now, let's assume limit is required for 'top k' feature
                # But actually, if limit is None, we could extract everything. 
                # Let's use a large number for 'all' or modify logic.
                limit = 10000 
            else:
                limit = args.limit
                
            dest_dir = args.dest if args.dest != '.' else f"{args.source}_extracted"
            self.extract_top_k(args.source, dest_dir, limit)
            print(f"Extraction complete to {dest_dir}")
            return

        # 3. Download and/or Extract Language
        if args.lang:
            if not self.parse_downloads_md():
                return
                
            lang = args.lang.lower()
            if lang not in self.data:
                print(f"Language '{lang}' not found.")
                return
            
            # Determine URL
            # If limit is 1, use mini package by default unless full is forced?
            # Actually, user wants "top 3". Mini only has 1. So we MUST download full if limit > 1.
            
            pkg_type = 'full'
            if args.limit and args.limit == 1:
                pkg_type = 'mini'
                print("Limit is 1, selecting 'mini' package.")
            
            if pkg_type not in self.data[lang]:
                print(f"Package type {pkg_type} not found for {lang}.")
                return
                
            url = self.data[lang][pkg_type]
            
            if args.download:
                # Download
                print(f"Selected package: {pkg_type} for {lang}")
                downloaded_file = self.download_file(url, args.dest)
                
                if downloaded_file and args.extract and args.limit:
                    # Extract immediately
                    # Naming convention: scale-spanish-package-k3
                    pkg_name = os.path.basename(downloaded_file).replace('.tgz', '').replace('.tar.gz', '')
                    extract_dest = os.path.join(args.dest, f"{pkg_name}-k{args.limit}")
                    
                    print(f"\nExtracting top {args.limit} images to {extract_dest}...")
                    self.extract_top_k(downloaded_file, extract_dest, args.limit)
                    
                    if not args.keep_full:
                        print(f"Removing large package file: {downloaded_file}")
                        os.remove(downloaded_file)
                        
                    print(f"\nDone! Your dataset is ready at: {extract_dest}")

            elif args.extract:
                # User asked to extract but didn't say download, assume file exists in dest?
                # Or maybe they meant "download and extract"?
                # Let's look for the file in dest.
                filename = url.split('/')[-1]
                possible_path = os.path.join(args.dest, filename)
                if os.path.exists(possible_path):
                     pkg_name = filename.replace('.tgz', '').replace('.tar.gz', '')
                     extract_dest = os.path.join(args.dest, f"{pkg_name}-k{args.limit if args.limit else 'all'}")
                     self.extract_top_k(possible_path, extract_dest, args.limit if args.limit else 10000)
                else:
                    print(f"File {filename} not found in {args.dest}. Use --download to fetch it.")
            
            else:
                # Just verifying language exists?
                print(f"Language '{lang}' is available.")
                print(f"URL: {url}")
                print("Use --download to download it.")

        else:
            parser.print_help()

if __name__ == "__main__":
    MMIDManager().run()
