# zoof-boot

Bootstrapping Zoof using Python.

## What's this?

This is me hacking on a new programming language called Zoof. This repo
is public but I probably don't accept any contributions for now. It's
all very experimental and I make small and large changes without warning.

This repo is to bootstrap the language, because the plan is that it is
eventually self-hosting.


## What is Zoof?

The idea is a language that targets WebAssembly, using jit-compilation
(similar to Julia) to create a language that is dynamic enough for
scientific use, but also very fast (where it matters).

The trait-based type system offers high flexibility while maintaining
safety so the compiler can spot errors early, and runtime errors should
be rare. Maybe not as rare as in Rust, but certainly less prevalent as
in Juliar or Python.

I also have ideas to make it partly compiled, partly bytecode, to offer
more flexibility, and make prototyping easier, without having to
complicate the type system.

Further, Zoof has a strong focus on readability and I try to include
results from research to programming, to make the language easy to learn
and fun.

## Research

There are two books which I kinda use as a basis:
* The programmer''s brain, by Felienne Hermans. This has taught me a lot about
  cognition and how this can be included into the design of a language.
* Crafting interpreters, by Robert Nystrom. This book is freaking awesome.
  It is fun to read and I've learned so much from it. I'm basically following
  the book but writing Zoof instead of Loc. I also draw inspiration from other
  work of Robert, e.g. his language [Wren](https://wren.io/).

I have a ton of private notes about various topics. I hope to turn some
of these into blog posts.


## Dev

Mostly note to self:

* There is currently no CI. I just run the below locally.
* Run `black .` to format the code.
* Run `flake8 .`  to lint the code.
* Run `test_snippets.py` to make sure all snippets have the expected result.
* Run `test_meta.py` to e.g. check that all errors are covered in the snippets.

