from noodles import gather, run_parallel, schedule, has_scheduled_methods

import numpy as np
import random
from ea.rastrigin import Rastrigin
from ea.chromosome import Chromosome
from ea.generation import Generation


@has_scheduled_methods
class EA:
    def __init__(self, population_size, generations, num_offspring, fitness_evaluator):
        self.population_size = population_size
        self.generations = generations
        self.num_offspring = num_offspring
        self.fitness_evaluator = fitness_evaluator

    @schedule
    def make_child(self, g: Generation) -> Chromosome:
        # Choose parents
        option1 = random.sample(g.individuals, 2)
        option2 = random.sample(g.individuals, 2)

        # Binary Tournament
        parent = [option1[0] if option1[0].fitness > option1[1].fitness else option1[1],
                  option2[0] if option2[0].fitness > option2[1].fitness else option2[1]]

        # Crossover
        child = self.crossover(parent)

        # Mutation
        self.mutate(child)

        return child

    def generate_offspring(self, g: Generation) -> Generation:
        individuals = [self.make_child(g) for _ in range(self.num_offspring)]
        generation = Generation(individuals)
        generation.number = g.number + 1

        return generation

    def crossover(self, parents) -> Chromosome:
        child = Chromosome(np.zeros(parents[0].values.shape))

        for i, v in enumerate(parents[1].values):
            child.values[i] = v if np.random.rand() > 0.5 \
                else parents[0].values[i]

        return child

    def mutate(self, child) -> Chromosome:
        mut = (np.random.rand(len(child.values)) > 0.5).astype(float)
        mut *= np.random.normal(0, 0.01, (len(child.values)))

        child.values += mut

        return child

    # Generate random individuals on the range [range_lower, range_upper]
    def initialize(self) -> Generation:
        individuals = [Chromosome(values=(np.random.rand(self.fitness_evaluator.dimensions)/2-1) *
                                  self.fitness_evaluator.range_upper) for _ in range(self.population_size)]
        generation = Generation(individuals)
        generation.number = 0

        return generation

    @schedule
    def next_generation(self, g: Generation) -> Generation:
        if g.number > self.generations:
            return g
        else:
            # Generate Children
            print("Generation: {:d}".format(g.number))
            new_generation = self.generate_offspring(g).evaluate(fitness_evaluator=self.fitness_evaluator)

            return self.next_generation(new_generation)


if __name__ == "__main__":
    # Problem definition
    dimensions = 10
    evaluator = Rastrigin(dimensions=dimensions)

    # Evolutionary Algorithm
    pop_size = 40   # mu
    offspring = 40  # lamda
    gens = 5

    ea = EA(population_size=pop_size, generations=gens, num_offspring=offspring,
            fitness_evaluator=evaluator)
    g = ea.next_generation(ea.initialize())

    answer = run_parallel(g, 2)

    print(answer)
