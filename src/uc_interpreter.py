# ---------------------------------------------------------------------------------
# uc: uc_interpreter.py
#
# uCInterpreter class: A simple interpreter for the uC intermediate representation
#                      see https://github.com/mc921
#
# Copyright (c) 2019-2020, Marcio M Pereira. All rights reserved.
#
# This software is provided by the author, "as is" without any warranties
# Redistribution and use in source form with or without modification are
# permitted but the source code must retain the above copyright notice.
# ---------------------------------------------------------------------------------
import sys


def format_instruction(t):
    operand = t[0].split('_')
    op = operand[0]
    ty = None
    if len(operand) > 1:
        ty = operand[1]
    if len(operand) >= 3:
        for _qual in operand[2:]:
            if _qual == '*':
                ty += '*'
            else:
                ty += f" [{_qual}]"
    if len(t) > 1:
        if op == "define":
            return f"{op} {ty} {t[1]} " + ', '.join(list(' '.join(el) for el in t[2]))
        else:
            _str = "" if op == "global" else "  "
            if op == 'jump':
                _str += f"{op} label {t[1]}"
            elif op == 'cbranch':
                _str += f"{op} {t[1]} label {t[2]} label {t[3]}"
            elif op == "global"  and ty.startswith('string'):
                _str += f"{t[1]} = {op} {ty} \'{t[2]}\'"
            elif op == "return":
                _str += f"{op} {ty} {t[1]}"
            elif op == "store":
                _str += f"{op} {ty} "
                for _el in t[1:]:
                    _str += f"{_el} "
            else:
                _str += f"{t[-1]} = {op} {ty} "
                for _el in t[1:-1]:
                    _str += f"{_el} "
            return _str
    elif ty == 'void':
        return f"  {op}"
    else:
        return f"{op}"


class Interpreter(object):
    """
    Runs an interpreter on the uC intermediate code generated for
    uC compiler.   The implementation idea is as follows.  Given
    a sequence of instruction tuples such as:

         code = [
              ('literal_int', 1, '%1'),
              ('literal_int', 2, '%2'),
              ('add_int', '%1', '%2, '%3')
              ('print_int', '%3')
              ...
         ]

    The class executes methods self.run_opcode(args).  For example:

             self.run_literal_int(1, '%1')
             self.run_literal_int(2, '%2')
             self.run_add_int('%1', '%2', '%3')
             self.run_print_int('%3')

    Instructions for use:
        1. Instantiate an object of the Interpreter class
        2. Call the run method of this object passing the produced
           code as a parameter
    """

    def __init__(self, debug):
        global inputline, M
        inputline = []
        M = 10000 * [None]      # Memory for global & local vars

        self.globals = {}       # Dictionary of address of global vars & constants
        self.vars = {}          # Dictionary of address of local vars relative to sp

        self.offset = 0         # offset (index) of local & global vars. Note that
                                # each instance of var has absolute address in Memory
        self.stack = []         # Stack to save address of vars between calls
        self.sp = []            # Stack to save & restore the last offset

        self.params = []        # List of parameters from caller (address)
        self.result = None      # Result Value (address) from the callee

        self.registers = []     # Stack of register names (in the caller) to return value
        self.returns = []       # Stack of return addresses (program counters)

        self.pc = 0             # Program Counter
        self.lastpc = 0         # last pc
        self.start = 0          # PC of the main function
        self.code = None
        self.debug = debug      # Set the debug mode

    def _extract_operation(self, source):
        _modifier = {}
        _aux = source.split('_')
        if _aux[0] not in {'fptosi', 'sitofp', 'label', 'jump', 'cbranch', 'call'}:
            _opcode = _aux[0] + '_' + _aux[1]
            for i, _val in enumerate(_aux[2:]):
                if _val.isdigit():
                    _modifier['dim' + str(i)] = _val
                elif _val == '*':
                    _modifier['ptr' + str(i)] = _val
        else:
            _opcode = _aux[0]
        return (_opcode, _modifier)

    def _copy_data(self, address, size, value):
        if isinstance(value, str):
            _value = list(value)
        elif any(isinstance(item, list) for item in value):
            _value = [item for sublist in value for item in sublist]
        else:
            _value = value
        M[address:address+size] = _value

    def _show_idb_help(self):
        msg = """ 
          s, step: run in step mode;
          g, go <pc>:  goto the program counter;
          l, list {<start> <end>}? : List the ir code;
          e, ex {<vars>}+ : Examine the variables;
          v, view : show he current line of execution;
          r, run : run (twerminate) the program in normal mode;
          q, quit : quit (abort) the program;
          h, help: print this text.
        """
        print(msg)

    def _idb(self, pos):
        _init = pos - 2
        if _init < 1:
            _init = 1
        _end = pos + 3
        if _end >= self.lastpc:
            _end = self.lastpc
        for i in range(_init, _end):
            mark = ": >> " if i == pos else ":    "
            print(str(i) + mark + format_instruction(self.code[i]))
        print()
        return self._parse_input()

    def _parse_input(self):
        while True:
            try:
                _cmd = list(input("idb> ").strip().split(' '))
                if _cmd[0] == 's' or _cmd[0] == 'step':
                    return None
                elif _cmd[0] == 'g' or _cmd[0] == 'go':
                    return int(_cmd[1])
                elif _cmd[0] == 'e' or _cmd[0] == 'ex':
                    for i in range(1, len(_cmd)):
                        if _cmd[i].startswith('%'):
                            print(_cmd[i] + " : " + str(M[self.vars[_cmd[i]]]))
                        elif _cmd[i].startswith('@'):
                            print(_cmd[i] + " : " + str(M[self.globals[_cmd[i]]]))
                        else:
                            print(_cmd[i] + ": unrecognized var or temp")
                elif _cmd[0] == 'l' or _cmd[0] == 'list':
                    if len(_cmd) == 3:
                        _start = int(_cmd[1])
                        _end = int(_cmd[2])
                    else:
                        _start = 1
                        _end = self.lastpc
                    for i in range(_start, _end):
                        print(str(i) + ":    " + format_instruction(self.code[i]))
                elif _cmd[0] == 'v' or _cmd[0] == 'view':
                    self._idb(self.pc)
                elif _cmd[0] == 'r' or _cmd[0] == 'run':
                    self.debug = False
                    return None
                elif _cmd[0] == 'q' or _cmd[0] == 'quit':
                    return 0
                elif _cmd[0] == 'h' or _cmd[0] == 'help':
                    self._show_idb_help()
                else:
                    print(_cmd[0] + " : unrecognized command")
            except:
                print("unrecognized command")

    def run(self, ircode):
        """
        Run intermediate code in the interpreter.  ircode is a list
        of instruction tuples.  Each instruction (opcode, *args) is
        dispatched to a method self.run_opcode(*args)
        """
        # First, store the global vars & constants
        # Also, set the start pc to the main function entry
        self.code = ircode
        self.pc = 0
        self.offset = 0
        while True:
            try:
                op = self.code[self.pc]
            except IndexError:
                break
            if len(op) > 1:  # that is, not label
                opcode, modifier = self._extract_operation(op[0])
                if opcode.startswith('global'):
                    self.globals[op[1]] = self.offset
                    # get the size of global var
                    if not modifier:
                        # size equals 1 or is a constant, so we use only
                        # one slot in the memory to make it simple.
                        if len(op) == 3:
                            M[self.offset] = op[2]
                        self.offset += 1
                    else:
                        _len = 1
                        for args in modifier.values():
                            if args.isdigit():
                                _len *= int(args)
                        if len(op) == 3:
                            self._copy_data(self.offset, _len, op[2])
                        self.offset += _len
                elif opcode.startswith('define'):
                        self.globals[op[1]] = self.offset
                        M[self.offset] = self.pc
                        self.offset += 1
                        if op[1] == '@main':
                            self.start = self.pc
            self.pc += 1

        # Now, running the program starting from the main function
        # If run in debug mode, show the available command lines.
        if self.debug:
            print("Interpreter running in debug mode:")
            self._show_idb_help()
        self.lastpc = self.pc - 1
        self.pc = self.start
        _breakpoint = None
        while True:
            try:
                if _breakpoint is not None:
                    if _breakpoint == 0:
                        sys.exit(0)
                    if self.pc == _breakpoint:
                        _breakpoint = self._idb(self.pc)
                elif self.debug:
                    _breakpoint = self._idb(self.pc)
                op = ircode[self.pc]
            except IndexError:
                break
            self.pc += 1
            if len(op) > 1 or op[0] == 'return_void' or op[0] == 'print_void':
                opcode, modifier = self._extract_operation(op[0])
                if hasattr(self, "run_" + opcode):
                    if not modifier:
                        getattr(self, "run_" + opcode)(*op[1:])
                    else:
                        getattr(self, "run_" + opcode + '_')(*op[1:], **modifier)
                else:
                    print("Warning: No run_" + opcode + "() method", flush=True)

    #
    # Auxiliary methods
    #
    def _alloc_labels(self):
        # Alloc labels for current function definition. Due to the uCIR and due to
        # the chosen memory model, this is done every time we enter a function.
        _lpc = self.pc
        while True:
            try:
                _op = self.code[_lpc]
                _opcode = _op[0]
                _lpc += 1
                if _opcode.startswith('define'):
                    break
                elif len(_op) == 1 and _opcode != 'return_void':
                    # labels don't go to memory, just store the pc on dictionary
                    # labels appears as name:, so we need to extract just the name
                    self.vars['%' + _opcode[:-1]] = _lpc
            except IndexError:
                break

    def _alloc_reg(self, target):
        # Alloc space in memory and save the offset in the dictionary
        # for new vars or temporaries, only.
        if target not in self.vars:
            self.vars[target] = self.offset
            self.offset += 1

    def _get_address(self, source):
        if source.startswith('@'):
            return self.globals[source]
        else:
            return self.vars[source]

    def _get_input(self):
        global inputline
        while True:
            if len(inputline) > 0:
                break
            inputline = sys.stdin.readline()
            if not inputline:
                print("Unexpected end of input file.", flush=True)
            inputline = inputline[:-1].strip().split()

    def _get_value(self, source):
        if source.startswith('@'):
            return M[self.globals[source]]
        else:
            return M[self.vars[source]]

    def _load_multiple_values(self, size, varname, target):
        self.vars[target] = self.offset
        self.offset += size
        self._store_multiple_values(size, target, varname)

    def _push(self, locs, no_return):
        # save the addresses of the vars from caller & their last offset
        self.stack.append(self.vars)
        self.sp.append(self.offset)

        # clear the dictionary of caller local vars and their offsets in memory
        # alloc the temporary with reg %0 in case of void function and initialize
        # the memory with None value. Copy the parameters passed to the callee in
        # their local vars. Finally, cleanup parameters list used to transfer vars
        self.vars = {}

        if no_return:
            self._alloc_reg('%0')
            M[self.vars['%0']] = None

        for idx, val in enumerate(self.params):
            # Note that arrays (size >=1) are passed by reference only.
            self.vars[locs[idx]] = self.offset
            M[self.offset] = M[val]
            self.offset += 1
        self.params = []
        self._alloc_labels()

    def _pop(self, target):
        if self.returns:
            # get the return value
            if target:
                _value = M[target]
            else:
                _value = None
            # restore the vars of the caller
            self.vars = self.stack.pop()
            # store in the caller return register the _value
            M[self.vars[self.registers.pop()]] = _value
            # restore the last offset from the caller
            self.offset = self.sp.pop()
            # jump to the return point in the caller
            self.pc = self.returns.pop()
        else:
            # We reach the end of main function, so return to system
            # with the code returned by main in the return register.
            print(end="", flush=True)
            if target is None:
                # void main () was defined, so exit with value 0
                sys.exit(0)
            else:
                sys.exit(M[target])

    def _store_deref(self, target, value):
        if target.startswith('@'):
            M[M[self.globals[target]]] = value
        else:
            M[M[self.vars[target]]] = value

    def _store_multiple_values(self, dim, target, value):
        _left = self._get_address(target)
        _right = self._get_address(value)
        if value.startswith('@'):
            if isinstance(M[_right], str):
                _value = list(M[_right])
                M[_left:_left+dim] = _value
                return
        M[_left:_left+dim] = M[_right:_right+dim]

    def _store_value(self, target, value):
        if target.startswith('@'):
            M[self.globals[target]] = value
        else:
            M[self.vars[target]] = value

    #
    # Run Operations, except Binary, Relational & Cast
    #
    def run_alloc_int(self, varname):
        self._alloc_reg(varname)
        M[self.vars[varname]] = 0

    run_alloc_float = run_alloc_int
    run_alloc_char = run_alloc_int

    def run_alloc_int_(self, varname, **kwargs):
        _dim = 1
        for arg in kwargs.values():
            if arg.isdigit():
                _dim *= int(arg)
        self.vars[varname] = self.offset
        M[self.offset:self.offset + _dim] = _dim * [0]
        self.offset += _dim

    run_alloc_float_ = run_alloc_int_
    run_alloc_char_ = run_alloc_int_

    def run_call(self, source, target):
        # alloc register to return and append it to register stack
        self._alloc_reg(target)
        self.registers.append(target)
        # save the return pc in the return stack
        self.returns.append(self.pc)
        # jump to the calle function
        if source.startswith('@'):
            self.pc = M[self.globals[source]]
        else:
            self.pc = M[self.vars[source]]

    def run_cbranch(self, expr_test, true_target, false_target):
        if M[self.vars[expr_test]]:
            self.pc = self.vars[true_target]
        else:
            self.pc = self.vars[false_target]

    # Enter the function
    def run_define_int(self, source, args):
        if source == '@main':
            # alloc register to the return value but initialize it with "None".
            # We use the "None" value when main function returns void.
            self._alloc_reg('%0')
            # alloc the labels with respective pc's
            self._alloc_labels()
        else:
            # extract the location names of function args
            _locs = [el[1] for el in args]
            self._push(_locs, False)

    run_define_float = run_define_int
    run_define_char = run_define_int

    def run_define_void(self, source, args):
        if source == '@main':
            # alloc register to the return value but not initialize it.
            # We use the "None" value to check if main function returns void.
            self._alloc_reg('%0')
            # alloc the labels with respective pc's
            self._alloc_labels()
        else:
            # extract the location names of function args
            _locs = [el[1] for el in args]
            self._push(_locs, True)


    def run_elem_int(self, source, index, target):
        self._alloc_reg(target)
        _aux = self._get_address(source)
        _idx = self._get_value(index)
        _address = _aux + _idx
        self._store_value(target, _address)

    run_elem_float = run_elem_int
    run_elem_char = run_elem_int

    def run_get_int(self, source, target):
        # We never generate this code without * (ref) but we need to define it
        pass

    def run_get_int_(self, source, target, **kwargs):
        # kwargs always contain * (ref), so we ignore it.
        self._store_value(target, self._get_address(source))

    run_get_float_ = run_get_int_
    run_get_char_ = run_get_int_

    def run_jump(self, target):
        self.pc = self.vars[target]

    # load literals into registers
    def run_literal_int(self, value, target):
        self._alloc_reg(target)
        M[self.vars[target]] = value

    run_literal_float = run_literal_int

    def run_literal_char(self, value, target):
        self._alloc_reg(target)
        M[self.vars[target]] = value.strip("'")

    # Load/stores
    def run_load_int(self, varname, target):
        self._alloc_reg(target)
        M[self.vars[target]] = self._get_value(varname)

    run_load_float = run_load_int
    run_load_char = run_load_int
    run_load_bool = run_load_int

    def run_load_int_(self, varname, target, **kwargs):
        _ref = 0
        _dim = 1
        for arg in kwargs.values():
            if arg.isdigit():
                _dim *= int(arg)
            elif arg == '*':
                _ref += 1
        if _ref == 0:
            self._load_multiple_values(_dim, varname, target)
        elif _dim == 1 and _ref == 1:
            self._alloc_reg(target)
            M[self.vars[target]] = M[self._get_value(varname)]

    run_load_float_ = run_load_int_
    run_load_char_ = run_load_int_

    def run_param_int(self, source):
        self.params.append(self.vars[source])

    run_param_float = run_param_int
    run_param_char = run_param_int

    def run_print_string(self, source):
        _res = list(self._get_value((source)))
        for c in _res:
            print(c, end="", flush=True)

    def run_print_int(self, source):
        print(self._get_value(source), end="", flush=True)

    run_print_float = run_print_int
    run_print_char = run_print_int
    run_print_bool = run_print_int

    def run_print_void(self):
        print(flush=True)

    def _read_int(self):
        global inputline
        self._get_input()
        try:
            v1 = inputline[0]
            inputline = inputline[1:]
            try:
                v2 = int(v1)
            except:
                v2 = v1
        except:
            print("Illegal input value.", flush=True)
        return v2

    def run_read_int(self, source):
        _value = self._read_int()
        self._store_value(source, _value)

    def run_read_int_(self, source, **kwargs):
        _value = self._read_int()
        self._store_deref(source, _value)

    def _read_float(self):
        global inputline
        self._get_input()
        try:
            v1 = inputline[0]
            inputline = inputline[1:]
            try:
                v2 = float(v1)
            except:
                v2 = v1
        except:
            print("Illegal input value.", flush=True)
        return v2

    def run_read_float(self, source):
        _value = self._read_float()
        self._store_value(source, _value)

    def run_read_float_(self, source, **kwargs):
        _value = self._read_float()
        self._store_deref(source, _value)

    def run_read_char(self, source):
        global inputline
        self._get_input()
        v1 = inputline[0]
        inputline = inputline[1:]
        self._store_value(source, v1)

    def run_read_char_(self, source, **kwargs):
        global inputline
        self._get_input()
        v1 = inputline[0]
        inputline = inputline[1:]
        self._store_deref(source, v1)

    def run_return_int(self, target):
        self._pop(self.vars[target])

    run_return_float = run_return_int
    run_return_char = run_return_int

    def run_return_void(self):
        self._pop(M[self.vars['%0']])

    def run_store_int(self, source, target):
        self._store_value(target, self._get_value(source))

    run_store_float = run_store_int
    run_store_char = run_store_int
    run_store_bool = run_store_int

    def run_store_int_(self, source, target, **kwargs):
        _ref = 0
        _dim = 1
        for arg in kwargs.values():
            if arg.isdigit():
                _dim *= int(arg)
            elif arg == '*':
                _ref += 1
        if _ref == 0:
            self._store_multiple_values(_dim, target, source)
        elif _dim == 1 and _ref == 1:
            self._store_deref(target, self._get_value(source))

    run_store_float_ = run_store_int_
    run_store_char_ = run_store_int_

    #
    # perform binary, relational & cast operations
    #
    def run_add_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] + M[self.vars[right]]

    def run_sub_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] - M[self.vars[right]]

    def run_mul_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] * M[self.vars[right]]

    def run_mod_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] % M[self.vars[right]]

    def run_div_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] // M[self.vars[right]]

    def run_div_float(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] / M[self.vars[right]]

    # Floating point ops (same as int)
    run_add_float = run_add_int
    run_sub_float = run_sub_int
    run_mul_float = run_mul_int

    # Integer comparisons
    def run_lt_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] < M[self.vars[right]]

    def run_le_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] <= M[self.vars[right]]

    def run_gt_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] > M[self.vars[right]]

    def run_ge_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] >= M[self.vars[right]]

    def run_eq_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] == M[self.vars[right]]

    def run_ne_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] != M[self.vars[right]]

    # Float comparisons
    run_lt_float = run_lt_int
    run_le_float = run_le_int
    run_gt_float = run_gt_int
    run_ge_float = run_ge_int
    run_eq_float = run_eq_int
    run_ne_float = run_ne_int

    # String comparisons
    run_lt_char = run_lt_int
    run_le_char = run_le_int
    run_gt_char = run_gt_int
    run_ge_char = run_ge_int
    run_eq_char = run_eq_int
    run_ne_char = run_ne_int

    # Bool comparisons
    run_eq_bool = run_eq_int
    run_ne_bool = run_ne_int

    def run_and_bool(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] and M[self.vars[right]]

    def run_or_bool(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] or M[self.vars[right]]

    def run_not_bool(self, source, target):
        self._alloc_reg(target)
        M[self.vars[target]] = not self._get_value(source)

    def run_sitofp(self, source, target):
        self._alloc_reg(target)
        M[self.vars[target]] = float(self._get_value(source))

    def run_fptosi(self, source, target):
        self._alloc_reg(target)
        M[self.vars[target]] = int(self._get_value(source))
