class Slice:
    def __init__(self, name: str, ratio: float,
                 connected_users: int, user_share: float, delay_tolerance: float, qos_class: int,
                 bandwidth_guaranteed: float, bandwidth_max: float, init_capacity: float,
                 usage_pattern):
        """
        Initialize a network slice.
        """
        self.name = name
        self.connected_users = connected_users
        self.user_share = user_share
        self.delay_tolerance = delay_tolerance
        self.qos_class = qos_class
        self.ratio = ratio
        self.bandwidth_guaranteed = bandwidth_guaranteed
        self.bandwidth_max = bandwidth_max
        self.init_capacity = init_capacity
        self.capacity = 0
        self.usage_pattern = usage_pattern
    
    def get_consumable_share(self) -> float:
        """
        Returns the share of bandwidth that can be consumed by each user.
        """
        if self.connected_users <= 0:
            return min(self.init_capacity, self.bandwidth_max)
        else:
            return min(self.init_capacity/self.connected_users, self.bandwidth_max)

    def is_available(self) -> bool:
        """
        Checks if the slice has enough bandwidth for another user.
        """
        real_cap = min(self.init_capacity, self.bandwidth_max)
        bandwidth_next = real_cap / (self.connected_users + 1)
        if bandwidth_next < self.bandwidth_guaranteed:
            return False
        return True

    def __str__(self) -> str:
        return f'{self.name:<10} init={self.init_capacity:<5} cap={self.capacity.level:<5} diff={(self.init_capacity - self.capacity.level):<5}'
