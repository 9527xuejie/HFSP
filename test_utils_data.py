__doc__ = """
生成数据
"""

from src import *

LOW, HIGH, DTYPE = 10, 100, int
LOW1, HIGH1, DTYPE1 = 1, 3, int


def do():
    n, m = 10, [3, 2, 4]
    p = len(m)
    for no in range(1, 2):
        instance = "n%sm%s-%s" % (n, sum(m), no)
        Utils.create_data_hfsp(instance, n, p, m, LOW, HIGH, dtype=DTYPE)
        Utils.create_data_hfsp_trans(instance, m, LOW1, HIGH1, dtype=DTYPE1)
        Utils.print("Create %s " % instance)


if __name__ == "__main__":
    do()
