import numpy as np
import tensorflow as tf
import sys
import run_train

learning_rate = 0.0005
beta = 0.5
beta2 = 0.01
gamma = 0.99
epsilon = 0.1
lamda = 0.95
max_grad_norm = 0.5

class PPO:
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
        self.policy = tf.layers.dense(network, self.action_size, activation=tf.nn.softmax, name="Policy")

        pi_a = self.policy * tf.one_hot(self.action, self.action_size)
        pi_a = tf.reduce_sum(pi_a, 1)

        ratio = tf.exp(tf.log(pi_a + 1e-4) - tf.log(self.old_pi_a + 1e-4))

        entropy = tf.reduce_sum(self.policy * tf.log(self.policy + 1e-4), 1)
        self.entropy = tf.reduce_mean(entropy)
        
        self.actor_gain = tf.reduce_mean(tf.minimum(ratio * self.advantage, tf.clip_by_value(ratio, 1 - epsilon, 1 + epsilon) * self.advantage))
        self.critic_loss = tf.reduce_mean(tf.squared_difference(self.td_target, tf.squeeze(self.value)))

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
        return self.sess.run(self.policy, feed_dict)

    def getAction(self, state):
        prob = np.squeeze(self.getPi([state]))
        choice = np.random.choice(np.arange(len(prob)), p=prob.ravel())
        return choice, prob[choice]

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