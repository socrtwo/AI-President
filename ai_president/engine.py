"""Orchestration: gather -> synthesize -> main recommendation -> vote -> Quaker consensus."""
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from .providers import AI


def _safe_ask(ai, prompt, system="You are a careful, honest advisor."):
    try:
        return ai.ask(prompt, system)
    except Exception as e:  # one failing AI must not stop the rest
        return f"[ERROR from {ai.name}: {e}]"


def _parallel(ais, prompt_for):
    with ThreadPoolExecutor(max_workers=max(1, len(ais))) as ex:
        return list(ex.map(lambda a: _safe_ask(a, prompt_for(a)), ais))


def _json(text):
    m = re.search(r"(\{.*\}|\[.*\])", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except ValueError:
        return None


def gather(question, assistants):
    """Every assistant AI independently works the problem. Returns {name: answer}."""
    prompt = ("Problem to analyze (weigh precedent, philosophy, political science, ethics, science, "
              "public information and likely cost/timeline):\n" + question +
              "\n\nGive your analysis and concrete options with rough cost and timeline.")
    return dict(zip([a.name for a in assistants], _parallel(assistants, lambda a: prompt)))


def synthesize(main, question, answers):
    """Main AI merges all answers into a deduplicated list of options + its suggested best."""
    body = "\n\n".join(f"### {n}\n{a}" for n, a in answers.items())
    prompt = (f"Problem:\n{question}\n\nAdvisor answers:\n{body}\n\n"
              'Synthesize every distinct option mentioned. Reply ONLY with JSON: '
              '{"options": ["short option 1", ...], "main_choice": "<one of the options>", "reasoning": "..."}')
    data = _json(_safe_ask(main, prompt))
    if not isinstance(data, dict) or not data.get("options"):
        raise RuntimeError("Main AI did not return a usable option list.")
    options = [str(o) for o in data["options"]]
    return options, str(data.get("main_choice", "")), str(data.get("reasoning", ""))


def vote(voters, question, options):
    """Each AI (including main) casts one vote. Returns (Counter, {voter: option})."""
    listing = "\n".join(f"{i + 1}. {o}" for i, o in enumerate(options))
    prompt = (f"Problem:\n{question}\n\nOptions:\n{listing}\n\n"
              'Vote for the single best option. Reply ONLY with JSON: {"vote": <option number>, "why": "..."}')
    ballots, tally = {}, Counter()
    for ai, raw in zip(voters, _parallel(voters, lambda a: prompt)):
        d = _json(raw)
        try:
            n = int(d["vote"]) if isinstance(d, dict) else int(re.search(r"\d+", raw).group())
        except (TypeError, ValueError, AttributeError, KeyError):
            continue  # invalid ballot is discarded
        if 1 <= n <= len(options):
            ballots[ai.name] = options[n - 1]
            tally[options[n - 1]] += 1
    return tally, ballots


def winners(tally):
    """All options tied for the most votes."""
    if not tally:
        return []
    top = max(tally.values())
    return [o for o, c in tally.items() if c == top]


def quaker_consensus(participants, question, options, max_rounds=3):
    """Rounds of 'friends' sharing a sense of the meeting. A proposal is adopted when nobody
    stands in the way (blocks). Unresolved concerns are carried into the next round.
    Returns (adopted_or_None, transcript)."""
    listing = "\n".join(f"- {o}" for o in options)
    transcript, proposal, concerns = [], None, []
    for rnd in range(1, max_rounds + 1):
        # 1. Each Friend speaks, hearing the concerns so far.
        heard = "\n".join(concerns) or "(none yet)"
        speak = (f"Problem:\n{question}\n\nOptions:\n{listing}\n\nConcerns raised so far:\n{heard}\n\n"
                 "In the spirit of a Quaker meeting, speak briefly from your own sense of what is right; "
                 "listen to others and seek the way forward that serves the whole.")
        spoken = _parallel(participants, lambda a: speak)
        transcript.append((rnd, "ministry", dict(zip([p.name for p in participants], spoken))))
        # 2. The clerk (first participant = main AI) drafts a sense of the meeting.
        clerk = participants[0]
        said = "\n\n".join(f"{p.name}: {s}" for p, s in zip(participants, spoken))
        draft = (f"You are the clerk. Options:\n{listing}\n\nWhat Friends said:\n{said}\n\n"
                 'Reply ONLY with JSON: {"minute": "<exact text of one option, or a combination>"}')
        d = _json(_safe_ask(clerk, draft))
        proposal = str(d.get("minute")) if isinstance(d, dict) and d.get("minute") else options[0]
        # 3. Test for unity: each Friend approves, stands aside, or blocks.
        test = (f"Problem:\n{question}\n\nProposed minute: {proposal}\n\n"
                'Reply ONLY with JSON: {"stance": "approve" | "stand_aside" | "block", "concern": "..."}')
        stances = {}
        for p, raw in zip(participants, _parallel(participants, lambda a: test)):
            r = _json(raw)
            s = str(r.get("stance", "")).lower() if isinstance(r, dict) else "block"
            stances[p.name] = (s if s in ("approve", "stand_aside", "block") else "block",
                               r.get("concern", "") if isinstance(r, dict) else "")
        transcript.append((rnd, "unity", stances))
        blockers = [(n, c) for n, (s, c) in stances.items() if s == "block"]
        if not blockers:
            return proposal, transcript
        concerns += [f"{n}: {c}" for n, c in blockers if c]
    return None, transcript
