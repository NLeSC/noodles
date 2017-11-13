"""
    This module implements a parallelized Evolutionary Strategy with Single
    Self-Adaptive Sigma.
"""

from noodles import (has_scheduled_methods, schedule_hint)
from .chromosome import (Chromosome)
from .generation import (Generation)

# from numpy import random
import random
import numpy as np


@has_scheduled_methods
class EA:
    def __init__(self, config, fitness_evaluator):
        self.config = config
        self.fitness_evaluator = fitness_evaluator

    def make_child(self, g: Generation) -> Chromosome:
        # Choose parents
        option1 = random.sample(g.individuals, 2)
        option2 = random.sample(g.individuals, 2)

        # Binary Tournament
        parent = [option1[0] if option1[0].fitness < option1[1].fitness
                  else option1[1],
                  option2[0] if option2[0].fitness < option2[1].fitness
                  else option2[1]]

        # Crossover
        child = self.crossover(parent)

        # Mutation
        self.mutate(child)

        return child

    def generate_offspring(self, g: Generation) -> Generation:
        individuals = [self.make_child(g)
                       for _ in range(self.config['offspring'])]
        generation = Generation(individuals)
        generation.number = g.number + 1

        return generation

    def crossover(self, parents) -> Chromosome:
        values = np.where(np.random.random(parents[0].values.shape) > 0.5,
                          parents[0].values, parents[1].values)
        sigma = parents[0].sigma if np.random.random() > 0.5 \
            else parents[1].sigma
        child = Chromosome(values=values, sigma=sigma)
        return child

    def mutate(self, child) -> Chromosome:
        # mutate the sigma
        child.sigma = child.sigma + self.config['learning_rate'] \
            * np.random.normal(0, child.sigma)

        # mutate the child using the mutated sigma
        mut = np.random.normal(0, child.sigma, (len(child.values)))

        child.values += mut

        return child

    # Generate random individuals on the range [range_lower, range_upper]
    def initialize(self) -> Generation:
        individuals = [
            Chromosome(values=(np.random.rand(
                self.fitness_evaluator.dimensions) / 2 - 1) *
                self.fitness_evaluator.range_upper,
                sigma=self.config['initial_sigma'])
            for _ in range(self.config['population_size'])]
        generation = Generation(individuals)
        generation.number = 1

        generation.evaluate(self.fitness_evaluator)

        return generation

    @schedule_hint(display="│   Generation {g.number} ... ",
                   confirm=True)
    def next_generation(self, g: Generation) -> Generation:
        if g.number >= self.config['generations']:
            return g
        else:
            # Generate Children
            new_generation = self.generate_offspring(g).evaluate(
                fitness_evaluator=self.fitness_evaluator)

            return self.next_generation(new_generation)
