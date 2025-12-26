#!/usr/bin/env python3
import os
import csv
import argparse
from tqdm import tqdm

def generate_csv(dataset_path, output_csv_path):
    if not os.path.exists(dataset_path):
        print(f"Error: Dataset path '{dataset_path}' does not exist.")
        return

    data = []
    
    # List all subdirectories
    subdirs = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
    
    print(f"Found {len(subdirs)} folders in {dataset_path}. Processing...")
    
    for subdir in tqdm(subdirs, desc="Reading word.txt files"):
        folder_path = os.path.join(dataset_path, subdir)
        word_txt_path = os.path.join(folder_path, 'word.txt')
        
        if os.path.exists(word_txt_path):
            try:
                with open(word_txt_path, 'r', encoding='utf-8') as f:
                    word = f.read().strip()
                    # Only add if word is not empty
                    if word:
                        data.append({'id': subdir, 'word': word})
            except Exception as e:
                print(f"Error reading {word_txt_path}: {e}")
        else:
            # Optional: print warning if word.txt is missing, but maybe too noisy
            pass
            
    # Sort by ID (numeric if possible, else string)
    try:
        data.sort(key=lambda x: int(x['id']) if x['id'].isdigit() else x['id'])
    except:
        data.sort(key=lambda x: x['id'])
        
    # Write to CSV
    if not output_csv_path:
        output_csv_path = os.path.join(dataset_path, 'index.csv')
        
    print(f"Writing {len(data)} entries to {output_csv_path}...")
    
    try:
        with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
            fieldnames = ['id', 'word']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        print("Done!")
    except Exception as e:
        print(f"Error writing CSV: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate CSV index from MMID extracted folders.")
    parser.add_argument("dataset_path", help="Path to the extracted dataset directory")
    parser.add_argument("--output", help="Path to the output CSV file (default: index.csv in dataset directory)")
    
    args = parser.parse_args()
    
    generate_csv(args.dataset_path, args.output)
