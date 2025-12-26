import os
import json

packages = [
    'scale-german-package-k3',
    'scale-japanese-package-k3',
    'scale-spanish-package-k3'
]

manifest = {}

for pkg in packages:
    if not os.path.exists(pkg):
        continue
        
    manifest[pkg] = {}
    
    # Iterate through all subdirectories (which are IDs)
    for entry in os.scandir(pkg):
        if entry.is_dir():
            folder_id = entry.name
            images = []
            
            # Look for images in the folder
            for file in os.scandir(entry.path):
                if file.is_file() and file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    images.append(file.name)
            
            if images:
                manifest[pkg][folder_id] = images

# Scan Audio Files
audio_manifest = {
    'posi': [],
    'neg': [],
    'cat': []
}

audio_base = 'assets/audio'
if os.path.exists(audio_base):
    # Scan Posi
    posi_path = os.path.join(audio_base, 'human', 'posi')
    if os.path.exists(posi_path):
        for f in os.scandir(posi_path):
            if f.is_file() and f.name.lower().endswith('.mp3'):
                audio_manifest['posi'].append(f.name)

    # Scan Neg
    neg_path = os.path.join(audio_base, 'human', 'neg')
    if os.path.exists(neg_path):
        for f in os.scandir(neg_path):
            if f.is_file() and f.name.lower().endswith('.mp3'):
                audio_manifest['neg'].append(f.name)

    # Scan Cat
    cat_path = os.path.join(audio_base, 'cat')
    if os.path.exists(cat_path):
        for f in os.scandir(cat_path):
            if f.is_file() and f.name.lower().endswith('.mp3'):
                audio_manifest['cat'].append(f.name)

# Scan Characters
character_manifest = []
char_base = 'assets/img'
if os.path.exists(char_base):
    for entry in os.scandir(char_base):
        if entry.is_dir():
            # Check if idle.png exists in this folder
            idle_path = os.path.join(entry.path, 'idle.png')
            if os.path.exists(idle_path):
                character_manifest.append(entry.name)

# Sort for consistency
character_manifest.sort()

# Write to package_manifest.js
with open("package_manifest.js", "w") as f:
    f.write("const PACKAGE_MANIFEST = ")
    json.dump(manifest, f, indent=2)
    f.write(";\n\n")
    f.write("const AUDIO_MANIFEST = ")
    json.dump(audio_manifest, f, indent=2)
    f.write(";\n\n")
    f.write("const CHARACTER_MANIFEST = ")
    json.dump(character_manifest, f, indent=2)
    f.write(";")

print("Manifest generated.")
