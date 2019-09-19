from sc2.ids.unit_typeid import UnitTypeId


class Strategy:
    def __init__(self, bot):
        self.bot = bot
        self.armys = list()

    def addUnit(self, unit):
        if len(self.armys) > 0:
            self.armys[0].addUnit(unit)

    async def update(self):
        actions = list()
        for army in self.armys:
            actions += await army.step()
        return actions
        
    async def step(self, iteration):
        return await self.update()

    def on_end(self):
        pass

        