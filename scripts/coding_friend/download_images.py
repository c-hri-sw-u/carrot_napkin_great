import os
import csv
import shutil
import re
from icrawler.builtin import BingImageCrawler
from PIL import Image

def safe_filename(text):
    # Replace spaces with underscores
    text = text.replace(' ', '_')
    # Remove invalid filename characters
    text = re.sub(r'[\\/*?:"<>|]', '', text)
    # Remove leading/trailing periods/spaces
    text = text.strip('. ')
    return text

def crop_to_square(image_path):
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            new_side = min(width, height)
            
            left = (width - new_side) / 2
            top = (height - new_side) / 2
            right = (width + new_side) / 2
            bottom = (height + new_side) / 2
            
            # Crop the center of the image
            img_cropped = img.crop((left, top, right, bottom))
            
            # Save the cropped image, overwriting the original
            img_cropped.save(image_path)
            print(f"  - Cropped to square: {image_path}")
    except Exception as e:
        print(f"  - Error cropping {image_path}: {e}")

def download_images(csv_path, output_dir):
    # Create output directory if not exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # Temporary directory for crawler downloads
    temp_dir = os.path.join(output_dir, 'temp_crawler')
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    updated_rows = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            if 'Image File' not in header:
                header.append('Image File')
            updated_rows.append(header)
            
            rows = list(reader)
            total = len(rows)
            
            for i, row in enumerate(rows):
                if not row:
                    continue
                    
                word = row[0]
                
                # Use search keywords if available (2nd column)
                search_query = word
                if len(row) > 1 and row[1].strip():
                     search_query = row[1].strip()
                     
                print(f"[{i+1}/{total}] Processing: {word} (Query: {search_query})")
                
                # Construct filename
                base_name = safe_filename(word)
                if not base_name:
                    base_name = "unnamed"
                
                # We aim for .jpg mostly with Bing crawler
                target_filename = f"{base_name}.jpg"
                target_path = os.path.join(output_dir, target_filename)
                
                # Check if already exists (optional, but good for retries)
                if os.path.exists(target_path):
                    print(f"  - Image already exists: {target_filename}")
                    # Ensure row has filename in correct column (3rd column now: Word, Keywords, Image)
                    # Input row: [Word, Keywords]
                    if len(row) < 3:
                        row.append(target_filename)
                    else:
                        row[2] = target_filename
                    updated_rows.append(row)
                    continue

                # Crawl
                # Clear temp dir to avoid confusion
                for f_name in os.listdir(temp_dir):
                    os.remove(os.path.join(temp_dir, f_name))
                
                try:
                    crawler = BingImageCrawler(storage={'root_dir': temp_dir}, log_level='ERROR')
                    # Filters can be added, e.g., license, type
                    crawler.crawl(keyword=search_query, max_num=1, overwrite=True)
                    
                    # Find the downloaded file
                    downloaded_files = os.listdir(temp_dir)
                    if downloaded_files:
                        src_file = os.path.join(temp_dir, downloaded_files[0])
                        # Rename and move
                        shutil.move(src_file, target_path)
                        print(f"  - Downloaded: {target_filename}")
                        
                        # Crop to square
                        crop_to_square(target_path)
                        
                        # Add filename to row
                        if len(row) < 3:
                            row.append(target_filename)
                        else:
                            row[2] = target_filename
                    else:
                        print(f"  - No image found for: {word}")
                        if len(row) < 3:
                            row.append("")
                        else:
                            row[2] = ""
                except Exception as e:
                    print(f"  - Error downloading {word}: {e}")
                    if len(row) < 3:
                        row.append("")
                    else:
                        row[2] = ""
                
                updated_rows.append(row)

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Cleanup temp dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # Write updated CSV
    try:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        print(f"Updated CSV saved to {csv_path}")
    except Exception as e:
        print(f"Error writing CSV: {e}")

if __name__ == "__main__":
    # Use relative paths or verify absolute paths
    base_dir = os.getcwd()
    # Updated path to match where the CSV actually is
    csv_file = os.path.join(base_dir, "coding_friend_vocabulary", "all_english_words.csv")
    img_dir = os.path.join(base_dir, "coding_friend_vocabulary", "~assets", "img")
    
    print(f"Working directory: {base_dir}")
    print(f"Target CSV: {csv_file}")
    
    download_images(csv_file, img_dir)
