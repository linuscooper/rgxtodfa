from dataclasses import dataclass
from typing import Optional, Tuple


# Base class
class Regex:
    pass


@dataclass(frozen=True)
class EmptySet(Regex):
    pass


@dataclass(frozen=True)
class Epsilon(Regex):
    pass


@dataclass(frozen=True)
class Literal(Regex):
    char: str


@dataclass(frozen=True)
class UnionExpr(Regex):
    left: Regex
    right: Regex


@dataclass(frozen=True)
class Concat(Regex):
    left: Regex
    right: Regex


@dataclass(frozen=True)
class Star(Regex):
    expr: Regex


class Node:
    def __init__(self, unique_id: int, r: Regex, is_accepting: bool = False):
        self.unique_id = unique_id
        self.r = r
        self.is_accepting = is_accepting
        self.transitions = {}

    def add_transition(self, char: str, state):
        self.transitions[char] = state  # overwrite if already exists

    def __repr__(self):
        return f"State({self.unique_id} with Regex {self.r}, {'accepting' if self.is_accepting else 'non-accepting'})"


def nullable(r: Regex) -> bool:
    if isinstance(r, EmptySet):
        return False
    elif isinstance(r, Epsilon):
        return True
    elif isinstance(r, Literal):
        return False
    elif isinstance(r, UnionExpr):
        return nullable(r.left) or nullable(r.right)
    elif isinstance(r, Concat):
        return nullable(r.left) and nullable(r.right)
    elif isinstance(r, Star):
        return True
    else:
        raise ValueError("Unknown regex type")


def simplify(r: Regex) -> Regex:
    if isinstance(r, UnionExpr):
        def flatten(expr):
            if isinstance(expr, UnionExpr):
                return flatten(expr.left) + flatten(expr.right)
            else:
                return [simplify(expr)]

        parts = flatten(r)
        seen = {}
        for p in parts:
            if not isinstance(p, EmptySet):
                seen[repr(p)] = p

        if not seen:
            return EmptySet()
        elif len(seen) == 1:
            return next(iter(seen.values()))
        else:
            parts_list = list(seen.values())
            result = parts_list[0]
            for p in parts_list[1:]:
                result = UnionExpr(result, p)
            return result

    elif isinstance(r, Concat):
        left = simplify(r.left)
        right = simplify(r.right)

        if isinstance(left, EmptySet) or isinstance(right, EmptySet):
            return EmptySet()
        elif isinstance(left, Epsilon):
            return right
        elif isinstance(right, Epsilon):
            return left
        else:
            return Concat(left, right)

    elif isinstance(r, Star):
        inner = simplify(r.expr)
        if isinstance(inner, EmptySet) or isinstance(inner, Epsilon):
            return Epsilon()
        else:
            return Star(inner)

    else:
        return r  #base cases


def derivative(r: Regex, a: str) -> Regex:
    if isinstance(r, EmptySet) or isinstance(r, Epsilon):
        return EmptySet()
    elif isinstance(r, Literal):
        return Epsilon() if r.char == a else EmptySet()
    elif isinstance(r, UnionExpr):
        return simplify(UnionExpr(
            derivative(r.left, a),
            derivative(r.right, a)
        ))
    elif isinstance(r, Concat):
        if nullable(r.left):
            return simplify(UnionExpr(
                Concat(derivative(r.left, a), r.right),
                derivative(r.right, a)
            ))
        else:
            return simplify(Concat(derivative(r.left, a), r.right))
    elif isinstance(r, Star):
        if isinstance(r.expr, Literal):
            if r.expr.char == a:
                return r
        return simplify(Concat(derivative(r.expr, a), r))
    else:
        raise ValueError("Unknown regex type")


def find_literals(r: Regex) -> set[str]:
    if isinstance(r, EmptySet) or isinstance(r, Epsilon):
        return set()
    elif isinstance(r, Literal):
        return {r.char}
    elif isinstance(r, UnionExpr) or isinstance(r, Concat):
        return find_literals(r.left) | find_literals(r.right)
    elif isinstance(r, Star):
        return find_literals(r.expr)
    else:
        raise ValueError("Unknown regex type")


def generate_nodes(r: Regex) -> set[Node]:
    if isinstance(r, EmptySet) or isinstance(r, Epsilon):
        raise ValueError("No valid regex given")

    literals = set(find_literals(r))
    regex_to_node = {}
    nodes = set()
    node_id = 0

    def get_or_create_node(regex: Regex) -> Node:
        nonlocal node_id
        key = repr(regex)  #unique identifier
        if key not in regex_to_node:
            accepting = nullable(regex)
            node = Node(node_id, regex, is_accepting=accepting)
            regex_to_node[key] = node
            nodes.add(node)
            node_id += 1
        return regex_to_node[key]

    start_node = get_or_create_node(r)

    to_process = [start_node]

    while to_process:
        current = to_process.pop()
        for literal in literals:
            next_regex = derivative(current.r, literal)
            next_node = get_or_create_node(next_regex)

            if literal not in current.transitions:
                current.add_transition(literal, next_node)

                if next_node not in to_process:
                    to_process.append(next_node)

    return nodes


def dfa_to_dot(nodes: set[Node], start_regex: Regex):
    dot_str = "digraph DFA {\n"
    dot_str += ("    ran"
                "kdir=LR;\n")
    dot_str += "    node [shape = circle];\n"

    start_node: Optional[Node] = None
    for node in nodes:
        if node.r == start_regex:
            start_node = node
            break
    if start_node is None:
        raise ValueError("Could not find start node")

    #start arrow
    dot_str += f"    start [shape = point];\n"
    dot_str += f"    start -> {start_node.unique_id};\n"

    for node in nodes:
        if node.is_accepting:
            dot_str += f"    {node.unique_id} [shape = doublecircle];\n"

    for node in nodes:
        for char, target in node.transitions.items():
            dot_str += f'    {node.unique_id} -> {target.unique_id} [label="{char}"];\n'

    dot_str += "}"

    return dot_str


def parse_regex(regex_str: str) -> Regex:
    if not regex_str:
        return Epsilon()

    pos, result = parse_union(regex_str, 0)

    if pos != len(regex_str):
        raise ValueError(f"Unexpected character at position {pos}: {regex_str[pos]}")

    return result


def parse_union(regex_str: str, pos: int) -> Tuple[int, Regex]:
    pos, left = parse_concat(regex_str, pos)

    if pos < len(regex_str) and regex_str[pos] == '|':
        pos, right = parse_union(regex_str, pos + 1)
        return pos, UnionExpr(left, right)

    return pos, left


def parse_concat(regex_str: str, pos: int) -> Tuple[int, Regex]:
    pos, left = parse_basic(regex_str, pos)

    # end, or ), or |
    if pos >= len(regex_str) or regex_str[pos] in ')|':
        return pos, left

    #concatenation
    pos, right = parse_concat(regex_str, pos)
    return pos, Concat(left, right)


def parse_basic(regex_str: str, pos: int) -> Tuple[int, Regex]:
    if pos >= len(regex_str):
        return pos, Epsilon()

    char = regex_str[pos]

    if char == '(':
        #parenthesized expression
        pos, expr = parse_union(regex_str, pos + 1)

        if pos >= len(regex_str) or regex_str[pos] != ')':
            raise ValueError(f"Expected closing parenthesis at position {pos}")

        pos += 1  # Skip ')'
    elif char in ')|*':
        raise ValueError(f"Unexpected character at position {pos}: {char}")
    else:
        #literal character
        expr = Literal(char)
        pos += 1

    #Kleene star
    if pos < len(regex_str) and regex_str[pos] == '*':
        expr = Star(expr)
        pos += 1

    return pos, expr

def run_dfa(start_node: Node, input_str: str) -> bool:
    current = start_node
    for c in input_str:
        if c not in current.transitions:
            return False
        current = current.transitions[c]
    return current.is_accepting


def get_start_node(regex: Regex) -> Node:
    nodes = generate_nodes(regex)
    return next(n for n in nodes if repr(n.r) == repr(regex))
