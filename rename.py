import os
import re

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return

    # Replacements
    new_content = re.sub(r'swayamfill', 'swayamfill', content)
    new_content = re.sub(r'swayamfill', 'swayamfill', new_content)
    new_content = re.sub(r'swayamfill', 'swayamfill', new_content)
    new_content = re.sub(r'swayamfill', 'swayamfill', new_content, flags=re.IGNORECASE)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

for root, dirs, files in os.walk('.'):
    # Skip .git and binary directories/files
    if '.git' in root or 'app-releases' in root or '.firebase' in root:
        continue
    for file in files:
        if file.endswith('.apk'): continue
        replace_in_file(os.path.join(root, file))

