import unittest
from nexus_learning.engine import LearningEngine
from nexus_learning.agents import ProductSupervisor

class ProductSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.engine=LearningEngine(':memory:')
        self.supervisor=ProductSupervisor(self.engine)
    def tearDown(self): self.engine.close()
    def test_reviewer_requires_valid_source_citations_when_research_context_exists(self):
        sources=[{'id':'src1','url':'https://example.org'}]
        self.assertEqual(self.supervisor.review_response('owner','Claim [S1].',100,sources).status,'completed')
        self.assertEqual(self.supervisor.review_response('owner','Claim [S2].',100,sources).status,'rejected')
        self.assertEqual(self.supervisor.review_response('owner','Claim without citation.',100,sources).status,'rejected')
    def test_reviewer_keeps_regular_conversation_unconstrained(self):
        self.assertEqual(self.supervisor.review_response('owner','Ordinary answer.',100).status,'completed')
    def test_analyst_reports_source_coverage_metadata_without_claiming_consensus(self):
        result=self.supervisor.analyze_sources('owner','parent',[
            {'url':'https://www.example.org/a','publication_date':'2026-01-01'},
            {'url':'https://other.example.net/b','publication_date':None}])
        self.assertEqual(result['distinct_domains'],2)
        self.assertEqual(result['dated_sources'],1)
        self.assertIsNone(result['coverage_warning'])

if __name__=='__main__': unittest.main()
