# ------------------------------------------------------------------------------
# CodeHawk C Analyzer
# Author: Henny Sipma
# ------------------------------------------------------------------------------
# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Kestrel Technology LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ------------------------------------------------------------------------------


stmt_constructors = {
    'instr': lambda x:CInstrsStmt(*x),
    'if': lambda x:CIfStmt(*x),
    'loop': lambda x:CLoopStmt(*x),
    'break': lambda x:CBreakStmt(*x),
    'return': lambda x:CReturnStmt(*x),
    'goto': lambda x:CGotoStmt(*x),
    'switch': lambda x:CSwitchStmt(*x),
    'continue': lambda x:CContinueStmt(*x)
    }

def get_statement(parent,xnode):
    """Return the appropriate kind of CStmt dependent on the stmt kind."""

    knode = xnode.find('skind')
    tag = knode.get('stag')
    if tag in stmt_constructors:
        return stmt_constructors[tag]((parent,xnode))
    else:
        print('Unknown statement tag found: ' + tag)
        exit(1)

class CBlock(object):

    def __init__(self,parent,xnode):
        self.xnode = xnode            # CFunctionBody or CStmt
        self.cfun = parent.cfun
        self.stmts = {}               # sid -> CStmt

    def iter_stmts(self,f):
        self._initialize_statements()
        for s in self.stmts.values(): f(s)

    def get_statements(self):
        self._initialize_statements()
        return self.stmts.values()

    def get_block_count(self):
        return sum( [ stmt.get_block_count() for stmt in self.get_statements() ])

    def get_stmt_count(self):
        return sum( [ stmt.get_stmt_count() for stmt in self.get_statements() ])

    def get_instr_count(self):
        return sum( [ stmt.get_instr_count() for stmt in self.get_statements() ])

    def get_call_instrs(self):
        return sum( [ stmt.get_call_instrs() for stmt in self.get_statements() ],[])

    def get_strings(self):
        return sum( [ stmt.get_strings() for stmt in self.get_statements() ],[])

    def get_variable_uses(self,vid):
        return sum( [ stmt.get_variable_uses(vid) for stmt in self.get_statements() ])

    def _initialize_statements(self):
        if len(self.stmts) > 0: return
        for s in self.xnode.find('bstmts').findall('stmt'):
            stmtid = int(s.get('sid'))
            self.stmts[stmtid] = get_statement(self,s)


class CFunctionBody(object):
    '''Function implementation.'''

    def __init__(self,cfun,xnode):
        self.cfun = cfun
        self.xnode = xnode
        self.block = CBlock(self,xnode)

    def iter_stmts(self,f): self.block.iter_stmts(f)

    def get_block_count(self): return self.block.get_block_count()

    def get_stmt_count(self): return self.block.get_stmt_count()

    def get_instr_count(self): return self.block.get_instr_count()

    def get_call_instrs(self): return self.block.get_call_instrs()

    def get_strings(self): return self.block.get_strings()

    def get_variable_uses(self,vid): return self.block.get_variable_uses(vid)

    def __str__(self):
        lines = []
        def f(s): lines.append(str(s))
        self.iter_stmts(f)
        return '\n'.join(lines)


class CStmt(object):
    """Function body statement."""

    def __init__(self,parentblock,xnode):
        self.parentblock = parentblock             # containing block CBlock
        self.cfun = self.parentblock.cfun
        self.cdictionary = self.cfun.fdecls.dictionary
        self.xnode = xnode                         # stmt element
        self.sid = int(self.xnode.get('sid'))
        self.kind = self.xnode.find('skind').get('stag')
        self.succs = []
        self.preds = []
        self._initialize_stmt()

    def is_instrs_stmt(self): return False
    def is_if_stmt(self): return False

    def iter_stmts(self,f): pass

    def get_block_count(self): return 1

    def get_stmt_count(self): return 1

    def get_instr_count(self): return 0

    def get_call_instrs(self): return []

    def get_strings(self): return []

    def get_variable_uses(self,vid): return 0

    def _initialize_stmt(self):
        xpreds = self.xnode.find('preds')
        if not xpreds is None:
            if 'r' in xpreds.attrib:
                self.preds = [ int(x) for x in xpreds.get('r').split(',') ]
        xsuccs = self.xnode.find('succs')
        if not xsuccs is None:
            if 'r' in xsuccs.attrib:
                self.succs = [ int(x) for x in xsuccs.get('r').split(',') ]

    def __str__(self):
        lines = []
        def f(s): lines.append('  ' + str(s))
        predecessors = ','.join( [ str(p) for p in self.preds ])
        successors = ','.join( [ str(p) for p in self.succs ])
        lines.append(str(self.sid).rjust(4) +': [' + predecessors + '] ' + 
                         self.kind + ' [' + successors + ']')
        self.iter_stmts(f)        
        return '\n'.join(lines)


class CIfStmt(CStmt):
    """If statement."""

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)
        self.thenblock = CBlock(self,self.xnode.find('skind').find('thenblock'))
        self.elseblock = CBlock(self,self.xnode.find('skind').find('elseblock'))
        self.condition = self.cdictionary.get_exp(int(self.xnode.find('skind').get('iexp')))
        self.location = self.cfun.fdecls.get_location(int(self.xnode.find('skind').get('iloc')))

    def iter_stmts(self,f):
        self.thenblock.iter_stmts(f)
        self.elseblock.iter_stmts(f)

    def get_block_count(self):
        return self.thenblock.get_block_count() + self.elseblock.get_block_count()

    def get_stmt_count(self):
        return self.thenblock.get_stmt_count() + self.elseblock.get_stmt_count()

    def get_instr_count(self):
        return self.thenblock.get_instr_count() + self.elseblock.get_instr_count()

    def get_call_instrs(self):
        return self.thenblock.get_call_instrs() + self.elseblock.get_call_instrs()

    def get_strings(self):
        thenresult = self.thenblock.get_strings()
        elseresult = self.elseblock.get_strings()
        condresult = self.condition.get_strings()
        return thenresult + elseresult + condresult

    def get_variable_uses(self,vid):
        thenresult = self.thenblock.get_variable_uses(vid)
        elseresult = self.elseblock.get_variable_uses(vid)
        condresult = self.condition.get_variable_uses(vid)
        return thenresult + elseresult + condresult

    def is_if_stmt(self): return True

    def __str__(self):
        return (CStmt.__str__(self) + ': ' + str(self.condition))
    

class CLoopStmt(CStmt):
    """Loop statement."""

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)
        self.loopblock = CBlock(self,self.xnode.find('skind').find('block'))

    def iter_stmts(self,f):
        self.loopblock.iter_stmts(f)

    def get_block_count(self): return self.loopblock.get_block_count()

    def get_instr_count(self): return self.loopblock.get_instr_count()

    def get_stmt_count(self): return self.loopblock.get_stmt_count()

    def get_call_instrs(self): return self.loopblock.get_call_instrs()

    def get_strings(self): return self.loopblock.get_strings()

    def get_variable_uses(self,vid):
        return self.loopblock.get_variable_uses(vid)



class CSwitchStmt(CStmt):
    """Switch statement."""

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)
        self.switchblock = CBlock(self,self.xnode.find('skind').find('block'))

    def iter_stmts(self,f):
        self.switchblock.iter_stmts(f)

    def get_block_count(self): return self.switchblock.get_block_count()

    def get_stmt_count(self): return self.switchblock.get_stmt_count()

    def get_instr_count(self): return self.switchblock.get_instr_count()

    def get_call_instrs(self): return self.switchblock.get_call_instrs()

    def get_strings(self): return self.switchblock.get_strings()

    def get_variable_uses(self,vid):
        return self.switchblock.get_variable_uses(vid)


class CBreakStmt(CStmt):
    """Break statement."""

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)


class CContinueStmt(CStmt):
    """Continue statement."""

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)


class CGotoStmt(CStmt):
    """Goto statement."""

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)


class CReturnStmt(CStmt):
    """Return statement."""

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)
        

class CInstrsStmt(CStmt):

    def __init__(self,parentblock,xnode):
        CStmt.__init__(self,parentblock,xnode)
        self.instrs = []
        self._initialize()

    def is_instrs_stmt(self): return True

    def iter_instrs(self,f):
        for i in self.instrs: f(i)

    def get_instr_count(self): return len(self.instrs)

    def get_call_instrs(self):
        return [ i for i in self.instrs if i.is_call() ]

    def get_strings(self):
        return sum([ i.get_strings() for i in self.instrs ],[])

    def get_variable_uses(self,vid):
        return sum([ i.get_variable_uses(vid) for i in self.instrs ])

    def _initialize(self):
        for inode in self.xnode.find('skind').find('instrs').findall('instr'):
            itag = inode.get('itag')
            if itag == 'call':
                self.instrs.append(CCallInstr(self,inode))
            elif itag == 'set':
                self.instrs.append(CAssignInstr(self,inode))
            elif itag == 'asm':
                self.instrs.append(CAsmInstr(self,inode))

    def __str__(self):
        lines = []
        lines.append(CStmt.__str__(self))
        for (n,instr) in enumerate(self.instrs):
            lines.append('  ' + str(n).rjust(4) + ': ' + str(instr))
        return '\n'.join(lines)



class CInstr(object):

    def __init__(self,parentstmt,xnode):
        self.parentstmt = parentstmt
        self.xnode = xnode
        self.cfun = self.parentstmt.cfun

    def is_assign(self): return False
    def is_call(self): return False
    def is_asm(self): return False

    def get_strings(self): return []
    def get_variable_uses(self,vid): return 0


class CCallInstr(CInstr):

    def __init__(self,parentstmt,xnode):
        CInstr.__init__(self,parentstmt,xnode)
        self.args = self.xnode.find('args').findall('exp')        

    def is_call(self): return True

    def get_lhs(self):
        if 'ilval' in self.xnode.attrib:
            return self.parentstmt.cdictionary.get_lval(int(self.xnode.get('ilval')))

    def get_callee(self):
        return self.parentstmt.cdictionary.get_exp(int(self.xnode.get('iexp')))

    def get_arg_exprs(self):
        return [ self.parentstmt.cdictionary.get_exp(int(a.get('iexp'))) for a in self.args ]

    def has_lhs(self): return 'ilval' in self.xnode.attrib

    def get_strings(self):
        return sum([ a.get_strings() for a in self.get_arg_exprs() ],[])

    def get_variable_uses(self,vid):
        lhsuse = self.get_lhs().get_variable_uses(vid) if self.has_lhs() else 0
        arguse = sum([ a.get_variable_uses(vid) for a in self.get_arg_exprs() ])
        calleeuse = self.get_callee().get_variable_uses(vid)
        return lhsuse + arguse +  calleeuse

    def to_dict(self):
        result = { 'base': 'call',
                       'callee': self.get_callee().to_idict(),
                       'args': [ e.to_idict() for e in self.get_arg_exprs() ] }
        if self.has_lhs():
            result['lhs'] = self.get_lhs().to_idict()
        return result

    def __str__(self):
        return '      call ' + str(self.get_callee())


class CAssignInstr(CInstr):

    def __init__(self,parentstmt,xnode):
        CInstr.__init__(self,parentstmt,xnode)

    def is_assign(self): return True

    def get_lhs(self):
        return self.parentstmt.cdictionary.get_lval(int(self.xnode.get('ilval')))

    def get_rhs(self):
        return self.parentstmt.cdictionary.get_exp(int(self.xnode.get('iexp')))

    def get_strings(self): return self.get_rhs().get_strings()

    def get_variable_uses(self,vid):
        lhsuse = self.get_lhs().get_variable_uses(vid)
        rhsuse = self.get_rhs().get_variable_uses(vid)
        return lhsuse + rhsuse

    def __str__(self):
        return ('      assign: ' +  str(self.get_lhs()) + ' := ' + str(self.get_rhs()))


class CAsmInstr(CInstr):

    def __init__(self,parentstmt,xnode):
        CInstr.__init__(self,parentstmt,xnode)
        self.asminputs = []
        self.asmoutputs = []
        self.templates = []
        self._initialize()

    def is_asm(self): return True

    def __str__(self):
        lines = []
        for s in self.templates:
            lines.append(str(s))
        for i in self.asminputs:
            lines.append('  ' + str(i))
        for o in self.asmoutputs:
            lines.append('  ' + str(o))
        return '\n'.join(lines)

    def _initialize(self):
        xinputs = self.xnode.find('asminputs')
        if not xinputs is None:
            for inode in xinputs.findall('asminput'):
                self.asminputs.append(CAsmInput(self,inode))
        xoutputs = self.xnode.find('asmoutputs')
        if not xoutputs is None:
            for onode in xoutputs.findall('asmoutput'):
                self.asmoutputs.append(CAsmOutput(self,onode))
        xtemplates = self.xnode.find('templates')
        if not xtemplates is None:
            for s in xtemplates.get('str-indices').split(','):
                self.templates.append(self.cfun.cfile.declarations.dictionary.get_string(int(s)))


class CAsmOutput(object):

    def __init__(self,parentinstr,xnode):
        self.parentinstr = parentinstr
        self.xnode = xnode
        self.constraint = xnode.get('constraint','none')
        self.lval = self.parentinstr.cfun.cfile.declarations.dictionary.get_lval(int(self.xnode.get('ilval')))

    def __str__(self):
        return (str(self.constraint) + ';  lval: ' + str(self.lval))


class CAsmInput(object):

    def __init__(self,parentinstr,xnode):
        self.parentinstr = parentinstr
        self.xnode = xnode
        self.constraint = xnode.get('constraint','none')
        self.exp = self.parentinstr.cfun.cfile.declarations.dictionary.get_exp(int(self.xnode.get('iexp')))

    def __str__(self):
        return (str(self.constraint) + '; exp: ' + str(self.exp))
