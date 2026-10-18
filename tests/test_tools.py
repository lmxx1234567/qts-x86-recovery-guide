import gzip, importlib.util, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
pack=module('pack_overlay');manifest=module('manifest')
class Tools(unittest.TestCase):
    def test_newc_roundtrip(self):
        raw=gzip.decompress(pack.build(b'model',b'#!/bin/sh\n'))
        pos=0;found={}
        while pos<len(raw):
            self.assertEqual(raw[pos:pos+6],b'070701')
            fields=[int(raw[pos+6+i*8:pos+14+i*8],16) for i in range(13)]
            size,namesize=fields[6],fields[11];pos+=110
            name=raw[pos:pos+namesize-1].decode();pos+=namesize;pos=(pos+3)//4*4
            data=raw[pos:pos+size];pos+=size;pos=(pos+3)//4*4
            found[name]=(data,fields[1])
            if name=='TRAILER!!!':break
        self.assertEqual(found['sbin/init'],(b'#!/bin/sh\n',0o100755))
        self.assertEqual(found['qts-profile/model.conf'],(b'model',0o100644))
    def test_archive_traversal(self):
        for name in ['/etc/passwd','../bad','a/../b']:
            with self.assertRaises(ValueError):pack.newc(name,b'',0,1)
    def test_template_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input';p.write_text('REPLACE_SERIAL')
            with self.assertRaises(ValueError):pack.regular(p)
            link=Path(d)/'link';link.symlink_to(p)
            with self.assertRaises(ValueError):pack.regular(link)
    def test_manifest_detects_changed_content(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'sample';p.write_bytes(b'abc');a=manifest.record(d,'sample')
            p.write_bytes(b'abd');b=manifest.record(d,'sample')
            self.assertEqual(a['size'],b['size']);self.assertNotEqual(a['sha256'],b['sha256'])
    def test_manifest_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):manifest.record(d,'../outside')
    def test_walkthrough_shell_syntax(self):
        import re, subprocess
        text=(ROOT/'docs/10-command-walkthrough.md').read_text()
        for i,block in enumerate(re.findall(r'```(?:bash|sh)\n(.*?)```',text,re.S),1):
            result=subprocess.run(['bash','-n'],input=block,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,f'block {i}: {result.stderr}')
    def test_local_markdown_links(self):
        import re
        for p in ROOT.rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
                if '://' in link or link.startswith('#'):continue
                self.assertTrue((p.parent/link.split('#')[0]).exists(),f'{p}: {link}')
if __name__=='__main__':unittest.main()
