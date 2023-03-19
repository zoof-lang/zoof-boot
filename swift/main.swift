//
//  main.swift
//  test
//
//  Created by Almar Klein on 10/02/2023.
//

import Foundation

let filename =

class Compiler {
    
    func main() {
        this.runFile("../syntax/syntax1.zf")
        //this.runPrompt()
    }
    
    func runFile(path) {
        let contents = try String(contentsOfFile: path, encoding: .utf8)
        this.run(contents)
        if hadError {
            exit(65)
        }
    }
    
    func run(source) {
        print(source)
    }
}
                    
func main(filename) {
    
    
}
