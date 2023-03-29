# Stuff that I like:
#
# * It looks ok.
# * Pretty smart way to allow methods be called using dot notation, and props by leaving out the braces.
#
# Stuff I like less:
#
# * Syntax looks like Python but also not so much :/
# * I felt it hard to find how to do stuff sometimes. This might have been the hardest to implement so far?
# * Error messages often not that useful.
# * No method hoisting wtf -> need to define functions bottom to top ...
#
#  Not sure what to think:
#
# * How come people praise Nim so much? I'm not impressed tbh.
# * I got stuck on code that looked the same as a Lox Nim example, and was not able to find the cause, so I quit.

import os
import std/strformat
import scanner
import errors


proc print(x: auto) =
    echo x


type Compiler = object
    handler: ErrorHandler

proc run(self: Compiler, source: string) = 
    var scanner: Scanner = newScanner(source, self.handler)
    var tokens = scanner.scanTokens()

    for token in tokens:
        echo token

proc runFile(self: Compiler, path: string) =
    #let f = open(path)
    #defer: f.close()
    let source = readFile(path)
    self.run(source)
    if self.handler.hadError:
        system.quit(65)

proc runPrompt(self: Compiler) =
    while true:
        stdout.write "zf> "
        let line = readLine(stdin)
        if len(line) == 0:
            break
        self.run(line)
        self.handler.hadError = false

proc main(self: Compiler, argv: seq[string]) =

    if len(argv) > 1:
        echo "Usage main.nim [script]"
        system.quit(64)
    elif len(argv) == 1:
        self.runFile(argv[0])
    else:
        self.runPrompt()


let c = Compiler(handler: ErrorHandler(hadError: false))
c.main(os.commandLineParams())
system.quit(0)
