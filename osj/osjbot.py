import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
import osj.map
import osj.tracker
from .armys import initarmy
from .strategies import simple_strategy, tank_strategy

DEBUG = True

class OsjBot(sc2.BotAI):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.prevtime = 0
        self.reset_bot()
    
    
    def reset_bot(self):
        self.map = osj.map.MapData(self)
        self.tracker = osj.tracker.Tracker(self)
        self.load_tags = set()
        self.prevtags = set()
        self.loop = -1
        self.elapsed_time = 0
        self.time_offset = 0
        self.rtime = 0
        self.strategy = tank_strategy.TankStrategy(self)
        self.my_units = dict()
        self.resetting = False

    def init_set(self):
        self.map.on_start()
        self.tracker.on_start()
        self.strategy.on_start()
        self.time_offset = self.time
        for unit in self.units:
            self.strategy.addUnit(unit)
            self.tracker.addunit(unit)
            self.my_units[unit.tag] = unit
        self.prevtags = self.units.tags

    async def on_step(self, iteration: int):
        if self.resetting:
            return

        if self.loop == -1:
            self.init_set()

        self.rtime = self.time - self.time_offset
        self.loop = self.state.game_loop
        self.elapsed_time = self.time - self.prevtime
        self.prevtime = self.time
        new_tags = self.units.tags - self.prevtags
        self.load_tags = set()
        for ship in self.units.of_type({UnitTypeId.MEDIVAC, UnitTypeId.BUNKER}):
            self.load_tags = self.load_tags.union(ship.passengers_tags)
        for tag in new_tags:
            unit = self.units.by_tag(tag)
            self.strategy.addUnit(unit)
            self.tracker.addunit(unit)
            self.my_units[tag] = unit

        for tag in self.state.dead_units:
            if tag in self.my_units:
                self.tracker.killunit(self.my_units[tag])
                del self.my_units[tag]


        self.map.step()
        self.tracker.step()
        await self.do_actions(await self.strategy.step(iteration))
        if DEBUG:
            await self._client.send_debug()
        if self.tracker.finished != -1:
            self.resetting = True
            await self.reset()
            
        self.prevtags = self.units.tags.union(self.load_tags)

    def on_end(self, result):
        pass

    async def reset(self):
        await self.chat_send("#RESET")
        await self._client.send_debug()

        self.reset_bot()