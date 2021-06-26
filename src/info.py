import copy
import datetime
import random

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly as py
import plotly.figure_factory as ff
from matplotlib import colors as mcolors

from .define import Crossover, Mutation
from .utils import Utils

deepcopy = copy.deepcopy
pyplt = py.offline.plot
dt = datetime.datetime
tmdelta = datetime.timedelta
COLORS = list(mcolors.CSS4_COLORS)
COLORS_REMOVE = ['black', "white"]
COLORS_REMOVE.extend([i for i in COLORS if i.startswith('dark')])
COLORS_REMOVE.extend([i for i in COLORS if i.startswith('light')])
[COLORS.remove(i) for i in COLORS_REMOVE]
LEN_COLORS = len(COLORS)
[COLORS.pop(j - i) for i, j in enumerate(range(12))]
[COLORS.pop(j - i) for i, j in enumerate([6, 10, ])]
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class GanttChart:
    def __init__(self, file=None, schedule=None, mac=None):
        self.schedule = schedule
        self.mac = mac
        if file is not None:
            from .shop.schedule import Schedule
            self.data = pd.read_csv(file)
            self.n = max(self.data.loc[:, "Job"])
            self.m = max(self.data.loc[:, "Machine"])
            self.makespan = max(self.data.loc[:, "End"])
            self.schedule = Schedule()
            self.schedule.with_key_block = True
            for i in range(self.m):
                self.schedule.add_machine(name=i, index=i)
            for i in range(self.n):
                self.schedule.add_job(name=i, index=i)
            for g, (start, operation, job, machine, end, duration) in enumerate(zip(
                    self.data.loc[:, "Start"], self.data.loc[:, "Operation"], self.data.loc[:, "Job"],
                    self.data.loc[:, "Machine"], self.data.loc[:, "End"], self.data.loc[:, "Duration"])):
                job, operation, machine = job - 1, operation - 1, machine - 1
                self.schedule.job[job].add_task(machine=machine, duration=duration, name=operation, index=operation)
                self.schedule.job[job].task[operation].start = start
                self.schedule.job[job].task[operation].end = end
                if end > self.schedule.machine[machine].end:
                    self.schedule.machine[machine].end = end

    def gantt_chart_png(self, filename="GanttChart", fig_width=9, fig_height=5, random_colors=False, lang=1, dpi=200,
                        height=0.8, scale_more=None, x_step=None, text_rotation=0,
                        with_operation=True, with_start_end=False, jobs_label=True, show=False):
        if random_colors:
            random.shuffle(COLORS)
        plt.figure(figsize=[fig_width, fig_height])
        plt.yticks(range(self.m), range(1, self.m + 1))
        plt.xticks([], [])
        scale_more = 12 if scale_more is None else scale_more
        x_step = max([1, self.schedule.makespan // 10 if x_step is None else x_step])
        ax = plt.gca()
        for job in self.schedule.job.values():
            for task in job.task.values():
                if self.mac is None:
                    machine = task.machine
                else:
                    machine = self.mac[job.index][task.index]
                duration = task.end - task.start
                edgecolor, linewidth = "black", 0.5
                plt.barh(
                    y=machine, width=duration,
                    left=task.start, color=COLORS[job.index % LEN_COLORS],
                    edgecolor=edgecolor, linewidth=linewidth,
                )
                if with_operation:
                    mark = r"$O_{%s,%s}$" % (job.index + 1, task.index + 1)
                    plt.text(
                        x=task.start + 0.5 * duration, y=machine,
                        s=mark, c="black",
                        ha="center", va="center", rotation="vertical",
                    )
                if with_start_end:
                    val = [task.start, task.end]
                    for x in val:
                        s = r"$_{%s}$" % int(x)
                        rotation = text_rotation
                        if text_rotation in [0, 1]:
                            rotation = ["horizontal", "vertical"][text_rotation]
                        plt.text(
                            x=x, y=machine - height * 0.5,
                            s=s, c="black",
                            ha="center", va="top",
                            rotation=rotation,
                        )
        if jobs_label:
            for job in self.schedule.job.values():
                plt.barh(0, 0, color=COLORS[job.index % LEN_COLORS], label=job.index + 1)
            plt.barh(y=0, width=self.schedule.makespan / scale_more, left=self.schedule.makespan, color="white")
            if lang == 0:
                title = r"${Job}$"
            else:
                title = "工件"
            plt.legend(loc="best", title=title)
        if not with_start_end:
            ymin = -0.5
            ymax = self.schedule.m + ymin
            plt.vlines(self.schedule.makespan, ymin, ymax, colors="red", linestyles="--")
            plt.text(self.schedule.makespan, ymin, "{}".format(int(self.schedule.makespan / self.schedule.time_unit)))
            x_ticks = range(0, self.schedule.makespan + x_step, x_step)
            plt.xticks(x_ticks, [int(i / self.schedule.time_unit) for i in x_ticks])
            [ax.spines[name].set_color('none') for name in ["top", "right"]]
        else:
            [ax.spines[name].set_color('none') for name in ["top", "right", "bottom", "left"]]
        if lang == 0:
            plt.ylabel(r"${Machine}$")
            if self.schedule.time_unit == 1:
                plt.xlabel(r"${Time}$")
            else:
                plt.xlabel(r"${Time}({%s}seconds/1)$" % self.schedule.time_unit)
        else:
            plt.ylabel("机器")
            if self.schedule.time_unit == 1:
                plt.xlabel("时间")
            else:
                plt.xlabel("时间（%s秒/1）" % self.schedule.time_unit)
        plt.margins()
        plt.tight_layout()
        plt.gcf().subplots_adjust(left=0.08, bottom=0.12)
        if not filename.endswith(".png"):
            filename += ".png"
        plt.savefig("{}".format(filename), dpi=dpi)
        if show:
            plt.show()
        plt.clf()
        Utils.print("Create {}".format(filename), fore=Utils.fore().LIGHTCYAN_EX)

    @property
    def rgb(self):
        return random.randint(0, 255)

    def gantt_chart_html(self, filename="GanttChart", date=None, lang=1, show=False):
        if date is None:
            today = dt.today()
            date = dt(today.year, today.month, today.day)
        else:
            tmp = list(map(int, date.split()))
            date = dt(tmp[0], tmp[1], tmp[2])
        df = []
        for job in self.schedule.job.values():
            for task in job.task.values():
                if task.start != task.end:
                    if self.mac is None:
                        machine = task.machine
                    else:
                        machine = self.mac[job.index][task.index]
                    mark = machine + 1
                    if self.schedule.m >= 100:
                        if mark < 10:
                            mark = "00" + str(mark)
                        elif mark < 100:
                            mark = "0" + str(mark)
                    elif self.schedule.m >= 10:
                        if mark < 10:
                            mark = "0" + str(mark)
                    start, finish = task.start, task.end
                    df.append(dict(Task="M%s" % mark, Start=date + tmdelta(0, int(start)),
                                   Finish=date + tmdelta(0, int(finish)),
                                   Resource=str(job.index + 1), complete=job.index + 1))
        df = sorted(df, key=lambda val: (val['Task'], val['complete']), reverse=True)
        colors = {}
        for i in self.schedule.job.keys():
            key = "%s" % (i + 1)
            colors[key] = "rgb(%s, %s, %s)" % (self.rgb, self.rgb, self.rgb)
        fig = ff.create_gantt(df, colors=colors, index_col='Resource', group_tasks=True, show_colorbar=True)
        if lang == 0:
            label = "Job"
        else:
            label = "工件"
        fig.update_layout(showlegend=True, legend_title_text=label)
        if not filename.endswith(".html"):
            filename += ".html"
        pyplt(fig, filename="{}".format(filename), auto_open=show)
        Utils.print("Create {}".format(filename), fore=Utils.fore().LIGHTCYAN_EX)


class Info(GanttChart):
    def __init__(self, schedule, code, mac=None):
        self.schedule = deepcopy(schedule)
        self.code = code
        self.mac = mac
        GanttChart.__init__(self, schedule=self.schedule, mac=self.mac)

    def print(self):
        code = self.code.tolist() if type(self.code) is np.ndarray else self.code
        a = {"code": code, "mac": self.mac, "makespan": self.schedule.makespan,
             "id": self, "schedule_id": self.schedule}
        for i, j in a.items():
            print("%s: %s" % (i, j))

    def save_code_to_txt(self, file):
        try:
            Utils.save_code_to_txt(file,
                                   {"code": self.code.tolist(), "mac": self.mac})
        except AttributeError:
            Utils.save_code_to_txt(file, {"code": self.code, "mac": self.mac})

    def save_start_end(self, file):
        with open(file, "w", encoding="utf-8") as f:
            f.writelines("Job,Operation,Machine,Start,Duration,End\n")
            for job in self.schedule.job.values():
                for task in job.task.values():
                    if self.mac is None:
                        machine = task.machine
                        duration = task.duration
                    else:
                        machine = self.mac[job.index][task.index]
                        index_machine = task.machine.index(machine)
                        duration = task.duration[index_machine]
                    f.writelines("{},{},{},{},{},{}\n".format(
                        job.index + 1, task.index + 1, machine + 1, task.start, duration, task.end))

    def save_gantt_chart_to_csv(self, file):
        if not file.endswith(".csv"):
            file = file + ".csv"
        self.save_start_end(file)

    """"
    =============================================================================
    Genetic operator: permutation based code
    =============================================================================
    """

    def ga_crossover_sequence_permutation(self, info):
        func_dict = {
            Crossover.default: self.ga_crossover_sequence_permutation_pmx,
            Crossover.pmx: self.ga_crossover_sequence_permutation_pmx,
            Crossover.ox: self.ga_crossover_sequence_permutation_ox,
        }
        func = func_dict[self.schedule.ga_operator[Crossover.name]]
        return func(info)

    def ga_mutation_sequence_permutation(self):
        func_dict = {
            Mutation.default: self.ga_mutation_sequence_permutation_tpe,
            Mutation.tpe: self.ga_mutation_sequence_permutation_tpe,
            Mutation.insert: self.ga_mutation_sequence_permutation_insert,
            Mutation.sub_reverse: self.ga_mutation_sequence_permutation_sr,
        }
        func = func_dict[self.schedule.ga_operator[Mutation.name]]
        return func()

    def ga_crossover_sequence_permutation_pmx(self, info):
        code1 = deepcopy(self.code)
        code2 = deepcopy(info.code)
        a, b = np.random.choice(self.schedule.n, 2, replace=False)
        if a > b:
            a, b = b, a
        r_a_b = range(a, b + 1)
        r_left = np.delete(range(self.schedule.n), r_a_b)
        middle_1, middle_2 = code1[r_a_b], code2[r_a_b]
        left_1, left_2 = code1[r_left], code2[r_left]
        code1[r_a_b], code2[r_a_b] = middle_2, middle_1
        mapping = [[], []]
        for i, j in zip(middle_1, middle_2):
            if j in middle_1 and i not in middle_2:
                index = np.argwhere(middle_1 == j)[0, 0]
                value = middle_2[index]
                while True:
                    if value in middle_1:
                        index = np.argwhere(middle_1 == value)[0, 0]
                        value = middle_2[index]
                    else:
                        break
                mapping[0].append(i)
                mapping[1].append(value)
            elif j not in middle_1 and i not in middle_2:
                mapping[0].append(i)
                mapping[1].append(j)
        for i, j in zip(mapping[0], mapping[1]):
            if i in left_1:
                left_1[np.argwhere(left_1 == i)[0, 0]] = j
            elif i in left_2:
                left_2[np.argwhere(left_2 == i)[0, 0]] = j
            if j in left_1:
                left_1[np.argwhere(left_1 == j)[0, 0]] = i
            elif j in left_2:
                left_2[np.argwhere(left_2 == j)[0, 0]] = i
        code1[r_left], code2[r_left] = left_1, left_2
        return code1, code2

    def ga_crossover_sequence_permutation_ox(self, info):
        code1 = deepcopy(self.code)
        code2 = deepcopy(info.code)
        a, b = np.random.choice(range(1, self.schedule.n - 1), 2, replace=False)
        if a > b:
            a, b = b, a
        r_a_b = range(a, b + 1)
        left_a, right_b = range(a), range(b + 1, self.schedule.n)
        left_b_a = np.hstack([right_b, left_a])
        middle1, middle2 = code1[r_a_b], code2[r_a_b]
        left1, left2 = code1[left_a], code2[left_a]
        right1, right2 = code1[right_b], code2[right_b]
        cycle1, cycle2 = np.hstack([right1, left1, middle1]), np.hstack([right2, left2, middle2])
        change1, change2 = [], []
        for i, j in zip(cycle1, cycle2):
            if j not in middle1:
                change1.append(j)
            if i not in middle2:
                change2.append(i)
        code1[left_b_a], code2[left_b_a] = change1, change2
        return code1, code2

    def ga_mutation_sequence_permutation_tpe(self):
        code = deepcopy(self.code)
        a = np.random.choice(range(self.schedule.n), 2, replace=False)
        code[a] = code[a[::-1]]
        return code

    def ga_mutation_sequence_permutation_insert(self):
        code = deepcopy(self.code)
        a, b = np.random.choice(range(self.schedule.n), 2, replace=False)
        if a > b:
            a, b = b, a
        if np.random.random() < 0.5:
            c = np.delete(code, b)
            code = np.insert(c, a, code[b])
        else:
            c = np.delete(code, a)
            code = np.insert(c, b - 1, code[a])
            code[b], code[b - 1] = code[b - 1], code[b]
        return code

    def ga_mutation_sequence_permutation_sr(self):
        code = deepcopy(self.code)
        a, b = np.random.choice(range(self.schedule.n), 2, replace=False)
        if a > b:
            a, b = b, a
        c = range(a, b + 1)
        code[c] = code[c[::-1]]
        return code

    """"
    =============================================================================
    Tabu search
    =============================================================================
    """

    @staticmethod
    def do_tabu_search(code, i, j, w):
        if i > j:
            i, j = j, i
        if w == 0:
            obj = np.delete(code, j)
            code = np.insert(obj, i, code[j])
        elif w == 1:
            obj = np.delete(code, i)
            code = np.insert(obj, j - 1, code[i])
            code[j], code[j - 1] = code[j - 1], code[j]
        else:
            code[i], code[j] = code[j], code[i]
        return code

    def ts_sequence_permutation_based(self, tabu_list, max_tabu):
        code = deepcopy(self.code)
        n_try = 0
        while n_try < max_tabu:
            n_try += 1
            try:
                i, j = np.random.choice(self.schedule.n, 2, replace=False)
                w = np.random.choice(range(3), 1, replace=False)[0]
                tabu = {"way-%s" % w, i, j}
                if tabu not in tabu_list:
                    tabu_list.append(tabu)
                    code = self.do_tabu_search(code, i, j, w)
                    break
            except ValueError:
                pass
        return code
