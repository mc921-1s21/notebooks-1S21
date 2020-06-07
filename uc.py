#!/usr/bin/env python3
# ============================================================
# uc -- uC (a.k.a. micro C) language compiler
#
# This is the main program for the uc compiler, which just
# parses command-line options, figures out which source files
# to read and write to, and invokes the different stages of
# the compiler proper.
# ============================================================

import sys
from contextlib import contextmanager
from uc_parser import UCParser
from uc_sema import Visitor
from uc_code import CodeGenerator
from uc_analysis import DataFlow
from uc_interpreter import Interpreter

"""
One of the most important (and difficult) parts of writing a compiler
is reliable reporting of error messages back to the user.  This file
defines some generic functionality for dealing with errors throughout
the compiler project. Error handling is based on a subscription/logging
based approach.

To report errors in uc compiler, we use the error() function. For example:

       error(lineno,"Some kind of compiler error message")

where lineno is the line number on which the error occurred.

Error handling is based on a subscription based model using context-managers
and the subscribe_errors() function. For example, to route error messages to
standard output, use this:

       with subscribe_errors(print):
            run_compiler()

To send messages to standard error, you can do this:

       import sys
       from functools import partial
       with subscribe_errors(partial(print,file=sys.stderr)):
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

    def __init__(self):
        self.total_errors = 0
        self.total_warnings = 0

    def _parse(self, susy, ast_file, debug):
        """ Parses the source code. If ast_file != None,
            prints out the abstract syntax tree.
        """
        self.parser = UCParser()
        self.ast = self.parser.parse(self.code, '', debug)

    def _sema(self, susy, ast_file):
        """ Decorate AST with semantic actions. If ast_file != None,
            prints out the abstract syntax tree. """
        try:
            self.sema = Visitor()
            self.sema.visit(self.ast)
            if not susy and ast_file is not None:
                self.ast.show(buf=ast_file, showcoord=True)
        except AssertionError as e:
            error(None, e)

    def _codegen(self, susy, ir_file, cfg):
        self.gen = CodeGenerator(cfg)
        self.gen.visit(self.ast)
        self.gencode = self.gen.code
        if not susy and ir_file is not None:
            self.gen.show(buf=ir_file)

    def _opt(self, susy, opt_file, cfg, debug):
        self.opt = DataFlow(cfg, debug)
        self.opt.visit(self.ast)
        self.optcode = self.opt.code
        if not susy and opt_file is not None:
            self.opt.show(buf=opt_file)

    def _do_compile(self, susy, ast_file, ir_file, opt_file, cfg, opt, debug):
        """ Compiles the code to the given file object. """
        self._parse(susy, ast_file, False)
        if not errors_reported():
            self._sema(susy, ast_file)
        if not errors_reported():
            self._codegen(susy, ir_file, cfg)
            if opt:
                self._opt(susy, opt_file, cfg, debug)

    def compile(self, code, susy, ast_file, ir_file, opt_file, opt, run_ir, cfg, debug):
        """ Compiles the given code string """
        self.code = code
        with subscribe_errors(lambda msg: sys.stderr.write(msg+"\n")):
            self._do_compile(susy, ast_file, ir_file, opt_file, cfg, opt, debug)
            if errors_reported():
                sys.stderr.write("{} error(s) encountered.".format(errors_reported()))
            else:
                if opt:
                    self.speedup = len(self.gencode) / len(self.optcode)
                    sys.stderr.write("speedup = %.2f\n" % self.speedup)
                if run_ir and not cfg:
                    self.vm = Interpreter()
                    if opt:
                        self.vm.run(self.optcode)
                    else:
                        self.vm.run(self.gencode)
        return 0


def run_compiler():
    """ Runs the command-line compiler. """

    if len(sys.argv) < 2:
        print("Usage: ./uc <source-file> [-at-susy] [-no-ast] [-no-ir] [-no-run] [-cfg] [-opt] [-debug]")
        sys.exit(1)

    emit_ast = True
    emit_ir = True
    run_ir = True
    susy = False
    cfg = False
    opt = False
    debug = False

    params = sys.argv[1:]
    files = sys.argv[1:]

    for param in params:
        if param[0] == '-':
            if param == '-no-ast':
                emit_ast = False
            elif param == '-no-ir':
                emit_ir = False
            elif param == '-at-susy':
                susy = True
            elif param == '-no-run':
                run_ir = False
            elif param == '-cfg':
                cfg = True
            elif param == '-opt':
                opt = True
            elif param == '-debug':
                debug = True
            else:
                print("Unknown option: %s" % param)
                sys.exit(1)
            files.remove(param)

    for file in files:
        if file[-3:] == '.uc':
            source_filename = file
        else:
            source_filename = file + '.uc'

        open_files = []

        ast_file = None
        if emit_ast and not susy:
            ast_filename = source_filename[:-3] + '.ast'
            print("Outputting the AST to %s." % ast_filename)
            ast_file = open(ast_filename, 'w')
            open_files.append(ast_file)

        ir_file = None
        if emit_ir and not susy:
            ir_filename = source_filename[:-3] + '.ir'
            print("Outputting the uCIR to %s." % ir_filename)
            ir_file = open(ir_filename, 'w')
            open_files.append(ir_file)

        opt_file = None
        if opt and not susy:
            opt_filename = source_filename[:-3] + '.opt'
            print("Outputting the optimized uCIR to %s." % opt_filename)
            opt_file = open(opt_filename, 'w')
            open_files.append(opt_file)

        source = open(source_filename, 'r')
        code = source.read()
        source.close()

        retval = Compiler().compile(code, susy, ast_file, ir_file, opt_file, opt, run_ir, cfg, debug)
        for f in open_files:
            f.close()
        if retval != 0:
            sys.exit(retval)

    sys.exit(retval)


if __name__ == '__main__':
    run_compiler()
