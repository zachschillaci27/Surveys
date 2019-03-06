#!/usr/bin/env /Users/zschillaci/Software/miniconda3/envs/pyenv/bin/python
import os
import sys
import glob
import collections
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def mkdir(path):
    if not os.path.isdir(path):
        os.makedirs(path)

def SavePlot(path, fname):
    mkdir(path)
    plt.savefig(path + '/' + fname + '.pdf')
    plt.close()

def GetFilesInDir(directory, extension='.txt'):
    listOfFiles = glob.glob(directory + '*' + extension)
    listOfFiles.sort()
    return listOfFiles

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

def RenameStages(stages):
    output = []
    for stage in stages:
        stage = stage.lower()
        if ('aftergluing' in stage) or ('afterglue' in stage) or ('ag' in stage):
            stage = 'AG'
        elif ('beforebridgeremoval' in stage) or ('bbr' in stage):
            stage = 'BBR'
        elif ('afterbridgeremoval' in stage) or ('abr' in stage):
            stage = 'ABR'
        else:
            stage = stage.capitalize()
        output.append(stage)
    return output

class TheSurvey(object):
    def __init__(self, module, stave, indir):
        self.module = module
        self.stave = stave
        self.indir = indir
        self.name = 'Module_' + str(module)
        self.infile = self.indir + '/' + self.stave + '/' + self.name + '.txt'
        self.dimensions = ['X', 'Y']
        self.tolerance = 25
        self.lines = self.GetLines()
        self.corners = self.SeparateByCorner()
        self.stages = self.GetStages()
        self.results = self.GetResults()
        self.passed, self.failures = self.DidItPass()

    def Dump(self):
        print('Module:', self.module)
        print('Stave:', self.stave)
        print('File:', self.infile)
        print('')

    def GetLines(self):
        infile = open(self.infile,"r")
        lines = infile.readlines()
        infile.close()
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

    def GetAbsolute(self, stage, corner, xyz):
        return (self.results[stage][corner][xyz])

    def GetRelative(self, stage, corner, xyz):
        return (1000 * (self.results[stage][corner][xyz] - self.results[self.stages[0]][corner][xyz]))

    def PopulateHistograms(self, placements, stage, corners='ABCD'):
        for xyz, dim in enumerate(self.dimensions):
            for corner in self.corners.keys():
                if (corner in corners):
                    placements[dim].append(self.GetRelative(stage, corner, xyz))

    def PlotXYZMovement(self, reference='relative', printOut=True):
        self.dframes = {}
        plt.figure("Movement - " + reference,(10,10))
        for xyz, dim in enumerate(self.dimensions):
            plt.subplot(211 + xyz)
            dframe = collections.OrderedDict()
            for corner in self.corners.keys():
                values = []
                for stage in self.stages:
                    value = None
                    if (reference == 'relative'):
                        value = self.GetRelative(stage, corner, xyz)
                    else:
                        value = self.GetAbsolute(stage, corner, xyz)
                    values.append(value)

                plt.plot(np.arange(0, len(values)), values, linestyle='--', marker='o', label=corner)
                dframe[corner] = values

            self.dframes[dim] = dframe

            units = ('[$\mu$m]' if (reference == 'relative') else ['mm'])

            if printOut:
                print('-----' + dim + ' ' + units + '-----')
                df = pd.DataFrame(dframe, index=self.stages)
                print(df)
                print('--------------------' + '\n')

            plt.ylim(-25.5, 25.5)
            plt.xlabel('Stage in Process')
            plt.xticks(np.arange(0, len(self.stages)), self.stages)
            plt.ylabel(dim + ' ' + units)
            plt.legend(loc=9, ncol=4)
        SavePlot(RESULTS_DIR + '/' + self.stave, self.name + '-' + reference + '.pdf')
       
    def DidItPass(self):
        passed = True
        failures = []
        for xyz, dim in enumerate(self.dimensions):
            for corner in self.corners.keys():
                for stage in self.stages:
                    movement = self.GetRelative(stage, corner, xyz)
                    if (abs(movement) >= self.tolerance):
                        passed = False
                        if (stage == self.stages[-1]):
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

def PlotHistogram(placements, corners, stave):
    for dim in placements:
        fig = plt.figure("Histogram - " + dim,(10,10))
        ax = fig.add_subplot(111)

        bins = np.arange(-30, 35, 7.5)
        width  = round(abs(bins[0] - bins[1]),2)

        plt.hist(placements[dim], bins=bins)
        plt.xlabel('$\Delta$' + dim + ' [$\mu$m]', fontsize=18)
        plt.ylabel('Counts / ' + str(width) + ' $\mu$m', fontsize=18)
        plt.xlim(-52.5, 52.5)
        plt.xticks(np.arange(-50, 55, 10))
        plt.ylim(0, 10.5)

        if (corners == 'ABCD'):
            plt.ylim(0, 15.5)

        mean = round(np.mean(placements[dim]),2)
        sigma = round(np.std(placements[dim]), 2)
        ax.annotate('$\mu$ = ' + str(mean) + ' $\mu$m',xy=(0.995,0.965),xycoords='axes fraction',fontsize=16,horizontalalignment='right',verticalalignment='bottom')
        ax.annotate('$\sigma$ = ' + str(sigma) + ' $\mu$m',xy=(0.995,0.925),xycoords='axes fraction',fontsize=16,horizontalalignment='right',verticalalignment='bottom')
        SavePlot(RESULTS_DIR + '/' + stave, dim + '-Corners' + corners + '-histogram.pdf')

# PARAMETERS #

# Input and output directories
INPUT_DIR = '/Users/zschillaci/BNL/Working/InnerTracker/Surveys/input/'
RESULTS_DIR = '/Users/zschillaci/BNL/Working/InnerTracker/Surveys/results/'

# Stave name (matching a sub-directory in INPUT_DIR)
STAVE = 'ElectricalStave_8'
# List of module numbers on the stave (corresponding to survey files in STAVE sub-directory)
MODULES = [1, 2, 3]

# Plot and printout all survey results, highlighting any failures (placements outside tolerance)
for module in MODULES:
    survey = TheSurvey(module, STAVE, INPUT_DIR)
    survey.Dump()

    survey.PlotXYZMovement(reference='relative', printOut=True)
    survey.PrintTheFailures()

# Plot placement histograms of all modules for specified corners
for corners in ['AB', 'CD', 'AC', 'AD', 'BC', 'BD', 'ABCD']:

    placements = {'X' : [], 'Y' : []}

    for module in MODULES:
        survey = TheSurvey(module, STAVE, INPUT_DIR)
        survey.PopulateHistograms(placements, survey.stages[-1], corners)

    PlotHistogram(placements, corners, STAVE)
