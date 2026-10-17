import json
import unittest

from ai_president import engine
from ai_president.providers import AI


def mock(name, *r):
    return AI(name=name, kind="mock", responses=list(r))


class T(unittest.TestCase):
    def test_vote(self):
        opts = ["A", "B"]
        vs = [mock("m", '{"vote": 2}'), mock("x", '{"vote": 2}'), mock("y", "1"), mock("z", "junk")]
        tally, ballots = engine.vote(vs, "q", opts)
        self.assertEqual(engine.winners(tally), ["B"])
        self.assertEqual(len(ballots), 3)

    def test_synthesize(self):
        m = mock("m", json.dumps({"options": ["A", "B"], "main_choice": "A", "reasoning": "r"}))
        self.assertEqual(engine.synthesize(m, "q", {"x": "..."})[:2], (["A", "B"], "A"))

    def test_quaker_consensus_after_block(self):
        ok = '{"stance":"approve"}'
        clerk = mock("m", '{"minute":"A"}', ok, '{"minute":"B"}', ok)
        f = mock("f", "speak", '{"stance":"block","concern":"c"}', "speak", ok)
        # clerk's own responses interleave: speak, minute, stance per round
        clerk = mock("m", "speak", '{"minute":"A"}', ok, "speak", '{"minute":"B"}', ok)
        adopted, tr = engine.quaker_consensus([clerk, f], "q", ["A", "B"])
        self.assertEqual(adopted, "B")
        self.assertEqual(len(tr), 4)

    def test_quaker_no_unity(self):
        blk = '{"stance":"block","concern":"no"}'
        m = mock("m", *(["s", '{"minute":"A"}', blk] * 2))
        adopted, _ = engine.quaker_consensus([m], "q", ["A"], max_rounds=2)
        self.assertIsNone(adopted)


if __name__ == "__main__":
    unittest.main()
