#!/usr/bin/python3

import sys
from collections import defaultdict
from collections import OrderedDict
from pprint import pprint
from copy import deepcopy

import parse_tree
import lr

class CFG:
    def __init__(self):
        self.production_rules = OrderedDict() #{ LHS -> list of lists }, where inner lists are possible alternations}
        self.terminals = set()
        self.non_terminals = set()
        self.start_symbol = ""
        self.ll1_parse_table = {}

    def from_str(data):
        cfg = CFG()
        current_LHS = ""
        for line in data.splitlines():
            # line = line.strip("\n")
            line = line.strip()

            if len(line) == 0:
                continue

            tokens = line.split(" ")
            #check if this line is a production
            if tokens[1] == "->":
                current_LHS = tokens[0]
                RHS_tokens = tokens[2:]
                cfg.non_terminals.add(current_LHS)
            else:   #else line starts with alternation
                RHS_tokens = tokens[1:]

            if current_LHS not in cfg.production_rules:
                 cfg.production_rules[current_LHS] = []

            alternation = []    #will contain symbols between each alternation
            for token in RHS_tokens:
                if token != "lambda" and token != "$" and token != "|":  #add the token to the cfg's respective set of terminals or non-terminals
                    if token.isupper():
                        cfg.non_terminals.add(token)
                    else:
                        cfg.terminals.add(token)

                if token == "$":    #set the start symbol in the CFG to the non-terminal with $ in the production
                    cfg.start_symbol = current_LHS
                    alternation.append(token)
                elif token == "|":  #when you reach an alternation, add the last alternation list to the dict and then empty it
                    cfg.production_rules[current_LHS].append(alternation)
                    alternation = []
                else:
                    alternation.append(token)

            cfg.production_rules[current_LHS].append(alternation)   #handles adding the last production to the dict

        return cfg

    def __repr__(self):
        result = "\n"

        result += f"Terminals: {', '.join(sorted(list(self.terminals)))}\n"
        result += f"Non-terminals: {', '.join(sorted(list(self.non_terminals)))}\n"

        counter = 1
        for k, v in sorted(list(self.production_rules.items())):
            for production in sorted(v):
                result += f"\n({counter})\t {k} -> {' '.join(production)}\n"
                result += f"Predict {sorted(list(self.predict_set(k, production)))}"
                counter += 1

        result += f"\nGrammar Start Symbol or Goal: {self.start_symbol}\n"
        result += "\n"

        # result += self.follow_set("S\n"[0])
        # result += self.follow_set("A\n"[0])
        # result += self.follow_set("B\n"[0])
        # result += self.follow_set("C\n"[0])

        result += "First sets:\n"
        for nt in sorted(list(self.non_terminals)):
            result += f"{nt} : {sorted(list(self.first_set(nt)[0]))}\n"

        result += "Follow sets:\n"
        for nt in sorted(list(self.non_terminals)):
            result += f"{nt} : {sorted(list(self.follow_set(nt)[0]))}\n"

        return result

    def contains_terminal(self, production):
        return any(map(lambda e: e in self.terminals or e == self.start_symbol, production))

    def contains_lambda(self, rule):
        if rule == "lambda":
            return True
        
        for production in self.production_rules[rule]:
            if len(production) == 1 and production[0] == "lambda":
                return True

        return False

    def derives_to_lambda(self, rule):
        if rule == '$':
            return False
        # assert rule in self.production_rules

        if self.contains_lambda(rule):
            return True

        alternations = self.production_rules[rule]

        for rhs in alternations:
            # rhs's that have a terminal cannot
            # derive to lambda by definition
            if self.contains_terminal(rhs):
                continue

            # If any production doesn't derive to lambda in the
            # rhs, then that rhs does not derive to lambda.
            if any(map(lambda prod: not self.derives_to_lambda(prod), rhs)):
                continue

            # If we've made it this far, then the rhs derives to lambda
            # and therefore the rule derives to lambda.
            return True

        return False

    def first_set(self, XB, T=None):
        # print(f"First Set: {XB} {T}")

        if T is None:
            T = set()
        if not XB:
            return (set(), set())

        result = set()
        
        if isinstance(XB, list):
            X = XB[0]
        elif isinstance(XB, str):
            X = XB

        if X in self.terminals or X == '$':
            result.add(X)
            return (result, T)

        if X not in T:
            T.add(X)

            # for each p in P with X on LHS of p
            for lhs, alternations in list(self.production_rules.items()):
                if lhs == X:
                    for rhs in alternations:

                        # rhs is rhs of p
                        G, S = self.first_set(rhs, T)
                        result = result | G
                        """
                        indices = (i for i, x in enumerate(rhs) if x == X)
                        for i in indices:
                            print("index", i)

                        for index in indices:
                            # AB is the sequence of grammar symbols with X on
                            # the LHS of of some production rule P.
                            AB = rhs[index + 1:]
                            for p in AB:
                                if p in self.production_rules.keys():
                                    rules = self.production_rules[p]

                                    for rule in rules:
                                        G, S = self.first_set(rule, T)
                                        result.update(G)
                        """
                for rhs in alternations:
                    indices = (i for i, x in enumerate(rhs) if x == X)

                    for index in indices:
                        # AB is the sequence of grammar symbols with X on
                        # the LHS of of some production rule P.
                        AB = rhs[index + 1:]
                        for p in AB:
                            if p in self.production_rules.keys():
                                rules = self.production_rules[p]

                                for rule in rules:
                                    G, S = self.first_set(rule, T)
                                    result.update(G)

        if X == "lambda" or self.derives_to_lambda(X):
            G, S = self.first_set(XB[1:], T)
            result.update(G)

        return result, T

    # A is the nonterminal whose follow set we want; T is our visited set
    # returns follow set of A and updated visited set T
    # this follows Keith's pseudocode *very* closely
    def follow_set(self, A, T=None):
        if T is None:
            T = set()
        if A in T:
            return (set(), T)

        T.add(A)
        F = set()
        # for each rule with A in its rhs
        for lhs in self.production_rules:
            # this looks non-pythonic, but it is correct. Don't fix it. One lhs can have many rhs'es
            for rhs in self.production_rules[lhs]:
                if A not in rhs:
                    continue

                # find each instance of A in the rhs
                indices = (i for i, x in enumerate(rhs) if x == A)
                # XB is the sequence of all grammar symbols following each instance of A
                for index in indices:
                    XB = rhs[index + 1:]
                    # if XB exists, then add the first set of XB
                    if len(XB) > 0:
                        G, S = self.first_set(XB)
                        F = F | G  # | is the set union operator

                    # if XB does not exist or it has no terminals and all its members derive to λ, then add the follow set of whatever produced A
                    if not len(XB) or (not len(set(XB) & self.terminals) and all((self.derives_to_lambda(C) for C in XB))):  # & is the set intersection operator
                        (G, S) = self.follow_set(lhs, T)
                        F = F | G

        return (F, T)

    # Returns the predict set for this production rule: LHS -> RHS
    #   LHS: Single nonterminal
    #   RHS: List of characters
    def predict_set(self, LHS, RHS):
        result = self.first_set(RHS)[0]

        for x in RHS:
            # Break if this isn't a non terminal, or it's a terminal that doesn't derive to lambda
            if x == 'lambda':
                continue
            if (x not in self.non_terminals) or not self.derives_to_lambda(x):
                break
        else:
            # If we never break, all derive to lambda
            result = result.union(self.follow_set(LHS)[0])

        return result

    def test_disjoint(self):
        for k, v in self.production_rules.items():
            all_predict_sets = set()
            for production in v:
                print(f"{k} -> {' '.join(production)}")
                this_predict = self.predict_set(k, production)
                if all_predict_sets.isdisjoint(this_predict):
                    all_predict_sets = all_predict_sets.union(this_predict)
                else:
                    return False
                # print("Predict", cfg.predict_set(k, production))
        return True

    #creates the parsing table, which is a dictionary of dictionaries
    # { non-terminal : { terminal : production-rule number } }
    def create_LL1_parsing_table(self):
        rule_counter = 1
        for LHS, RHS in self.production_rules.items():
            if LHS not in self.ll1_parse_table:
                self.ll1_parse_table[LHS] = {}

            for production in RHS:
                predict_set = self.predict_set(LHS, production)
                print(LHS, production, predict_set)
                for terminal in predict_set:
                    self.ll1_parse_table[LHS][terminal] = rule_counter

                rule_counter += 1


    class Item:
        def __init__(self, lhs, symbols, marker_index=0):
            self.lhs = lhs
            self.symbols = symbols
            self.marker = marker_index  # the symbols index right after the marker. So for say a.bc, marker would be 1

        def __hash__(self): #to create a set of items
            return hash((self.lhs, tuple(self.symbols), self.marker))

        def __eq__(self, other):    #to check if an item is in a list of items
            return self.lhs == other.lhs and self.symbols == other.symbols and self.marker == other.marker

        def __repr__(self):
            return f"{self.lhs} -> {self.symbols[:self.marker]} . {self.symbols[self.marker:]}"

    """
    I: an item set of the grammar G
    returns an item set of G, which may be the same as I
    """
    def closure(self, I):
        # print(f"I: {I}")
        C = list(deepcopy(I))   #create a copy, and convert the set to a list so we can append to the list while looping through it
        C_change_flag = True
        while C_change_flag:    #while C keeps getting changed
            C_change_flag = False
            for item in C:
                right_of_marker = item.symbols[item.marker]
                if right_of_marker.isupper(): #if the symbol to the right of the marker is a non-terminal
                    for alternation in self.production_rules[right_of_marker]:    #create a new item for every alternation
                        new_item = self.Item(right_of_marker, "".join(alternation))
                        if new_item not in C:
                            C.append(new_item)
                            C_change_flag = True

        return set(C)


    """
    I: an item set of the grammar G
    X: is a symbol of the grammar: in N or in Σ or is $
    returns an item set generated by the items in I progressed past X, which may be the same as I
    """
    def go_to(I, X):
        K = set()
        for k in I:
            if k.symbols[k.marker] == X:
                K.add(k)

        for k in K:
            k.marker += 1

        return closure(K)



#creates and returns a CFG object from the given input file
def parse_input_file():
    # Read CFG from file
    file_name = sys.argv[1]
    cfg = CFG()
    with open(file_name) as f:
        current_LHS = ""
        for line in f:
            # line = line.strip("\n")
            line = line.strip()

            if len(line) == 0:
                continue

            print("LINE", line)
            tokens = line.split(" ")
            tokens = [t for t in tokens if t]  # fix bug when splitting on multiple spaces
            #check if this line is a production
            if tokens[1] == "->":
                current_LHS = tokens[0]
                RHS_tokens = tokens[2:]
                cfg.non_terminals.add(current_LHS)
            else:   #else line starts with alternation
                RHS_tokens = tokens[1:]

            if current_LHS not in cfg.production_rules:
                 cfg.production_rules[current_LHS] = []

            alternation = []    #will contain symbols between each alternation
            for token in RHS_tokens:
                if token != "lambda" and token != "$" and token != "|":  #add the token to the cfg's respective set of terminals or non-terminals
                    if token.isupper():
                        cfg.non_terminals.add(token)
                    else:
                        cfg.terminals.add(token)

                if token == "$":    #set the start symbol in the CFG to the non-terminal with $ in the production
                    cfg.start_symbol = current_LHS
                    alternation.append(token)
                elif token == "|":  #when you reach an alternation, add the last alternation list to the dict and then empty it
                    cfg.production_rules[current_LHS].append(alternation)
                    alternation = []
                else:
                    alternation.append(token)

            cfg.production_rules[current_LHS].append(alternation)   #handles adding the last production to the dict

        return cfg


def print_stuff(cfg):
    print(f"Terminals: {', '.join(sorted(list(cfg.terminals)))}")
    print(f"Non-terminals: {', '.join(sorted(list(cfg.non_terminals)))}\n")

    counter = 1
    for k, v in cfg.production_rules.items():
        for production in v:
            print(f"({counter})\t {k} -> {' '.join(production)}")
            print("Predict", cfg.predict_set(k, production))
            counter += 1

    print(f"\nGrammar Start Symbol or Goal: {cfg.start_symbol}")
    print()

    # print(cfg.follow_set("S")[0])
    # print(cfg.follow_set("A")[0])
    # print(cfg.follow_set("B")[0])
    # print(cfg.follow_set("C")[0])

    print("First sets:")
    for nt in cfg.non_terminals:
        print(nt, ":", cfg.first_set([nt])[0])

    print("Follow sets:")
    for nt in cfg.non_terminals:
        print(nt, ":", cfg.follow_set(nt)[0])


    # print(cfg.test_disjoint())
    #
    # for k,v in cfg.ll1_parse_table.items():
    #     print(k, " : ", v)


def test_closure_goto(cfg):
        """
        For testing closure and goto
        CFG in closure-test.cfg:
                    Z -> S
                    S -> AA
                    A -> aA
                       | b
        """
        item_1 = CFG.Item("Z", "S")
        item_2 = CFG.Item("S", "AA")
        item_3 = CFG.Item("A", "aA", 1)
        item_4 = CFG.Item("A", "b")
        
        s = {item_3}
        new_item_set = cfg.closure(s)
        for item in new_item_set:
            print(f"{item.lhs} -> {item.symbols[:item.marker] + '.' + item.symbols[item.marker:]}")


def main():
    cfg = parse_input_file()
    test_closure_goto(cfg)

    # cfg.create_LL1_parsing_table()
    #
    # print_stuff(cfg)
    #
    # pt = parse_tree.ll_tabular_parsing(parse_tree.TokenStream(sys.argv[2]), cfg)
    # print("parse tree:", pt)

if __name__ == "__main__":
    main()
