from ..units import unitwrapper
import tensorflow as tf

class UnitAgent:
    def __init__(self, name):
        with tf.variable_scope(name):
            self.observation = tf.placeholder(tf.float32, shape=[None, 2, 32, 32, 22], name="observation")
            self.unitdata = tf.placeholder(tf.float32, shape=[None, 8])
            net = self.observation.spli

            with tf.variable_scope("conv1"):
                net = tf.layers.conv2d(net,
                                       filters=64,
                                       kernel_size=(8, 8),
                                       strides=(4, 4),
                                       name="conv")
                net = tf.nn.relu(net, name="relu")

            with tf.variable_scope("conv2"):
                net = tf.layers.conv2d(net,
                                       filters=128,
                                       kernel_size=(4, 4),
                                       strides=(2, 2),
                                       name="conv")
                net = tf.nn.relu(net, name="relu")

            with tf.variable_scope("dense1"):
                net = tf.contrib.layers.flatten(net)
                net = tf.layers.dense(net, 64, name='dense')
                net = tf.nn.relu(net, name='relu')

            with tf.variable_scope("dense2"):
                net = tf.concat(1, [net, unitdata])
                net = tf.layers.dense(net, 32, name='dense')
                net = tf.nn.relu(net, name='relu')

            
            
            
