class BaseStation:
    def __init__(self, pk: int, coverage, capacity_bandwidth: float, slices=None):
        """
        Initialize a base station with coverage, capacity, and slices.
        """
        self.pk = pk
        self.coverage = coverage
        self.capacity_bandwidth = capacity_bandwidth
        self.slices = slices
        import logging
        logging.info(self)

    def __str__(self) -> str:
        return f'BS_{self.pk:<2}\t cov:{self.coverage}\t with cap {self.capacity_bandwidth:<5}'

