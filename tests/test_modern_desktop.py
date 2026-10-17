import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent/"fixtures"))
import mini_asar
import dagami_ag_localizer as app

class ModernDesktop(unittest.TestCase):
    def test_modern_patch_repeat_switch_and_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/"resources").mkdir();(root/"Antigravity.exe").write_bytes(b"fixture")
            asar=root/"resources"/"app.asar"
            mini_asar.build_mini_asar(asar,{"package.json":json.dumps({"version":"2.23.1"}).encode(),
                "dist/preload.js":b'const value = 1;\n',"dist/menu.js":b"const text='File';","dist/main.js":b"const text='Open';","unknown.bin":bytes(range(256))})
            original=asar.read_bytes()
            localizer=app.DagamiLocalizer(desktop_path=root,no_kill=True,log_fn=lambda *_:None)
            self.assertTrue(localizer.install_desktop("ru"))
            header,data=app.read_asar(asar)
            item=header["files"]["dist"]["files"]["preload.js"]
            js=data[int(item["offset"]):int(item["offset"])+item["size"]].decode()
            self.assertIn("StructuredThoughts.install",js);self.assertNotIn("holder.innerText = tr",js)
            unknown=header["files"]["unknown.bin"]
            self.assertEqual(data[int(unknown["offset"]):int(unknown["offset"])+unknown["size"]],bytes(range(256)))
            first=asar.read_bytes();self.assertTrue(localizer.install_desktop("ru"));self.assertEqual(asar.read_bytes(),first)
            self.assertTrue(localizer.install_desktop("es"))
            header,data=app.read_asar(asar);item=header["files"]["dist"]["files"]["preload.js"]
            js=data[int(item["offset"]):int(item["offset"])+item["size"]].decode()
            self.assertIn('TARGET_LANG = "es"',js);self.assertEqual(js.count(app.PRELOAD_MARKER),1)
            self.assertTrue(localizer.restore_all());self.assertEqual(asar.read_bytes(),original)

if __name__=="__main__":unittest.main()
