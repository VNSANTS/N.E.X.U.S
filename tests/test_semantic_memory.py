import unittest
from nexus_learning.engine import LearningEngine
from nexus_learning.semantic import SemanticMemoryIndex

class FakeEmbedder:
    model='fake-embed'
    def embed(self,text,**kwargs):
        t=text.casefold()
        return [1.0,0.0] if ('bank' in t or 'river' in t) else [0.0,1.0]

class SemanticMemoryTests(unittest.TestCase):
    def setUp(self): self.engine=LearningEngine(':memory:'); self.index=SemanticMemoryIndex(self.engine,FakeEmbedder())
    def tearDown(self): self.engine.close()
    def test_semantic_index_retrieves_related_memory_and_persists_vector(self):
        mid=self.engine.add_memory('semantic','River bank','A stream passes by the bank.')
        self.assertTrue(self.index.index(mid))
        result=self.index.search('bank near river')
        self.assertEqual(result[0]['id'],mid)
    def test_invalid_embedding_values_are_rejected(self):
        with self.assertRaises(ValueError): SemanticMemoryIndex._validate([float('nan')])

if __name__=='__main__': unittest.main()
