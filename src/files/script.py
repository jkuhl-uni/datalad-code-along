#!/usr/local/bin/python3
import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt
import sys


def read_array(file):
    with open(file, "r") as fp:
        rar = fp.readlines()
    rar = [float(r) for r in rar]
    return rar

def plot_and_fit(ar, save):

    mini = round(min(ar))
    maxi = round(max(ar))
    hist = np.zeros(maxi - mini)

    for elem in ar:
        binned_elem = int(elem - mini)-1
        hist[binned_elem] += 1

    def normal(x, a, b, c):
        return np.exp(-a*(x-c)**2)*b

    param = opt.curve_fit(normal,[x+ mini for x in range(maxi-mini)], hist, p0=[1/20, 200, 500])

    fitx = np.linspace(450, 550, 1000)

    plt.plot([x+ mini for x in range(maxi-mini)], hist, linestyle = "None", marker = ".")
    plt.plot(fitx, normal(fitx, param[0][0], param[0][1], param[0][2]), color = "red")
    plt.savefig(save)

if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        raise Exception("You can only plot exactly one file at a time with this script!")
    ar = read_array(args[1])
    plot_and_fit(ar, args[2])