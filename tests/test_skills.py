import unittest
from nexus_learning import LearningEngine
from nexus_learning.skills import SkillRegistry

class SkillRegistryTests(unittest.TestCase):
    def setUp(self): self.engine=LearningEngine(":memory:"); self.skills=SkillRegistry(self.engine)
    def tearDown(self): self.engine.close()
    def test_discovery_only_returns_owner_approved_and_load_is_audited(self):
        draft=self.skills.propose("research-brief","1.0.0","Prepare research briefs","Use concise, sourced summaries.")
        self.assertEqual(self.skills.discover("research"),[])
        with self.assertRaises(PermissionError): self.skills.approve(draft,owner_id="owner",approved=False)
        self.skills.approve(draft,owner_id="owner",approved=True)
        self.assertEqual(self.skills.discover("research")[0]["version"],"1.0.0")
        loaded=self.skills.load("research-brief",owner_id="owner")
        self.assertIn("sourced",loaded["instructions"])
        with self.engine.db() as c:
            self.assertEqual(c.execute("SELECT count(*) FROM runtime_skill_events").fetchone()[0],2)
    def test_skill_cannot_grant_tools_or_execute_content(self):
        with self.assertRaises(ValueError):
            self.skills.propose("unsafe-skill","1.0.0","Unsafe","run arbitrary command",tools=("system.exec",))
    def test_proposals_list_only_pending_skills_with_reviewable_instructions(self):
        pending = self.skills.propose(
            "research-brief", "1.0.0", "Research source evidence", "Use cited sources.")
        approved = self.skills.propose(
            "code-review", "1.0.0", "Review software code", "Inspect regressions.")
        self.skills.approve(approved, owner_id="owner", approved=True)
        rows = self.skills.proposals()
        self.assertEqual([row["id"] for row in rows], [pending])
        self.assertEqual(rows[0]["status"], "proposed")
        self.assertEqual(rows[0]["instructions"], "Use cited sources.")
        self.assertNotIn("tool_allowlist", rows[0])

    def test_proposal_list_limit_is_strictly_bounded(self):
        for limit in (0, -1, 51, True, 1.5, "10"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.skills.proposals(limit=limit)

    def test_discovery_treats_sql_like_wildcards_as_literal_text(self):
        skill = self.skills.propose(
            "research-brief", "1.0.0", "Research source evidence", "Use cited sources.")
        self.skills.approve(skill, owner_id="owner", approved=True)
        self.assertEqual(self.skills.discover("%"), [])
        self.assertEqual(self.skills.discover("_"), [])
        self.assertEqual(self.skills.discover("research")[0]["name"], "research-brief")

    def test_skill_discovery_limit_is_strictly_bounded(self):
        for limit in (0, -1, 51, True, 1.5, "10"):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.skills.discover("", limit=limit)

    def test_skill_selection_limits_reject_invalid_values(self):
        for kwargs in ({"max_skills": -1}, {"max_skills": 11},
                       {"max_skills": True}, {"max_chars": -1},
                       {"max_chars": 12001}, {"max_chars": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.skills.select_for_message("research sources", owner_id="owner", **kwargs)

    def test_approved_skill_content_hash_drift_is_rejected(self):
        skill = self.skills.propose(
            "research-brief", "1.0.0", "Research source evidence", "Use cited sources.")
        self.skills.approve(skill, owner_id="owner", approved=True)
        with self.engine.db() as c:
            c.execute("UPDATE runtime_skills SET instructions=? WHERE id=?",
                      ("Changed after approval", skill))
        with self.assertRaisesRegex(ValueError, "integrity validation failed"):
            self.skills.load("research-brief", owner_id="owner")

    def test_message_selects_only_relevant_approved_skill_with_size_bound(self):
        a=self.skills.propose("research-brief","1.0.0","Research and source summaries","Use sources and list evidence.")
        b=self.skills.propose("code-review","1.0.0","Review software code","Inspect changes for regressions.")
        self.skills.approve(a,owner_id="owner",approved=True)
        self.skills.approve(b,owner_id="owner",approved=True)
        selected=self.skills.select_for_message("Prepare research sources and evidence",owner_id="owner",max_chars=12)
        self.assertEqual(len(selected),1)
        self.assertEqual(selected[0]["name"],"research-brief")
        self.assertLessEqual(len(selected[0]["instructions"]),12)

if __name__=="__main__": unittest.main()
