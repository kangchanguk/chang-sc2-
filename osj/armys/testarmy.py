from sc2.ids.unit_typeid import UnitTypeId
from . import army

class TestArmy(army.Army):
    def __init__(self, bot):
        super().__init__(bot, bot.map.points[5], bot.map.points[4])
        print(str(bot.map.points[5]))
        print(str(bot.map.points[4]))
        
    
    async def step(self):
        if self.patrolship == None:
            newone = self.getFreeShip()
            if newone != None:
                self.setPatrolship(newone)
        else:
            self.center = self.patrolship.unit.position
        return self.updateUnits()