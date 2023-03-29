# Stuff that I like:
#
# * Syntax clean, no curly braces
# * multiple dispatch is very powerful
# * Feels very dynamic. Types are very much optional
#
# Stuff I like less:
#
# * Curly braces for type templates feels nasty
# * 1-based index makes porting code hard
# * Defining methods is somewhat verbose.
# * Calling a method would be so much friendlier if you could do xx.func()
# * Importing  / including wtf
# * So many ends! I can see how ppl would prefer curly braces if they see this.
#
# Stuff I was somewhat surprised about, but maybe it makes sense?
#
# * Indexing in a string produces a Char

include("./scanner.jl")

mutable struct ErrorHandler
    hadError:: Bool
end

function error(handler::ErrorHandler, line::Int, message::String)
    report(handler, line, "", message)
end

function report(handler::ErrorHandler, line::Int, wher::String, message::String)
    println("[line $line] Error $wher: $message")
end


function main(args)
    if length(args) == 0
       runPrompt()
    elseif length(args) == 1
        runFile(args[1])
    else
        println("Usage zoofpyc [script]")
        exit(64)
    end
end

function runFile(path)
    handler = ErrorHandler(false)
    source = open(path) do f
        read(f, String)
    end
    run(source, handler)
    if handler.hadError
        sys.exit(65)
    end
end

function runPrompt()
    handler = ErrorHandler(false)
    while true
        print("zf> ")
        line = readline()
        if length(line) == 0
            break
        end
        run(line, handler)
        handler.hadError = false
    end
end

function run(source::String, handler::ErrorHandler)
    scanner = Scanner(source, handler)
    tokens = scanTokens(scanner)
    for token in tokens
        println(token)
    end
end


main(["/Users/almar/dev/zf/zoof-boot/syntax/syntax1.zf"])
#main(ARGS)
