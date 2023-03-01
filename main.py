import colorama
import inquirer
import pint
import pyperclip

ureg = pint.UnitRegistry()
ureg.default_format = ".4g~P"

# resistance
color_values = {
    # digit values (match multipler as well)
    "black": 0,
    "brown": 1,
    "red": 2,
    "orange": 3,
    "yellow": 4,
    "green": 5,
    "blue": 6,
    "violet": 7,
    "gray": 8,
    "white": 9,
    # magnitude multiplier
    "gold": -1,
    "silver": -2,
}
# tolerance
tolerance_value = {
    "brown": 1,
    "red": 2,
    "green": 0.5,
    "blue": 0.25,
    "violet": 0.1,
    "gray": 0.05,
    "gold": 5,
    "silver": 10,
    "none": 20,
}


def calculate_resistance(colors):
    resistance = 0
    while len(colors) > 2:
        resistance *= 10
        resistance += color_values[colors.pop(0).lower()]
    resistance *= 10 ** color_values[colors.pop(0).lower()]

    tolerance = tolerance_value[colors.pop(0).lower()]
    uncertainty = resistance * tolerance / 100

    # result
    resistance = resistance * ureg.ohm
    uncertainty = uncertainty * ureg.ohm

    # simplify
    resistance = resistance.to_compact()
    uncertainty = uncertainty.to_compact()
    return resistance, uncertainty


class _TrieNode:
    def __init__(self):
        self.children: dict[str, "_TrieNode"] = {}
        self.is_end_of_word: bool = False


class Trie:
    def __init__(self):
        self._root: _TrieNode = _TrieNode()

    def insert(self, word: str) -> None:
        current_node: _TrieNode = self._root
        for letter in word:
            if letter not in current_node.children:
                current_node.children[letter] = _TrieNode()
            current_node = current_node.children[letter]
        current_node.is_end_of_word = True

    def prompt(self, prefix: str) -> list[str]:
        node: _TrieNode = self._search(prefix)
        if not node:
            return []
        return self._get_all_words(node, prefix)

    def _search(self, prefix: str) -> _TrieNode | None:
        current_node: _TrieNode = self._root
        for letter in prefix:
            if letter not in current_node.children:
                return None
            current_node = current_node.children[letter]
        return current_node

    def _get_all_words(self, node: _TrieNode, prefix: str) -> list[str]:
        words: list[str] = []
        if node.is_end_of_word:
            words.append(prefix)
        for letter, child in node.children.items():
            words.extend(self._get_all_words(child, prefix + letter))
        return words


color_tree = Trie()
[color_tree.insert(x) for x in color_values.keys() | tolerance_value.keys()]


def canonicalize_colors(colors: list[str]) -> list[str]:
    for color in colors:
        canonical_color, *rest = color_tree.prompt(color.lower())
        if rest:
            questions = [
                inquirer.List(
                    "color",
                    message=f"Which color did you mean?",
                    choices=[canonical_color, *rest],
                ),
            ]
            canonical_color = inquirer.prompt(questions)["color"]
        yield canonical_color


def print_colors(colors: list[str]) -> None:
    print(
        "R: [ "
        + " ".join(
            {
                "black": colorama.Back.BLACK,
                "brown": colorama.Back.RED,
                "red": colorama.Back.RED,
                "orange": colorama.Back.YELLOW,
                "yellow": colorama.Back.YELLOW,
                "green": colorama.Back.GREEN,
                "blue": colorama.Back.BLUE,
                "violet": colorama.Back.MAGENTA,
                "gray": colorama.Back.WHITE,
                "white": colorama.Back.WHITE,
                "gold": colorama.Back.YELLOW,
                "silver": colorama.Back.WHITE,
                "none": "",
            }.get(color, colorama.Back.WHITE)
            + " "
            + color[0]
            + " "
            + colorama.Style.RESET_ALL
            for color in colors
        )
        + " ]"
    )


def bold(text: str) -> str:
    return colorama.Style.BRIGHT + text + colorama.Style.RESET_ALL


def main():
    colorama.init()

    # repl
    while True:
        try:
            single()
            print()
        except KeyboardInterrupt:
            break


def single():
    while True:
        try:
            colors = list(canonicalize_colors(input("Enter colors: ").split()))
            break
        except ValueError:
            print(bold("Invalid color"))

    print_colors(colors)
    try:
        resistance, uncertainty = calculate_resistance(colors)
    except KeyError:
        print(bold("Invalid tolerance"))
        return
    except IndexError:
        print(bold("Insufficient colors"))
        return

    for k, v in {
        "Resistance": resistance,
        "Uncertainty": uncertainty,
        "Interval": f"{resistance - uncertainty} to {resistance + uncertainty}",
    }.items():
        print(f"{str(bold(k)):20}: {v}")
        if k == "Interval":
            pyperclip.copy(str(v))


if __name__ == "__main__":
    main()
