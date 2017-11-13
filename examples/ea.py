from noodles import (run_logging)

import subprocess
import numpy as np
from ea import (EA, Rastrigin)
from noodles.display import SimpleDisplay


def error_filter(xcptn):
    if isinstance(xcptn, subprocess.CalledProcessError):
        return xcptn.stderr
    else:
        return None


if __name__ == "__main__":
    # Problem definition
    dimensions = 10
    evaluator = Rastrigin(dimensions=dimensions)

    # Evolutionary Algorithm
    config = {
        'population_size': 40,   # mu
        'offspring': 40,  # lamda
        'generations': 10,
        'initial_sigma': 0.01,
        'learning_rate': 1.0 / np.sqrt(dimensions)
    }

    ea = EA(config=config, fitness_evaluator=evaluator)
    g = ea.next_generation(ea.initialize())
    print("╭─(Running evolution...)")
    with SimpleDisplay(error_filter) as display:
        answer = run_logging(g, 1, display)
    # answer = run_single(g)

    for i in answer.individuals:
        print(i.fitness)
