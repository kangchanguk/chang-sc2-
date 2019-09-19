from ...units import unitwrapper
from ..continuous_ppo import ContinuousPPO
from ..environment2 import Environment
import tensorflow as tf
import os
import numpy as np

class ArmyAgent:
    def __init__(self, bot, session, name):
        self.bot = bot
        self.army = None
        self.env = Environment(self.bot)
        self.s_lst = list()
        self.a_lst = list()
        self.r_lst = list()
        self.done_lst = list()
        self.oldpi = list()
        self.currstep = -1     

        self.epoch = 4
        self.minibatch = 4
        self.steps = 64

        self.action = None

        with tf.variable_scope(name, reuse=tf.AUTO_REUSE):
            self.state = tf.placeholder(tf.float32, shape=[None, self.env.state_size], name="state")
            map_data, players = tf.split(self.state, [self.env.map_obs_size, 14], 1)
            map_data = tf.reshape(map_data, [-1, *self.env.map_obs.shape])

            map_data = tf.layers.conv2d(map_data, 128, kernel_size=(8, 8), strides=(4, 4), activation=tf.nn.relu, name="conv1")
            map_data = tf.layers.conv2d(map_data, 128, kernel_size=(8, 8), strides=(1, 1), activation=tf.nn.relu, name="conv2")
            map_data = tf.layers.flatten(map_data)
            net = tf.layers.dense(map_data, 512, activation=tf.nn.relu, name="map_dense")
            net = tf.concat([net, players], 1)
            net = tf.layers.dense(net, 256, activation=tf.nn.relu, name="all_dense")
            self.ppo = ContinuousPPO(session, self.state, net, 2, name)
            

    
    def set_army(self, army):
        self.army = army
        self.env.set_army(army)
        self.action = (self.army.center.x, self.army.center.y)
        

    def update(self):
        if len(self.s_lst) >= 2:
            print(f"{len(self.s_lst)}, {len(self.a_lst)}, {len(self.r_lst)}, {len(self.done_lst)}, {len(self.oldpi)}")
            self.ppo.TrainBatch(self.s_lst, self.a_lst, self.r_lst, self.done_lst, self.oldpi, self.minibatch, self.epoch)
            self.s_lst = [self.s_lst[-1]]
            self.a_lst = list()
            self.r_lst = list()
            self.done_lst = list()
            self.oldpi = list()
            self.currstep = 0
        

    def step(self):
        if self.env.done:
            return
            
        self.env.step()
        self.s_lst.append(self.env.state.copy())
        if self.currstep != -1:
            self.r_lst.append(self.env.reward)
            self.done_lst.append(0 if self.env.done else 1)
        self.currstep += 1
        if self.env.done:
            self.update()
        elif self.currstep >= 20:
            self.update()
        action, prob = self.ppo.getAction(self.env.state)
        self.a_lst.append(action)
        self.oldpi.append(prob)
        self.action = (action[0] * 64 + 12, action[1] * 64 + 12)
