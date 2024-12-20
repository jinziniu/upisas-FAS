import random
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam


from UPISAS.strategy import Strategy


class ReactiveAdaptationManager(Strategy):
    def __init__(self, state_size, action_size, initial_params):
        """
        初始化 DQN 模型和初始参数
        """
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95  # 折扣因子
        self.epsilon = 1.0  # 初始探索率
        self.epsilon_min = 0.01  # 最小探索率
        self.epsilon_decay = 0.995  # 探索率的衰减速度
        self.learning_rate = 0.001
        self.model = self._build_model()

        # 当前参数
        self.exploration_percentage = initial_params["explorationPercentage"]
        self.average_edge_duration_factor = initial_params["averageEdgeDurationFactor"]
        self.route_random_sigma = initial_params["routeRandomSigma"]

        # 分析和计划数据
        self.analysis_data = {}
        self.plan_data = {}

    def _build_model(self):
        """
        构建用于 DQN 的神经网络模型
        """
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(lr=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        """
        存储经验回放的数据
        """
        self.memory.append((state, action, reward, next_state, done))

    def replay(self):
        """
        用于从记忆中采样并训练 DQN 的经验回放机制
        """
        if len(self.memory) < 32:
            return
        minibatch = random.sample(self.memory, 32)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = reward + self.gamma * np.max(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def analyze(self, state):
        """
        分析当前环境状态，将结果存储到 self.analysis_data 中
        """
        q_values = self.model.predict(state)
        best_action = np.argmax(q_values[0])
        parameter_adjustments = self._decode_action(best_action)

        self.analysis_data = {
            "q_values": q_values,
            "best_action": best_action,
            "parameter_adjustments": parameter_adjustments,
        }
        return self.analysis_data

    def _decode_action(self, action):
        """
        根据动作索引解码成具体的参数调整
        """
        adjustment_ranges = {
            "explorationPercentage": [0.0, 1.0],
            "averageEdgeDurationFactor": [0.1, 2.0],
            "routeRandomSigma": [0.0, 1.0],
        }

        exploration = adjustment_ranges["explorationPercentage"][0] + \
                      (adjustment_ranges["explorationPercentage"][1] - adjustment_ranges["explorationPercentage"][0]) * (action % 10) / 9.0
        edge_duration = adjustment_ranges["averageEdgeDurationFactor"][0] + \
                        (adjustment_ranges["averageEdgeDurationFactor"][1] - adjustment_ranges["averageEdgeDurationFactor"][0]) * ((action // 10) % 10) / 9.0
        route_sigma = adjustment_ranges["routeRandomSigma"][0] + \
                      (adjustment_ranges["routeRandomSigma"][1] - adjustment_ranges["routeRandomSigma"][0]) * (action // 100) / 9.0

        return {
            "explorationPercentage": exploration,
            "averageEdgeDurationFactor": edge_duration,
            "routeRandomSigma": route_sigma,
        }

    def plan(self):
        """
        基于分析结果调整参数
        """
        adjustments = self.analysis_data["parameter_adjustments"]
        self.plan_data = {
            "explorationPercentage": adjustments["explorationPercentage"],
            "averageEdgeDurationFactor": adjustments["averageEdgeDurationFactor"],
            "routeRandomSigma": adjustments["routeRandomSigma"],
        }
        return self.plan_data

    def step(self, state, reward, next_state, done):
        """
        更新 DQN 的记忆和模型
        """
        action = self.analysis_data["best_action"]
        self.remember(state, action, reward, next_state, done)
        self.replay()


class CrowdNavEnvironment:
    def __init__(self):
        self.state = [0.1, 0.2, 0.3]
        self.step_count = 0
        self.max_steps = 100

    def reset(self):
        self.state = [0.1, 0.2, 0.3]
        self.step_count = 0
        return self.state

    def step(self, action):
        self.step_count += 1
        next_state = [s + 0.01 * action for s in self.state]
        reward = -sum(abs(x - 0.5) for x in next_state)
        done = self.step_count >= self.max_steps
        self.state = next_state
        return next_state, reward, done


def train_manager(manager, environment, episodes=100):
    """
    训练 ReactiveAdaptationManager
    """
    for episode in range(episodes):
        state = environment.reset()
        state = np.reshape(state, [1, manager.state_size])  # 调整输入形状
        total_reward = 0
        done = False

        while not done:
            analysis_data = manager.analyze(state)  # 分析状态
            plan_data = manager.plan()  # 生成计划
            action = analysis_data["best_action"]  # 选择最佳动作

            next_state, reward, done = environment.step(action)  # 环境反馈
            next_state = np.reshape(next_state, [1, manager.state_size])  # 调整形状

            manager.step(state, reward, next_state, done)  # 更新模型
            state = next_state  # 更新当前状态
            total_reward += reward

        print(f"Episode {episode + 1}/{episodes}, Total Reward: {total_reward}")


if __name__ == "__main__":
    state_size = 3
    action_size = 1000

    initial_params = {
        "explorationPercentage": 0.1,
        "averageEdgeDurationFactor": 0.5,
        "routeRandomSigma": 0.2,
    }

    manager = ReactiveAdaptationManager(state_size, action_size, initial_params)
    environment = CrowdNavEnvironment()

    train_manager(manager, environment, episodes=10)


