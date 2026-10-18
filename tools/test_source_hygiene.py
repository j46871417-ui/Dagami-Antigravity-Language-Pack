"""Behavior checks for the source guard; all repositories are disposable fixtures."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

CHECKER=Path(__file__).with_name('check_source_hygiene.py')

class SourceGuardChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='source-guard-')
        self.root=Path(self.temp.name)
        (self.root/'tools').mkdir()
        shutil.copy2(CHECKER,self.root/'tools/check_source_hygiene.py')
        (self.root/'tools/source-policy.json').write_text('{"allowed_duplicate_groups": []}')
        (self.root/'.gitignore').write_text('.env\n')
        self.git('init','--quiet')
        self.git('add','tools','.gitignore')

    def tearDown(self): self.temp.cleanup()

    def git(self,*args):
        return subprocess.run(['git','-c',f'safe.directory={self.root.as_posix()}','-C',str(self.root),*args],check=True,capture_output=True)

    def check(self):
        return subprocess.run(['python',str(self.root/'tools/check_source_hygiene.py')],capture_output=True,text=True)

    def test_staged_secret_cannot_be_hidden_by_editing_worktree(self):
        (self.root/'settings.txt').write_text('credential='+'ghp_'+'aB7cD9eF2gH4jK6mN8pQ1rS3tU5vW0xY9zA7bC6d')
        self.git('add','settings.txt')
        (self.root/'settings.txt').write_text('credential=example')
        result=self.check()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('GitHub token',result.stderr)
        self.assertNotIn('aB7cD9eF',result.stderr)

    def test_forced_ignored_file_is_rejected(self):
        (self.root/'.env').write_text('SETTING=example')
        self.git('add','--force','.env')
        self.assertIn('Tracked ignored file: .env',self.check().stderr)

    def test_new_duplicate_is_rejected(self):
        (self.root/'one.txt').write_text('one canonical copy')
        (self.root/'copy.txt').write_text('one canonical copy')
        self.git('add','one.txt','copy.txt')
        self.assertIn('Unexpected exact duplicate',self.check().stderr)

if __name__=='__main__': unittest.main()
