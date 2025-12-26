import os
import csv

def extract_english_words(root_dir, output_file):
    english_words = set()
    
    # Walk through the directory
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith('.csv') and filename != output_file:
                file_path = os.path.join(dirpath, filename)
                # Skip the output file if it's in the directory being scanned (though we save to root usually)
                if os.path.abspath(file_path) == os.path.abspath(output_file):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # Inspect the first line to sniff the format if needed, but assuming ';' based on checks
                        reader = csv.reader(f, delimiter=';')
                        for row in reader:
                            if len(row) > 1:
                                word = row[1].strip()
                                if word:
                                    english_words.add(word)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    # Write to output file
    try:
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['English Word'])  # Header
            for word in sorted(english_words):
                writer.writerow([word])
        print(f"Successfully extracted {len(english_words)} unique English words to {output_file}")
    except Exception as e:
        print(f"Error writing to {output_file}: {e}")

if __name__ == "__main__":
    vocabulary_dir = "/Users/chriswu/Documents/GitHub/carrot_napkin_great/coding_friend_vocabulary"
    output_csv = "all_english_words.csv"
    extract_english_words(vocabulary_dir, output_csv)
