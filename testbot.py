import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId


class TestBot(sc2.BotAI):
    def __init__(self, *args, **kwargs):
        super().__init__()

    async def on_step(self, iteration: int):
        if iteration % 100 == 0:
            for unit in self.units:
                print("{}, {}, {}".format(unit.position3d.x, unit.position3d.y, unit.position3d.z))
                self._client.debug_text_world("{}, {}, {}".format(unit.position3d.x, unit.position3d.y, unit.position3d.z), unit.position3d, size=16)
            await self._client.send_debug()
        actions = list()
        await self.do_actions(actions)
'''
main points
start view: 35.91650390625, 51.93310546875, 12
center: 44, 44, 10
frontyard: 63, 66 | 24, 22
radius: 6.5?

boundary: 12

'''