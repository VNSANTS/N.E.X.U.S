import unittest
from nexus_learning.discovery import build_research_service, CompositeDiscovery
from nexus_learning.engine import LearningEngine

class DiscoveryTests(unittest.TestCase):
    def setUp(self): self.engine=LearningEngine(':memory:')
    def tearDown(self): self.engine.close()
    def test_tavily_autonomous_adapter_requires_standing_cost_approval(self):
        denied=build_research_service(self.engine,tavily_enabled=True,environ={'TAVILY_API_KEY':'fake','NEXUS_CROSSREF_ENABLED':'false','NEXUS_TAVILY_AUTONOMOUS_APPROVED':'false'})
        self.assertEqual(denied.adapter.names,[])
        allowed=build_research_service(self.engine,tavily_enabled=True,environ={'TAVILY_API_KEY':'fake','NEXUS_CROSSREF_ENABLED':'false','NEXUS_TAVILY_AUTONOMOUS_APPROVED':'true'})
        self.assertEqual(allowed.adapter.name,'tavily')
        self.assertEqual(allowed.adapter.request_budget,2)
    def test_crossref_can_be_independently_disabled(self):
        off=build_research_service(self.engine,environ={'NEXUS_CROSSREF_ENABLED':'false'})
        self.assertEqual(off.adapter.names,[])

if __name__=='__main__': unittest.main()
