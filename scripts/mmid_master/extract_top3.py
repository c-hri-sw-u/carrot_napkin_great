import os
import shutil
import tarfile
from tqdm import tqdm

def extract_top_k(source_dir, dest_dir, k=3):
    """
    Extracts top k images from each word package in source_dir to dest_dir.
    Handles both directory structures and tar.gz files.
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        print(f"Created destination directory: {dest_dir}")

    # Walk through the source directory
    # We expect the source directory to contain either folders (unpacked) or .tar.gz files (packed)
    # for each word ID.
    
    if not os.path.exists(source_dir):
        print(f"Error: Source directory not found: {source_dir}")
        return

    # First, let's look for what's inside the source directory
    items = os.listdir(source_dir)
    
    # Filter for word items (usually numeric IDs)
    # They can be directories or .tar.gz files
    word_items = []
    for item in items:
        # Check if it's likely a word package (digits)
        # It could be "10" (dir) or "10.tar.gz" (file)
        name = item.replace('.tar.gz', '')
        if name.isdigit():
            word_items.append(item)
            
    print(f"Found {len(word_items)} word packages to process.")
    
    for item in tqdm(word_items, desc="Processing words"):
        src_path = os.path.join(source_dir, item)
        word_id = item.replace('.tar.gz', '')
        dest_word_dir = os.path.join(dest_dir, word_id)
        
        if os.path.isdir(src_path):
            # Case 1: Source is a directory
            process_directory(src_path, dest_word_dir, k)
        elif tarfile.is_tarfile(src_path):
            # Case 2: Source is a tar.gz file
            process_tarball(src_path, dest_word_dir, k)

def process_directory(src_path, dest_path, k):
    """Copies top k images from src_path directory to dest_path."""
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        
    # Get all image files
    files = [f for f in os.listdir(src_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    files.sort() # Sort to ensure we get 01.png, 02.png, etc.
    
    # Select top k
    to_copy = files[:k]
    
    # Copy images
    for f in to_copy:
        shutil.copy2(os.path.join(src_path, f), os.path.join(dest_path, f))
        
    # Also copy metadata/word.txt files if they exist
    for meta_file in ['word.txt', 'metadata.json', 'errors.json']:
        if os.path.exists(os.path.join(src_path, meta_file)):
            shutil.copy2(os.path.join(src_path, meta_file), os.path.join(dest_path, meta_file))

def process_tarball(src_path, dest_path, k):
    """Extracts top k images from src_path tarball to dest_path."""
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        
    try:
        with tarfile.open(src_path, "r:gz") as tar:
            members = tar.getmembers()
            
            # Filter images
            images = [m for m in members if m.name.lower().endswith(('.png', '.jpg', '.jpeg'))]
            images.sort(key=lambda x: x.name)
            
            # Select top k
            to_extract = images[:k]
            
            # Also get metadata files
            meta_files = [m for m in members if os.path.basename(m.name) in ['word.txt', 'metadata.json', 'errors.json']]
            
            # Extract
            for member in to_extract + meta_files:
                # We need to handle paths inside tar. Sometimes they are like "./01.png" or just "01.png"
                # We want to extract them directly to dest_path
                f = tar.extractfile(member)
                if f:
                    # Determine output filename (flatten structure)
                    out_filename = os.path.basename(member.name)
                    out_path = os.path.join(dest_path, out_filename)
                    with open(out_path, 'wb') as out_f:
                        shutil.copyfileobj(f, out_f)
                        
    except Exception as e:
        print(f"Error processing {src_path}: {e}")

if __name__ == "__main__":
    # Configure paths
    SOURCE_DIR = "/Users/chriswu/Documents/GitHub/carrot_napkin_great/scale-spanish-package/scale-spanish-package"
    DEST_DIR = "/Users/chriswu/Documents/GitHub/carrot_napkin_great/scale-spanish-package-k3"
    
    print(f"Source: {SOURCE_DIR}")
    print(f"Destination: {DEST_DIR}")
    
    extract_top_k(SOURCE_DIR, DEST_DIR, k=3)
    print("\nExtraction complete!")
