from noodles import Storable, gather
from ea import Chromosome


class Generation(Storable):
    def __init__(self, individuals):
        super(Storable, self).__init__()
        self.individuals = individuals
        self.number = -1

    # Evaluate individuals
    def evaluate(self, fitness_evaluator):
        evaluate = [Chromosome(fitness=fitness_evaluator.evaluate(c.values), values=c.values, sigma=c.sigma)
                    for c in self.individuals]
        self.individuals = gather(*evaluate)

        return self
