import os, sys, glob
import importlib
import time

base_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_path)

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
from PyQt5.QtCore import QThread
import threading

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from kube_sim_gym.envs.sim_kube_env import SimKubeEnv

from_class = uic.loadUiType('KubeSimGui.ui')[0]

# class SchedulerThread(QThread):
#     def __init__(self, myWindow):
#         super().__init__()
#         self.scheduler = myWindow.scheduler
#         self.myWindow = myWindow

#     def run(self):
#         while self.myWindow.env.done == False:
#             self.myWindow.scheduler_step()
#             self.myWindow.update_all()
#             time.sleep(self.myWindow.runSpeed)

class WindowClass(QMainWindow, from_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle('Kubernetes Simulator')

        # ================== Scenario ==================

        # Fetch Scenarios 
        self.scenarios_path = glob.glob(os.path.join(base_path, 'scenarios', '*.csv'))
        self.scenarios = [os.path.basename(path) for path in self.scenarios_path]
        self.scenarioCombo.addItems(['Select Scenario'])
        self.scenarioCombo.addItems(self.scenarios)

        # Disable btns
        self.runStrategyBtn.setEnabled(False)
        self.stopStrategyBtn.setEnabled(False)
        self.actionBtn_0.setEnabled(False)
        self.actionBtn_1.setEnabled(False)
        self.actionBtn_2.setEnabled(False)
        self.actionBtn_3.setEnabled(False)
        self.actionBtn_4.setEnabled(False)
        self.actionBtn_5.setEnabled(False)

        # Scenario Combo
        self.scenarioCombo.currentIndexChanged.connect(lambda: self.update_scenario())

        # Scenario btns
        self.scenario = None

        # Action
        self.action = None
        self.nextAction = None

        # Info
        self.info = None

        # Reward
        self.reward = 0
        self.reward_accumulated = 0

        # Pending Pods
        self.pending_pod1 = None
        self.pending_pod2 = None
        self.pending_pod3 = None

        # ================== Scheduler ==================

        self.scheduler = None
        # self.schedulerThread = None

        


        # ================== Strategy ==================

        # Fetch Strategies reward
        self.rl_strategies_reward_path = glob.glob(os.path.join(base_path, 'kube_rl_scheduler', 'strategies', 'reward', '*.py'))
        print(os.path.join(base_path, 'kube_sim_gym', 'strategies', 'reward', '*.py'))
        self.rl_strategies_reward_path = [path for path in self.rl_strategies_reward_path if '__init__' not in path]
        self.rl_strategies_reward = [os.path.basename(path) for path in self.rl_strategies_reward_path]
        # hr_strategies_path = glob.glob(os.path.join(os.path.dirname(__file__), 'kube_python_scheduler', 'strategies', '*.py'))
        # hr_strategies = [os.path.basename(path) for path in hr_strategies_path]

        # Fetch Strategies model
        self.rl_strategies_model_path = glob.glob(os.path.join(base_path, 'kube_rl_scheduler', 'strategies', 'model', '*'))
        self.rl_strategies_model_path = [path for path in self.rl_strategies_model_path if '__init__' not in path]
        self.rl_strategies_model = [os.path.basename(path) for path in self.rl_strategies_model_path]

        # Strategy kind
        self.strategyKind_1.clicked.connect(lambda: self.update_strategyList('HR'))
        self.strategyKind_2.clicked.connect(lambda: self.update_strategyList('RL'))

        # Strategy btns
        self.strategyReward = None
        self.strategyModel = None
        self.strategyRewardCombo.currentIndexChanged.connect(lambda: self.update_strategyReward())
        self.strategyModelCombo.currentIndexChanged.connect(lambda: self.update_strategyModel())

        self.runStrategyBtn.clicked.connect(lambda: self.btn_runStrategy())
        self.stopStrategyBtn.clicked.connect(lambda: self.btn_stopStrategy())
        self.oneStepBtn.clicked.connect(lambda: self.scheduler_step())


        # Running speed
        self.runSpeed_spin.setMinimum(1)
        self.runSpeed_spin.setMaximum(10)
        self.runSpeed_spin.setValue(1)
        self.runSpeed = self.runSpeed_spin.value()
        self.runSpeed_spin.valueChanged.connect(lambda: self.update_runSpeed())


        # ================== Action ==================

        # Action btns
        self.actionBtn_0.clicked.connect(lambda: self.btn_step('actionBtn_0'))
        self.actionBtn_1.clicked.connect(lambda: self.btn_step('actionBtn_1'))
        self.actionBtn_2.clicked.connect(lambda: self.btn_step('actionBtn_2'))
        self.actionBtn_3.clicked.connect(lambda: self.btn_step('actionBtn_3'))
        self.actionBtn_4.clicked.connect(lambda: self.btn_step('actionBtn_4'))
        self.actionBtn_5.clicked.connect(lambda: self.btn_step('actionBtn_5'))

        # Reset btn
        self.resetBtn.clicked.connect(lambda: self.btn_reset())

        # Info area
        self.info_Area.setPlainText(f"scenario: {self.scenario} / strategy: {self.strategyReward}")

        # Progress bar
        self.progressBar.setValue(0)
        self.progressBarLabel.setText(str(0) + '%')

        # Environment
        self.env = SimKubeEnv()
        self.env.reset()

        # Timer
        self.update_time()

        # ================== Last Action ==================
        self.update_lastAction()

        # ================== Node State ==================
        self.initialize_node_state()

        # ================== Pod State ==================
        self.initialize_pod_state()

    # ================== Scheduler Functions ==================

    # def start_schedulerThread(self):
    #     self.schedulerThread.start()

    # def stop_schedulerThread(self):
    #     self.schedulerThread.stop()

    def update_scheduler(self):
        if not self.strategyModel:
            return
        if "py" in self.strategyModel:
            scheduler_module_path = os.path.join(f"kube_rl_scheduler", "strategies", "model", os.path.splitext(self.strategyModel)[0]).replace('/', '.')
            self.scheduler = importlib.import_module(scheduler_module_path)
        else:
            scheduler_module_path = os.path.join(f"kube_rl_scheduler", "scheduler", "rl_scheduler").replace('/', '.')
            _scheduler_module = importlib.import_module(scheduler_module_path)
            self.scheduler = _scheduler_module.RlScheduler(self.env, self.strategyModel.split('.')[0])


    def scheduler_step(self):
        self.action = self.nextAction # self.scheduler.decision(self.env)
        self.state, self.reward, self.done, self.info = self.env.step(self.action)
        self.reward_accumulated += self.reward
        self.update_lastAction(self.info)
        self.update_all()

    def update_runSpeed(self):
        self.runSpeed = self.runSpeed_spin.value()
        print('run speed changed : ' + str(self.runSpeed))

    # ================== Scenario Functions ==================

    def update_scenario(self):
        self.scenario = self.scenarioCombo.currentText()
        print('scenario changed : ' + self.scenario)
        self.update_all()
        if self.scenario and self.strategyReward:
            self.init_env()

    # ================== Strategy Functions ==================

    def update_strategyReward(self):
        self.strategyReward = self.strategyRewardCombo.currentText()
        print('reward changed : ' + self.strategyReward)
        self.update_all()
        if self.strategyReward and self.strategyModel:
            self.init_env()
            self.activate_strategyBtn()
            self.activate_actionBtns()

    def update_strategyModel(self):
        self.strategyModel = self.strategyModelCombo.currentText()
        self.init_env()
        print('reward changed : ' + self.strategyModel)
        self.update_all()
        if self.strategyReward and self.strategyModel:
            self.activate_strategyBtn()
            self.activate_actionBtns()
        self.update_scheduler()
        # self.schedulerThread = SchedulerThread(self)
        # self.start_schedulerThread()

    def update_strategyList(self, kind):
        if kind == 'HR':
            print('HR clicked')
            self.update_strategyRewardList('HR')
            self.update_strategyModelList('HR')
        elif kind == 'RL':
            print('RL clicked')
            self.update_strategyRewardList('RL')
            self.update_strategyModelList('RL')
        self.update_all()


    def update_strategyRewardList(self, rewardKind):
        if rewardKind == 'HR':
            print('HR clicked')
            self.strategyRewardCombo.clear()
            self.strategyRewardCombo.addItems(self.rl_strategies_reward) # Need to be changed to hr_strategies
        elif rewardKind == 'RL':
            print('RL clicked')
            self.strategyRewardCombo.clear()
            self.strategyRewardCombo.addItems(self.rl_strategies_reward)
        self.update_all()

    def update_strategyModelList(self, modelKind):
        if modelKind == 'HR':
            print('HR clicked')
            self.strategyModelCombo.clear()
            self.strategyModelCombo.addItems(self.rl_strategies_model) # Need to be changed to hr_strategies
        elif modelKind == 'RL':
            print('RL clicked')
            self.strategyModelCombo.clear()
            self.strategyModelCombo.addItems(self.rl_strategies_model)
        self.update_all()

    def btn_runStrategy(self):
        print('runStrategyBtn clicked')
        # Run scheduler until done\
        if not self.schedulerThread or not self.scheduler:
            return
        # self.start_schedulerThread()

    def btn_stopStrategy(self):
        print('stopStrategyBtn clicked')
        # Stop the scheduler thread
        if not self.schedulerThread or not self.scheduler:
            return
        # self.stop_schedulerThread()




    # ================== Action Functions ==================

    def btn_step(self, btn):
        print(btn + ' clicked')
        self.info_Area.setPlainText(btn + ' clicked')
        self.action = int(btn[-1])
        self.state, self.reward, self.done, self.info = self.env.step(self.action)
        self.reward_accumulated += self.reward
        self.update_lastAction(self.info)
        self.update_all()

    # ================== ETC ==================

    def btn_clicked(self, btn):
        print(btn + ' clicked')
        self.info_Area.setPlainText(btn + ' clicked')

    def update_lastAction(self, info=None):
        if self.action == None:
            lastAction = 'None'
        elif self.action == 0:
            lastAction = 'Stand by'
        elif self.action in  [1,2,3,4,5]:
            if info:
                if info['is_scheduled']:
                    pod = info['last_pod']
                    lastAction = f"Schedule {pod.pod_idx}th pod (cpu: {int(pod.spec['cpu_ratio']*100)}% / mem: {int(pod.spec['mem_ratio']*100)}%) to node {self.action}"
                else:
                    lastAction = f"Failed to schedule pod to node {self.action}"
        self.lastActionLabel.setText(lastAction)

    def update_time(self):
        time = self.env.time
        self.timeLabel.setText(str(time))

    def btn_reset(self):
        print('reset clicked')
        self.env = SimKubeEnv(self.strategyReward, self.scenario)
        self.env.reset()
        self.state = None
        self.action = None
        self.nextAction = None
        self.reward = 0
        self.reward_accumulated = 0
        self.done = None
        self.update_all()


    def init_env(self):
        self.env = SimKubeEnv(self.strategyReward, self.scenario)
        self.env.reset()

    def update_settings(self):
        settings = f"scenario:\n{self.scenario}\nreward:\n{self.strategyReward}\nmodel:\n{self.strategyModel}"
        self.settings_Area.setPlainText(settings)

    def update_info(self):
        text = f"""state: {self.env.get_state()}\naction: {self.action}\nreward: {round(self.env.reward, 2)}\nreward(accumulated): {round(self.reward_accumulated, 2)}\ndone: {self.env.get_done()}"""
        self.info_Area.setPlainText(text)

    def update_progressBar(self):
        len_scenario = len(self.env.stress_gen.scenario)
        len_scheduled = len(self.env.cluster.terminated_pods + self.env.cluster.running_pods)
        progress = int(len_scheduled / len_scenario * 100)
        self.progressBar.setValue(progress)
        self.progressBarLabel.setText(f"{str(progress)}% ({len_scheduled}/{len_scenario})")

    def update_nextAction(self):
        if self.scheduler:
            self.nextAction = self.scheduler.decision(self.env)
            self.nextAction_Area.setPlainText(str(self.nextAction))

    def update_all(self):
        print('update_all')
        self.update_settings()
        self.update_info()
        self.update_progressBar()
        self.update_time()
        self.update_node_state()
        self.update_pod_state()
        self.update_nextAction()

    # Activation

    def activate_strategyBtn(self):
        self.runStrategyBtn.setEnabled(True)
        self.stopStrategyBtn.setEnabled(True)
        self.oneStepBtn.setEnabled(True)
        

    def activate_actionBtns(self):
        self.actionBtn_0.setEnabled(True)
        self.actionBtn_1.setEnabled(True)
        self.actionBtn_2.setEnabled(True)
        self.actionBtn_3.setEnabled(True)
        self.actionBtn_4.setEnabled(True)
        self.actionBtn_5.setEnabled(True)

    # ================== Draw Node state ==================

    def initialize_node_state(self):
        self.node1_cpu_bar.setValue(0)
        self.node1_mem_bar.setValue(0)
        self.node2_cpu_bar.setValue(0)
        self.node2_mem_bar.setValue(0)
        self.node3_cpu_bar.setValue(0)
        self.node3_mem_bar.setValue(0)
        self.node4_cpu_bar.setValue(0)
        self.node4_mem_bar.setValue(0)
        self.node5_cpu_bar.setValue(0)
        self.node5_mem_bar.setValue(0)

    def update_node_state(self):
        self.node2_cpu_bar.setValue(int(self.env.cluster.nodes[1].status['cpu_ratio'] * 100))
        self.node1_cpu_bar.setValue(int(self.env.cluster.nodes[0].status['cpu_ratio'] * 100))
        self.node1_mem_bar.setValue(int(self.env.cluster.nodes[0].status['mem_ratio'] * 100))
        self.node2_mem_bar.setValue(int(self.env.cluster.nodes[1].status['mem_ratio'] * 100))
        self.node3_cpu_bar.setValue(int(self.env.cluster.nodes[2].status['cpu_ratio'] * 100))
        self.node3_mem_bar.setValue(int(self.env.cluster.nodes[2].status['mem_ratio'] * 100))
        self.node4_cpu_bar.setValue(int(self.env.cluster.nodes[3].status['cpu_ratio'] * 100))
        self.node4_mem_bar.setValue(int(self.env.cluster.nodes[3].status['mem_ratio'] * 100))
        self.node5_cpu_bar.setValue(int(self.env.cluster.nodes[4].status['cpu_ratio'] * 100))
        self.node5_mem_bar.setValue(int(self.env.cluster.nodes[4].status['mem_ratio'] * 100))

    # ================== Draw Pod state ==================

    def initialize_pod_state(self, scope=0): # 0: All
        if scope == 1 or scope == 0:
            # Pod 1
            self.pod1_idx.setText('')
            self.pod1_cpu_req.setText('')
            self.pod1_mem_req.setText('')
            self.pod1_duration.setText('')
            self.pod1_arrival_t.setText('')
        if scope == 2 or scope == 0:
            # Pod 2
            self.pod2_idx.setText('')
            self.pod2_cpu_req.setText('')
            self.pod2_mem_req.setText('')
            self.pod2_duration.setText('')
            self.pod2_arrival_t.setText('')
        if scope == 3 or scope == 0:
            # Pod 3
            self.pod3_idx.setText('')
            self.pod3_cpu_req.setText('')
            self.pod3_mem_req.setText('')
            self.pod3_duration.setText('')
            self.pod3_arrival_t.setText('')

    def update_pod_state(self):
        # Pod 1
        if len(self.env.cluster.pending_pods) > 0:
            self.pending_pod1 = self.env.cluster.pending_pods[0]
            self.pod1_idx.setText(f"{self.pending_pod1.pod_idx}th")
            self.pod1_cpu_req.setText(f"{self.pending_pod1.spec['cpu_req']}m ({int(self.pending_pod1.spec['cpu_ratio'] * 100)}%)")
            self.pod1_mem_req.setText(f"{self.pending_pod1.spec['mem_req']}Mi ({int(self.pending_pod1.spec['mem_ratio'] * 100)}%)")
            self.pod1_duration.setText(f"{self.pending_pod1.spec['duration']}m")
            self.pod1_arrival_t.setText(f"{self.pending_pod1.spec['arrival_time']}s")
        else:
            self.initialize_pod_state(1)
        # Pod 2
        if len(self.env.cluster.pending_pods) > 1:
            self.pending_pod2 = self.env.cluster.pending_pods[1]
            self.pod2_idx.setText(f"{self.pending_pod2.pod_idx}th")
            self.pod2_cpu_req.setText(f"{self.pending_pod2.spec['cpu_req']}m ({int(self.pending_pod2.spec['cpu_ratio'] * 100)}%)")
            self.pod2_mem_req.setText(f"{self.pending_pod2.spec['mem_req']}Mi ({int(self.pending_pod2.spec['mem_ratio'] * 100)}%)")
            self.pod2_duration.setText(f"{self.pending_pod2.spec['duration']}m")
            self.pod2_arrival_t.setText(f"{self.pending_pod2.spec['arrival_time']}s")
        else:
            self.initialize_pod_state(2)
        # Pod 3
        if len(self.env.cluster.pending_pods) > 2:
            self.pending_pod3 = self.env.cluster.pending_pods[2]
            self.pod3_idx.setText(f"{self.pending_pod3.pod_idx}th")
            self.pod3_cpu_req.setText(f"{self.pending_pod3.spec['cpu_req']}m ({int(self.pending_pod3.spec['cpu_ratio'] * 100)}%)")
            self.pod3_mem_req.setText(f"{self.pending_pod3.spec['mem_req']}Mi ({int(self.pending_pod3.spec['mem_ratio'] * 100)}%)")
            self.pod3_duration.setText(f"{self.pending_pod3.spec['duration']}m")
            self.pod3_arrival_t.setText(f"{self.pending_pod3.spec['arrival_time']}s")
        else:
            self.initialize_pod_state(3)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = WindowClass()
    myWindow.show()
    app.exec_()