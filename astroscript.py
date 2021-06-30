"""
AstroScript Interpreter for AstroShell
Version 0.5.0
6/24/2021

Data Types
- String
- Integer
- Array

Explicit "Shell" Commands
./ - launch application
pwd - print working directory
mkdir - create a directory
ls - list directory contents
cd - go to directory

Function arguments go in an array (__fnargs)

Features to Add
- Assignment to array indices
- For loops
"""

import sys
import re
import os

outfile = sys.stdout
infile = sys.stdin
oldEval = eval

#custom str function
#custom array conversion function

def delin(string): #delimit by comas
    commaLocs = []
    depth = 0

    #search for commas - ignore any time you're inside parens
    for index in range(len(string)):
        i = string[index]
        if i == "(" or i == "[": depth += 1
        if i == ")" or i == "]": depth -= 1
        if i == "," and not depth: commaLocs.append(index)

    #divide it up
    lastComma = 0
    newList = []
    
    for i in commaLocs:
        newList.append(string[lastComma:i])
        lastComma = i + 1
    newList.append(string[commaLocs[-1]+1:])
    
    return newList

def numberOf(element, body):
    count = 0

    for i in body:
        if i == element: count += 1

    return count

def cleanMetaString(string):
    newstring = []
    closing = False
    beginning = 0
    #throughout each character, when you find an opening quote, find the closing quote
    #separate off into a new entry and remove yourself from the old one, continue to iterate
    for i in range(len(string)):
        if string[i] == '"' and closing:
            return [string[:beginning], string[beginning:i+1], string[i+1:]]
        if string[i] == '"' and not closing:
            beginning = i
            closing = True
    return [string]

def cleanString(string):
    newtokens = [string]
    tokens = []

    if len(cleanMetaString(newtokens[-1])) > 1:

        while newtokens[-1] != cleanMetaString(newtokens[-1])[1]:
            entry = cleanMetaString(newtokens[-1])

            while "" in entry:
                entry.remove("")
            
            newtokens[-1] = entry[0]

            for i in range(1, len(entry)):
                newtokens.append(entry[i])

    for i in range(len(newtokens)):
        tokens += tokenize(newtokens[i])

    return tokens

def tokenize(string):
    tokens = re.findall("[__#a-zA-Z][__#a-zA-Z0-9]*|->|\".*\"|==|@|!=|>=|<=|&&|\\|\\||_?\\d+|[+\-*/=!<>()[\\]{},.;:$&\\|]|'.*'|\".*\"", string)

    #fix tokens for string termination issue
    i = 0
    while i < len(tokens):
        if numberOf('"', tokens[i]) > 2:
            tokens = tokens[:i] + cleanString(tokens[i]) + tokens[i+1:]
        
        i += 1

    if len(tokens) == 0: tokens = [None]

    #return final
    return tokens

def eval(string):
    if str(string).isdigit(): return int(string)
    elif string == "False": return 0
    elif string == "True": return 1
    elif (string[0] == '"' and string[-1] == '"') or (string[0] == "'" and string[-1] == "'"): return string[1:-1]
    else: return string

def XinY(X, Y):
    _in = False

    for i in X:
        if i in Y: _in = True

    return _in

def parseExpr(text, vars, funcs): #remove and resolve/evaluate
    #replace all variables with literals
    for i in range(len(text)):
        if text[i] in vars: text[i] = vars[text[i]]
        
    #remove all function calls, array literals - run parseexpr for each argument/array index, array subscripts - run parseexpr to calculate the subscript and then fetch the array index
    while XinY(funcs, text) or "[" in text:
        i = 0
        while i < len(text):
            #print(text)
            if text[i] == "[":
                #is this an array literal or an array index?
                typ = 1 #array literal
                if i != 0:
                    if type(text[i-1]) == list: typ = 0
                    
                #find matching ]
                depth = 0
                firstBracket = 0
                o = i

                while o < len(text):
                    if text[o] == "[":
                        firstBracket = 1
                        depth += 1
                    if text[o] == "]": depth -= 1
                    if not depth and firstBracket: break
                    o += 1
                data = text[i+1:o]

                if typ: #array literal
                    rawarray = delin(data)

                    for index in range(len(rawarray)):
                        rawarray[index] = parseExpr(rawarray[index], vars, funcs)

                    text = text[:i] + [rawarray] + text[o+1:]
                    
                if not typ: #array index
                    index = parseExpr(data, vars, funcs)
                    if type(text[i-1][index]) != list: value = [text[i-1][index]]
                    else: value = text[i-1][index]
                    text = text[:i-1] + value + text[o+1:]

                i = 0
                #continue
            
            if not(type(text[i]) == list):
                if text[i] in funcs:
                    #find closing )
                    depth = 0
                    firstParen = 0
                    o = i+1

                    while o < len(text):
                        if text[o] == "(":
                            firstParen = 1
                            depth += 1
                        if text[o] == ")":
                            depth -= 1
                        if not depth and firstParen: break
                        o += 1
                    rawargs = delin(text[i+2:o])

                    for index in range(len(rawargs)):
                        rawargs[index] = parseExpr(rawargs[index], vars, funcs)

                    #print("Calling function {} with arguments {}".format(text[i], rawargs))
                    result = execute(funcs[text[i]], {"__fnargs": rawargs}, funcs)

                    if type(result[0]["__fnout"]) != list: value = [result[0]["__fnout"]]
                    else: value = result[0]["__fnout"]
                    
                    text = text[:i] + value + text[o+1:]
                    i = 0
          
            
            i += 1
    
    #remove all "len" statements to get array size
    while "len" in text:
        i = 0
        while i < len(text):
            if text[i] == "len":
                text = text[:i] + [len(text[i+1])] + text[i+2:]
            
            i += 1
            
    #remove all parenthesis - find the matching paren to the opening paren and run in its own parseexpr
    while "(" in text:
        i = 0
        while i < len(text):
            if text[i] == "(":
                depth = 0
                firstBracket = 0
                o = i
                while o < len(text):
                    if text[o] == "(":
                        firstBracket = 1
                        depth += 1
                    if text[o] == ")": depth -= 1
                    if depth == 0 and firstBracket: break
                    o += 1
                before = text[:i]
                during = text[i+1:o]
                after = text[o+1:]
                text = before + [parseExpr(during, vars, funcs)] + after
            i += 1                    
        
    #remove all string conversions ($) or number conversions (#) or array conversions (^)
    while "$" in text or "#" in text:
        i = 0
        while i < len(text):
            if text[i] == "$":
                text = text[:i] + ["\"{}\"".format(str(text[i+1]))] + text[i+2:]
                i = 0
                
            if text[i] == "^":
                text = text[:i] + [text[i+1]] + text[i+2:]
                i = 0

            if text[i] == "#":
                pass
            
            i += 1
    
    #remove all * / %
    while "*" in text or "/" in text or "%" in text:
        i = 0
        while i < len(text):
            if text[i] == "*":
                text = text[:i-1] + [str(eval(text[i-1]) * eval(text[i+1]))] + text[i+2:]
                i = 0

            if text[i] == "/":
                text = text[:i-1] + [str(eval(text[i-1]) / eval(text[i+1]))] + text[i+2:]
                i = 0

            if text[i] == "%":
                text = text[:i-1] + [str(eval(text[i-1]) % eval(text[i+1]))] + text[i+2:]
                i = 0
            
            i += 1
            
    #remove all + -
    while "+" in text or "-" in text:
        i = 0
        while i < len(text):
            if text[i] == "+":
                text = text[:i-1] + [str(eval(text[i-1]) + eval(text[i+1]))] + text[i+2:]
                i = 0

            if text[i] == "-":
                text = text[:i-1] + [str(eval(text[i-1]) - eval(text[i+1]))] + text[i+2:]
                i = 0

            i += 1
            
    #remove all < <= > >=
    while "<" in text or ">" in text or "<=" in text or ">=" in text:
        i = 0
        while i < len(text):
            if text[i] == "<":
                text = text[:i-1] + [str(eval(text[i-1]) < eval(text[i+1]))] + text[i+2:]
                i = 0

            if text[i] == ">":
                text = text[:i-1] + [str(eval(text[i-1]) > eval(text[i+1]))] + text[i+2:]
                i = 0

            if text[i] == "<=":
                text = text[:i-1] + [str(eval(text[i-1]) <= eval(text[i+1]))] + text[i+2:]
                i = 0

            if text[i] == ">=":
                text = text[:i-1] + [str(eval(text[i-1]) >= eval(text[i+1]))] + text[i+2:]
                i = 0

            i += 1
            
    #remove == !=
    while "==" in text or "!=" in text:
        i = 0
        while i < len(text):
            if text[i] == "==":
                text = text[:i-1] + [str(eval(text[i-1]) == eval(text[i+1]))] + text[i+2:]
                i = 0

            if text[i] == "!=":
                text = text[:i-1] + [str(eval(text[i-1]) != eval(text[i+1]))] + text[i+2:]
                i = 0

            i += 1
            
    #remove logical and &&
    while "&&" in text:
        i = 0
        while i < len(text):
            if text[i] == "&&":
                text = text[:i-1] + [str(eval(text[i-1]) and eval(text[i+1]))] + text[i+2:]
                i = 0

            i += 1
                
    #remove logical or ||
    while "||" in text:
        i = 0
        while i < len(text):
            if text[i] == "||":
                text = text[:i-1] + [str(eval(text[i-1]) or eval(text[i+1]))] + text[i+2:]
                i = 0

            i += 1
    
    return eval(text[0])

def execute(string, variables = {}, functions = {}): 
    string = string.split("\n")
    whileFrames = []
    ifstack = []
    o = 0

    #for o in range(len(string)):
    while o < len(string):
        i = tokenize(string[o])
        #print(i)
        
        if i[0] == "input": #see note below
            #form input prompt var
            variables[i[-1]] = input(parseExpr(i[1:-1], variables, functions))

        if i[0] == "set" or i[0] == "@": #eventually check for array index assignment
            if i[2] == "=":
                variables[i[1]] = parseExpr(i[3:], variables, functions)

            if i[2] == "+" and i[3] == "+":
                variables[i[1]] = eval(variables[i[1]]) + 1

            if i[2] == "*" and i[3] == "=":
                variables[i[1]] = parseExpr(i[4:], variables, functions) * variables[i[1]]

                

        if i[0] == "echo": #I/O redirection
            outfile.write(str(parseExpr(i[1:], variables, functions)) + "\n")

        if i[0] == "clrscr":
            os.system("cls")

        if i[0] == "tests":
            for x in tests:
                print(x)
            execute(tests[input("? ")])

        if i[0] == "if":
            #find matching endif
            index = o
            depth = 0
            firstif = 0
            while index < len(string):
                current = tokenize(string[index])
                if current[0] == "if":
                    firstif = 1
                    depth += 1
                if current[0] == "endif":
                    depth -= 1
                if not depth and firstif: break
                index += 1
            ifstack.append(index)
            #evaluate expression
            expression = parseExpr(i[1:], variables, functions)
            if expression: pass

            if not expression:
                #find matching endblk and go one after
                index = o
                depth = 0
                firstif = 0
                while index < len(string):
                    current = tokenize(string[index])
                    if current[0] == "if" or current[0] == "else":
                        firstif = 1
                        depth += 1
                    if current[0] == "endblk":
                        depth -= 1
                    if not depth and firstif: break
                    index += 1
                if "endif" not in string[index + 1]:
                    o = index + 1
                else: o = index
                continue

        if i[0] == "else":
            #determine - is this an "else" or an "else if"?
            if len(i) > 1:
                condition = parseExpr(i[2:], variables, functions)
            else:
                condition = True
            if condition:
                pass
            if not condition:
                #find matching endblk and go one after
                index = o
                depth = 0
                firstif = 0
                while index < len(string):
                    current = tokenize(string[index])
                    if current[0] == "if" or current[0] == "else":
                        firstif = 1
                        depth += 1
                    if current[0] == "endblk":
                        depth -= 1
                    if not depth and firstif: break
                    index += 1
                o = index + 1

        if i[0] == "endblk":
            o = ifstack.pop()
            continue

        if i[0] == "return":
            variables["__fnout"] = parseExpr(i[1:], variables, functions)

        if i[0] == "while":
            #find the matching endwhile
            index = o
            depth = 0
            firstwhile = 0
            while index < len(string):
                current = tokenize(string[index])
                if current[0] == "while":
                    firstwhile = 1
                    depth += 1
                if current[0] == "end":
                    depth -= 1
                if depth == 0 and firstwhile: break
                index += 1
            endwhileaddr = index + 1
            #if the condition is false, jump to it
            condition = parseExpr(i[1:], variables, functions)
            if not condition:
                o = endwhileaddr
                continue
            #if not, push the current "address" and keep going
            else:
                whileFrames.append(o)

        if i[0] == "end":
            o = whileFrames.pop()
            continue

        if i[0] == "for": #for x = y to z
            pass

        if i[0] == "endFor":
            pass

        if i[0] in functions: #function call
            parseExpr(i, variables, functions)

        if i[0] == "fn": #ignore everything until endfn, put it all into a buffer mapped to the function name in functions
            functionname = i[1]
            lines = ""
            index = o

            while index < len(string):
                index += 1
                if tokenize(string[index])[0] == "endfn": break
                lines += string[index] + "\n"
            o = index
            functions[functionname] = lines[:-1]
               

        o += 1
    
    return variables, functions

variables, functions = ({}, {})
depth = 0
lines = ""
inIf = 0
inFn = False

#option for interactive shell and running script passed as command line argument
if __name__ == "__main__":
    os.system("title AstroShell")

    if len(sys.argv) == 1:
        while True:
            line = input("$ ")

            if line == "exit":
                outfile.close()
                break

            if tokenize(line)[0] == "fn":
                inFn = True

            if tokenize(line)[0] == "endfn":
                inFn = False

            if tokenize(line)[0] == "if":
                inIf += 1

            if tokenize(line)[0] == "endif":
                inIf -= 1

            if tokenize(line)[0] == "while":
                depth += 1

            if tokenize(line)[0] == "end":
                depth -= 1

            if not depth and not inIf and not inFn:
                if lines != "":
                    lines += line + "\n"
                    variables, functions = execute(lines)
                    lines = "" #flush for new input

                else:
                    variables, functions = execute(line)

            else:
                lines += line + "\n"

    else:
        for i in range(2, len(sys.argv)): #put them in an array instead
            variables["__arg{}".format(i)] = sys.argv[i]

        file = open(sys.argv[1], "r")
        execute(file.read(), variables, functions)
        input()
