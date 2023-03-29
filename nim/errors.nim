import std/strformat

type ErrorHandler* = ref object
    hadError*: bool

proc report*(self: ErrorHandler, line: int, where: string, message: string) =
    echo fmt"[line {line}] Error {where}: {message}"
    self.hadError = true 

proc error*(self: ErrorHandler, line: int, message: string) =
    self.report(line, "", message)
    