import sc2
from sc2.position import Point2, Point3
from sc2.ids.unit_typeid import UnitTypeId
from sc2.data import Result
import osj.map
import osj.tracker
from .armys import initarmy
from .rl.agents import armyagent, contarmyagent
from .strategies import tankai_strategy, ai_strategy
import tensorflow as tf
import os

DEBUG = True

class OsjAiBot(sc2.BotAI):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.prevtime = 0
        self.prepare_networks()
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
        self.strategy = tankai_strategy.TankAiStrategy(self)
        self.my_units = dict()
        self.episode_steps = 0
        self.resetting = False

    def prepare_networks(self):
        self.savers = list()
        self.save_paths = list()
        tf.reset_default_graph()
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        self.session = tf.Session(config=config)
        self.agents = { #"PushArmyAgent" : armyagent.ArmyAgent(self, self.session, 128, False, "PushArmyAgent"),
                        "TankArmyAgent" : armyagent.ArmyAgent(self, self.session, 4, False, "TankArmyAgent")
                        }
        init = tf.global_variables_initializer()
        self.session.run(init)

        for agent in self.agents.values():
            var_list = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, agent.name)
            saver = tf.train.Saver(var_list=var_list)
            save_path = "models/" + agent.name + "/model.ckpt"

            if not os.path.exists("models/" + agent.name):
                os.makedirs("models/" + agent.name)
                print("Directory models/" + agent.name + " was created")

            if tf.train.get_checkpoint_state(os.path.dirname(save_path)):
                saver.restore(self.session, save_path)
                print("Model restored to global")
            else:
                print("No model is found")
            self.savers.append(saver)
            self.save_paths.append(save_path)

    def save_network(self):
        for i in range(len(self.savers)):
            self.savers[i].save(self.session, self.save_paths[i])
        self.episode_steps += 1
        print("Saved!")

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
        self.tracker.reward = 0
        
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
        self.prevtags = self.units.tags.union(self.load_tags)
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
            self.save_network()
            await self.reset()

    def on_end(self, result):
        self.session.close()
        pass

    async def reset(self):
        await self.chat_send("#RESET")
        await self._client.send_debug()
        self.reset_bot()
        
