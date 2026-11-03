"""stub: the multiple-choice task module was not published. mathqa.py imports loop_signals from it at import time;
evaluate.py's math path never calls it. MMLU-Pro / GPQA (mcqa.extract) are not run in this reproduction."""


def loop_signals(text):
    raise NotImplementedError("mcqa.loop_signals was not published")


def extract(text):
    raise NotImplementedError("mcqa.extract (MMLU-Pro / GPQA grader) was not published")
