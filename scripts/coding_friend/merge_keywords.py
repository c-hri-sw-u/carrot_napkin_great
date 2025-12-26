import csv
import os

def parse_markdown_table(md_file):
    keywords_map = {}
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Skip header and separator lines if they exist
        # Assuming format: | English Word | Search Keywords |
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('|') or '---' in line:
                continue
            if 'English Word' in line and 'Search Keywords' in line:
                continue
                
            parts = [p.strip() for p in line.split('|')]
            # split results in ['', 'word', 'keywords', ''] usually
            if len(parts) >= 3:
                word = parts[1]
                keywords = parts[2]
                if word and keywords:
                    keywords_map[word] = keywords
    except Exception as e:
        print(f"Error reading Markdown file: {e}")
        return {}
    
    return keywords_map

def update_csv_with_keywords(csv_file, keywords_map):
    updated_rows = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            
            # Check if 'Search Keywords' column already exists
            keyword_idx = -1
            if 'Search Keywords' in header:
                keyword_idx = header.index('Search Keywords')
            else:
                # Insert after 'English Word' (index 0)
                header.insert(1, 'Search Keywords')
                keyword_idx = 1
            
            updated_rows.append(header)
            
            for row in reader:
                if not row:
                    continue
                    
                word = row[0]
                keywords = keywords_map.get(word, "")
                
                # If column existed, update it
                if keyword_idx < len(row):
                     # If we are inserting a new column, the row length might be short or long
                     # Wait, if we added to header, we need to restructure the row
                     if 'Search Keywords' in header and len(row) == len(header):
                         # Column existed and row has it
                         if keywords:
                             row[keyword_idx] = keywords
                     elif 'Search Keywords' in header and len(row) < len(header):
                          # Column added to header, but row doesn't have it yet (if we are appending)
                          # But here we are rewriting.
                          # If we inserted at index 1
                          row.insert(1, keywords)
                else:
                    # Fallback for safe insert
                    if len(row) >= 1:
                        row.insert(1, keywords)
                    else:
                        row.append(keywords)
                
                updated_rows.append(row)
                
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    try:
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(updated_rows)
        print(f"Successfully updated {csv_file} with search keywords.")
    except Exception as e:
        print(f"Error writing CSV file: {e}")

if __name__ == "__main__":
    base_dir = os.getcwd()
    md_file = os.path.join(base_dir, "coding_friend_vocabulary", "search_keywords.md")
    csv_file = os.path.join(base_dir, "all_english_words.csv") # Assuming it's in root based on previous context
    # Or checking if it's in vocabulary folder? Previous LS showed it in root.
    
    if not os.path.exists(csv_file):
        # Check alternate location just in case
        alt_csv = os.path.join(base_dir, "coding_friend_vocabulary", "all_english_words.csv")
        if os.path.exists(alt_csv):
            csv_file = alt_csv
    
    print(f"Reading keywords from: {md_file}")
    print(f"Updating CSV: {csv_file}")
    
    if os.path.exists(md_file) and os.path.exists(csv_file):
        mapping = parse_markdown_table(md_file)
        if mapping:
            update_csv_with_keywords(csv_file, mapping)
        else:
            print("No keywords found in Markdown file.")
    else:
        print("Files not found.")
