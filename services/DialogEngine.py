#takes in: script file
#produces: specific text for texttospeech, actions for actionrunner

import re

class DialogEngine:
    def __init__(self):
        self.file = None
        self.userRules = []
        self.proposals = []

    def add_file(self, fileName):
        self.file = open(fileName, 'r')


    def read_script(self):
        line = self.file.readline()
        line = line.strip()
        if line[0] != '#' :
            instructions = self.parse_line(line)

    def add_Rule(self, newRule):
        self.userRules.append(newRule)

    def parse_line(self, line):
        if match(line[0:2], "u:"):
            input = line.split("(")[1].split(")")[0]
            answer = line.split(")")[1]
            rule = UserRule(input, answer)
            self.userRules.append(rule)
        elif match(line.split()[0], "proposal"):
            newProposal = Proposal(line.split()[1])
            self.proposals.append(newProposal)

class UserRule:
    def __init__(self, input, output):
        self.input = input
        self.output = output

class Proposal:
    def __init__(self, sentence):
        self.sentence = sentence

def match(input, goal):
    if input == goal:
        return True

