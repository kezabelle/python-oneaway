"""
Generate alternative sequences for strings, where things are "one away" from being the correct
string, to accommodate typos. Give or take, that ought to mean everything has a Levenshtein
distance of 1, I think?

Does this work on long strings? Probably not. The Big-O time is probably horrible in various ways,
but that's OK because I have only short strings to worry about. Famous last words 😅
"""
import enum
import functools
from types import MappingProxyType
from typing import Set, Iterator, Sequence, Callable

__all__ = [
    "dropped_letter",
    "swapped_letter",
    "proximity_typo",
    "multiple",
    "common",
    "mix",
    "aggregate",
    "amalgam",
    "solution",
]


def dropped_letter(value: str, /) -> Iterator[str]:
    """Generates variations on `value` where one of the letters is missing"""
    seen: Set[str] = set()
    for position in range(len(value)):
        char = value[position]
        if char.isspace():
            raise ValueError(
                "Encountered whitespace in `value`",
                "Split your sentence/fragment by whitespace and provide each word "
                "as `value` individually",
            )
        before, after = (
            value[0:position],
            value[position + 1 :],
        )
        new_value = f"{before}{after}"
        if new_value not in seen:
            yield new_value
            seen.add(new_value)


def swapped_letter(value: str, /) -> Iterator[str]:
    """Generates variations on `value` where the letters `ab` have been swapped and appear as `ba`"""
    seen: Set[str] = set()
    for position in range(len(value)):
        prechars = value[0:position]
        thischar = value[position]
        try:
            nextchar = value[position + 1]
        except IndexError:
            break
        if thischar.isspace() or nextchar.isspace():
            raise ValueError(
                "Encountered whitespace in `value`",
                "Split your sentence/fragment by whitespace and provide each word "
                "as `value` individually",
            )
        postchars = value[position + 2 :]
        new_value = f"{prechars}{nextchar}{thischar}{postchars}"
        if new_value not in seen:
            yield new_value
            seen.add(new_value)


def swapped_casing(value: str, /) -> Iterator[str]:
    """
    Generates variations on `value` where the user may have pressed shift/caps-lock incorrectly.
    Generally not useful for my need, as I'm anticipating everything being forcibly cased to one
    or the other...
    Works well enough as a post-processor for `common` or `mix` though, by doing something like::
    >>> import itertools
    >>> import oneaway
    >>> variations = oneaway.common("thing")
    >>> casing_variations = (oneaway.swapped_casing(variant) for variant in variations)
    >>> final_variations = itertools.chain.from_iterable(casing_variations)
    >>> tuple(final_variations)
    """
    seen: Set[str] = set()
    for position, char in enumerate(value):
        if char.isspace():
            raise ValueError(
                f"Encountered whitespace in `value` at position {position}",
                "Split your sentence/fragment by whitespace and provide each word "
                "as `value` individually",
            )
        before, dropped, after = value.partition(char)
        # is swapcase() the same thing? The docs don't actually say that it does _this_ under the
        # hood, but I assume so given `s.swapcase().swapcase()` may not be `s`
        #
        # Cased characters are those with general category property being one
        # of “Lu” (Letter, uppercase), “Ll” (Letter, lowercase), or “Lt” (Letter, titlecase)
        #
        # Note that s.upper().isupper() might be False if s contains uncased characters or
        # if the Unicode category of the resulting character(s) is not “Lu” (Letter, uppercase),
        # but e.g. “Lt” (Letter, titlecase).
        #
        # The lowercasing & uppercasing algorithms used are described in section 3.13 of the
        # Unicode Standard... apparently.
        if dropped.islower():
            replacement = dropped.upper()
        elif dropped.isupper():
            replacement = dropped.lower()
        else:
            raise ValueError(
                "I didn't handle this, because I'm ignorant and monolingual and don't"
                "have a good enough versing in unicode and normalization to have thought"
                "through everything. Sorry.",
                "Please open a ticket providing `value` which failed",
            )
        new_value = f"{before}{replacement}{after}"
        if new_value not in seen:
            yield new_value
            seen.add(new_value)


class Proximities(enum.Enum):
    QWERTY_HORIZONTAL = MappingProxyType(
        {
            # Row 1
            "q": ("w",),
            "w": ("q", "e"),
            "e": ("w", "r"),
            "r": ("e", "t"),
            "t": ("r", "y"),
            "y": ("t", "u"),
            "u": ("y", "i"),
            "i": ("u", "o"),
            "o": ("i", "p"),
            "p": ("o",),
            # Row 2
            "a": ("s",),
            "s": ("a", "d"),
            "d": ("s", "f"),
            "f": ("d", "g"),
            "g": ("f", "h"),
            "h": ("g", "j"),
            "j": ("h", "k"),
            "k": ("j", "l"),
            "l": ("k",),
            # Row 3
            "z": ("x",),
            "x": ("z", "c"),
            "c": ("x", "v"),
            "v": ("c", "b"),
            "b": ("v", "n"),
            "n": ("b", "m"),
            "m": ("n",),
        }
    )
    # The verticalities do not account for things like ortholinear keyboard layouts.
    QWERTY_VERTICAL = MappingProxyType(
        {
            # Row 1
            "q": ("a",),
            "w": ("a", "s"),
            "e": ("s", "d"),
            "r": ("d", "f"),
            "t": ("f", "g"),
            "y": ("g", "h"),
            "u": ("h", "j"),
            "i": ("j", "k"),
            "o": ("k", "l"),
            "p": ("l",),
            # Row 2
            "a": ("q", "w", "z"),
            "s": ("w", "e", "z", "x"),
            "d": ("e", "r", "x", "c"),
            "f": ("r", "t", "c", "v"),
            "g": ("t", "y", "v", "b"),
            "h": ("y", "u", "b", "n"),
            "j": ("u", "i", "n", "m"),
            "k": ("i", "o", "m"),
            "l": ("o", "p"),
            # Row 3
            "z": ("a", "s"),
            "x": ("s", "d"),
            "c": ("d", "f"),
            "v": ("f", "g"),
            "b": ("g", "h"),
            "n": ("h", "j"),
            "m": ("j", "k"),
        }
    )


def proximity_typo(value: str, /, *, layout: Proximities) -> Iterator[str]:
    """Generates variations on `value` where a letter may've been fat-fingered from `g` to `h` etc."""
    seen: Set[str] = set()
    for position, letter in enumerate(value):
        before, dropped, after = value.partition(letter)
        if letter.isspace():
            raise ValueError(
                "Encountered whitespace in `value`",
                "Split your sentence/fragment by whitespace and provide each word "
                "as `value` individually",
            )
        if letter not in layout.value:
            raise ValueError(
                "Unsupported character.",
                "Please open a ticket providing `value` which failed",
                value,
            )
        for replacement_letter in layout.value[letter]:
            new_value = f"{before}{replacement_letter}{after}"
            if new_value not in seen:
                yield new_value
                seen.add(new_value)


horizontal_proximity_typo = functools.partial(
    proximity_typo, layout=Proximities.QWERTY_HORIZONTAL
)
vertical_proximity_typo = functools.partial(
    proximity_typo, layout=Proximities.QWERTY_VERTICAL
)


def multiple(
    value: str,
    handlers: Sequence[Callable[..., Iterator[str]]],
) -> Iterator[str]:
    """Generation of variations on `value` across multiple generator types."""
    seen: Set[str] = set()
    for handler in handlers:
        for typo in handler(value):
            if typo not in seen:
                yield typo
                seen.add(typo)


common = functools.partial(
    multiple,
    handlers=(
        dropped_letter,
        swapped_letter,
        horizontal_proximity_typo,
    ),
)
"""Allows for missing letters, swapped letters, and adjacent horizontal typos."""

mix = functools.partial(
    multiple,
    handlers=(
        dropped_letter,
        swapped_letter,
        horizontal_proximity_typo,
        vertical_proximity_typo,
    ),
)
"""Allow for missing letters, swapped letters, and complete horizontal & vertical typos"""

aggregate = mix
"""Alternative export name for `mix`"""

amalgam = mix
"""Alternative export name for `mix`"""

solution = mix
"""Alternative export name for `mix`"""


if __name__ == "__main__":
    """
    Allow running from the CLI.
    """
    import argparse, sys, os

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "word", help="The word you want to generate off-by-one variants (typos) for."
    )
    args = parser.parse_args()
    if not args.word:
        sys.stderr.write(f"No word provided.{os.linesep}")
        sys.exit(1)

    default_words: set[str] = set()
    if os.path.exists("/usr/share/dict/words"):
        try:
            with open("/usr/share/dict/words", "r") as default_dictionary:
                default_words = {line.strip().lower() for line in default_dictionary}
        except Exception:
            sys.stderr.write(f"Failed to read file /usr/share/dict/words{os.linesep}")

    # The resources in pyspellchecker seem to ultimately *include* typos intentionally
    # so they aren't a good candidate for a separate dictionary 🤷
    # try:
    #     pyspellchecker_words = pkgutil.get_data("spellchecker", "resources/en.json.gz")
    # except FileNotFoundError:
    #     sys.stderr.write(f"Failed to find file pyspellchecker dictionary{os.linesep}")
    # else:
    #     if pyspellchecker_words is not None:
    #         words_counts = json.loads(gzip.decompress(pyspellchecker_words).decode("utf-8"))
    #         default_words.update({line.strip().lower() for line in words_counts.keys()})

    sys.stdout.write(f"# Variants allowed: {os.linesep}")
    sys.stdout.write(f"  - missing letters{os.linesep}")
    sys.stdout.write(f"  - swapped letters{os.linesep}")
    sys.stdout.write(f"  - horizonal typos{os.linesep}")
    sys.stdout.write(
        f"# Dictionary file `/usr/share/dict/words` being used:{os.linesep}"
    )
    if default_words:
        sys.stdout.write(f"  - yes{os.linesep}")
    else:
        sys.stdout.write(f"  - no{os.linesep}")
    sys.stdout.write(f"# Variations for `{args.word}`:{os.linesep}")
    index = 0
    clashes: set[str] = set()
    variations: list[str] = []
    for index, variation in enumerate(common(args.word), start=1):
        # This will allow for "" as a valid variation of "a"
        sys.stdout.write(f'  - "{variation}"')
        if default_words:
            # We only want to show clashes for meaningful ones.
            # e.g. given "a" there's not much point in indicating that "s" is a clash.
            if variation.lower() in default_words and len(variation) > 1:
                clashes.add(variation)
                sys.stdout.write(f" (clashes!)")
        # Don't include empty matches for the regex output.
        if variation:
            variations.append(variation)
        sys.stdout.write(os.linesep)
    sys.stdout.write(f"# Total: {index}{os.linesep}")
    if clashes:
        sys.stdout.write(
            f"# Variations which clash with known words: {len(clashes)}{os.linesep}"
        )
        for clash in clashes:
            sys.stdout.write(f'  - "{clash}"{os.linesep}')
    if variations:

        def _by_length_then_similarity(v: str, original: str) -> tuple[int, bool, bool]:
            return len(v), set(v.lower()) == set(original.lower()), v[0] == original[0]

        by_length_then_similarity = functools.partial(
            _by_length_then_similarity, original=args.word
        )
        alternations = "|".join(
            sorted(
                variations,
                key=by_length_then_similarity,
                reverse=True,
            )
        )
        sys.stdout.write(
            f"# Variations as a (naïve) regular expression alternation:{os.linesep}"
        )
        sys.stdout.write(f"  - ({alternations}){os.linesep}")
    sys.exit(0)
