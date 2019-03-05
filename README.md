# Surveys

Surveys is a Python package for analyzing the placement precision of module loading for the ITk Barrel Strip project. It can plot displacement from the ideal in x and y dimensions for the four corners of a given module. Additionally, it can plot displacement distributions for a collection of modules to show overall placement performance.

## Usage

Developed for python3.5, requires additional packages. Create a basic survey results script:

```
from methods import *

INPUT_DIR = './input/'
RESULTS_DIR = './results/'
STAVE = 'StaveName'

#Plot survey results for Module_1
survey = TheSurveys(1, STAVE, INPUT_DIR)
survey.Dump()

survey.PlotXYZMovement(reference='relative', printOut=True)
survey.PrintTheFailures()

```
