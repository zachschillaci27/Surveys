#!/usr/bin/env /Users/zschillaci/Software/miniconda3/envs/pyenv/bin/python
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import collections
import pandas as pd

def StringtoFlt(string):
    flt = None
    if ("\n" in string):
        string.replace("\n", "")
    if ("=" in string):
        string = string[string.find("=") + 1:]
    try:
        flt = float(string)
    except ValueError:
        print("Cannot convert string to float!")
    return flt

def RepealAndReplace(string, repeal, replace = 1):
    if (repeal in string):
        ind = string.index(repeal)
        string = string[0 : ind + replace] + string[ind + len(repeal) : ]
    return string

def RenameStages(stages):
    output = []
    for stage in stages:
        if ('AfterGluing' in stage) or ('AfterGlue' in stage) or ('AG' in stage):
            stage = 'AG'
        elif ('BeforeBridgeRemoval' in stage) or ('BBR' in stage):
            stage = 'BBR'
        elif ('AfterBridgeRemoval' in stage) or ('ABR' in stage):
            stage = 'ABR'
        # stage = RepealAndReplace(stage, 'Right', 0)
        # stage = RepealAndReplace(stage, 'Before')
        # stage = RepealAndReplace(stage, 'After')
        # stage = RepealAndReplace(stage, 'Gluing')
        # stage = RepealAndReplace(stage, 'Bridge', 2)
        # stage = RepealAndReplace(stage, 'Removal')
        # while ('_' in stage):
        #     stage = stage.replace('_','')
        output.append(stage)
    return output

class TheSurveys(object):
    def __init__(self, module, dir):
        self.name = "Module_" + str(module)
        self.dir = dir
        self.infile = self.dir + self.name + '.txt'
        self.lines = self.GetLines()
        self.corners = self.SeparateByCorner()
        self.stages = self.GetStages()
        self.results = self.GetResults()
        self.tolerance = 25
        self.passed, self.failures = self.DidItPass()

    def GetLines(self):
        input = open(self.infile,"r")
        lines = input.readlines()
        input.close()
        return lines

    def SeparateByCorner(self):
        indA, indB, indC, indD = 0, 0, 0, 0
        for ind, line in enumerate(self.lines):
            if ("CornerA" in line):
                indA = ind + 1
            elif ("CornerB" in line):
                indB = ind + 1
            elif ("CornerC" in line):
                indC = ind + 1
            elif ("CornerD" in line):
                indD = ind + 1

        corners = collections.OrderedDict()
        corners['A'] = self.lines[indA : indB - 2]
        corners['B'] = self.lines[indB : indC - 2]
        corners['C'] = self.lines[indC : indD - 2]
        corners['D'] = self.lines[indD : ]
        return corners

    def GetStages(self):
        stages = []
        for line in self.corners['A']:
            stage = line[line.find("_") + 1: line.find("=") - 1]
            if (stage not in stages):
                stages.append(stage)
        stages = RenameStages(stages)
        return stages

    def GetResults(self):
        results = collections.OrderedDict()
        for ind, stage in enumerate(self.stages):
            results[stage] = collections.OrderedDict()
            for corner in self.corners.keys():
                results[stage][corner] = []
                for xyz in range(3):
                    pos = StringtoFlt(self.corners[corner][(3 * ind) + xyz])
                    results[stage][corner].append(pos)
        return results

    def PlotXYZMovement(self, reference='relative', printOut=True, save=True):
        dims = ['X', 'Y']

        plt.figure("Movement - " + reference,(10,10))
        for xyz, dim in enumerate(dims):
            plt.subplot(211 + xyz)
            dframe = collections.OrderedDict()
            for corner in self.corners.keys():
                values = []
                for stage in self.stages:
                    origin = 0
                    scale = 1
                    units = '[mm]'
                    if (reference == 'relative'):
                        origin = self.results[self.stages[0]][corner][xyz]
                        scale = 1000
                        units = '[um]'
                    diff = scale * (self.results[stage][corner][xyz] - origin)
                    values.append(diff)

                    if (stage == self.stages[-1]):
                        all_placements[dim].append(diff)

                plt.plot(np.arange(0, len(values)), values, linestyle='--', marker='o', label=corner)
                dframe[corner] = values

            if printOut:
                print('-----' + dim + ' ' + units + '-----')
                df = pd.DataFrame(dframe, index=self.stages)
                print(df)
                print('--------------------' + '\n')

            plt.xlabel('Stage in Process')
            plt.xticks(np.arange(0, len(self.stages)), self.stages)
            plt.ylabel(dim + ' ' + units)
            plt.legend()
        if save:
            plt.savefig(self.dir + self.name + '-' + reference + '.pdf')
        else:
            plt.show()
        plt.close()

    def DidItPass(self):
        dims = ['X', 'Y']
        passed = True
        failures = []
        for xyz, dim in enumerate(dims):
            for corner in self.corners.keys():
                for stage in self.stages:
                    movement = 1000 * (self.results[stage][corner][xyz] - self.results[self.stages[0]][corner][xyz])
                    if (abs(movement) >= self.tolerance):
                        passed = False
                        if (stage == 'ABR'):
                            failures.append(corner + ' - ' + stage + ': delta' + dim + ' = ' + str(movement) + ' um')
        return passed, failures

    def PrintTheFailures(self):
        if self.passed:
            print("---> Passed! All surveys within " + str(self.tolerance) + " um tolerance.")
        else:
            print("---> Failed! The following corners are out of " + str(self.tolerance) + " um tolerance: ")
            for failure in self.failures:
                print(failure)
        print('-----------------------------------------------------------------' + '\n')

global all_placements
all_placements = {'X' : [], 'Y' : []}

folder = "/Users/zschillaci/BNL/Working/StaveAssembly/Surveys/Complete/ElectricalStave_1/"
sys.stdout = open(folder + 'output.txt',"w")
for module in np.arange(2,14):
    survey = TheSurveys(module, folder)

    print(survey.name)
    survey.PlotXYZMovement(reference='relative', save=True, printOut=True)
    survey.PrintTheFailures()

for dim in all_placements:
    fig = plt.figure("Histogram - " + dim,(10,10))
    ax = fig.add_subplot(111)

    bins = np.arange(-30, 30, 5.0)
    width  = round(abs(bins[0] - bins[1]),2)

    plt.hist(all_placements[dim], bins=bins)
    plt.xlabel('$\Delta$' + dim + ' [um]', fontsize=18)
    plt.ylabel('Counts / ' + str(width) + ' um', fontsize=18)
    plt.xlim(bins[0] - width, bins[-1] + width)
    plt.ylim(0,12.5)

    sigma = round(np.std(all_placements[dim]),2)
    ax.annotate('$\sigma$ = ' + str(sigma) + ' um',xy=(0.995,0.965),xycoords='axes fraction',fontsize=16,horizontalalignment='right',verticalalignment='bottom')
    plt.savefig(folder + dim + '-histogram.pdf')
    plt.close()
