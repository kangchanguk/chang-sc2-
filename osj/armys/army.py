from osj.units import unitwrapper, marine, marauder, medivac, reaper, siegetank, bunker, autoturret
from .. import tracker
import osj.osjbot
from sc2.position import Point3
from sc2.ids.unit_typeid import UnitTypeId

class Army:
    def __init__(self, bot, start, end):
        self.patrolship = None
        self.unitws = list()
        self.bot = bot
        self.state = 0
        self.name = "None"
        self.start = start
        self.end = end
        self.center = self.start
        self.attack_power = 0
        self.defence_power = 0
        self.enemy_power = 0
        self.unit_count = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    def setPatrolship(self, ship):
        if self.patrolship != None:
            self.patrolship.setState(0)
        ship.army = self
        ship.setState(1, self.start, self.end)

    def give_all(self, army):
        for i in range(0, 6):
            army.unit_count[i] += self.unit_count[i]
            self.unit_count[i] = 0
        for unit in self.unitws:
            unit.army = army
        army.unitws.extend(self.unitws)
        self.unitws = []

    def give_unit(self, army, unittype):
        if self == army:
            return False

        closest = None
        closest_d = 100
        for unitw in self.unitws:
            if unitw.unit.type_id == unittype:
                d = army.center.distance_to(unitw.unit.position)
                if closest_d > d:
                    closest = unitw
                    closest_d = d
        if closest == None:
            return False

        typ = tracker.gettype(unittype)
        army.unit_count[typ] += 1
        self.unit_count[typ] -= 1
        closest.army = army
        army.unitws.append(closest)
        self.unitws.remove(closest)
        self.onAddUnit(closest)
        return True

    def addUnit(self, unit):
        if isinstance(unit, unitwrapper.UnitWrapper):
            unit = unit.unit
        
        if isinstance(unit, int):
            unit = self.bot.units.by_tag(unit)
        if unit == None:
            return
        typ = unit.type_id
        unitw = None
        if typ == UnitTypeId.MARINE:
            unitw = marine.Marine(unit.tag, self)
            self.unit_count[0] += 1
        elif typ == UnitTypeId.MARAUDER:
            unitw = marauder.Marauder(unit.tag, self)
            self.unit_count[1] += 1
        elif typ == UnitTypeId.MEDIVAC:
            unitw = medivac.Medivac(unit.tag, self)
            self.unit_count[2] += 1
        elif typ == UnitTypeId.REAPER:
            unitw = reaper.Reaper(unit.tag, self, self.bot)
            self.unit_count[3] += 1
        elif typ == UnitTypeId.SIEGETANK or typ == UnitTypeId.SIEGETANKSIEGED:
            unitw = siegetank.SiegeTank(unit.tag, self, self.bot.tracker)
            self.unit_count[4] += 1
        elif typ == UnitTypeId.AUTOTURRET:
            unitw = autoturret.AutoTurret(unit.tag, self)
            self.unit_count[6] += 1
        elif typ == UnitTypeId.BUNKER:
            unitw = bunker.Bunker(unit.tag, self)
            self.unit_count[7] += 1
        if unitw != None:
            unitw.unit = unit
            self.unitws.append(unitw)
            self.onAddUnit(unitw)

    def onAddUnit(self, unitw):
        return

    def getFreeShip(self):
        for unitw in self.unitws:
            if unitw.unit != None:
                if unitw.unit.type_id == UnitTypeId.MEDIVAC and unitw.state == 0:
                    return unitw

    def getRideShip(self, rideunit, start, end, force=False):
        for unitw in self.unitws:
            if unitw.unit != None:
                if unitw.unit.type_id == UnitTypeId.MEDIVAC:
                    if unitw.state == 0 or (force and unitw.state == 1):
                        if unitw.addLoad(rideunit):
                            unitw.setState(-4, start, end)
                            return True
                    elif unitw.state == -4 and unitw.start.distance_to_point2(start) < 1 and unitw.end.distance_to_point2(end) < 1:
                        if unitw.addLoad(rideunit):
                            return True
        return False

    async def updateUnits(self):
        actions = list()
        units = self.bot.units
        enemys = self.bot.known_enemy_units
        if self.patrolship == None:
            enemys = enemys.closer_than(20, self.center)
        else:
            enemys = enemys.closer_than(17, self.patrolship.unit)
            
        self.enemy_power = self.bot.tracker.evaluate_units(enemys)
        attack_power = 0
        defence_power = 0

        for unitw in self.unitws:
            if unitw.check_alive(units, self.bot.state.dead_units):
                action = await unitw.step(self.bot.known_enemy_units)
                if action != None:
                    actions.append(action)
                attack_power += self.bot.tracker.evaluate_unit(unitw.unit, True)
                defence_power += self.bot.tracker.evaluate_unit(unitw.unit, False)
            else:
                self.unitws.remove(unitw)
                typ = tracker.gettype(unitw.unit.type_id)
                self.unit_count[typ] -= 1
                
        self.attack_power = attack_power
        self.defence_power = defence_power
        if osj.osjbot.DEBUG:
            self.bot._client.debug_text_world(f"{self.name} Units: {self.unit_count}\nState: {self.state}", Point3((self.center.x, self.center.y, 12)), size=16)
        return actions

    async def step(self):
        return await self.updateUnits()
