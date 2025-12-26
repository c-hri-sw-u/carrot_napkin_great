import os
import csv
import re
import shutil
from icrawler.builtin import BingImageCrawler
from PIL import Image

def safe_filename(text):
    """Converts text to a safe filename, replacing spaces with underscores."""
    # Keep only alphanumeric, underscores, hyphens, and periods
    text = re.sub(r'[^\w\s\.-]', '', text)
    return text.strip().replace(' ', '_')

def crop_to_square(image_path):
    """Crops an image to a square, keeping the center."""
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            new_side = min(width, height)
            
            left = (width - new_side) / 2
            top = (height - new_side) / 2
            right = (width + new_side) / 2
            bottom = (height + new_side) / 2
            
            img_cropped = img.crop((left, top, right, bottom))
            # Convert to RGB if necessary (e.g. for PNGs with alpha) before saving as JPG
            if img_cropped.mode in ("RGBA", "P"):
                img_cropped = img_cropped.convert("RGB")
            
            img_cropped.save(image_path)
            print(f"  - Cropped to square: {image_path}")
    except Exception as e:
        print(f"  - Error cropping {image_path}: {e}")

def download_retry_images(csv_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Read the CSV
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    total = len(reader)
    print(f"Found {total} words to retry.")

    for i, row in enumerate(reader, 1):
        word = row.get("English Word")
        keyword = row.get("Search Keywords")
        
        # Use keyword if available, else word
        search_query = keyword if keyword else word
        
        if not word:
            continue

        print(f"[{i}/{total}] Retrying: {word} (Query: {search_query})")
        
        # Define safe filename
        filename_base = safe_filename(word)
        # We will let icrawler download to a temp folder, then move/rename
        temp_dir = os.path.join(output_dir, "temp_download")
        
        # Configure crawler
        crawler = BingImageCrawler(storage={'root_dir': temp_dir})
        
        # Download 1 image
        # Using filters to try to get better quality (photo) if possible, 
        # but icrawler filter options for bing are limited. 
        # 'type': 'photo' is often a good default filter for Bing if supported, 
        # but icrawler's Bing crawler filter support is sometimes tricky.
        # We'll just rely on the specific keywords.
        crawler.crawl(keyword=search_query, max_num=1, overwrite=True)
        
        # Find the downloaded file
        downloaded_files = os.listdir(temp_dir)
        if downloaded_files:
            # Assume the first file is the one we want (since max_num=1)
            # Usually named 000001.jpg or similar
            src_file = os.path.join(temp_dir, downloaded_files[0])
            ext = os.path.splitext(src_file)[1]
            dest_filename = f"{filename_base}{ext}"
            dest_file = os.path.join(output_dir, dest_filename)
            
            # Move and rename
            shutil.move(src_file, dest_file)
            print(f"  - Downloaded: {dest_filename}")
            
            # Crop
            crop_to_square(dest_file)
            
            # Clean up temp dir content for next iteration
            # (icrawler might not clean up if we don't)
            # Actually, since we move the file, the dir should be empty or contain other junk?
            # Best to remove the temp dir completely to be safe for next run
            shutil.rmtree(temp_dir) 
            
        else:
            print(f"  - No image found for: {word}")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

if __name__ == "__main__":
    base_dir = os.getcwd()
    retry_csv = os.path.join(base_dir, "coding_friend_vocabulary", "bad_words_retry.csv")
    retry_img_dir = os.path.join(base_dir, "coding_friend_vocabulary", "~assets", "img", "retry")
    
    download_retry_images(retry_csv, retry_img_dir)
