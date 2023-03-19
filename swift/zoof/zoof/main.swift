// Stuff that I like:
//
// * Inline linting
// * Real enums
// * Clean syntax
// * Run code from the IDE
// * Seems to work reasonably well with having multiple possible types (for the literals)
// * Overloading with different arg types seems nice, but also a bit weird.
//
// Stuff I like less:
//
// * Awkward string indexing and slicing.
// * Feels odd that self is optional.
// * Positional args only possible if defined with weird underscore syntax.

import Foundation


class Compiler {
    
    var handler: ErrorHandler
    
    init() {
        self.handler = ErrorHandler()
    }
    
    func main() throws {
        try runFile(path:"/Users/almar/dev/zf/zoof-boot/syntax/syntax1.zf")
        //this.runPrompt()
    }
    
    func runFile(path: String) throws {
        let contents = try String(contentsOfFile: path, encoding: .utf8)
        run(source:contents)
        if handler.hadError {
            exit(65)
        }
    }
    
    func run(source: String) {
        let scanner = Scanner(source, handler)
        let tokens = scanner.scanTokens()
        for token in tokens {
            print(token)
        }
    }
}


class ErrorHandler{
    var hadError: Bool
    
    init() {
        self.hadError = false
    }
    
    func error(_ line: Int, _ message:String) {
        report(line, "", message)
    }
    
    func report(_ line: Int, _ wher: String, _ message:String) {
        print("[line \(line)] Error \(wher): \(message)")
        self.hadError = true
    }
    
}

let compiler = Compiler()
try compiler.main()


