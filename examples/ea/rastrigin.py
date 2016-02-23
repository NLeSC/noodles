from noodles import schedule, has_scheduled_methods
import numpy as np

@has_scheduled_methods
class Rastrigin:
    def __init__(self, dimensions):
        self.dimensions = dimensions
        self.range_upper = 5.12
        self.range_lower = -5.12

    @schedule
    def evaluate(self, values):
        """F5 Rastrigin's function
        multimodal, symmetric, separable
        defined on range -5.12 to 5.12"""
        fitness = 10*len(values) + np.sum(values ** 2 - (10 * np.cos(2 * np.pi * values)))

        return fitness