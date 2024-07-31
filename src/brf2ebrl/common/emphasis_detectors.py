#  Copyright (c) 2024. American Printing House for the Blind.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Detectors for Emphasis

Currently the regular expressions are built when the module loads.
I think I might change this after it is working so that all
the regular expressions are pre-built  and I might remove the for loops that create them.
"""

import re
from typing import Callable

letter = {
    "\u2828\u2806": ("<em>", "</em>"),
    "\u2818\u2806": ("<strong>", "</strong>"),
    "\u2838\u2806": ('<em class="underline">', "</em>"),
    "\u2808\u2806": ('<em class="script">', "</em>"),
    "\u2808\u283c\u2806": ('<em class="trans1">', "</em>"),
    "\u2818\u283c\u2806": ('<em class="trans2">', "</em>"),
    "\u2838\u283c\u2806": ('<em class="trans3">', "</em>"),
    "\u2810\u283c\u2806": ('<em class="trans4">', "</em>"),
    "\u2828\u283c\u2806": ('<em class="trans5">', "</em>"),
}

letter_re = re.compile(
    "(?:"
    + "|".join([f"({uni})" for uni in letter])
    + ")+([\u2808\u2810\u2820\u2830\u2818\u2828\u2838\u283c]*)([\u2801-\u28ff])"
)


def letter_groups(match):
    """CREATES LETTER SUBSTITUTION"""
    start_tags = "".join(
        [f"{letter[uni][0]}{uni}" for uni in match.groups()[:-2] if uni is not None]
    )
    _end_tags = "".join(
        [letter[uni][1] for uni in match.groups()[:-2] if uni is not None]
    )
    if match.groups()[-2] == "":
        return f"{start_tags}{match.groups()[-1]}{_end_tags}"
    return f"{start_tags}{match.groups()[-2]}{match.groups()[-1]}{_end_tags}"


word = {
    "\u2828\u2802": ("\u2828\u2804", "<em>", "</em>"),  # italic
    "\u2818\u2802": ("\u2818\u2804", "<strong>", "</strong>"),  # bold
    "\u2838\u2802": ("\u2838\u2804", '<em class="underline">', "</em>"),
    "\u2808\u2802": ("\u2808\u2804", '<em class="script">', "</em>"),
    "\u2808\u283c\u2802": ("\u2808\u283c\u2804", '<em class="trans1">', "</em>"),
    "\u2818\u283c\u2802": ("\u2818\u283c\u2804", '<em class="trans2">', "</em>"),
    "\u2838\u283c\u2802": ("\u2838\u283c\u2804", '<em class="trans3">', "</em>"),
    "\u2810\u283c\u2802": ("\u2810\u283c\u2804", '<em class="trans4">', "</em>"),
    "\u2828\u283c\u2802": ("\u2828\u283c\u2804", '<em class="trans5">', "</em>"),
}

_end_tags = r"\u2800|</h[1-6]>|</pre>|</p>|</li>|</t[hd]>|</strong>|</em"
words_re = []
for key, value in word.items():
    end_re = f"{value[0]}|{_end_tags}"
    words_re.append(re.compile(f"({key})(.*?)({end_re})"))


def word_groups(match):
    """create the word substitution"""
    if match.group(3).startswith("<") or match.group(3) == "\u2800":
        return (
                f"{word[match.group(1)][1]}{match.group(1)}"
                + f"{match.group(2)}{word[match.group(1)][2]}{match.group(3)}"
        )
    return (
            f"{word[match.group(1)][1]}{match.group(1)}"
            + f"{match.group(2)}{match.group(3)}{word[match.group(1)][2]}"
    )


phrase = {
    "\u2828\u2836": ("\u2828\u2804", "<em>", "</em>"),  # phrase start
    "\u2818\u2836": ("\u2818\u2804", "<strong>", "</strong>"),  # phrase start
    "\u2838\u2836": ("\u2838\u2804", '<em class="underline">', "</em>"),  # phrase start
    "\u2808\u2836": ("\u2808\u2804", '<em class="script">', "</em>"),  # phrase start
    "\u2808\u283c\u2836": (
        "\u2808\u283c\u2804",
        '<em class="trans1">',
        "</em>",
    ),  # phrase start
    "\u2818\u283c\u2836": (
        "\u2818\u283c\u2804",
        '<em class="trans2">',
        "</em>",
    ),  # phrase start
    "\u2838\u283c\u2836": (
        "\u2838\u283c\u2804",
        '<em class="trans3">',
        "</em>",
    ),  # phrase start
    "\u2810\u283c\u2836": (
        "\u2810\u283c\u2804",
        '<em class="trans4">',
        "</em>",
    ),  # phrase start
    "\u2828\u283c\u2836": (
        "\u2828\u283c\u2804",
        '<em class="trans5">',
        "</em>",
    ),  # phrase start
}

_end_tags = r"</h[1-6]>|</pre>|</p>|</li>|</t[hd]>"
phrases_re = []
for key, value in phrase.items():
    end_re = f"{value[0]}|{_end_tags}"
    phrases_re.append(re.compile(f"({key})(.*?)({end_re})"))


def phrase_groups(match):
    """Create the phrase substitution"""
    if match.group(3).startswith("<"):
        return (
                f"{phrase[match.group(1)][1]}{match.group(1)}"
                + f"{match.group(2)}{phrase[match.group(1)][2]}{match.group(3)}"
        )
    return (
            f"{phrase[match.group(1)][1]}{match.group(1)}"
            + f"{match.group(2)}{match.group(3)}{phrase[match.group(1)][2]}"
    )


def tag_emphasis(text: str, _: Callable[[], None] = lambda: None) -> str:
    # Add letter tags
    text = letter_re.sub(letter_groups, text)
    # add Word tags
    for word_re in words_re:
        text = word_re.sub(word_groups, text)
    # Add Phrase tags
    for phrase_re in phrases_re:
        text = phrase_re.sub(phrase_groups, text)
    return text
