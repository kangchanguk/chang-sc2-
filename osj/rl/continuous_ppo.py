import numpy as np
import math
import tensorflow as tf
import run_train

learning_rate = 0.001
beta = 0.5
beta2 = 0.001
gamma = 0.99
epsilon = 0.2
lamda = 0.95
max_grad_norm = 0.5



class ContinuousPPO:
    def __init__(self, sess, state, network, action_size, value_network=None, name=""):
        self.state = state
        self.sess = sess
        self.action_size = action_size
        self.name = name
        self.global_step = 0
        self.bulidNetwork(network, value_network)
        
    def bulidNetwork(self, network, value_network=None):
        tf.summary.histogram('net', network)

        self.advantage = tf.placeholder(tf.float32, [None], name="Advantage")
        self.td_target = tf.placeholder(tf.float32, [None], name="td_target")
        self.action = tf.placeholder(tf.int32, [None], name="Action")
        self.old_pi_a = tf.placeholder(tf.float32, [None], name="Old_pi_a")
        self.reward = tf.placeholder(tf.float32, [None], name="reward")
        if value_network == None:
            self.value = tf.layers.dense(network, 1, name="Value")
        else:
            self.value = tf.layers.dense(value_network, 1, name="Value")
        self.policy_mean = tf.layers.dense(network, self.action_size, activation=tf.nn.sigmoid, name="Policy_mean")
        self.policy_var = tf.layers.dense(network, self.action_size, activation=tf.nn.softplus, name="Policy_var")

        log_pi_a = -tf.reduce_sum((self.policy_mean - self.action) ** 2 / (2*self.policy_var) - tf.log(tf.sqrt(2 * math.pi * self.policy_var)), 1)

        ratio = tf.exp(log_pi_a - self.old_pi_a)
        
        entropy = -tf.reduce_sum(tf.log(tf.sqrt(2 * math.pi * math.e * self.policy_var)), 1)
        
        self.entropy = tf.reduce_mean(entropy)
        self.actor_gain =  tf.reduce_mean(tf.minimum(ratio * self.advantage, tf.clip_by_value(ratio, 1 - epsilon, 1 + epsilon) * self.advantage))
        self.critic_loss =  tf.reduce_mean(tf.square(self.td_target - tf.squeeze(self.value)))

        self.loss =  -self.actor_gain + self.entropy * beta2 + self.critic_loss * beta
        trainer = tf.train.AdamOptimizer(learning_rate=learning_rate,epsilon=1e-5)

        params = tf.trainable_variables(self.name)
        grads_and_var = trainer.compute_gradients(self.loss, params)
        grads, var = zip(*grads_and_var)
        if max_grad_norm != None:
            grads, _ = tf.clip_by_global_norm(grads, max_grad_norm)
        grads_and_var = list(zip(grads, var))
        self.train = trainer.apply_gradients(grads_and_var)


        tf.summary.scalar('loss', self.loss)
        tf.summary.scalar('actor_gain', self.actor_gain)
        tf.summary.scalar('critic_loss', self.critic_loss)
        tf.summary.scalar('entropy', self.entropy)
        tf.summary.scalar('value', tf.reduce_mean(self.value))
        tf.summary.scalar('average reward', tf.reduce_mean(self.reward))
        
        self.summarys = tf.summary.merge_all()
        self.writer = tf.summary.FileWriter("./logs/" + self.name, self.sess.graph)

    def getValue(self, state):
        feed_dict = {self.state : state}
        return self.sess.run(self.value, feed_dict)

    def getPi(self, state):
        feed_dict = {self.state : state}
        return self.sess.run([self.policy_mean, self.policy_var], feed_dict=feed_dict)

    def getAction(self, state):
        mean, var = self.getPi([state])
        mean = np.squeeze(mean, 0)
        var = np.squeeze(var, 0)
        choices = np.clip(np.random.normal(mean, var), 0, 1)
        return choices, np.sum(self.get_log_prob(choices, mean, var))

    def get_log_prob(self, value, mean, var):
        return -((mean - value) ** 2 / (2*var)) - np.log(np.sqrt(2*np.pi*var))

    def TrainBatch(self, s_lst, a_lst, r_lst, done_lst, action_prob_lst, minibatch_size, epochs):
        s2_lst = np.array(s_lst[1:])
        s_lst = np.array(s_lst[:-1])
        r_lst = np.array(r_lst)
        a_lst = np.array(a_lst)
        done_lst = np.array(done_lst)
        action_prob_lst = np.array(action_prob_lst)

        td_target_lst = r_lst + gamma * np.reshape(self.getValue(s2_lst), [-1]) * done_lst
        value_lst = np.reshape(self.getValue(s_lst), [-1])
        advantage_lst = td_target_lst - value_lst
        
        advantage_lst = (advantage_lst - np.mean(advantage_lst)) / (np.std(advantage_lst) + 1e-8)
        size = len(a_lst)
        for _ in range(epochs):
            for i in range(0, size, minibatch_size):
                end = min(i + minibatch_size, size)
                datas, _ = self.sess.run([self.summarys, self.train], feed_dict={self.state : s_lst[i:end], self.td_target:td_target_lst[i:end], self.action:a_lst[i:end], self.advantage:advantage_lst[i:end], self.old_pi_a:action_prob_lst[i:end], self.reward:r_lst[i:end]})
                self.writer.add_summary(datas, run_train.getsteps())