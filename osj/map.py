import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2

class MapData:

    def __init__(self, bot):
        self.bot = bot
        self.invert = False
        self.height_map = np.zeros((64, 64))

    #0 1 2 3 4: score area
    #5 6: Front
    #7 8: Front Down
    #9 10: Side
    #11 12: home drop, enemy drop
    #13 14: first land, land walk
    #15 16: home savedrop1 frontyard save
        self.points = [Point2((28, 61)), Point2((63, 66)), Point2((44, 44)), Point2((25, 22)), Point2((55, 27.5)),
        Point2((36, 52)), Point2((52, 36)), 
        Point2((40, 50)), Point2((49, 38)), 
        Point2((31, 47)), Point2((23, 27)), 
        Point2((20, 52)), Point2((72, 36)),
        Point2((13.5, 32)), Point2((18.2, 21.2)),
        Point2((32, 50)), Point2((70, 67))]

        self.turrets = [Point2((44, 56)), Point2((47, 59)), Point2((44, 49)), Point2((49, 44)), Point2((61, 61)), Point2((64, 60))]
        self.bunkers = [Point2((58.5, 63.5)), Point2((47.5, 47.5))]
        self.supplys = [Point2((43, 64)), Point2((44, 62)), Point2((46, 61))]
        self.Command = Point2((28.5, 60.5))
    def on_start(self):
        if self.bot.start_location.x > 44:
            self.invert = True
            self.flip()
        for x in range(0, 64):
            for y in range(0, 64):
                self.height_map[x, y] = (self.bot.game_info.terrain_height[x + 12, y + 12] - 127) / 96
        
        
    def flip(self):
        for i, point in enumerate(self.points):
            self.points[i] = Point2((88 - point.x, 88 - point.y))
        for i, point in enumerate(self.turrets):
            self.turrets[i] = Point2((88 - point.x, 88 - point.y))
        for i, point in enumerate(self.supplys):
            self.supplys[i] = Point2((88 - point.x, 88 - point.y))
        for i, point in enumerate(self.bunkers):
            self.bunkers[i] = Point2((88 - point.x, 88 - point.y))
        self.Command = Point2((88 - self.Command.x, 88 - self.Command.y))
            
    def step(self):
        pass