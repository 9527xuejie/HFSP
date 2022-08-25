__doc__ = """
遗传算法
"""

import copy
import time

import numpy as np

from ..define import Selection
from ..resource.code import Code
from ..utils import Utils


class Ga:
    def __init__(self, pop_size, rc, rm, max_generation, objective, schedule, max_stay_generation=None):
        """
        初始化参数。
        pop_size: 种群规模；rc: 交叉概率；rm: 变异概率；max_generation: 最大迭代次数；
        objective: 求解目标值的函数；schedule: 调度对象；max_stay_generation：最大滞留代数
        """
        self.pop_size = pop_size
        self.rc = rc
        self.rm = rm
        self.max_generation = max_generation
        self.objective = objective
        self.schedule = schedule
        self.max_stay_generation = max_stay_generation
        self.best = [None, None, None, []]  # (info, objective, fitness, tabu)
        self.pop = [[], [], []]  # (info, objective, fitness)
        # (start, end, best_objective, best_fitness, worst_fitness, mean_fitness)
        self.record = [[], [], [], [], [], []]
        # (code, mac, tech)
        self.max_tabu = Utils.len_tabu(self.schedule.m, self.schedule.n)
        self.individual = range(self.pop_size)
        self.tabu_list = [[] for _ in self.individual]
        # for selection
        self.pop_copy = [[], [], []]
        self.tabu_copy = [[] for _ in self.individual]
        self.pop_selection_pool = [[], [], []]
        self.pop_selection_tabu_pool = []

    def clear(self):
        self.best = [None, None, None, [[], [], []]]
        self.pop = [[], [], []]
        self.record = [[], [], [], [], [], []]
        self.tabu_list = [[] for _ in self.individual]

    def get_obj_fit(self, info):
        a = self.objective(info)
        b = Utils.calculate_fitness(a)
        return a, b

    def decode(self, code):
        pass

    def replace_individual(self, i, info_new):
        obj_new, fit_new = self.get_obj_fit(info_new)
        self.pop[0][i] = info_new
        self.pop[1][i] = obj_new
        self.pop[2][i] = fit_new
        self.tabu_list[i] = []
        self.replace_best(info_new, obj_new, fit_new)

    def replace_individual_comp(self, i, info_new, info_new2):
        obj_new, fit_new = self.get_obj_fit(info_new)
        obj_new1, fit_new1 = self.pop_copy[1][i], self.pop_copy[2][i]
        obj_new2, fit_new2 = self.get_obj_fit(info_new2)
        fit_list = [fit_new, fit_new1, fit_new2]
        max_fit = max(fit_list)
        idx_max_fit = fit_list.index(max_fit)
        if idx_max_fit == 1:
            info_new, obj_new, fit_new = self.pop_copy[0][i], obj_new1, fit_new1
        elif idx_max_fit == 2:
            info_new, obj_new, fit_new = info_new2, obj_new2, fit_new2
        self.pop[0][i] = info_new
        self.pop[1][i] = obj_new
        self.pop[2][i] = fit_new
        self.tabu_list[i] = []
        self.replace_best(info_new, obj_new, fit_new)

    def replace_individual_better(self, i, info_new):
        obj_new, fit_new = self.get_obj_fit(info_new)
        if Utils.update_info(self.pop[1][i], obj_new):
            self.pop[0][i] = info_new
            self.pop[1][i] = obj_new
            self.pop[2][i] = fit_new
            self.tabu_list[i] = []
            self.replace_best(info_new, obj_new, fit_new)

    def replace_best(self, info_new, obj_new, fit_new):
        if Utils.update_info(self.best[1], obj_new):
            self.best[0] = info_new
            self.best[1] = obj_new
            self.best[2] = fit_new
            self.best[3] = []

    def show_generation(self, g):
        self.record[2].append(self.best[1])
        self.record[3].append(self.best[2])
        self.record[4].append(min(self.pop[2]))
        self.record[5].append(np.mean(self.pop[2]))
        Utils.print(
            "Generation {:<4} Runtime {:<8.4f} fBest: {:<.8f}, fWorst: {:<.8f}, fMean: {:<.8f}, gBest: {:<.2f} ".format(
                g, self.record[1][g] - self.record[0][g], self.record[3][g], self.record[4][g], self.record[5][g],
                self.record[2][g]))

    def selection_roulette(self):
        a = np.array(self.pop_selection_pool[2]) / sum(self.pop_selection_pool[2])
        b = np.array([])
        for i in range(a.shape[0]):
            b = np.append(b, sum(a[:i + 1]))
        pop = self.pop_selection_pool
        tabu_list = self.pop_selection_tabu_pool
        self.pop = [[], [], []]
        self.tabu_list = [[] for _ in self.individual]
        c = np.random.random(self.pop_size)
        for i in range(self.pop_size):
            j = np.argwhere(b > c[i])[0, 0]  # 轮盘赌选择
            self.pop[0].append(pop[0][j])
            self.pop[1].append(pop[1][j])
            self.pop[2].append(pop[2][j])
            self.tabu_list[i] = tabu_list[j]

    def selection_champion2(self):
        pop = self.pop_selection_pool
        tabu_list = self.pop_selection_tabu_pool
        self.pop = [[], [], []]
        self.tabu_list = [[] for _ in self.individual]
        for i in range(self.pop_size):
            a = np.random.choice(range(self.pop_size), 2, replace=False)
            j = a[0] if pop[2][a[0]] > pop[2][a[1]] else a[1]
            self.pop[0].append(pop[0][j])
            self.pop[1].append(pop[1][j])
            self.pop[2].append(pop[2][j])
            self.tabu_list[i] = tabu_list[j]

    def update_best(self):
        self.best[2] = max(self.pop[2])
        index = self.pop[2].index(self.best[2])
        self.best[1] = self.pop[1][index]
        self.best[0] = self.pop[0][index]
        self.best[3] = self.tabu_list[index]

    def save_best(self):
        self.pop[0][0] = self.best[0]
        self.pop[1][0] = self.best[1]
        self.pop[2][0] = self.best[2]
        self.tabu_list[0] = self.best[3]

    @property
    def func_selection(self):
        func_dict = {
            Selection.default: self.selection_roulette,
            Selection.roulette: self.selection_roulette,
            Selection.champion2: self.selection_champion2,
        }
        return func_dict[self.schedule.ga_operator[Selection.name]]

    def do_selection(self):
        for i in range(3):
            self.pop_selection_pool[i].extend(self.pop[i])
            self.pop_selection_pool[i].extend(self.pop_copy[i])
        self.pop_selection_tabu_pool.extend(self.tabu_list)
        self.pop_selection_tabu_pool.extend(self.tabu_copy)
        self.func_selection()
        self.save_best()
        self.pop_selection_pool = [[], [], []]
        self.pop_selection_tabu_pool = []

    def do_init(self):
        pass

    def do_crossover(self, i, j, p):
        pass

    def do_mutation(self, i, q):
        pass

    def do_tabu_search(self, i):
        pass

    def reach_max_stay_generation(self, g):
        if self.max_stay_generation is not None and g > self.max_stay_generation and self.record[2][g - 1] == \
                self.record[2][g - self.max_stay_generation]:
            return True
        return False

    def reach_best_known_solution(self):
        if self.schedule.best_known is not None and self.best[1] <= self.schedule.best_known:
            return True
        return False

    def do_evolution(self, exp_no=None):
        exp_no = "" if exp_no is None else exp_no
        Utils.print("{}Evolution {}  start{}".format("=" * 48, exp_no, "=" * 48), fore=Utils.fore().LIGHTYELLOW_EX)
        self.clear()
        self.do_init()
        self.update_best()
        self.show_generation(0)
        for g in range(1, self.max_generation + 1):
            self.pop_copy = copy.deepcopy(self.pop)
            self.tabu_copy = copy.deepcopy(self.tabu_list)
            if self.reach_best_known_solution():
                break
            if self.reach_max_stay_generation(g):
                break
            self.record[0].append(time.perf_counter())
            p, q = np.random.random(self.pop_size), np.random.random(self.pop_size)
            for i in range(self.pop_size):
                if self.reach_best_known_solution():
                    break
                if self.schedule.para_tabu:
                    self.do_tabu_search(i)
                j = np.random.choice(np.delete(np.arange(self.pop_size), i), 1, replace=False)[0]
                self.do_crossover(i, j, p[i])
                self.do_mutation(i, q[i])
            self.do_selection()
            self.record[1].append(time.perf_counter())
            self.show_generation(g)
        Utils.print("{}Evolution {} finish{}".format("=" * 48, exp_no, "=" * 48), fore=Utils.fore().LIGHTRED_EX)


class GaHfsp(Ga):
    def __init__(self, pop_size, rc, rm, max_generation, objective, schedule, max_stay_generation=None):
        Ga.__init__(self, pop_size, rc, rm, max_generation, objective, schedule, max_stay_generation)

    def decode(self, code):
        return self.schedule.decode(code)

    def do_init(self):
        self.record[0].append(time.perf_counter())
        for i in range(self.pop_size):
            code = Code.sequence_permutation(self.schedule.n)
            info = self.decode(code)
            obj, fit = self.get_obj_fit(info)
            self.pop[0].append(info)
            self.pop[1].append(obj)
            self.pop[2].append(fit)
        self.record[1].append(time.perf_counter())

    def do_crossover(self, i, j, p):
        if p < self.rc:
            # code1, code2 = self.pop[0][i].ga_crossover_sequence_permutation(self.pop[0][j])
            code1, code2 = self.pop[0][i].ga_crossover_sequence_permutation(self.pop_copy[0][j])
            # self.replace_individual(i, self.decode(code1))
            self.replace_individual_comp(i, self.decode(code1), self.decode(code2))
            # self.replace_individual(j, self.decode(code2))

    def do_mutation(self, i, q):
        if q < self.rm:
            code1 = self.pop[0][i].ga_mutation_sequence_permutation()
            self.replace_individual(i, self.decode(code1))

    def do_tabu_search(self, i):
        code1 = self.pop[0][i].ts_sequence_permutation_based(self.tabu_list[i], self.max_tabu)
        self.replace_individual_better(i, self.decode(code1))
        if len(self.tabu_list[i]) >= self.max_tabu:
            self.tabu_list[i] = []
