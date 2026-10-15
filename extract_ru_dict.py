import re
import json
from pathlib import Path

repo_root = Path(__file__).parent
dom_file = repo_root / "translations" / "dom_translator.js"

with open(dom_file, "r", encoding="utf-8") as f:
    text = f.read()

m = re.search(r'const DICT = \{(.*?)\n  \};', text, re.DOTALL)
if not m:
    print("Could not find DICT in dom_translator.js")
    exit(1)

dict_str = "{" + m.group(1) + "\n}"
# Parse JSON-like key-value pairs
ru_dict = {}
for line in m.group(1).splitlines():
    line = line.strip()
    if not line or line.startswith("//"):
        continue
    # Match "key": "value"
    pm = re.match(r'^"(.*)"\s*:\s*"(.*)",?$', line)
    if pm:
        k = pm.group(1).replace(r'\"', '"').replace(r'\\', '\\')
        v = pm.group(2).replace(r'\"', '"').replace(r'\\', '\\')
        ru_dict[k] = v

print(f"Extracted {len(ru_dict)} terms from dom_translator.js")

# Merge with resources/web_bundle_ru/i18n-ru.js if it exists
i18n_ru_file = repo_root / "resources" / "web_bundle_ru" / "i18n-ru.js"
if i18n_ru_file.exists():
    with open(i18n_ru_file, "r", encoding="utf-8") as f:
        i18n_text = f.read()
    m2 = re.search(r'const DICT = \{(.*?)\n  \};', i18n_text, re.DOTALL)
    if m2:
        added = 0
        for line in m2.group(1).splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            pm = re.match(r'^"(.*)"\s*:\s*"(.*)",?$', line)
            if pm:
                k = pm.group(1).replace(r'\"', '"').replace(r'\\', '\\')
                v = pm.group(2).replace(r'\"', '"').replace(r'\\', '\\')
                if k not in ru_dict:
                    ru_dict[k] = v
                    added += 1
        print(f"Merged additional {added} terms from i18n-ru.js (total: {len(ru_dict)})")

# Save to translations/languages/ru/dict.json
ru_dir = repo_root / "translations" / "languages" / "ru"
ru_dir.mkdir(parents=True, exist_ok=True)

with open(ru_dir / "dict.json", "w", encoding="utf-8") as f:
    json.dump(ru_dict, f, ensure_ascii=False, indent=2)

ru_meta = {
    "code": "ru",
    "name": "Russian",
    "nativeName": "Русский",
    "version": "1.0.0",
    "translatorTarget": "ru",
    "flag": "🇷🇺",
    "buttonLabel": "🌐 RU",
    "buttonTitle": "Перевести размышления на русский",
    "autoLabelOn": "⚡ Авто: ВКЛ",
    "autoLabelOff": "⚡ Авто: ВЫКЛ",
    "autoTitle": "Автоперевод мыслей",
    "vscodeLocale": "ru"
}
with open(ru_dir / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(ru_meta, f, ensure_ascii=False, indent=2)

# Copy desktop and ide strings
desktop_src = repo_root / "translations" / "desktop_strings.json"
if desktop_src.exists():
    with open(desktop_src, "r", encoding="utf-8") as f:
        desktop_data = json.load(f)
    with open(ru_dir / "desktop.json", "w", encoding="utf-8") as f:
        json.dump(desktop_data, f, ensure_ascii=False, indent=2)

ide_src = repo_root / "translations" / "ide_strings.json"
if ide_src.exists():
    with open(ide_src, "r", encoding="utf-8") as f:
        ide_data = json.load(f)
    with open(ru_dir / "ide.json", "w", encoding="utf-8") as f:
        json.dump(ide_data, f, ensure_ascii=False, indent=2)

print("Russian language pack initialized successfully.")
