import os
import csv

# Define paths
base_dir = os.getcwd()
bad_img_dir = os.path.join(base_dir, "coding_friend_vocabulary", "~assets", "img", "bad")
main_csv_path = os.path.join(base_dir, "coding_friend_vocabulary", "all_english_words.csv")
retry_csv_path = os.path.join(base_dir, "coding_friend_vocabulary", "bad_words_retry.csv")

# Better keywords mapping (manual improvement based on file list)
better_keywords = {
    "(I/you/we/they) can": "I can do it concept",
    "Hello!": "greeting handshake",
    "How much is it?": "price tag",
    "How …?": "question mark puzzle",
    "Monday": "Monday coffee cup",
    "No problem!": "ok gesture",
    "Saturday": "Saturday park relax",
    "Sunday": "Sunday relaxation hammock",
    "Thursday": "Thursday calendar page",
    "Tuesday": "Tuesday calendar page",
    "What is …?": "person thinking question",
    "address": "house number plate",
    "adult": "diverse group of adults",
    "arm": "strong arm biceps",
    "back": "person looking away back view",
    "bag": "shopping bag",
    "bar": "pub beer taps",
    "beach": "beach umbrella",
    "blue": "blue paint texture",
    "bright": "bright sun",
    "café": "coffee cup latte art",
    "cheese": "cheese wedge",
    "colorful": "rainbow colors",
    "date of birth": "birthday cake candle",
    "earlier": "sunrise alarm clock",
    "fruits": "fruit basket",
    "hand": "handshake business",
    "head": "human head anatomy model",
    "hospital": "hospital room interior",
    "hotel": "luxury hotel bedroom",
    "hundred": "100 percent sign",
    "internet": "world wide web globe",
    "lake": "calm lake reflection",
    "last name": "hello my name is sticker",
    "later": "sticky note with text later",
    "leg": "human leg isolated",
    "museum": "ancient statue museum",
    "new": "brand new tag",
    "nine": "9 number balloon",
    "no": "forbidden sign",
    "on foot": "walking shoes",
    "on time": "man looking at wrist watch",
    "painkiller": "medicine pills",
    "pharmacy": "pharmacy green cross sign",
    "rain": "rainy window",
    "restaurant": "restaurant table setting",
    "river": "river stream forest",
    "socket": "electrical outlet wall",
    "sun": "sunny day sky",
    "tampon": "feminine hygiene product",
    "tea": "cup of tea with lemon",
    "time": "clock face",
    "to ask": "raising hand in class",
    "to be": "meditation silhouette",
    "to call": "smartphone call screen",
    "to give": "gift giving hands",
    "to recharge": "charging battery icon",
    "to take": "picking an apple",
    "to want": "person dreaming bubble",
    "train": "high speed train",
    "train station": "subway station platform",
    "tram": "tram in city",
    "vegetarian": "vegetables heart shape",
    "way": "road sign way",
    "white": "white fluffy clouds",
    "year": "new year fireworks"
}

def create_retry_csv():
    # 1. Get list of bad files
    if not os.path.exists(bad_img_dir):
        print(f"Directory not found: {bad_img_dir}")
        return

    bad_files = set(os.listdir(bad_img_dir))
    print(f"Found {len(bad_files)} files in bad directory.")

    # 2. Read main CSV to link files to words
    words_to_retry = []
    
    try:
        with open(main_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                img_file = row.get("Image File")
                if img_file and img_file in bad_files:
                    word = row["English Word"]
                    old_keyword = row.get("Search Keywords", "")
                    
                    # Determine new keyword
                    new_keyword = better_keywords.get(word, old_keyword + " high quality") # Fallback if not in manual list
                    
                    words_to_retry.append({
                        "English Word": word,
                        "Search Keywords": new_keyword,
                        "Image File": img_file # Keep for reference, but download script will ignore or overwrite in new dir
                    })
    except Exception as e:
        print(f"Error reading main CSV: {e}")
        return

    # 3. Write to new CSV
    if words_to_retry:
        with open(retry_csv_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ["English Word", "Search Keywords", "Image File"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(words_to_retry)
        print(f"Created {retry_csv_path} with {len(words_to_retry)} entries.")
    else:
        print("No matching words found for bad images.")

if __name__ == "__main__":
    create_retry_csv()
