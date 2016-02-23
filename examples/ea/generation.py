from noodles import Storable, gather
from ea.chromosome import Chromosome


class Generation(Storable):
    def __init__(self, individuals):
        super(Storable, self).__init__()
        self.individuals = individuals
        self.number = -1

    # Evaluate individuals
    def evaluate(self, fitness_evaluator):
        for c in self.individuals:
            c.fitness = fitness_evaluator.evaluate(c.values)

        evaluate = [Chromosome(fitness=fitness_evaluator.evaluate(c.values), values=c.values) for c in self.individuals]
        self.individuals = gather(*evaluate)

        return self
