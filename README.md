# MC921 -- Compiler Construction.

The goal of the practical part of this course is to write a complete compiler
for uC (micro C) Language, designed exclusively for this purpose. uC has the
essential features of a realistic programming language, but is small and simple
enough that it can be implemented in a few thousand lines of code. We chose the
Python programming language for this task because it has clear and direct syntax
and allows for rapid prototyping. In addition, we will have at our disposal a
wonderful combination of tools and code in Python that make compilers so cool.

*C is not a "very high level" language, nor a "big" one, and is not specialized
to any particular area of application. But its absence of restrictions and its
generality make it more convenient and effective for many tasks than supposedly
more powerful languages.*
-- Kernighan and Ritchie

While you don’t need to be a Python wizard to complete the task, you should feel
comfortable working with the language, and in particular should know how to
program with classes. If you’d like a Python refresher, there are a bunch of
useful links on the website to help you get up to speed.  I hope that the use of
Python in this task doesn’t deter you from taking it.

This task will revolve around several programming projects that taken together
form a complete working compiler. You will learn how to put into practice the
techniques presented in the theoretical part of this course and will study most
of the details involved in the implementation of a "real" compiler.

## First Project: Lexer

The first project requires you to implement a scanner for the uC language,
specified by [uC BNF Grammar](./doc/uC_Grammar.ipynb) notebook. Study the
specification of uC grammar carefully. To complete this first project, you will
use the [PLY](http://www.dabeaz.com/ply/), a Python version of the
[lex/yacc](http://dinosaur.compilertools.net/) toolset with same functionality
but with a friendlier interface. Details about this project are in the
[First Project](./P1-Lexer.ipynb) notebook.

## Second Project: Parser

The second project requires you to implement a Parser (note that the Abstract
Syntax Tree will be built only in the third project) for the uC language.
To complete this second project, you will also use the [PLY](http://www.dabeaz.com/ply/),
a Python version of the [lex/yacc](http://dinosaur.compilertools.net/) toolset
with same functionality but with a friendlier interface. Details about this
project are in the [Second Project](./P2-Parser.ipynb) notebook.

## Third Project: AST

Abstract syntax trees are data structures that better represent the structure of
the program code than the parse tree. An AST can be edited and enhanced with
information such as properties and annotations for each element it contains.
Your goal in this third project is to transform the parse tree into an AST.
Details about this project are in the [Third Project](./P3-AST.ipynb) notebook.

## Fourth Project: Semantic Analysis

Once syntax trees are built, additional analysis can be done by evaluating
attributes on tree nodes to gather necessary semantic information from the
source code not easily detected during parsing. It usually includes type
checking, and symbol table construction. Details about this project are in the
[Fourth Project](./P4-Semantic.ipynb) notebook.

## Fifth Project: Code Generation

Once semantic analysis are done, we can walk through the decorated AST to
generate a linear N-address code, analogously to [LLVM IR](https://llvm.org/docs/index.html).
We call this intermediate machine code as uCIR. So, in this fifth project, you
will turn the AST into uCIR. uCIR uses a Single Static Assignment (SSA), and can
promote stack allocated scalars to virtual registers and remove the load and
store operations, allowing better optimizations since values propagate directly
to their use sites.  The main thing that distinguishes SSA from a conventional
three-address code is that all assignments in SSA are for distinguished name
variables.

Once you've got your compiler emitting intermediate code, you should be able to
use a simple interpreter, provided for this purpose, that runs the code.  This
can be useful for testing, and other tasks involving the generated code. Details
about this project are in the [Fifth Project](./P5-CodeGeneration.ipynb)
notebook.

## Sixth Project: Data Flow Analysis & Optimization

In this sixth project, you will do some analysis and optimizations in uCIR.
First, you will implement the Reaching Definitions Analysis followed by the
Constant Propagation Optimization. Then you will implement the Liveness Analysis
followed by the Dead Code Optimization. Finally, you will implement an
optimization called CFG Simplify. Details about this project are in the
[Sixth Project](./P6-Dataflow.ipynb) notebook.

## Seventh Project: LLVM IR Code Generation

In this last project, you're going to translate the optimized SSA intermediate
representation uCIR into LLVM IR, the intermediate representation of LLVM that
is partially specified in [LLVM Primer](./doc/llvm_primer.ipynb). LLVM is a set
of production-quality reusable libraries for building compilers. LLVM separates
computer architectures from language issues and simplifies the design and
portability of new compilers. Details about this project are in the
[Seventh Project](./P7-LLVM-IR.ipynb) notebook.

# Readings

The course website is available at https://akluz.wordpress.com/mc921-1s21/ and
is loaded with resources for this course. There, you will find the project
schedule, the slides for this course, additional class notes and articles
presented in class. It can also contain useful links to learn more about the
tools we will use (e.g., Python Lex and Yacc), the Python programming language
and compilers in general.

# Assignments

The final course grade  will be based on 7 programming projects, and 2 exams
distributed as follows (more details about the grade should be consulted in
the course website):

    - Projects: 70%
    - Exams: 30%

Projects  will use the GitHub Classroom environment, where each project has an
associated template repository. Students have to pull the assignment template
locally to work, and push it for testing, and before the deadline for grading.
The GitHub system will run the tests and automatically compute the assignment
grade.

All test inputs for the projects  are open, and there are no closed tests. The
correct output for each test is open, and their evaluation will take into
consideration not only execution correctness but also performance.

GitHub will automatically close the submission system after each project
deadline, and there will be no extensions. Hence, we strongly recommend that the
student submit its work even if the testing is incomplete.

# Collaboration policy

Projects are assigned in pairs. The pairs can collaborate with each other for the
purpose of understanding and discussing the task solution. However, code sharing
and copying is not allowed and will be considered fraud.

Exams are individual assignments, and collaboration for their execution is not
permitted. Any violation will be considered fraud.

Frauds  will not be accepted, G = 0.0  will be assigned to everyone involved,
and the case will be brought to the Undergraduate Dean.
