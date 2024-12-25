from argparse import ArgumentParser
from pathlib import Path

import numpy as np
from emout import InpFile, Units
from lark import Lark, Transformer


class Functions(object):
    def __init__(self, inp):
        self._inp = inp

    @property
    def inp(self):
        return self._inp

    def hole(self, z, wx, wy, h, synmetric=""):
        zu = z
        zl = z - h

        xc = self._inp.nx // 2
        xl = xc - wx / 2
        xu = xc + wx / 2

        yc = self._inp.ny // 2
        yl = yc - wy / 2
        yu = yc + wy / 2

        if "x" in synmetric:
            xl -= xc
            xu -= xc

        if "y" in synmetric:
            yl -= yc
            yu -= yc

        text = f"xlrechole(1:2) = {xl}, {xl}\n" + \
               f"xurechole(1:2) = {xu}, {xu}\n" + \
               f"ylrechole(1:2) = {yl}, {yl}\n" + \
               f"yurechole(1:2) = {yu}, {yu}\n" + \
               f"zlrechole(1:2) = {zu-1}, {zl}\n" + \
               f"zurechole(1:2) = {zu}, {zu-1}\n"

        return text


class CallFunctionTransformer(Transformer):
    def __init__(self, inp, functions, unit=None):
        super().__init__()
        self._env = {}
        self._inp = inp
        self._current_group = None
        self._functions = functions
        self._unit = unit

    @property
    def unit(self):
        return self._unit

    def set_current_group(self, group):
        self._current_group = group

    def define(self, tree):
        return f"    {tree[0]} = {tree[1]}\n"

    def define_list(self, tree):
        return f"    {tree[0]} = {tree[1]}\n"
    
    def define_list_with_index(self, tree):
        return f"    {tree[0]}({tree[1]}) = {tree[2]}\n"

    def assignment(self, tree):
        self._env[tree[0]] = tree[1]

        return ""

    def convert_expr(self, tree):
        if len(tree) == 3:
            function_name, arguments, keyword_arguments = tree
        elif len(tree) == 2:
            if isinstance(tree[1], list):
                function_name, arguments, keyword_arguments = tree[0], tree[1], dict()
            else:
                function_name, arguments, keyword_arguments = tree[0], list(), tree[1]
        else:
            function_name, arguments, keyword_arguments = tree[0], list(), dict()

        return getattr(self._functions, function_name)(*arguments, **keyword_arguments)

    def function_name(self, tree):
        return tree[0]

    def arguments(self, tree):
        return list(tree)

    def arg(self, value):
        return value[0]

    def keyword_arguments(self, tree):
        return {k: v for k, v in tree}

    def kwarg(self, tree):
        kwarg_name, value = tree
        return (kwarg_name, value)
    
    def values(self, tree):
        return ', '.join(map(str, tree[0].children))
    
    def array_key(self, tree):
        if hasattr(tree[0], "children"):
            indexes = tree[0].children
        else:
            indexes = [tree[0]]
        return ', '.join(map(str, indexes))

    def slice(self, tree):
        num1, num2 = tree
        return f"{num1}:{num2}"

    def num_add(self, tree):
        return tree[0] + tree[1]

    def num_sub(self, tree):
        return tree[0] - tree[1]

    def num_min(self, tree):
        return min(tree[0], tree[1])

    def num_max(self, tree):
        return max(tree[0], tree[1])

    def num_mul(self, tree):
        return tree[0] * tree[1]

    def num_div(self, tree):
        return tree[0] / tree[1]
    
    def num_if_else(self, tree):
        return tree[0] if tree[1] else tree[2]
    
    def cond_lt(self, tree):
        return tree[0] < tree[1]
    
    def cond_le(self, tree):
        return tree[0] <= tree[1]
    
    def cond_eq(self, tree):
        return tree[0] == tree[1]
    
    def cond_ge(self, tree):
        return tree[0] >= tree[1]
    
    def cond_gt(self, tree):
        return tree[0] > tree[1]
    
    def cond_ne(self, tree):
        return tree[0] != tree[1]

    def factor(self, tree):
        return tree[0]

    def num_cos(self, tree):
        return np.cos(tree[0])

    def num_sin(self, tree):
        return np.sin(tree[0])

    def num_to_int(self, tree):
        return int(tree[0])

    def trans_unit(self, tree):
        if self.unit is None:
            raise ValueError()

        name, value = tree
        return getattr(self.unit, name).trans(value)

    def reverse_unit(self, tree):
        if self.unit is None:
            raise ValueError()

        name, value = tree
        return getattr(self.unit, name).reverse(value)

    def kwarg_name(self, tree):
        return tree[0]

    def number(self, tree):
        return tree[0]

    def variable_element(self, tree):
        return tree[0][tree[1]]

    def variable(self, tree):
        if tree[0] in self._env:
            return self._env[tree[0]]
        else:
            return getattr(self._inp, tree[0])

    def symbol(self, tree):
        return str(tree[0])

    def string(self, tree):
        return str(tree[0])

    def integer(self, tree):
        return int(tree[0].value)

    def float(self, tree):
        return float(tree[0].value)


def parse_args():
    parser = ArgumentParser()

    parser.add_argument("--directory", "-d", default="./")
    parser.add_argument("--preinp_file", "-i", default="plasma.preinp")
    parser.add_argument("--output", "-o", default="plasma.inp")
    parser.add_argument("--verbose", "-v", action='store_true')

    return parser.parse_args()


def main():
    args = parse_args()

    with open(Path(__file__).parent / "preinp_grammer.lark", encoding="utf-8") as f:
        lark_parser = Lark(f.read())

    directory = Path(args.directory)
    preinp_path = directory / args.preinp_file

    inp = InpFile(preinp_path)

    if inp.convkey:
        unit = Units(dx=inp.convkey.dx, to_c=inp.convkey.to_c)
    else:
        unit = None

    functions = Functions(inp)
    inp_transformer = CallFunctionTransformer(inp, functions, unit=unit)

    with open(preinp_path, encoding="utf-8") as f:
        lines = f.readlines()
    
    with open(directory / args.output, "w", encoding='utf-8') as f:
        chained_line = ''
        for line in lines:
            if args.verbose:
                print(line, end="")

            if line.strip().startswith("!!>"):
                line = line.replace('!!>', '')

                if len(line.strip()) == 0:
                    continue

                chained_line += line.replace('\\', '')

                if line.strip().endswith('\\'):
                    continue

                tree = lark_parser.parse(chained_line)
                line = inp_transformer.transform(tree)
                chained_line = ''

                if args.verbose:
                    s = line.replace('\n', '')
                    print(f'==> "{s.replace("    ", "")}"', end="\n")

            f.write(line)

            if line.strip().startswith("&"):
                group = line.strip().replace("&", "")
                inp_transformer.set_current_group(group)

            elif line.strip().startswith("/"):
                inp_transformer.set_current_group(None)



if __name__ == "__main__":
    main()
