"""Check staged sources without printing credentials or using third-party packages."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
GIT = ['git', '-c', f'safe.directory={ROOT.as_posix()}', '-C', str(ROOT)]
PATTERNS = {
    'GitHub token': rb'\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{40,})',
    'Telegram bot token': rb'\b[0-9]{6,12}:[A-Za-z0-9_-]{30,}\b',
    'private key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'OpenAI key': rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}',
    'AWS access ID': rb'\bAKIA[A-Z0-9]{16}\b',
    'Google API key': rb'\bAIza[0-9A-Za-z_-]{35}\b',
}

def main():
    issues=[]
    for raw in subprocess.check_output(GIT+['ls-files','-ci','--exclude-standard','-z']).split(b'\0'):
        if raw: issues.append('Tracked ignored file: '+raw.decode('utf-8','replace'))
    entries=[]
    for raw in subprocess.check_output(GIT+['ls-files','-s','-z']).split(b'\0'):
        if not raw: continue
        info,name=raw.split(b'\t',1)
        mode,oid,stage=info.split()
        if stage!=b'0': issues.append('Unresolved merge: '+name.decode()); continue
        if mode==b'160000': continue
        entries.append((oid.decode(),name.decode('utf-8')))
    queries=''.join(oid+'\n' for oid,_ in entries).encode()
    proc=subprocess.run(GIT+['cat-file','--batch'],input=queries,stdout=subprocess.PIPE,check=True)
    offset=0; groups=defaultdict(list)
    for _,name in entries:
        end=proc.stdout.index(b'\n',offset)
        header=proc.stdout[offset:end].split()
        size=int(header[2]); offset=end+1
        data=proc.stdout[offset:offset+size]; offset+=size+1
        if data: groups[hashlib.sha256(data).hexdigest()].append(name)
        for label,pattern in PATTERNS.items():
            for match in re.finditer(pattern,data):
                line=data[:match.start()].count(b'\n')+1
                issues.append(f'{name}:{line}: possible {label}; value withheld')
    # Intentional install-layout resources are explicit; a new copy is rejected.
    policy_data=subprocess.check_output(GIT+['show',':tools/source-policy.json'])
    allowed=[set(group) for group in json.loads(policy_data)['allowed_duplicate_groups']]
    for paths in groups.values():
        if len(paths)>1 and not any(set(paths)<=group for group in allowed):
            issues.append('Unexpected exact duplicate: '+', '.join(paths))
    if issues:
        print('\n'.join(issues),file=sys.stderr); return 1
    print(f'PASS: {len(entries)} staged source files; no ignored files, new copies or known secret formats')
    return 0

if __name__=='__main__': raise SystemExit(main())
