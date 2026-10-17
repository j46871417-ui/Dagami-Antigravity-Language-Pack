import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app_updates as u
import dagami_ag_localizer as app
from tests.test_app_updates import release

@unittest.skipUnless(sys.platform=="win32","Tk GUI checked on Windows")
class GuiUpdates(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        self.temp=tempfile.TemporaryDirectory();self.env=patch.dict(os.environ,{"DAGAMI_LANGUAGE_STATE":self.temp.name});self.env.start()
        u.save_settings(False,False)
        self.root=tk.Tk();self.root.withdraw();self.gui=app.DagamiGUI(self.root)
        self.errors=[];self.root.report_callback_exception=lambda *args:self.errors.append(args)
    def tearDown(self):
        if not self.gui.updates.closed:self.gui.close()
        self.env.stop();self.temp.cleanup()
    def wait(self):
        deadline=time.monotonic()+4
        while self.gui.updates.running and time.monotonic()<deadline:self.root.update();time.sleep(.02)
        self.root.update();self.assertFalse(self.gui.updates.running);self.assertEqual(self.errors,[])
    def test_background_check_never_downloads(self):
        with patch.object(u,"check",return_value=release()),patch.object(u,"download") as download:
            self.gui.updates.check();self.wait();download.assert_not_called()
        self.assertEqual(self.gui.updates.button.cget("text"),"Обновить")
    def test_dialog_and_opt_in(self):
        self.gui.updates.open();self.root.update()
        self.assertFalse(self.gui.updates.automatic_var.get());self.assertFalse(self.gui.updates.pre_var.get())
        self.assertEqual(str(self.gui.updates.install_button.cget("state")),"disabled")
        self.assertGreater(self.gui.updates.dialog.winfo_reqheight(),200)
    def test_active_patch_blocks_install(self):
        self.gui._busy=True;self.gui.updates.release=release()
        with patch.object(u,"download") as download:self.gui.updates.install();download.assert_not_called()
    def test_source_download_never_installs(self):
        self.gui.updates.release=release()
        with patch.object(u,"download",return_value=Path(self.temp.name)/"download.exe"),patch.object(u,"start_install") as install:
            self.gui.updates.install();self.wait();install.assert_not_called()
        self.assertFalse(self.gui._update_busy)
    def test_ready_installer_closes_cleanly(self):
        self.gui.updates.release=release()
        with patch.object(sys,"frozen",True,create=True),patch.object(u,"download",return_value=Path(self.temp.name)/"download.exe"),patch.object(u,"start_install",return_value=Path(self.temp.name)/"plan.dat"):
            self.gui.updates.install()
            deadline=time.monotonic()+3
            while not self.gui.updates.closed and time.monotonic()<deadline:self.root.update();time.sleep(.02)
        self.assertTrue(self.gui.updates.closed);self.assertEqual(self.errors,[])

if __name__=="__main__":unittest.main()
