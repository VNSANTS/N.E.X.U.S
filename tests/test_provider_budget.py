import unittest
from nexus_learning.engine import LearningEngine
from nexus_learning.provider_budget import BudgetedProvider, ProviderBudget, ProviderBudgetExceededError
from nexus_learning.providers.base import ModelResponse

class FakeProvider:
    provider_name='gemini'; model='model-x'
    def __init__(self): self.calls=0
    def generate(self,messages,*,max_tokens=800,timeout=30):
        self.calls+=1
        return ModelResponse('ok','gemini','model-x',input_tokens=10,output_tokens=4)

class ProviderBudgetTests(unittest.TestCase):
    def setUp(self):
        self.engine=LearningEngine(':memory:'); self.budget=ProviderBudget(self.engine); self.inner=FakeProvider(); self.provider=BudgetedProvider(self.inner,self.budget)
    def tearDown(self): self.engine.close()
    def config(self,**kwargs):
        data={'enabled':True,'daily_calls':2,'daily_tokens':5000,'daily_usd':1.0,'task_calls':2,'task_tokens':5000,'task_usd':1.0,'input_price':1.0,'output_price':2.0}; data.update(kwargs); return self.budget.update(**data)
    def test_remote_calls_fail_closed_until_budget_configured(self):
        with self.assertRaises(ProviderBudgetExceededError): self.provider.generate([{'role':'user','content':'hello'}])
        self.assertEqual(self.inner.calls,0)
    def test_can_reserve_is_read_only_and_fails_closed_at_limits(self):
        self.assertFalse(self.budget.can_reserve(self.inner,10,10))
        self.config(daily_calls=1,task_calls=1,daily_tokens=100,task_tokens=100)
        self.assertTrue(self.budget.can_reserve(self.inner,10,10))
        with self.engine.db() as c:
            count=c.execute('SELECT COUNT(*) FROM provider_usage').fetchone()[0]
        self.assertEqual(count,0)
        self.provider.generate([{'role':'user','content':'hello'}],max_tokens=1,task_id='done')
        self.assertFalse(self.budget.can_reserve(self.inner,10,10))
    def test_route_preflight_rejects_estimate_above_per_task_dollar_limit(self):
        self.config(daily_usd=5.0, task_usd=0.00001)
        self.assertFalse(self.budget.can_reserve(self.inner, 100, 100))
    def test_batch_preflight_checks_call_and_cost_caps_without_reserving(self):
        self.config(daily_calls=4, task_calls=3, task_usd=0.001)
        requests = [{"messages": [{"role": "user", "content": f"specialist {i}"}],
                     "max_tokens": 100} for i in range(3)]
        self.assertTrue(self.budget.can_reserve_batch(self.inner, requests, task_id="agent-task"))
        with self.engine.db() as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM provider_usage").fetchone()[0], 0)
        self.budget.generate(self.inner, [{"role": "user", "content": "already used"}],
                             max_tokens=10, task_id="agent-task")
        self.assertFalse(self.budget.can_reserve_batch(self.inner, requests, task_id="agent-task"))

        self.config(daily_calls=4, task_calls=4, task_usd=0.00001)
        self.assertFalse(self.budget.can_reserve_batch(self.inner, requests, task_id="other-task"))
    def test_records_actual_usage_and_stops_at_daily_call_cap(self):
        self.config(daily_calls=1)
        self.provider.generate([{'role':'user','content':'hello'}])
        usage=self.budget.usage()['today'][0]
        self.assertEqual(usage['calls'],1); self.assertEqual(usage['tokens'],14)
        with self.assertRaises(ProviderBudgetExceededError): self.provider.generate([{'role':'user','content':'hello'}])
        self.assertEqual(self.inner.calls,1)
    def test_per_task_calls_are_limited_independently(self):
        self.config(daily_calls=3,task_calls=1)
        self.budget.generate(self.inner,[{'role':'user','content':'first'}],task_id='task-a')
        with self.assertRaises(ProviderBudgetExceededError):
            self.budget.generate(self.inner,[{'role':'user','content':'second'}],task_id='task-a')
        self.budget.generate(self.inner,[{'role':'user','content':'other'}],task_id='task-b')
        self.assertEqual(self.inner.calls,2)

    def test_uncertain_vendor_error_retains_reservation(self):
        self.config(daily_calls=1)
        def fail(*args,**kwargs): raise TimeoutError()
        self.inner.generate=fail
        with self.assertRaises(TimeoutError): self.provider.generate([{'role':'user','content':'x'}])
        with self.engine.db() as c: self.assertEqual(c.execute('SELECT state FROM provider_usage').fetchone()[0],'uncertain')

    def test_unicode_input_is_reserved_conservatively_before_remote_call(self):
        self.config(daily_tokens=70,task_tokens=70)
        def report_usage(messages,**kwargs):
            self.inner.calls+=1
            return ModelResponse('ok','gemini','model-x',input_tokens=100,output_tokens=1)
        self.inner.generate=report_usage
        with self.assertRaises(ProviderBudgetExceededError):
            self.provider.generate([{'role':'user','content':'🙂'*20}],max_tokens=1)
        self.assertEqual(self.inner.calls,0)

from unittest.mock import patch
from nexus_learning.engine import LearningEngine
from nexus_learning.provider_budget import ProviderBudget, ProviderBudgetExceededError

class ProviderBudgetAuthorizationRaceTests(unittest.TestCase):
    def test_reservation_reads_authorization_inside_atomic_transaction(self):
        engine = LearningEngine(':memory:')
        try:
            budget = ProviderBudget(engine)
            authorized = budget.update(enabled=True, daily_calls=2, daily_tokens=1000,
                daily_usd=1.0, task_calls=2, task_tokens=1000, task_usd=1.0,
                input_price=1.0, output_price=1.0)
            with engine.db() as connection:
                connection.execute("UPDATE provider_budget_settings SET enabled=0 WHERE id=1")
            with patch.object(budget, 'settings', return_value=authorized):
                with self.assertRaises(ProviderBudgetExceededError):
                    budget._reserve(object(), 10, 10, None)
            with engine.db() as connection:
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM provider_usage').fetchone()[0], 0)
        finally:
            engine.close()

if __name__=='__main__': unittest.main()
