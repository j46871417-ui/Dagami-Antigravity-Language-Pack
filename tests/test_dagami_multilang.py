"""
Tests for Dagami Antigravity Language Pack — Multilingual support and CLI.
"""

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import dagami_translator_builder as dtb
import dagami_ag_localizer as dal


class TestDagamiMultilingualPacks(unittest.TestCase):

    def test_all_standard_languages_available(self):
        langs = dal.list_available_languages()
        codes = [l["code"] for l in langs]
        self.assertIn("ru", codes)
        self.assertIn("zh", codes)
        self.assertIn("es", codes)
        self.assertIn("ja", codes)

    def test_metadata_fields(self):
        for code in ["ru", "zh", "es", "ja"]:
            meta = dtb.get_language_metadata(code)
            self.assertEqual(meta["code"], code)
            self.assertIn("name", meta)
            self.assertIn("nativeName", meta)
            self.assertIn("translatorTarget", meta)
            self.assertIn("buttonLabel", meta)

    def test_dictionaries_not_empty(self):
        for code in ["ru", "zh", "es", "ja"]:
            d = dtb.get_language_dictionary(code)
            self.assertGreater(len(d), 0, f"Dictionary for {code} is empty")

    def test_build_runtime_translator_marker(self):
        for code in ["ru", "zh", "es", "ja"]:
            js = dtb.build_runtime_translator_js(code)
            self.assertTrue(
                js.startswith(dal.PRELOAD_MARKER),
                f"Generated JS for {code} must start with PRELOAD_MARKER"
            )
            # Must contain donation and telegram links
            self.assertIn("https://pay.cloudtips.ru/p/671fda86", js)
            self.assertIn("https://t.me/+8qU7020rMF84OWNi", js)

    def test_build_runtime_translator_target_lang(self):
        js_ru = dtb.build_runtime_translator_js("ru")
        self.assertIn('TARGET_LANG = "ru"', js_ru)

        js_zh = dtb.build_runtime_translator_js("zh")
        self.assertIn('TARGET_LANG = "zh-CN"', js_zh)

        js_es = dtb.build_runtime_translator_js("es")
        self.assertIn('TARGET_LANG = "es"', js_es)

    def test_switching_languages_idempotent(self):
        base_preload = 'const { contextBridge } = require("electron");\n'
        js_ru = dtb.build_runtime_translator_js("ru")
        js_zh = dtb.build_runtime_translator_js("zh")
        js_es = dtb.build_runtime_translator_js("es")

        # Step 1: Install RU
        step1 = dal.inject_dom_translator(base_preload, js_ru)
        self.assertEqual(step1.count(dal.PRELOAD_MARKER), 1)
        self.assertIn('TARGET_LANG = "ru"', step1)

        # Step 2: Switch to ZH
        step2 = dal.inject_dom_translator(step1, js_zh)
        self.assertEqual(step2.count(dal.PRELOAD_MARKER), 1)
        self.assertIn('TARGET_LANG = "zh-CN"', step2)
        self.assertNotIn('TARGET_LANG = "ru"', step2)

        # Step 3: Switch to ES
        step3 = dal.inject_dom_translator(step2, js_es)
        self.assertEqual(step3.count(dal.PRELOAD_MARKER), 1)
        self.assertIn('TARGET_LANG = "es"', step3)
        self.assertNotIn('TARGET_LANG = "zh-CN"', step3)

    def test_action_card_rules_present(self):
        for code in ["ru", "zh", "es", "ja", "de", "fr"]:
            js = dtb.build_runtime_translator_js(code)
            self.assertIn("Searching for", js)
            self.assertIn("Thought for", js)
            self.assertIn("Reading", js)
            self.assertIn("Editing", js)

    def test_thought_toolbar_styling_and_isolation(self):
        js = dtb.build_runtime_translator_js("ru")
        self.assertIn("display:inline-flex !important", js)
        self.assertIn("white-space:nowrap !important", js)
        self.assertIn("ag-thought-overlay", js)
        self.assertIn("stopEvt", js)


if __name__ == "__main__":
    unittest.main()
