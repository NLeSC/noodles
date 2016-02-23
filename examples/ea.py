from noodles import gather, run_parallel, schedule, has_scheduled_methods, run_process, serial

import numpy as np
import random
from ea import (EA, Chromosome, Generation, Rastrigin, registry)


if __name__ == "__main__":
    # Problem definition
    dimensions = 10
    evaluator = Rastrigin(dimensions=dimensions)

    # Evolutionary Algorithm
    pop_size = 40   # mu
    offspring = 40  # lamda
    gens = 10

    ea = EA(population_size=pop_size, generations=gens, num_offspring=offspring,
            fitness_evaluator=evaluator)
    g = ea.next_generation(ea.initialize())

    # answer = run_process(g, n_processes=1, registry=registry)
    answer = run_parallel(g, n_threads=1)

    for i in answer.individuals:
        print(i.fitness)
