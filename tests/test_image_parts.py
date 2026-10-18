import importlib.util, tempfile, unittest, struct, zlib
from pathlib import Path
spec=importlib.util.spec_from_file_location('parts',Path(__file__).resolve().parents[1]/'tools/image_parts.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def fixture():
    data=bytearray(1024*1024);table=bytearray(128*128)
    table[:16]=b'1'*16;table[16:32]=b'2'*16;struct.pack_into('<QQ',table,32,40,47)
    data[1024:1024+len(table)]=table
    h=bytearray(512);h[:8]=b'EFI PART';struct.pack_into('<II',h,8,0x10000,92)
    struct.pack_into('<QQQQ',h,24,1,2047,34,2014)
    struct.pack_into('<QIII',h,72,2,128,128,zlib.crc32(table))
    struct.pack_into('<I',h,16,zlib.crc32(h[:92]));data[512:1024]=h
    return data
class ImageParts(unittest.TestCase):
    def test_partition_replacement_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            image=Path(d)/'disk';piece=Path(d)/'part';out=Path(d)/'out'
            before=fixture();image.write_bytes(before);piece.write_bytes(b'X'*4096)
            m.replace(image,1,piece);after=image.read_bytes()
            self.assertEqual(before[:40*512],after[:40*512]);self.assertEqual(before[48*512:],after[48*512:])
            m.extract(image,1,out);self.assertEqual(out.read_bytes(),piece.read_bytes())
    def test_crc_and_size_reject_without_write(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'disk';part=Path(d)/'part';p.write_bytes(fixture());part.write_bytes(b'x')
            before=p.read_bytes()
            with self.assertRaises(ValueError):m.replace(p,1,part)
            self.assertEqual(before,p.read_bytes())
            bad=fixture();bad[16+512]^=1;p.write_bytes(bad)
            with m.open_regular(p) as f:
                with self.assertRaises(ValueError):m.geometry(f)
    def test_symlink_and_device_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'link';p.symlink_to('/dev/null')
            with self.assertRaises(OSError):m.open_regular(p)
            with self.assertRaises(ValueError):m.open_regular('/dev/null')
