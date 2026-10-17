import argparse
import sys

from . import config, engine, wizard


def run_decision(main, assistants, question, mode, out=print):
    out("Gathering answers from assistant AIs...")
    answers = engine.gather(question, assistants)
    for n, a in answers.items():
        out(f"\n--- {n} ---\n{a}")
    options, choice, why = engine.synthesize(main, question, answers)
    out("\n=== Options synthesized by main AI (%s) ===" % main.name)
    for i, o in enumerate(options, 1):
        out(f"{i}. {o}")
    out(f"\nMain AI suggests: {choice}\nReasoning: {why}")
    everyone = [main] + list(assistants)
    if mode in ("vote", "all"):
        tally, ballots = engine.vote(everyone, question, options)
        out("\n=== Vote ===")
        for v, o in ballots.items():
            out(f"{v} -> {o}")
        w = engine.winners(tally)
        out("Result: " + (", ".join(w) + (f" (tie, {tally[w[0]]} votes each)" if len(w) > 1 else
                                          f" ({tally[w[0]]} votes)") if w else "no valid votes"))
    if mode in ("quaker", "all"):
        adopted, transcript = engine.quaker_consensus(everyone, question, options)
        out("\n=== Quaker consensus ===")
        for rnd, phase, data in transcript:
            out(f"Round {rnd} ({phase}):")
            for n, v in data.items():
                out(f"  {n}: {v}")
        out("Consensus reached: " + adopted if adopted else "No unity reached; the meeting holds the matter over.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="ai-president")
    p.add_argument("--setup", action="store_true", help="run the setup wizard")
    p.add_argument("--mode", choices=["suggest", "vote", "quaker", "all"], default="all")
    p.add_argument("question", nargs="*")
    a = p.parse_args(argv)
    m, assistants = config.load()
    if a.setup or m is None:
        m, assistants = wizard.run()
    q = " ".join(a.question) or input("Describe the decision/problem: ").strip()
    if not q:
        return 1
    run_decision(m, assistants, q, a.mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
