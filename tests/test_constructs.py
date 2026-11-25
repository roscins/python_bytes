"""Check grader/constructs.py: which constructs does a piece of code use?

Each test gives a small program and looks at the labels of the constructs
found in it, like "call:print" or "Compare:Eq".
"""

import unittest

from grader.constructs import find_needs


def labels(code):
    """Return the labels of everything `code` needs, as a sorted list."""
    result = []
    for need in find_needs(code):
        result.append(need.label)
    return sorted(result)


class TestAlwaysAllowed(unittest.TestCase):
    """Things that are never listed in concepts.toml."""

    def test_print_of_a_string(self):
        """print("x") needs only the call and the string constant."""
        self.assertEqual(labels('print("hi")'), ["Constant:str", "call:print"])

    def test_empty_code_needs_nothing(self):
        """An empty program, or only comments, needs nothing."""
        self.assertEqual(labels(""), [])
        self.assertEqual(labels("# just a comment\n"), [])

    def test_called_name_is_not_a_variable(self):
        """The name of a called function does not need Name."""
        self.assertNotIn("Name", labels("print()"))

    def test_other_names_need_name(self):
        """A variable that is read needs Name."""
        self.assertIn("Name", labels("print(x)"))

    def test_blank_is_ignored(self):
        """The ___ blank of a fill-in starter is not a construct."""
        self.assertEqual(labels("print(___)"), ["call:print"])


class TestConstants(unittest.TestCase):
    """Constant:<type> for every kind of literal."""

    def test_each_type(self):
        """int, float, str, bool, None and bytes literals."""
        self.assertIn("Constant:int", labels("x = 1"))
        self.assertIn("Constant:float", labels("x = 1.5"))
        self.assertIn("Constant:str", labels("x = 'a'"))
        self.assertIn("Constant:bool", labels("x = True"))
        self.assertIn("Constant:None", labels("x = None"))
        self.assertIn("Constant:bytes", labels("x = b'a'"))

    def test_options_include_the_bare_node(self):
        """A bare Constant in the allowed set would allow every literal."""
        for need in find_needs("x = 1"):
            if need.label == "Constant:int":
                self.assertEqual(need.options, ["Constant:int", "Constant"])


class TestOperators(unittest.TestCase):
    """Operators are separate constructs."""

    def test_binary_operators(self):
        """Each arithmetic operator has its own label."""
        self.assertIn("BinOp:FloorDiv", labels("x = a // b"))
        self.assertIn("BinOp:Pow", labels("x = a ** b"))
        self.assertIn("BinOp:BitXor", labels("x = a ^ b"))

    def test_unary_and_boolean_operators(self):
        """-x, not x, a and b, a or b."""
        self.assertIn("UnaryOp:USub", labels("x = -a"))
        self.assertIn("UnaryOp:Not", labels("x = not a"))
        self.assertIn("BoolOp:And", labels("x = a and b"))
        self.assertIn("BoolOp:Or", labels("x = a or b"))

    def test_every_comparison_operator_is_found(self):
        """a < b < c needs both Lt operators (counted once)."""
        self.assertEqual(labels("a < b <= c").count("Compare:Lt"), 1)
        self.assertIn("Compare:LtE", labels("a < b <= c"))

    def test_not_in_counts_as_in_and_is_not_as_is(self):
        """Compare:In covers `not in`; Compare:Is covers `is not`."""
        self.assertIn("Compare:In", labels("a not in b"))
        self.assertIn("Compare:Is", labels("a is not b"))

    def test_aug_assign_is_its_own_construct(self):
        """x += 1 needs AugAssign."""
        self.assertIn("AugAssign", labels("x += 1"))


class TestStatements(unittest.TestCase):
    """Statements and expressions that are named after their ast class."""

    def test_statement_names(self):
        """Each statement needs a construct called like its ast class."""
        self.assertIn("While", labels("while x:\n    break"))
        self.assertIn("Break", labels("while x:\n    break"))
        self.assertIn("For", labels("for i in x:\n    continue"))
        self.assertIn("Continue", labels("for i in x:\n    continue"))
        self.assertIn("If", labels("if x:\n    pass"))
        self.assertIn("Pass", labels("if x:\n    pass"))
        self.assertIn("Delete", labels("del x[0]"))
        self.assertIn("Assert", labels("assert x"))
        self.assertIn("Global", labels("def f():\n    global x"))

    def test_expression_names(self):
        """Containers, subscripts, comprehensions, lambda, conditional expressions."""
        self.assertIn("List", labels("x = [1]"))
        self.assertIn("Tuple", labels("x = 1, 2"))
        self.assertIn("Dict", labels("x = {1: 2}"))
        self.assertIn("Set", labels("x = {1}"))
        self.assertIn("Subscript", labels("x[0]"))
        self.assertIn("Slice", labels("x[1:2]"))
        self.assertIn("ListComp", labels("[i for i in x]"))
        self.assertIn("GeneratorExp", labels("(i for i in x)"))
        self.assertIn("Lambda", labels("f = lambda: 1"))
        self.assertIn("IfExp", labels("x = 1 if a else 2"))
        self.assertIn("JoinedStr", labels('f"{x}"'))
        self.assertIn("FormattedValue", labels('f"{x}"'))

    def test_try_and_with(self):
        """try, except and with."""
        code = "try:\n    pass\nexcept ValueError:\n    pass\n"
        self.assertIn("Try", labels(code))
        self.assertIn("ExceptHandler", labels(code))
        self.assertIn("With", labels("with a as b:\n    pass"))

    def test_match_and_its_patterns_need_only_match(self):
        """A match statement needs Match, not each pattern."""
        code = "match x:\n    case 1:\n        pass\n    case _:\n        pass\n"
        result = labels(code)
        self.assertIn("Match", result)
        self.assertNotIn("MatchValue", result)

    def test_unknown_node_is_named_after_its_class(self):
        """Something no level lists, like await, still gets a label."""
        self.assertIn("Await", labels("async def f():\n    await g()"))

    def test_keyword_argument(self):
        """print(end="") needs keyword; f(**x) needs pattern:varargs instead."""
        self.assertIn("keyword", labels('print("a", end="")'))
        self.assertIn("pattern:varargs", labels("f(**x)"))
        self.assertNotIn("keyword", labels("f(**x)"))


class TestCalls(unittest.TestCase):
    """call:<name>, method:<name> and defined names."""

    def test_builtin_call(self):
        """A call of a built-in needs call:<name>."""
        self.assertIn("call:len", labels("len(x)"))

    def test_defined_function_needs_no_call(self):
        """A function the code defines is gated by FunctionDef, not by call:."""
        result = labels("def f():\n    pass\nf()")
        self.assertIn("FunctionDef", result)
        self.assertNotIn("call:f", result)

    def test_parameter_and_imported_name_need_no_call(self):
        """Calling a parameter or a from-imported name is free."""
        self.assertNotIn("call:g", labels("def f(g):\n    g()"))
        self.assertNotIn("call:isclose", labels("from math import isclose\nisclose(1, 2)"))

    def test_assigned_name_needs_no_call(self):
        """A name the code assigns can be called."""
        self.assertNotIn("call:g", labels("g = len\ng()"))

    def test_builtin_method_needs_method(self):
        """Methods of str, list, dict, set and files are gated."""
        self.assertIn("method:upper", labels("x.upper()"))
        self.assertIn("method:append", labels("x.append(1)"))
        self.assertIn("method:items", labels("x.items()"))
        self.assertIn("method:write", labels("f.write('a')"))

    def test_module_function_is_free(self):
        """math.sqrt needs only the import."""
        result = labels("import math\nmath.sqrt(4)")
        self.assertIn("import:math", result)
        self.assertNotIn("method:sqrt", result)

    def test_library_and_unknown_methods_are_free(self):
        """A method that is not a built-in one is not gated."""
        self.assertEqual(labels("x.info()"), ["Name"])

    def test_own_method_with_a_builtin_name_is_free(self):
        """A class that defines pop() can call pop() without method:pop."""
        code = "class S:\n    def pop(self):\n        pass\ns = S()\ns.pop()"
        self.assertNotIn("method:pop", labels(code))

    def test_method_on_imported_name_is_free(self):
        """Path(...).read_text() and Path.cwd() need only the import."""
        code = "from pathlib import Path\nPath.cwd()"
        self.assertNotIn("method:cwd", labels(code))


class TestImports(unittest.TestCase):
    """import:<module>, with prefixes and local modules."""

    def test_plain_import(self):
        """import math needs import:math."""
        self.assertIn("import:math", labels("import math"))

    def test_from_import(self):
        """from math import pi also needs import:math."""
        self.assertIn("import:math", labels("from math import pi"))

    def test_dotted_module_accepts_a_prefix(self):
        """import:unittest is enough for unittest.mock."""
        need = find_needs("import unittest.mock")[0]
        self.assertEqual(need.label, "import:unittest.mock")
        self.assertIn("import:unittest", need.options)

    def test_module_outside_the_standard_library_is_local(self):
        """import robot needs import:local."""
        need = find_needs("import robot")[0]
        self.assertIn("import:local", need.options)

    def test_relative_import_is_local(self):
        """from . import robot needs import:local."""
        need = find_needs("from . import robot")[0]
        self.assertIn("import:local", need.options)


class TestDefinitions(unittest.TestCase):
    """def, class, decorators and the patterns."""

    def test_function_def_and_return(self):
        """def and return."""
        result = labels("def f():\n    return 1")
        self.assertIn("FunctionDef", result)
        self.assertIn("Return", result)

    def test_docstring_pattern(self):
        """A string as the first statement of a function is a docstring."""
        self.assertIn("pattern:docstring", labels('def f():\n    "Doc."\n    return 1'))
        self.assertNotIn("pattern:docstring", labels("def f():\n    return 1"))

    def test_class_docstring_pattern(self):
        """The same for a class."""
        self.assertIn("pattern:docstring", labels('class A:\n    "Doc."'))

    def test_default_args_pattern(self):
        """A default value needs pattern:default_args."""
        self.assertIn("pattern:default_args", labels("def f(a=1):\n    pass"))
        self.assertIn("pattern:default_args", labels("def f(*, a=1):\n    pass"))
        self.assertNotIn("pattern:default_args", labels("def f(a):\n    pass"))

    def test_varargs_pattern(self):
        """*args and **kwargs in a def, and *x in a call."""
        self.assertIn("pattern:varargs", labels("def f(*args):\n    pass"))
        self.assertIn("pattern:varargs", labels("def f(**kw):\n    pass"))
        self.assertIn("pattern:varargs", labels("f(*x)"))

    def test_annotations_pattern(self):
        """Parameter and return annotations."""
        self.assertIn("pattern:annotations", labels("def f(a: int):\n    pass"))
        self.assertIn("pattern:annotations", labels("def f() -> int:\n    pass"))
        self.assertIn("AnnAssign", labels("x: int = 1"))

    def test_recursion_pattern(self):
        """A function that calls itself, also through self."""
        self.assertIn("pattern:recursion", labels("def f(n):\n    return f(n - 1)"))
        code = "class A:\n    def f(self, n):\n        return self.f(n - 1)"
        self.assertIn("pattern:recursion", labels(code))
        self.assertNotIn("pattern:recursion", labels("def f(n):\n    return g(n)"))

    def test_main_guard_pattern(self):
        """if __name__ == "__main__" needs pattern:main_guard as well as If."""
        result = labels('if __name__ == "__main__":\n    pass')
        self.assertIn("pattern:main_guard", result)
        self.assertIn("If", result)
        self.assertNotIn("pattern:main_guard", labels("if x == 1:\n    pass"))

    def test_class_bases_pattern(self):
        """class A(B) needs pattern:class_bases."""
        self.assertIn("pattern:class_bases", labels("class A(B):\n    pass"))
        self.assertNotIn("pattern:class_bases", labels("class A:\n    pass"))

    def test_dunder_methods(self):
        """A special method defined in a class needs dunder:<name>."""
        code = "class A:\n    def __init__(self):\n        pass\n    def go(self):\n        pass"
        result = labels(code)
        self.assertIn("dunder:__init__", result)
        self.assertNotIn("dunder:go", result)

    def test_dunder_name_outside_a_class_is_not_a_method(self):
        """A plain function called __x__ is not a special method."""
        self.assertNotIn("dunder:__x__", labels("def __x__():\n    pass"))

    def test_decorators(self):
        """@property and @x.setter are decorator:<name>."""
        code = "class A:\n    @property\n    def x(self):\n        pass\n    @x.setter\n    def x(self, v):\n        pass"
        result = labels(code)
        self.assertIn("decorator:property", result)
        self.assertIn("decorator:setter", result)

    def test_custom_decorator(self):
        """A decorator defined in the same code needs pattern:custom_decorator."""
        code = "def deco(f):\n    return f\n@deco\ndef g():\n    pass"
        result = labels(code)
        self.assertIn("pattern:custom_decorator", result)
        self.assertNotIn("decorator:deco", result)

    def test_imported_decorator_is_free(self):
        """@wraps(f) from functools needs only the import."""
        code = "from functools import wraps\n@wraps(f)\ndef g():\n    pass"
        result = labels(code)
        self.assertNotIn("decorator:wraps", result)
        self.assertNotIn("call:wraps", result)


class TestNeedDetails(unittest.TestCase):
    """The line number, and each construct listed once."""

    def test_line_number_is_the_first_use(self):
        """A construct used twice is listed once, at its first line."""
        needs = find_needs("x = 1\ny = 2\nprint(x)\nprint(y)")
        print_needs = []
        for need in needs:
            if need.label == "call:print":
                print_needs.append(need)
        self.assertEqual(len(print_needs), 1)
        self.assertEqual(print_needs[0].line, 3)

    def test_label_is_the_first_option(self):
        """The label shown to the author is the most specific option."""
        for need in find_needs("x = a + 1"):
            self.assertEqual(need.label, need.options[0])

    def test_syntax_error_is_raised(self):
        """Code that does not parse raises SyntaxError for the caller to handle."""
        with self.assertRaises(SyntaxError):
            find_needs("print(")


if __name__ == "__main__":
    unittest.main()
