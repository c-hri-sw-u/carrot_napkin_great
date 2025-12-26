import os
import json

root_dir = "coding_friend_vocabulary/~assets/img"
manifest = []

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            # path relative to project root
            # dirpath is e.g. "coding_friend_vocabulary/~assets/img"
            # we want "coding_friend_vocabulary/~assets/img/filename"
            full_path = os.path.join(dirpath, filename)
            manifest.append(full_path)

# Write to manifest.js
with open("manifest.js", "w") as f:
    f.write("const IMAGE_MANIFEST = ")
    json.dump(manifest, f, indent=2)
    f.write(";")
