import numpy as np
from pampy import match

class Horse:
    death_reason = ['996工作', '未知原因', '突发恶疾', '马腿抽筋', '精疲力尽']
    death_icon = '\N{skull and crossbones}'
    running_icon = '\N{horse}'

    @staticmethod
    def _limiter(data: float, lower: float, upper: float) -> float:
        if data < lower:
            return lower
        elif data > upper:
            return upper
        else:
            return data

    def __init__(self, num: int):
        self.speed = Horse._limiter(np.random.normal(5, 1.5), 0, 10)
        self.death_rate = Horse._limiter(np.random.normal(3, 3), 0, 30)/100
        self.stability = Horse._limiter(np.random.normal(2.5, 2.5), 0, 6)
        _stop_icon_bernoulli_pointer = np.random.rand()
        self.stop_icon = '\N{horse face}' if _stop_icon_bernoulli_pointer < 0.8 else '\N{unicorn face}'
        self.track_length = 30
        self.position = 0
        self.state = 'stop'
        self.number = num
        self.finish_distance = 0
    
    def get_current_track_str(self):
        track = list(' ' * self.track_length)
        icon = match(self.state,
                     'stop',    self.stop_icon,
                     'running', self.running_icon,
                     'dead',    self.death_icon)
        track[self.position] = icon
        return ''.join(track[::-1])

    def move(self):
        if self.state in ['running', 'stop']:
            self.state = 'running'
            if np.random.rand() < self.death_rate:
                self.state = 'dead'
                return
            self.position += Horse._limiter(
                                round(self.speed + np.random.normal(0, self.stability)
                            ), 0, 15)
            if self.position >= self.track_length-1:
                self.finish_distance = self.position
                self.position = self.track_length - 1
    
    def get_property(self):
        return f'{self.number}号马，速度{self.speed:.2f}，不稳定性{self.stability:.4f}，每次移动意外出局率{self.death_rate:.2%}'

    def __str__(self):
        return self.get_property()

def get_tracks_str(horse_list: list[Horse]) -> str:
    return '\n'.join(map(lambda x: f'{x[0]} |{x[1].get_current_track_str()}', enumerate(horse_list, 1)))