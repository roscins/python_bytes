"""Find the constructs a piece of Python code uses.

The progression checker (grader/progression.py) compares these with what
levels/concepts.toml allows. This module only reads code: find_needs(code)
returns one Need for each construct the code uses, for example
call:round or Compare:Eq. The grammar of the names is in docs/curriculum.md,
section 6.
"""

import ast
import builtins
import io
import sys

# The blank of a fill-in starter. It is a normal Python name, so it parses.
BLANK = "___"

# ast classes that are never listed in concepts.toml. Each one either
# belongs to a parent that is checked, or is always allowed.
ALWAYS_ALLOWED = (
    ast.Module, ast.Expr,
    ast.expr_context,                    # Load, Store, Del
    ast.operator, ast.unaryop, ast.boolop, ast.cmpop,
    ast.comprehension, ast.alias, ast.withitem, ast.match_case,
)

# Python calls the type of None "NoneType"; concepts.toml says Constant:None.
CONSTANT_NAMES = {"NoneType": "None", "ellipsis": "Ellipsis"}


def builtin_method_names():
    """Return the names of the methods of str, list, dict, set, tuple, int, float and files.

    A call like x.upper() is only checked when the method is one of these.
    Methods of the player's own classes and of library classes are free.
    """
    names = set()
    for kind in (str, list, dict, set, tuple, int, float, io.TextIOWrapper):
        for name in dir(kind):
            if not name.startswith("_"):
                names.add(name)
    return names


BUILTIN_METHODS = builtin_method_names()


class Need:
    """One construct that a piece of code uses.

    Attributes:
        label: how the construct is named for people, for example "call:round".
        options: names that would allow it; any one of them in the allowed
            set is enough. The first option is the label. For example
            ["BinOp:Add", "BinOp"]: listing the bare node allows every operator.
        line: the line of the first use (1 is the first line), or 0 if unknown.
    """

    def __init__(self, options, line):
        """Remember the options and the line; the label is the first option."""
        self.options = list(options)
        self.label = self.options[0]
        self.line = line


def is_main_guard(test):
    """Return True if `test` is the condition __name__ == "__main__"."""
    if not isinstance(test, ast.Compare):
        return False
    if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
        return False
    if len(test.comparators) != 1 or not isinstance(test.comparators[0], ast.Constant):
        return False
    return test.comparators[0].value == "__main__"


def is_dunder(name):
    """Return True for a special name like __init__."""
    return len(name) > 4 and name.startswith("__") and name.endswith("__")


class Scanner(ast.NodeVisitor):
    """Walks a syntax tree and collects a Need for each construct.

    Before the walk, scan() collects the names the code defines itself
    (functions, classes, parameters, imports, assigned names), because
    calling those is not a construct of its own.
    """

    def __init__(self):
        """Start with nothing found and nothing defined."""
        self.needs = []
        self.line = 0
        self.skip = set()           # ids of nodes that need nothing themselves
        self.known_names = {BLANK}  # names that code may call freely
        self.library_names = set()  # imported modules and names: their methods are free
        self.user_methods = set()   # names of functions the code defines
        self.user_functions = set()

    def need(self, *options):
        """Record that the code uses a construct that any of `options` would allow."""
        self.needs.append(Need(options, self.line))

    def scan(self, tree):
        """Collect the defined names, then walk the whole tree."""
        for node in ast.walk(tree):
            self.collect_names(node)
        self.visit(tree)

    def collect_names(self, node):
        """Remember what `node` defines, if it defines a name."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.known_names.add(node.name)
            self.user_methods.add(node.name)
            self.user_functions.add(node.name)
        elif isinstance(node, ast.ClassDef):
            self.known_names.add(node.name)
        elif isinstance(node, ast.arg):
            self.known_names.add(node.arg)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                self.known_names.add(name)
                self.library_names.add(name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                self.known_names.add(name)
                self.library_names.add(name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            # An assigned name is the player's own, unless it hides a built-in.
            if not hasattr(builtins, node.id):
                self.known_names.add(node.id)

    def visit(self, node):
        """Find what `node` needs, then visit its children."""
        if hasattr(node, "lineno"):
            self.line = node.lineno
        if id(node) in self.skip or isinstance(node, ALWAYS_ALLOWED):
            self.generic_visit(node)
            return
        handler = getattr(self, "check_" + type(node).__name__, None)
        if handler is not None:
            handler(node)
        elif type(node).__name__.startswith("Match"):
            self.need("Match")
        else:
            self.need(type(node).__name__)
        self.generic_visit(node)

    # ---- names and literals

    def check_Name(self, node):
        """A name that is read or assigned needs Name (the blank does not)."""
        if node.id != BLANK:
            self.need("Name")

    def check_Constant(self, node):
        """A literal needs Constant:<type>, for example Constant:str."""
        type_name = type(node.value).__name__
        type_name = CONSTANT_NAMES.get(type_name, type_name)
        self.need("Constant:" + type_name, "Constant")

    # ---- operators

    def check_BinOp(self, node):
        """+, -, *, /, //, %, **, |, &, ^ and so on."""
        name = type(node.op).__name__
        self.need("BinOp:" + name, "BinOp")

    def check_UnaryOp(self, node):
        """-x, +x, not x, ~x."""
        name = type(node.op).__name__
        self.need("UnaryOp:" + name, "UnaryOp")

    def check_BoolOp(self, node):
        """and, or."""
        name = type(node.op).__name__
        self.need("BoolOp:" + name, "BoolOp")

    def check_Compare(self, node):
        """Each comparison operator is its own construct.

        `not in` is counted as In and `is not` as Is.
        """
        for operator in node.ops:
            name = type(operator).__name__
            if name == "NotIn":
                name = "In"
            if name == "IsNot":
                name = "Is"
            self.need("Compare:" + name, "Compare")

    def check_Attribute(self, node):
        """x.name needs nothing: calls are checked, plain attributes are free."""

    # ---- calls

    def check_Call(self, node):
        """A call needs call:<name> or method:<name>, unless the code defines it."""
        function = node.func
        if isinstance(function, ast.Name):
            self.skip.add(id(function))
            if function.id not in self.known_names:
                self.need("call:" + function.id)
        elif isinstance(function, ast.Attribute):
            base = function.value
            from_library = isinstance(base, ast.Name) and base.id in self.library_names
            own_method = function.attr in self.user_methods
            if not from_library and not own_method and function.attr in BUILTIN_METHODS:
                self.need("method:" + function.attr)

    def check_keyword(self, node):
        """name=value needs keyword; **mapping needs pattern:varargs."""
        if node.arg is None:
            self.need("pattern:varargs")
        else:
            self.need("keyword")

    def check_Starred(self, node):
        """*items in a call or an assignment."""
        self.need("pattern:varargs")

    # ---- imports

    def check_Import(self, node):
        """import a.b needs import:a.b or import:a."""
        for alias in node.names:
            self.need_import(alias.name, local=False)

    def check_ImportFrom(self, node):
        """from a import b needs import:a; a relative import is a local module."""
        module = node.module or ""
        self.need_import(module, local=node.level > 0)

    def need_import(self, module, local):
        """Record the need for a module; a module outside the standard library is local."""
        top = module.split(".")[0]
        if top not in sys.stdlib_module_names:
            local = True
        options = ["import:" + module]
        parts = module.split(".")
        while len(parts) > 1:
            parts = parts[:-1]
            options.append("import:" + ".".join(parts))
        if local:
            options.append("import:local")
        self.need(*options)

    # ---- definitions

    def check_FunctionDef(self, node):
        """def needs FunctionDef, plus the patterns the definition shows."""
        self.need("FunctionDef")
        self.check_definition(node)
        if node.returns is not None:
            self.need("pattern:annotations")
        if self.calls_itself(node):
            self.need("pattern:recursion")

    def check_ClassDef(self, node):
        """class needs ClassDef, plus base classes, special methods and the like."""
        self.need("ClassDef")
        self.check_definition(node)
        if node.bases or node.keywords:
            self.need("pattern:class_bases")
        for statement in node.body:
            if isinstance(statement, ast.FunctionDef) and is_dunder(statement.name):
                self.need("dunder:" + statement.name)

    def check_definition(self, node):
        """Docstring and decorators, which functions and classes share."""
        if ast.get_docstring(node, clean=False) is not None:
            self.need("pattern:docstring")
        for decorator in node.decorator_list:
            self.check_decorator(decorator)

    def check_decorator(self, decorator):
        """@name needs decorator:name; one the code defines needs pattern:custom_decorator.

        A decorator imported from a module is free: the import is checked.
        """
        self.skip.add(id(decorator))
        target = decorator
        if isinstance(target, ast.Call):
            target = target.func
        if isinstance(target, ast.Name):
            if target.id in self.user_functions:
                self.need("pattern:custom_decorator")
            elif target.id not in self.library_names:
                self.need("decorator:" + target.id)
        elif isinstance(target, ast.Attribute):
            base = target.value
            if not (isinstance(base, ast.Name) and base.id in self.library_names):
                self.need("decorator:" + target.attr)

    def calls_itself(self, function):
        """Return True if `function` calls itself by name, or as self.name()."""
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            called = node.func
            if isinstance(called, ast.Name) and called.id == function.name:
                return True
            if isinstance(called, ast.Attribute) and called.attr == function.name:
                if isinstance(called.value, ast.Name) and called.value.id in ("self", "cls"):
                    return True
        return False

    def check_arguments(self, node):
        """Default values and *args or **kwargs in a parameter list."""
        has_default = bool(node.defaults)
        for default in node.kw_defaults:
            if default is not None:
                has_default = True
        if has_default:
            self.need("pattern:default_args")
        if node.vararg is not None or node.kwarg is not None:
            self.need("pattern:varargs")

    def check_arg(self, node):
        """A parameter with an annotation, like n: int."""
        if node.annotation is not None:
            self.need("pattern:annotations")

    def check_If(self, node):
        """if needs If; if __name__ == "__main__" also needs pattern:main_guard."""
        self.need("If")
        if is_main_guard(node.test):
            self.need("pattern:main_guard")


def find_needs(code):
    """Return a list of Need, one for each construct `code` uses, first use only.

    Raises SyntaxError if the code does not parse.
    """
    tree = ast.parse(code)
    scanner = Scanner()
    scanner.scan(tree)
    needs = []
    seen = set()
    for need in scanner.needs:
        if need.label not in seen:
            seen.add(need.label)
            needs.append(need)
    return needs
