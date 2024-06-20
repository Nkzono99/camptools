from argparse import ArgumentParser
from pathlib import Path

import numpy as np
from emout import InpFile
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

        self.inp.nml["ptcond"].start_index["xlrechole"] = [1]
        self.inp.nml["ptcond"].start_index["xurechole"] = [1]
        self.inp.nml["ptcond"].start_index["ylrechole"] = [1]
        self.inp.nml["ptcond"].start_index["yurechole"] = [1]
        self.inp.nml["ptcond"].start_index["zlrechole"] = [1]
        self.inp.nml["ptcond"].start_index["zurechole"] = [1]

        self.inp.nml["ptcond"]["xlrechole"] = [xl, xl]
        self.inp.nml["ptcond"]["xurechole"] = [xu, xu]
        self.inp.nml["ptcond"]["ylrechole"] = [yl, yl]
        self.inp.nml["ptcond"]["yurechole"] = [yu, yu]
        self.inp.nml["ptcond"]["zlrechole"] = [zu - 1, zl]
        self.inp.nml["ptcond"]["zurechole"] = [zu, zu - 1]

        return self.inp


class CallFunctionTransformer(Transformer):
    def __init__(self, inp, functions):
        super().__init__()
        self._env = {}
        self._inp = inp
        self._current_group = None
        self._functions = functions

    def set_current_group(self, group):
        self._current_group = group

    def define(self, tree):
        self._inp.nml[self._current_group][tree[0]] = tree[1]

    def define_list(self, tree):
        if self._current_group is None:
            raise Exception(
                f"{tree[0]} is defined outside the any group: {tree[0]} = {tree[1]}"
            )
        self._inp.nml[self._current_group].start_index[tree[0]] = [1]
        self._inp.nml[self._current_group][tree[0]] = tree[1].children

    def assignment(self, tree):
        self._env[tree[0]] = tree[1]

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

    def num_add(self, tree):
        return tree[0] + tree[1]

    def num_sub(self, tree):
        return tree[0] - tree[1]

    def num_mul(self, tree):
        return tree[0] * tree[1]

    def num_div(self, tree):
        return tree[0] / tree[1]

    def factor(self, tree):
        return tree[0]

    def num_cos(self, tree):
        return np.cos(tree[0])

    def num_sin(self, tree):
        return np.sin(tree[0])
    
    def num_to_int(self, tree):
        return int(tree[0])

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

    return parser.parse_args()


def main():
    args = parse_args()

    with open(Path(__file__).parent / "preinp_grammer.lark", encoding="utf-8") as f:
        lark_parser = Lark(f.read())

    directory = Path(args.directory)
    preinp_path = directory / args.preinp_file

    inp = InpFile(preinp_path)

    functions = Functions(inp)
    inp_transformer = CallFunctionTransformer(inp, functions)

    with open(preinp_path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("&"):
                group = line.strip().replace("&", "")
                inp_transformer.set_current_group(group)

            elif line.strip().startswith("/"):
                inp_transformer.set_current_group(None)

            elif line.strip().startswith("!!>"):
                tree = lark_parser.parse(line)
                inp_transformer.transform(tree)

    inp.save(directory / args.output)


if __name__ == "__main__":
    main()
