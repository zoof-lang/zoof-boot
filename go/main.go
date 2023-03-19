// Stuff that I like:
//
// * Type checking is nice.
// * Clean syntax in general. Don't even have to spell out types that much.
//
// Stuff I like less:
//
// * modules don't feel very dynamic, though I guess that makes sense.
// * methods feel verbose to write.
// * Eek, pointers!
// * No default args, wtf
// * Not a lot of batteries included, e.g. Array.contains
//
// Note: could also apply https://www.youtube.com/watch?v=HxaD_trXwRE
// Which beasically has "state functions" that consume characters until it
// hits something, this then returns a new state function, etc.

package main

import (
	"os"
)

func main() {
	args := os.Args
	if len(args) > 2 {
		println("Usage zoofpyc [script]")
		os.Exit(64)
	} else if len(args) < 2 {
		runPrompt()
	} else {
		runFile(args[1])
	}
}

func runPrompt() {
	//handler := ErrorHandler{}
	//while true {
	//	line = input("zf>")
	//}
}

func runFile(filename string) {
	source, err := os.ReadFile(filename)
	if err != nil {
		println("unable to read file: ", err)
		os.Exit(2)
	}
	handler := ErrorHandler{}
	run(string(source), handler)
	if handler.hadError {
		os.Exit(2)
	}
}

func run(source string, handler ErrorHandler) {
	scanner := NewScanner(source, handler)
	tokens := scanner.scanTokens()

	for _, token := range tokens {
		println(token.ToString())
	}

}

type ErrorHandler struct {
	hadError bool
}

func (handler *ErrorHandler) error(line int, message string) {
	handler.report(line, "", message)
}
func (handler *ErrorHandler) report(line int, where string, message string) {
	println("[line " + string(line) + "] Error " + where + ": " + message)
	handler.hadError = true
}
