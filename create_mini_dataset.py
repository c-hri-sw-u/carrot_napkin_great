import os
import csv
import shutil

# Configuration
SOURCE_PACKAGES = [
    'scale-german-package-k3',
    'scale-japanese-package-k3',
    'scale-spanish-package-k3'
]

TARGET_PREFIX = 'mini-'
ITEMS_TO_KEEP = 600 # Adjust this to fit within size limits

def create_mini_package(package_name):
    target_name = package_name.replace('scale-', TARGET_PREFIX)
    
    if os.path.exists(target_name):
        print(f"Removing existing {target_name}...")
        shutil.rmtree(target_name)
    
    os.makedirs(target_name)
    print(f"Processing {package_name} -> {target_name}")

    # Read index.csv
    csv_path = os.path.join(package_name, 'index.csv')
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    kept_ids = []
    
    with open(csv_path, 'r', encoding='utf-8') as f_in, \
         open(os.path.join(target_name, 'index.csv'), 'w', encoding='utf-8', newline='') as f_out:
        
        reader = csv.reader(f_in)
        writer = csv.writer(f_out)
        
        header = next(reader)
        writer.writerow(header)
        
        # Read all rows and shuffle
        all_rows = list(reader)
        import random
        random.shuffle(all_rows)
        
        count = 0
        for row in all_rows:
            if count >= ITEMS_TO_KEEP:
                break
                
            # Copy the folder associated with this ID
            # row is [id, word] (based on previous cat output)
            if len(row) < 2:
                continue
                
            folder_id = row[0]
            src_folder = os.path.join(package_name, folder_id)
            dst_folder = os.path.join(target_name, folder_id)
            
            if os.path.exists(src_folder):
                shutil.copytree(src_folder, dst_folder)
                writer.writerow(row)
                kept_ids.append(folder_id)
                count += 1
            else:
                # If folder doesn't exist, skip writing to CSV (or keep it? Better to skip to avoid errors)
                # print(f"Warning: Folder {src_folder} missing.")
                pass
                
    print(f"Created {target_name} with {count} items.")

def main():
    for pkg in SOURCE_PACKAGES:
        if os.path.exists(pkg):
            create_mini_package(pkg)
        else:
            print(f"Skipping missing package: {pkg}")

if __name__ == "__main__":
    main()
