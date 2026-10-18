import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app_updates as u

def release(tag="v1.2.1", data=b"MZ"+b"x"*1022):
    name="AntigravityLocalizer.exe"
    return {"tag":tag,"page":"https://github.com/"+u.REPOSITORY+"/releases/tag/"+tag,
            "name":name,"url":"https://github.com/"+u.REPOSITORY+"/releases/download/"+tag+"/"+name,
            "size":len(data),"sha256":hashlib.sha256(data).hexdigest(),"notes":"text"}
def feed(value):
    return {"tag_name":value["tag"],"html_url":value["page"],"draft":False,"prerelease":"-" in value["tag"],
            "body":value["notes"],"assets":[{"name":value["name"],"browser_download_url":value["url"],"size":value["size"],"digest":"sha256:"+value["sha256"]}]}

class UpdateChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{"DAGAMI_LANGUAGE_STATE":str(self.root/"updates")});self.env.start()
    def tearDown(self):self.env.stop();self.temp.cleanup()
    def test_numeric_versions(self):self.assertGreater(u.version_key("v1.10.0"),u.version_key("1.9.99"))
    def test_alpha_numeric(self):self.assertGreater(u.version_key("1.2.0-alpha.10"),u.version_key("1.2.0-alpha.2"))
    def test_stable_after_pre(self):self.assertGreater(u.version_key("1.2.0"),u.version_key("1.2.0-rc.9"))
    def test_bad_versions(self):
        for v in ("1.2","v01.2.0","1.2.0-alpha.01","1.2.0-a..b","v1.2.0;evil"):
            with self.assertRaises(ValueError):u.version_key(v)
    def test_build_metadata(self):self.assertEqual(u.version_key("1.2.0+build"),u.version_key("v1.2.0"))
    def test_redirect_hosts(self):
        for url in ("https://api.github.com/repos/a/b","https://release-assets.githubusercontent.com/path?sig=test"):
            self.assertTrue(u.allowed(url))
    def test_bad_redirects(self):
        for url in ("http://github.com/a","https://github.com.evil.test/x","https://user:secret@github.com/x","https://github.com:8443/x","file:///x","https://github.com/x#fragment"):
            self.assertFalse(u.allowed(url))
    def test_select_newest(self):self.assertEqual(u.select_release([feed(release("v1.2.9")),feed(release("v1.10.0"))],platform="win32")["tag"],"v1.10.0")
    def test_no_drafts(self):
        f=feed(release());f["draft"]=True;self.assertIsNone(u.select_release([f],platform="win32"))
    def test_prerelease_opt_in(self):
        f=feed(release("v1.3.0-alpha.1"));self.assertIsNone(u.select_release([f],platform="win32"))
        self.assertIsNotNone(u.select_release([f],True,"win32"))
    def test_digest_required(self):
        f=feed(release());f["assets"][0].pop("digest");self.assertIsNone(u.select_release([f],platform="win32"))
    def test_wrong_repo_rejected(self):
        f=feed(release());f["assets"][0]["browser_download_url"]=f["assets"][0]["browser_download_url"].replace(u.REPOSITORY,"evil/repo")
        self.assertIsNone(u.select_release([f],platform="win32"))
    def test_negative_size(self):
        r=release();r["size"]=-1
        with self.assertRaises(ValueError):u.validate_release(r)
    def test_asset_limit(self):
        r=release();r["size"]=u.MAX_FILE+1
        with self.assertRaises(ValueError):u.validate_release(r)
    def test_platform_asset(self):
        self.assertRegex(u.asset_name("v1.2.1","darwin"), r"^DagamiAntigravityLanguagePack-v1\.2\.1-macOS-(?:x64|arm64)\.tar\.gz$")
        self.assertRegex(u.asset_name("v1.2.1","linux"), r"^DagamiAntigravityLanguagePack-v1\.2\.1-Linux-(?:x64|arm64)\.tar\.gz$")
    def test_foreign_asset_name(self):
        r=release();r["name"]="../../evil.exe"
        with self.assertRaises(ValueError):u.validate_release(r)
    def test_same_version_not_newer(self):self.assertFalse(u.newer(release("v"+u.APP_VERSION)))
    def test_old_version_not_newer(self):self.assertFalse(u.newer(release("v1.1.0")))
    def test_future_version_newer(self):self.assertTrue(u.newer(release()))
    def test_preferences(self):
        self.assertEqual(u.settings(),{"automatic":True,"prereleases":False})
        u.save_settings(False,True);self.assertEqual(u.settings(),{"automatic":False,"prereleases":True});self.assertFalse(u.due())
    def test_corrupt_settings(self):
        (u.state_root()/"settings.json").write_text("broken")
        self.assertTrue(u.settings()["automatic"])
    def test_check_interval(self):
        self.assertTrue(u.due());u.save_json(u.state_root()/"check.json",{"checked":u.time.time()});self.assertFalse(u.due())
    def test_corrupt_timestamp(self):
        u.save_json(u.state_root()/"check.json",{"checked":"bad"});self.assertTrue(u.due())
    def test_non_dict_settings(self):
        u.save_json(u.state_root()/"settings.json",[]);self.assertTrue(u.settings()["automatic"])
    def test_nan_timestamp(self):
        u.save_json(u.state_root()/"check.json",{"checked":float("nan")});self.assertTrue(u.due())
    def test_check_only_saves_metadata(self):
        with patch.object(u,"network",return_value=json.dumps([feed(release())]).encode()),patch.object(u.sys,"platform","win32"):
            self.assertEqual(u.check()["tag"],"v1.2.1")
        self.assertFalse((u.state_root()/"staged").exists())
    def test_hash_and_size(self):
        p=self.root/"asset";p.write_bytes(b"MZ"+b"x"*1022);u.verify_download(release(),p)
        p.write_bytes(p.read_bytes()+b"x")
        with self.assertRaises(ValueError):u.verify_download(release(),p)
    def test_equal_size_corruption(self):
        p=self.root/"asset";p.write_bytes(b"MZ"+b"z"*1022)
        with self.assertRaises(ValueError):u.verify_download(release(),p)
    def test_download_failure_cleanup(self):
        def net(url,limit,dest):Path(dest).write_bytes(b"bad")
        with patch.object(u,"network",side_effect=net):
            with self.assertRaises(ValueError):u.download(release())
        self.assertFalse(list((u.state_root()/"staged").rglob("*.exe")))
    def test_malformed_exe(self):
        p=self.root/"bad.exe";p.write_bytes(b"MZ"+b"\0"*100)
        with self.assertRaises(ValueError):u.validate_exe(p,"1.2.1")
    def test_source_never_runs_installer(self):
        with patch.object(u.sys,"frozen",False,create=True):
            with self.assertRaises(OSError):u.start_install(release(),self.root/"anything")
        self.assertFalse((u.state_root()/"attempts").exists())
    def test_foreign_helper_plan_no_write(self):
        p=self.root/"foreign"/"plan.dat";p.parent.mkdir();p.write_bytes(b"bad")
        self.assertEqual(u.run_helper(p),1);self.assertFalse((p.parent/"error.json").exists())
    @unittest.skipUnless(sys.platform=="win32","DPAPI Windows")
    def test_dpapi_tamper(self):
        data=u.protect(b'{"safe":1}');self.assertEqual(u.protect(data,True),b'{"safe":1}')
        changed=bytearray(data);changed[-8]^=1
        with self.assertRaises(OSError):u.protect(bytes(changed),True)
    @unittest.skipUnless(sys.platform=="win32","Windows process identity")
    def test_process_identity(self):
        identity=u.process_identity(os.getpid())
        self.assertEqual(Path(identity["path"]),Path(sys.executable).resolve());self.assertGreater(identity["start"],0)
    @unittest.skipUnless(sys.platform=="win32","Windows process identity")
    def test_exited_process_with_open_parent_handle(self):
        import subprocess
        child=subprocess.Popen([sys.executable,"-c","pass"],env=dict(os.environ))
        child.wait(timeout=10)
        self.assertIsNone(u.process_identity(child.pid))
    def _plan(self):
        folder=self.root/"attempt";folder.mkdir()
        old=self.root/"old.exe";old.write_bytes(b"original EXE")
        payload=self.root/"new.exe";payload.write_bytes(b"MZ"+b"x"*1022)
        return {"target":str(old),"payload":str(payload),"old_sha256":u.file_hash(old),"release":release()},folder,old
    def test_swap_and_backup(self):
        plan,folder,old=self._plan()
        with patch.object(u,"validate_exe"):
            backup=u.install_files(plan,folder)
        self.assertEqual(backup.read_bytes(),b"original EXE");self.assertEqual(u.file_hash(old),plan["release"]["sha256"])
    def test_locked_file_no_change(self):
        plan,folder,old=self._plan()
        with patch.object(u,"validate_exe"):
            with self.assertRaises(PermissionError):u.install_files(plan,folder,replace=lambda *args:(_ for _ in ()).throw(PermissionError()))
        self.assertEqual(old.read_bytes(),b"original EXE")
    def test_late_foreign_change_refused(self):
        plan,folder,old=self._plan();old.write_bytes(b"foreign")
        with patch.object(u,"validate_exe"):
            with self.assertRaises(ValueError):u.install_files(plan,folder)
        self.assertEqual(old.read_bytes(),b"foreign")
    def test_post_write_failure_rolls_back(self):
        plan,folder,old=self._plan();calls=[]
        def validate(path,tag):
            calls.append(str(path))
            if Path(path)==old:raise ValueError("bad post-write")
        with patch.object(u,"validate_exe",side_effect=validate):
            with self.assertRaises(ValueError):u.install_files(plan,folder)
        self.assertEqual(old.read_bytes(),b"original EXE")
        self.assertFalse(list(old.parent.glob(".dagami-update-*.exe")))

if __name__=="__main__":unittest.main()
