#!/usr/bin/env python3
# ```
# ============================================================
# uc -- uC (a.k.a. micro C) language compiler
#
# This is the main program for the uc compiler, which just
# parses command-line options, figures out which source files
# to read and write to, and invokes the different stages of
# the compiler proper.
# ============================================================
# ```

import sys
import argparse
from contextlib import contextmanager
from uc_parser import UCParser
from uc_sema import Visitor
from uc_code import CodeGenerator
from uc_analysis import DataFlow
from uc_interpreter import Interpreter
from uc_llvm import LLVMCodeGenerator

"""
One of the most important (and difficult) parts of writing a compiler
is reliable reporting of error messages back to the user.  This file
defines some generic functionality for dealing with errors throughout
the compiler project. Error handling is based on a subscription/logging
based approach.

To report errors in uc compiler, we use the error() function. For example:

       error(lineno, "Some kind of compiler error message")

where lineno is the line number on which the error occurred.

Error handling is based on a subscription based model using context-managers
and the subscribe_errors() function. For example, to route error messages to
standard output, use this:

       with subscribe_errors(print):
            run_compiler()

To send messages to standard error, you can do this:

       import sys
       from functools import partial
       with subscribe_errors(partial(print, file=sys.stderr)):
            run_compiler()

To route messages to a logger, you can do this:

       import logging
       log = logging.getLogger("somelogger")
       with subscribe_errors(log.error):
            run_compiler()

To collect error messages for the purpose of unit testing, do this:

       errs = []
       with subscribe_errors(errs.append):
            run_compiler()
       # Check errs for specific errors

The utility function errors_reported() returns the total number of
errors reported so far.  Different stages of the compiler might use
this to decide whether or not to keep processing or not.

Use clear_errors() to clear the total number of errors.
"""

_subscribers = []
_num_errors = 0


def error(lineno, message, filename=None):
    """ Report a compiler error to all subscribers """
    global _num_errors
    if not filename:
        if not lineno:
            errmsg = "{}".format(message)
        else:
            errmsg = "{}: {}".format(lineno, message)
    else:
        if not lineno:
            errmsg = "{}: {}".format(filename, message)
        else:
            errmsg = "{}:{}: {}".format(filename, lineno, message)
    for subscriber in _subscribers:
        subscriber(errmsg)
    _num_errors += 1


def errors_reported():
    """ Return number of errors reported. """
    return _num_errors


def clear_errors():
    """ Clear the total number of errors reported. """
    global _num_errors
    _num_errors = 0


@contextmanager
def subscribe_errors(handler):
    """ Context manager that allows monitoring of compiler error messages.
        Use as follows where handler is a callable taking a single argument
        which is the error message string:

        with subscribe_errors(handler):
            ... do compiler ops ...
    """
    _subscribers.append(handler)
    try:
        yield
    finally:
        _subscribers.remove(handler)


class Compiler:
    """ This object encapsulates the compiler and serves as a
        facade interface to the 'meat' of the compiler underneath.
    """

    def __init__(self, cl_args):
        self.code = None
        self.total_errors = 0
        self.total_warnings = 0
        self.args = cl_args

    def _parse(self):
        """ Parses the source code. If ast_file != None,
            prints out the abstract syntax tree.
        """
        self.parser = UCParser()
        self.ast = self.parser.parse(self.code, '', False)

    def _sema(self):
        """ Decorate AST with semantic actions. If ast_file != None,
            prints out the abstract syntax tree. """
        try:
            self.sema = Visitor()
            self.sema.visit(self.ast)
            if not self.args.susy and self.ast_file is not None:
                self.ast.show(buf=self.ast_file, showcoord=True)
        except AssertionError as e:
            error(None, e)

    def _codegen(self):
        self.gen = CodeGenerator(self.args.cfg)
        self.gen.visit(self.ast)
        self.gencode = self.gen.code
        if not self.args.susy and self.ir_file is not None:
            self.gen.show(buf=self.ir_file)

    def _opt(self):
        self.opt = DataFlow(self.args.cfg, self.args.verbose)
        self.opt.visit(self.ast)
        self.optcode = self.opt.code
        if not self.args.susy and self.opt_file is not None:
            self.opt.show(buf=self.opt_file)

    def _llvm(self):
        self.llvm = LLVMCodeGenerator(self.args.cfg)
        self.llvm.visit(self.ast)
        if not self.args.susy and self.llvm_file is not None:
            self.llvm.save_ir(self.llvm_file)
        if self.run:
            self.llvm.execute_ir(self.args.llvm_opt, self.llvm_opt_file)

    def _do_compile(self):
        """ Compiles the code to the given source file. """
        self._parse()
        if not errors_reported():
            self._sema()
        if not errors_reported():
            self._codegen()
            if self.args.opt:
                self._opt()
            if self.args.llvm:
                self._llvm()

    def compile(self):
        """ Compiles the given  filename """

        if self.args.filename[-3:] == '.uc':
            filename = self.args.filename
        else:
            filename = self.args.filename + '.uc'

        open_files = []

        self.ast_file = None
        if self.args.ast and not self.args.susy:
            ast_filename = filename[:-3] + '.ast'
            sys.stderr.write("Outputting the AST to %s.\n" % ast_filename)
            self.ast_file = open(ast_filename, 'w')
            open_files.append(self.ast_file)

        self.ir_file = None
        if self.args.ir and not self.args.susy:
            ir_filename = filename[:-3] + '.ir'
            sys.stderr.write("Outputting the uCIR to %s.\n" % ir_filename)
            self.ir_file = open(ir_filename, 'w')
            open_files.append(self.ir_file)

        self.opt_file = None
        if self.args.opt and not self.args.susy:
            opt_filename = filename[:-3] + '.opt'
            sys.stderr.write("Outputting the optimized uCIR to %s.\n" % opt_filename)
            self.opt_file = open(opt_filename, 'w')
            open_files.append(self.opt_file)

        self.llvm_file = None
        if self.args.llvm and not self.args.susy:
            llvm_filename = filename[:-3] + '.ll'
            sys.stderr.write("Outputting the LLVM IR to %s.\n" % llvm_filename)
            self.llvm_file = open(llvm_filename, 'w')
            open_files.append(self.llvm_file)

        self.llvm_opt_file = None
        if self.args.llvm_opt and not self.args.susy:
            llvm_opt_filename = filename[:-3] + '.opt.ll'
            sys.stderr.write("Outputting the optimized LLVM IR to %s.\n" % llvm_opt_filename)
            self.llvm_opt_file = open(llvm_opt_filename, 'w')
            open_files.append(self.llvm_opt_file)

        source = open(filename, 'r')
        self.code = source.read()
        source.close()

        self.run = not self.args.no_run
        with subscribe_errors(lambda msg: sys.stderr.write(msg+"\n")):
            self._do_compile()
            if errors_reported():
                sys.stderr.write("{} error(s) encountered.".format(errors_reported()))
            elif not self.args.llvm:
                if self.args.opt:
                    speedup = len(self.gencode) / len(self.optcode)
                    sys.stderr.write("original = %d, otimizado = %d, speedup = %.2f\n" %
                                     (len(self.gencode), len(self.optcode), speedup))
                if self.run and not self.args.cfg:
                    vm = Interpreter(self.args.idb)
                    if self.args.opt:
                        vm.run(self.optcode)
                    else:
                        vm.run(self.gencode)

        for f in open_files:
            f.close()
        return 0


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-s", "--susy", help="run in the susy machine", action='store_true')
    parser.add_argument("-a", "--ast", help="dump the AST in the 'filename'.ast", action='store_true')
    parser.add_argument("-i", "--ir", help="dump the uCIR in the 'filename'.ir", action='store_true')
    parser.add_argument("-n", "--no-run", help="do not execute the program", action='store_true')
    parser.add_argument("-d", "--idb", help="run the interpreter in debug mode", action='store_true')
    parser.add_argument("-c", "--cfg", help="show the CFG for each function in pdf format", action='store_true')
    parser.add_argument("-o", "--opt", help="optimize the uCIR with const prop and dce", action='store_true')
    parser.add_argument("-v", "--verbose", help="print in the stderr some data analysis informations", action='store_true')
    parser.add_argument("-l", "--llvm", help="generate LLVM IR code in the 'filename'.ll", action='store_true')
    parser.add_argument("-p", "--llvm-opt", choices=['ctm', 'dce', 'cfg', 'all'],
                        help="specify which llvm pass optimizations is enabled")
    args = parser.parse_args()

    retval = Compiler(args).compile()
    sys.exit(retval)
