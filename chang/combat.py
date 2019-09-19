import sc2
import math
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units
from enum import Enum

class Tactics(Enum):
    NORMAL = 0
    FIRST = 1

class CombatGroupManager(object):
    """
    개별 유닛에게 직접 명령을 내리는 매니저
    """
    def __init__(self, bot_ai, tactics):
        self.bot = bot_ai
        self.strategy = None
        self.target = None
        self.unit_tags = None
        # 그룹의 경계 범위
        self.count = 0
        self.tactics = tactics
        self.state = ''
        self.count=0
        self.perimeter_radious = 13
        self.region_radius = 10
        self.strategic_points = [
            #        x   y   z
            Point3((28, 60, 12)),  # A
            Point3((63, 65, 10)),  # B
            Point3((44, 44, 10)),  # C
            Point3((24, 22, 10)),  # D
            Point3((59, 27, 12)),  # E
        ]

        self.arriveplace = [
            Point3((67.78,37.33,11.99)),
            Point3((64.38,35.83,11.99)),
            Point3((56.08,37.39,11.99))

        ]

        self.arriveplace2 = [
            Point3((20.22,50.67,11.99)),
            Point3((23.62,52.17,11.99)),
            Point3((31,48.39,11.99)),
        ]
    def reset(self):
        self.target = self.strategic_points[2]
        self.unit_tags = (self.bot.units & list()).tags

    def units(self):
        return self.bot.units.filter(lambda unit: unit.tag in self.unit_tags)

    async def step(self):
        actions = list()

        # 이 전투그룹에 속한 아군 유닛들
        units = self.units()

        if units.amount == 0 or self.target is None:
            return actions

        # 이 전투그룹 근처의 적군 유닛들
        enemy = self.bot.known_enemy_units.closer_than(
            self.perimeter_radious, units.center)

        for unit in units:

            if self.tactics == Tactics.NORMAL:
                actions += await self.normal_step(unit, units, enemy)
            elif self.tactics == Tactics.FIRST:
                actions += await self.first_step(unit, units, enemy)    
          

            if self.bot.debug:
                # 모든 유닛의 공격목표롤 시각화
                if len(unit.orders) > 0:
                    # if unit.type_id == UnitTypeId.MARINE:
                    #     embed(); exit()
                    skill = unit.orders[0].ability.id.name
                    target = unit.orders[0].target

                    if type(target) is Point3:
                        self.bot._client.debug_line_out(unit.position3d, target)
                        self.bot._client.debug_text_world(skill, target, size=16)

                    elif type(target) is int:
                        all_units = self.bot.units | self.bot.known_enemy_units
                        target_unit = all_units.find_by_tag(target)
                        if target_unit is not None:
                            target = target_unit.position3d
                            self.bot._client.debug_line_out(unit.position3d, target)
                            self.bot._client.debug_text_world(skill, target, size=16)

        if self.bot.debug:
            # 전투그룹의 중심점과 목표지점 시각화
            p1 = units.center
            p2 = self.target.to3
            self.bot._client.debug_sphere_out(
                Point3((p1.x, p1.y, 12)), 5, Point3((0, 255, 0)))
            self.bot._client.debug_line_out(
                Point3((p1.x, p1.y, 12)), p2, color=Point3((0, 255, 0)))
            self.bot._client.debug_sphere_out(
                self.target.to3, 5, Point3((0, 255, 0)))

        return actions
    
    async def first_step(self, unit, friends, foes):
        actions = list()
        base = self.bot.start_location
        center = self.strategic_points[2]
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        if base.x<50:
            protectplace = Point3((25.32,52.24,11.99))
        else:
            protectplace = Point3((62,35,11.99))

        if unit.type_id == UnitTypeId.MARINE or unit.type_id == UnitTypeId.MEDIVAC:
            if self.bot.time < 7:
                actions.append(unit.move(upper_bush))
            else:
                actions.append(unit.move(protectplace))

        return actions

    async def normal_step(self, unit, friends, foes):
        actions = list()
        base = self.bot.start_location
        center = self.strategic_points[2]
        if base.x<50:
            protectplace = Point3((25.32,52.24,11.99))
            arriveplace = Point3((63.92,34.5,11.99))
            arriveplace2 =  Point3((56.08,36.39,11.99))
            enemyplace = self.strategic_points[4]
            gatherplace = self.strategic_points[1]
            restplace = Point3((23.31,62.53,11.99 ))
            transplace = Point3((50.30,66.31,9))

        else:
            protectplace = Point3((62,35,11.99))
            arriveplace = Point3((24.08, 53.0,11.99))
            arriveplace2 = Point3((31.62,52.17,11.99))
            enemyplace = self.strategic_points[0]
            gatherplace = self.strategic_points[3]
            restplace = Point3((64.65,25.47,11.99))
            transplace = Point3((37,21.6,9))
            
        our_bush = Point2(
                (
                    (base.x + center.x * 4) / 5, (base.y + center.y * 4) / 5
                )
            )
        upper_bush = Point3(((base.x + center.x) / 2, (base.y + center.y) / 2, 12))
        bush_backward = Point3(
                ((base.x * 2 + center.x * 3) / 5, (base.y * 2 + center.y * 3) / 5, 10)
            )
        bush_center = Point2(
            (
                (bush_backward.x + our_bush.x) / 2, (bush_backward.y + our_bush.y) / 2
            )
        )
        last_point =  Point2(
                (
                    (our_bush.x + center.x * 1) / 2, (our_bush.y + center.y * 1) / 2
                )
            )
        bunk = self.bot.units.of_type(UnitTypeId.BUNKER).owned
        MEDI = self.bot.units.of_type(UnitTypeId.MEDIVAC).owned
        tank = self.bot.units.of_type(UnitTypeId.SIEGETANK).owned
        marine = self.bot.units.of_type(UnitTypeId.MARINE).owned
        reap = self.bot.units.of_type(UnitTypeId.REAPER).owned
        can_atk = self.bot.known_enemy_units.in_attack_range_of(unit)
        if reap.amount > 0:
            self.count = 1
            

        if unit.type_id == UnitTypeId.MARINE:
            distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            if self.count == 0:
                actions.append(unit.move(protectplace))
            else:
                if distance > 10 and distance3 >20:
                    actions.append(unit.move(transplace))
                elif unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK) and distance3<5:
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)
                
                
                               


        elif unit.type_id == UnitTypeId.REAPER:
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            if distance>10 and distance3>20:
                order=unit.move(transplace)
                actions.append(order)
            else:
                threaten = self.bot.known_enemy_units.closer_than(
                        self.perimeter_radious, unit.position)

                if unit.energy >= 50:
                    if unit.health_percentage >= 0.7  and threaten.amount > 0:
                        if unit.orders and unit.orders[0].ability.id != AbilityId.BUILDAUTOTURRET_AUTOTURRET:
                            closest_threat = threaten.closest_to(unit.position)
                            
                            pos = unit.position.towards(closest_threat.position, 5)
                            pos = await self.bot.find_placement(
                                UnitTypeId.AUTOTURRET,pos, 10)
                            
                            order = unit(AbilityId.BUILDAUTOTURRET_AUTOTURRET, pos)
                            actions.append(order)
                

          

        elif unit.type_id == UnitTypeId.MARAUDER:
            distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
            enemy = self.bot.known_enemy_units
            n_enemy = enemy.closer_than(5, unit.position).amount
            if distance2 > 5:
                actions.append(unit.move(protectplace))
            
           
            elif n_enemy >= 1:
                if unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK):
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)

                '''
            distance2=((protectplace.x-unit.position3d.x)**2 + (protectplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            if self.count == 0:
                elif distance2 > 5 and distance3 >20:
                    actions.append(unit.move(protectplace))
            else:
                if distance > 10 and distance3 > 20:
                    actions.append(unit.move(transplace))
                elif unit.health_percentage >= 0.7 and not unit.has_buff(BuffId.STIMPACK) and distance3<5:
                    order = unit(AbilityId.EFFECT_STIM)
                    actions.append(order)
                else:
                    if foes.amount>0:
                        if (foes.of_type(UnitTypeId.REAPER) & can_atk) :
                            order = unit.attack(foes.of_type({UnitTypeId.REAPER}).closest_to(unit.position))
                        elif(foes.of_type(UnitTypeId.AUTOTURRET) & can_atk):
                            order = unit.attack(foes.of_type({UnitTypeId.AUTOTURRET}).closest_to(unit.position))
                        else:
                            order = unit.attack(foes.closest_to(unit.position))
                '''

        elif unit.type_id == UnitTypeId.SIEGETANK:
            distance2=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance3=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            if distance >= 10 and distance2 >= 20:
                actions.append(unit.move(transplace))
            
          

            else:
                if distance3<10:
                    enemy = self.bot.known_enemy_units
                    n_enemy = enemy.closer_than(10, unit.position).amount
                    if n_enemy <= 1:
                        order = unit(AbilityId.SIEGEMODE_SIEGEMODE)  
                        actions.append(order)
               
       

        elif unit.type_id == UnitTypeId.MEDIVAC:
          
            distance=((transplace.x-unit.position3d.x)**2 + (transplace.y-unit.position3d.y)**2)**0.5 
            distance2=((arriveplace.x-unit.position3d.x)**2 + (arriveplace.y-unit.position3d.y)**2)**0.5 
            
            
           
            target_pssn = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARINE) 
               
            target_pssn3 = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.SIEGETANK)   
            target_pssn2 = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.REAPER) 
                    
        
            if len(unit.passengers)==0 and distance > 2 and distance2 >= 20:
                actions.append(unit.move(transplace))
        
            elif target_pssn3.exists and unit.cargo_used==0 and distance2 >= 20 and distance <=2:
                
                actions.append(unit(AbilityId.LOAD,target_pssn3.closest_to(unit.position) ))
            elif target_pssn2.exists and unit.cargo_used==4 and distance2 >= 20 and distance <=2:
                
                actions.append(unit(AbilityId.LOAD,target_pssn2.closest_to(unit.position) ))
            elif target_pssn.exists and unit.cargo_used<8 and distance2 >= 20 and distance <=2 and unit.cargo_used>=5:
                actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(unit.position) ))

            elif unit.cargo_used>=8:
                if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                    order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                    actions.append(order)
                else:
                    
                    if distance2 >10:
                        actions.append(unit.move(arriveplace))
                    else:
                        enemy = self.bot.known_enemy_units
                        n_enemy1 = enemy.closer_than(10, unit.position).amount

                        if n_enemy1 >7:
                            print(n_enemy1)
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace2))
                        
                        elif n_enemy1 <=7:
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace))

                        elif friends.of_type({UnitTypeId.REAPER}).closest_to(unit.position).health_percentage < 0.7:
                            order = unit(AbilityId.MEDIVACHEAL_HEAL,friends.of_type({UnitTypeId.REAPER}).closest_to(unit.position))
                            actions.append(order)
                            
                    '''
                    enemy = self.bot.known_enemy_units
                    n_enemy1 = enemy.closer_than(3, self.arriveplace[0]).amount
                    n_enemy2 = enemy.closer_than(3, self.arriveplace[1]).amount
                    n_enemy3 = enemy.closer_than(3, self.arriveplace[2]).amount
                    if n_enemy1 < 5:
                        actions.append(actions.append(unit(AbilityId.UNLOADALLAT, self.arriveplace[0])))
                    elif n_enemy2<5:
                        actions.append(actions.append(unit(AbilityId.UNLOADALLAT, self.arriveplace[1])))
                    elif n_enemy3<5:
                        actions.append(actions.append(unit(AbilityId.UNLOADALLAT, self.arriveplace[2])))
                    else:
                        actions.append(actions.append(unit.move(transplace)))
                    '''
                    '''
                    if len(unit.passengers)<=5:
                        actions.append(unit(AbilityId.UNLOADALLAT, arriveplace2))
                    else:
                        actions.append(unit(AbilityId.UNLOADALLAT, arriveplace))
                    '''
                
            '''   
            else:
                target_pssn = self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARAUDER) \
                    | self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.SIEGETANK) \
                    | self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.REAPER) \
                    | self.bot.units.filter(lambda u: u.position3d.z < 11).of_type(UnitTypeId.MARINE)   
                    

                units = self.bot.units.of_type(ARMY_TYPES).owned
                n_units = units.closer_than(self.region_radius, arriveplace).amount
                full = self.bot.units.filter(lambda u : u.cargo_used >=7).of_type(UnitTypeId.MEDIVAC)
                if len(unit.passengers)==0 and distance > 2 and distance2 >= 20:
                    actions.append(unit.move(transplace))
            
                elif target_pssn.exists and len(unit.passengers) < 6 and distance2 >= 20:
                    actions.append(unit(AbilityId.LOAD,target_pssn.closest_to(unit.position) ))

                elif unit.cargo_used == 8:  
                    if not unit.has_buff(BuffId.MEDIVACSPEEDBOOST) :
                        order = unit(AbilityId.EFFECT_MEDIVACIGNITEAFTERBURNERS)
                        actions.append(order)
                    else:
                        if len(unit.passengers)<=5:
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace2))
                        else:
                            actions.append(unit(AbilityId.UNLOADALLAT, arriveplace))
            '''
                
                
            

        

        return actions

    

    def debug(self):
        text = [

            f'Tactics: {self.tactics}, state: {self.state}',
        ]
        self.bot._client.debug_text_screen(
            '\n\n'.join(text), pos=(0.02, 0.14), size=10)