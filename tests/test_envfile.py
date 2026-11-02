import os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from nexus_learning.envfile import load_local_env

class EnvFileTests(unittest.TestCase):
    def test_loads_values_without_overriding_process_and_rejects_large_file(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d,'.env').write_text('GEMINI_API_KEY=local-secret\nNEXUS_PROVIDER="gemini"\n# comment\nINVALID-NAME=x\n',encoding='utf-8')
            with patch.dict(os.environ,{'NEXUS_PROVIDER':'mock'},clear=True):
                self.assertTrue(load_local_env(d))
                self.assertEqual(os.environ['GEMINI_API_KEY'],'local-secret')
                self.assertEqual(os.environ['NEXUS_PROVIDER'],'mock')
                self.assertNotIn('local-secret',str(Path(d,'.env')))
            Path(d,'.env').write_text('X='+('x'*65000),encoding='utf-8')
            with self.assertRaises(ValueError): load_local_env(d)

if __name__=='__main__': unittest.main()
