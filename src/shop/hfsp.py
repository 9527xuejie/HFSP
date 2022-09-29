import copy

import numpy as np

from .schedule import Schedule
from ..info import Info

deepcopy = copy.deepcopy


class Hfsp(Schedule):
    def __init__(self):
        Schedule.__init__(self)

    def decode(self, code):  # 基于最早完工时间和最小加工时间策略指派机器的解码算法
        self.clear()
        copy_code = deepcopy(code)
        mac, j = [[None for _ in range(job.nop)] for job in self.job.values()], 0
        while self.any_task_not_done():
            for i in copy_code:
                try:
                    a = self.job[i].task[j - 1].end
                except KeyError:
                    a = 0
                start, end, duration, index = [], [], [], []
                for k, p in zip(self.job[i].task[j].machine, self.job[i].task[j].duration):
                    for r, (b, c) in enumerate(zip(self.machine[k].idle[0], self.machine[k].idle[1])):
                        early_start = max([a, b])
                        if early_start + p <= c:
                            start.append(early_start)
                            end.append(early_start + p)
                            duration.append(p)
                            index.append(r)
                            break
                index_min_end = np.argwhere(np.array(end) == min(end))[:, 0]
                duration_in_min_end = np.array([duration[i] for i in index_min_end])
                choice_min_end_and_duration = np.argwhere(duration_in_min_end == np.min(duration_in_min_end))[:, 0]
                choice = index_min_end[np.random.choice(choice_min_end_and_duration, 1, replace=False)[0]]
                k, p, r = self.job[i].task[j].machine[choice], duration[choice], index[choice]
                mac[i][j] = k
                self.job[i].task[j].start = start[choice]
                self.job[i].task[j].end = end[choice]
                self.decode_update_machine_idle(i, j, k, r, start[choice])
            # copy_code = code[np.argsort([self.job[i].task[j].end for i in code])]
            copy_code = copy_code[np.argsort([self.job[i].task[j].end for i in copy_code])]
            j += 1
        return Info(self, code, mac=mac)

    def decode_hfsp(self, code, mac):
        self.clear()
        copy_code, j = deepcopy(code), 0
        while self.any_task_not_done():
            for i in copy_code:
                k = mac[i][j]
                p = self.job[i].task[j].duration[self.job[i].task[j].machine.index(k)]
                try:
                    a = self.job[i].task[j - 1].end
                except KeyError:
                    a = 0
                for r, (b, c) in enumerate(zip(self.machine[k].idle[0], self.machine[k].idle[1])):
                    early_start = max([a, b])
                    if early_start + p <= c:
                        self.job[i].task[j].start = early_start
                        self.job[i].task[j].end = early_start + p
                        self.decode_update_machine_idle(i, j, k, r, self.job[i].task[j].start)
                        break
            # copy_code = code[np.argsort([self.job[i].task[j].end for i in code])]
            copy_code = copy_code[np.argsort([self.job[i].task[j].end for i in copy_code])]
            j += 1
        return Info(self, code, mac=mac)

    def decode_with_trans(self, code):  # 基于最早完工时间和最小加工时间策略指派机器的解码算法，考虑机器之间的运输时间
        self.clear()
        copy_code = deepcopy(code)
        mac, j = [[None for _ in range(job.nop)] for job in self.job.values()], 0
        while self.any_task_not_done():
            for i in copy_code:
                try:
                    a = self.job[i].task[j - 1].end
                    pre_k = mac[i][j - 1]
                except KeyError:
                    a = 0
                    pre_k = None
                start, end, duration, index = [], [], [], []
                for k, p in zip(self.job[i].task[j].machine, self.job[i].task[j].duration):
                    try:
                        trans = self.machine[pre_k].trans[k]
                    except KeyError:
                        trans = 0
                    for r, (b, c) in enumerate(zip(self.machine[k].idle[0], self.machine[k].idle[1])):
                        early_start = max([a + trans, b])
                        if early_start + p <= c:
                            start.append(early_start)
                            end.append(early_start + p)
                            duration.append(p)
                            index.append(r)
                            break
                index_min_end = np.argwhere(np.array(end) == min(end))[:, 0]
                duration_in_min_end = np.array([duration[i] for i in index_min_end])
                choice_min_end_and_duration = np.argwhere(duration_in_min_end == np.min(duration_in_min_end))[:, 0]
                choice = index_min_end[np.random.choice(choice_min_end_and_duration, 1, replace=False)[0]]
                k, p, r = self.job[i].task[j].machine[choice], duration[choice], index[choice]
                mac[i][j] = k
                self.job[i].task[j].start = start[choice]
                self.job[i].task[j].end = end[choice]
                self.decode_update_machine_idle(i, j, k, r, start[choice])
            # copy_code = code[np.argsort([self.job[i].task[j].end for i in code])]
            copy_code = copy_code[np.argsort([self.job[i].task[j].end for i in copy_code])]
            j += 1
        return Info(self, code, mac=mac)

    def decode_hfsp_with_trans(self, code, mac):
        self.clear()
        copy_code, j = deepcopy(code), 0
        while self.any_task_not_done():
            for i in copy_code:
                k = mac[i][j]
                p = self.job[i].task[j].duration[self.job[i].task[j].machine.index(k)]
                try:
                    a = self.job[i].task[j - 1].end
                    pre_k = mac[i][j - 1]
                except KeyError:
                    a = 0
                    pre_k = None
                try:
                    trans = self.machine[pre_k].trans[k]
                except KeyError:
                    trans = 0
                for r, (b, c) in enumerate(zip(self.machine[k].idle[0], self.machine[k].idle[1])):
                    early_start = max([a + trans, b])
                    if early_start + p <= c:
                        self.job[i].task[j].start = early_start
                        self.job[i].task[j].end = early_start + p
                        self.decode_update_machine_idle(i, j, k, r, self.job[i].task[j].start)
                        break
            # copy_code = code[np.argsort([self.job[i].task[j].end for i in code])]
            copy_code = copy_code[np.argsort([self.job[i].task[j].end for i in copy_code])]
            j += 1
        return Info(self, code, mac=mac)
