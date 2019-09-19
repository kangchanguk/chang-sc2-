from ...units import unitwrapper
from ..ppo import PPO
from ..continuous_ppo import ContinuousPPO
from ..environment2 import Environment
import tensorflow as tf
import os
import numpy as np

class ArmyAgent:
    def __init__(self, bot, session, action_size, is_continuous, name):
        self.bot = bot
        self.army = None
        self.sess = session
        self.env = Environment(self.bot)
        self.s_lst = list()
        self.a_lst = list()
        self.r_lst = list()
        self.done_lst = list()
        self.oldpi = list()
        self.currstep = -1     
        self.name = name
        self.epoch = 4
        self.minibatch = 16
        self.steps = 64
        self.action_size = action_size
        self.rnn_size = 512
        self.rnn_state = np.zeros(self.rnn_size * 2)

        self.action = None
        self.prob = 0

        with tf.variable_scope(name, reuse=tf.AUTO_REUSE):
            self.state = tf.placeholder(tf.float32, shape=[None, self.env.state_size + self.rnn_size + self.rnn_size], name="state")
            map_data, players, pprev_rnn, vprev_rnn = tf.split(self.state, [self.env.map_obs_size, self.env.state_size - self.env.map_obs_size, self.rnn_size, self.rnn_size], 1)
            map_data = tf.reshape(map_data, [-1, *self.env.map_obs.shape])

            unit_map = map_data[:, :, :, 0:10]
            enemy_map = map_data[:, :, :, 10:20]
            height_map = map_data[:, :, :, 20]
            
            unit_map = tf.reduce_sum(unit_map, 3)
            enemy_map = tf.reduce_sum(enemy_map, 3)

            tf.summary.image("map", tf.stack([unit_map, height_map, enemy_map], axis=3))

            pmap_data = tf.layers.conv2d(map_data, 128, kernel_size=(8, 8), strides=(4, 4), activation=tf.nn.leaky_relu, name="pconv1")
            pmap_data = tf.layers.conv2d(pmap_data, 256, kernel_size=(4, 4), strides=(1, 1), activation=tf.nn.leaky_relu, name="pconv2")
            pmap_data = tf.layers.conv2d(pmap_data, 256, kernel_size=(4, 4), strides=(1, 1), activation=tf.nn.leaky_relu, name="pconv3")
            pmap_data = tf.layers.flatten(pmap_data)
            pmap_data = tf.layers.dense(pmap_data, 512, activation=tf.nn.leaky_relu, name="pmap_dense")
            pplayers = tf.layers.dense(players, 32, activation=tf.nn.leaky_relu, name="pplayer_dense")
            net = tf.concat([pmap_data, pplayers, pprev_rnn], 1)
            self.rnn = tf.layers.dense(net, self.rnn_size, activation=tf.nn.leaky_relu, name="prnn1")
            self.rnn = tf.layers.dense(self.rnn, self.rnn_size, activation=tf.nn.tanh, name="prnn2")

            vmap_data = tf.layers.conv2d(map_data, 128, kernel_size=(8, 8), strides=(4, 4), activation=tf.nn.leaky_relu, name="vconv1")
            vmap_data = tf.layers.conv2d(vmap_data, 256, kernel_size=(4, 4), strides=(1, 1), activation=tf.nn.leaky_relu, name="vconv2")
            vmap_data = tf.layers.conv2d(vmap_data, 256, kernel_size=(4, 4), strides=(1, 1), activation=tf.nn.leaky_relu, name="vconv3")
            vmap_data = tf.layers.flatten(vmap_data)
            vmap_data = tf.layers.dense(vmap_data, 512, activation=tf.nn.leaky_relu, name="vmap_dense")
            vplayers = tf.layers.dense(players, 32, activation=tf.nn.leaky_relu, name="vplayer_dense")
            net = tf.concat([vmap_data, vplayers, vprev_rnn], 1)
            self.vrnn = tf.layers.dense(net, self.rnn_size, activation=tf.nn.leaky_relu, name="vrnn1")
            self.vrnn = tf.layers.dense(self.vrnn, self.rnn_size, activation=tf.nn.tanh, name="vrnn2")
            if is_continuous:
                self.ppo = ContinuousPPO(session, self.state, self.rnn, action_size, value_network=self.vrnn, name=name)
            else:
                self.ppo = PPO(session, self.state, self.rnn, action_size, value_network=self.vrnn, name=name)
            

    
    def set_army(self, army):
        self.army = army
        self.env.set_army(army)

    def get_rnn_state(self):
        return self.sess.run([self.rnn, self.vrnn], feed_dict={self.state:[self.s_lst[-1]]})

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
    
    def debug(self):
        self.bot._client.debug_text_screen(f"Action:{self.action}\nProbability:{self.prob*100}%", pos=(0.02, 0.3), size=15)

    def step(self):
        if self.env.done:
            return
            
        self.env.step()
        self.s_lst.append(np.concatenate((self.env.state, self.rnn_state), axis=0))
        if self.currstep != -1:
            self.r_lst.append(self.env.reward)
            self.done_lst.append(0 if self.env.done else 1)
        self.currstep += 1
        if self.env.done:
            self.update()
        elif self.currstep >= 20:
            self.update()
        action, prob = self.ppo.getAction(self.s_lst[-1])
    
        self.rnn_state = np.squeeze(np.concatenate(self.get_rnn_state(), 1))
        self.a_lst.append(action)
        self.oldpi.append(prob)
        self.action = action
        self.prob = prob
