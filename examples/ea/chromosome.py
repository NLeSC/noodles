from noodles import Storable


class Chromosome(Storable):
    def __init__(self, values, fitness=-1):
        super(Chromosome, self).__init__()
        self.fitness = fitness
        self.values = values
