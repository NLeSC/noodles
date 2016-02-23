from noodles import Storable


class Chromosome(Storable):
    def __init__(self, values):
        super(Chromosome, self).__init__()
        self.fitness = fitness
        self.values = values
