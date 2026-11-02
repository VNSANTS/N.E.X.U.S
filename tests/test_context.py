import unittest
from nexus_learning.context import ContextRetriever
from nexus_learning.engine import LearningEngine

class ContextRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.engine=LearningEngine(':memory:')
    def tearDown(self):
        self.engine.close()
    def test_combined_semantic_lexical_and_claim_results_respect_total_item_limit(self):
        self.engine.add_memory('semantic','Project context','Nexus routing project notes')
        self.engine.add_memory('semantic','More project context','Nexus provider project notes')
        sid=self.engine.add_source('https://example.test/reference','Reference')
        cid=self.engine.propose_claim('Nexus uses a bounded local router',source_ids=[sid])
        self.engine.review_claim(cid,'validated','verified',confidence=.9)
        class Semantic:
            def search(self,query,limit):
                return [{'kind':'memory','id':f'sem-{n}','text':f'semantic result {n}'} for n in range(limit)]
        result=ContextRetriever(self.engine,max_items=2,semantic_index=Semantic()).retrieve('Nexus project routing')
        self.assertEqual(len(result),2)
        self.assertEqual(len({item['id'] for item in result}),2)
        self.assertTrue(any(item['kind']=='validated_claim' for item in result))

if __name__=='__main__': unittest.main()
