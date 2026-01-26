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

from brf2ebrl import ParserContext
import re

_TAG_RE = re.compile(r"(?s)<[^>]*?>")
_FIX = {"em", "strong"}

def fix_em_strong_xml(s: str) -> str:
    """
    XML-oriented fixer that ONLY repairs <em> and <strong> nesting.

    - Non-em/strong tags are emitted exactly as-is.
    - Text/whitespace is emitted exactly as-is.
    - Only </em>, </strong>, and re-openings of the *original* <em...>/<strong...>
      (including attributes) may be inserted/moved.
    - Stray </em>/<strong> with no matching open are dropped.
    - Self-closing tags are recognized only by '/>' (XML style).
    """

    def tag_name(tag_text: str) -> str | None:
        t = tag_text.strip()
        if not (t.startswith("<") and t.endswith(">")):
            return None
        inner = t[1:-1].strip()
        if not inner:
            return None
        # XML comment / PI / doctype-ish forms:
        if inner.startswith("!--") or inner.startswith("?") or inner.startswith("!"):
            return None
        if inner.startswith("/"):
            inner = inner[1:].lstrip()
        m = re.match(r"([A-Za-z_][A-Za-z0-9:_.-]*)", inner)
        return m.group(1).lower() if m else None

    def is_closing(tag_text: str) -> bool:
        return tag_text.lstrip().startswith("</")

    def is_self_closing(tag_text: str) -> bool:
        return (not is_closing(tag_text)) and tag_text.rstrip().endswith("/>")

    def close_tag(name: str) -> str:
        return f"</{name}>"

    # Tokenize into ("text", ...) and ("tag", ...)
    tokens: list[tuple[str, str]] = []
    pos = 0
    for m in _TAG_RE.finditer(s):
        if m.start() > pos:
            tokens.append(("text", s[pos:m.start()]))
        tokens.append(("tag", m.group(0)))
        pos = m.end()
    if pos < len(s):
        tokens.append(("text", s[pos:]))

    # Stack holds (name, open_text). open_text preserves attributes exactly.
    stack: list[tuple[str, str]] = []
    out: list[str] = []

    def find_last_open(name: str) -> int:
        for i in range(len(stack) - 1, -1, -1):
            if stack[i][0] == name:
                return i
        return -1

    def close_fix_above(open_index: int) -> list[tuple[str, str]]:
        """
        Close any open em/strong above stack[open_index] (boundary close),
        and return those frames in the order they should be reopened.
        """
        to_reopen: list[tuple[str, str]] = []
        for nm, open_txt in reversed(stack[open_index + 1:]):
            if nm in _FIX:
                out.append(close_tag(nm))
                to_reopen.append((nm, open_txt))
        to_reopen.reverse()
        return to_reopen

    def reopen_fix(frames: list[tuple[str, str]]) -> None:
        for _nm, open_txt in frames:
            out.append(open_txt)

    for kind, val in tokens:
        if kind == "text":
            out.append(val)
            continue

        tag_txt = val
        name = tag_name(tag_txt)

        # Pass through comments/PI/doctype unchanged
        if name is None:
            out.append(tag_txt)
            continue

        # Self-closing tag: emit unchanged; do not affect stack
        if is_self_closing(tag_txt):
            out.append(tag_txt)
            continue

        if not is_closing(tag_txt):
            # Opening tag: emit unchanged and push (keeps attributes in open_text)
            out.append(tag_txt)
            stack.append((name, tag_txt))
            continue

        # Closing tag:
        if name in _FIX:
            # If top matches, normal close
            if stack and stack[-1][0] == name:
                out.append(tag_txt)
                stack.pop()
                continue

            # Crossing close:
            idx = find_last_open(name)
            if idx == -1:
                # stray </em>/<strong> -> drop
                continue

            # If anything above idx is non-fix, we cannot touch those tags.
            # Drop this close; it will effectively be handled by boundary closes.
            if any(nm not in _FIX for nm, _ in stack[idx + 1:]):
                continue

            # Otherwise only em/strong above => close/reopen them around this close
            intervening = stack[idx + 1:]
            del stack[idx:]  # remove target + above from bookkeeping

            for nm, _open_txt in reversed(intervening):
                out.append(close_tag(nm))
            out.append(tag_txt)
            for nm, open_txt in intervening:
                out.append(open_txt)
                stack.append((nm, open_txt))
            continue

        # Closing a NON-fix tag:
        # Emit unchanged, but if em/strong are open above its matching open, close/reopen them.
        idx = find_last_open(name)
        if idx != -1:
            to_reopen = close_fix_above(idx)
            out.append(tag_txt)
            del stack[idx:]  # pop the open tag and anything above it (bookkeeping)
            reopen_fix(to_reopen)
            for nm, open_txt in to_reopen:
                stack.append((nm, open_txt))
        else:
            # stray non-fix close: keep as-is (we are not fixing XML structure)
            out.append(tag_txt)

    # End: close any remaining open em/strong (remove this block if you don't want EOF closes)
    for nm, _open_txt in reversed(stack):
        if nm in _FIX:
            out.append(close_tag(nm))

    return "".join(out)


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
    "\u2838\u2802": ("\u2838\u2804", '<em class="underline">', "</em>"),
    "\u2808\u2802": ("\u2808\u2804", '<em class="script">', "</em>"),
    "\u2808\u283c\u2802": ("\u2808\u283c\u2804", '<em class="trans1">', "</em>"),
    "\u2818\u283c\u2802": ("\u2818\u283c\u2804", '<em class="trans2">', "</em>"),
    "\u2838\u283c\u2802": ("\u2838\u283c\u2804", '<em class="trans3">', "</em>"),
    "\u2810\u283c\u2802": ("\u2810\u283c\u2804", '<em class="trans4">', "</em>"),
    "\u2828\u283c\u2802": ("\u2828\u283c\u2804", '<em class="trans5">', "</em>"),
    "\u2818\u2802": ("\u2818\u2804", "<strong>", "</strong>"),  # bold
}



_end_tags = r"(?:</strong>)*?(?:</em>)*?(?:</strong>)*?\u2800|</h[1-6]>|</pre>|</p>|</span>|</li>|</t[hd]>"
words_re = []
for key, value in word.items():
    end_re = f"{value[0]}|{_end_tags}"
    words_re.append(re.compile(f"({key})(.*?)({end_re})"))


def word_groups(match: re.Match[str]) -> str:
    """create the word substitution"""
    if match.group(3) == word[match.group(1)][0]:
        return (
            f"{word[match.group(1)][1]}{match.group(1)}"
            + f"{match.group(2)}{match.group(3)}{word[match.group(1)][2]}"
        )
    return (
            f"{word[match.group(1)][1]}{match.group(1)}"
            + f"{match.group(2)}{word[match.group(1)][2]}@r@{match.group(3)}"
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
#|</strong>|</em.*?>"
phrases_re = []
for key, value in phrase.items():
    end_re = f"{value[0]}(?:</strong>)*(?:</em.*?>)*(?:</strong>)*|{_end_tags}"
    phrases_re.append(re.compile(f"({key})(.*?)({end_re})"))


def phrase_groups(match: re.Match[str]) -> str:
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


def tag_emphasis(text: str, _: ParserContext = ParserContext()) -> str:
    # Add letter tags
    text = letter_re.sub(letter_groups, text)
    # add Word tags
    for word_re in words_re:
        text = word_re.sub(word_groups, text)

    #Word cleanup markers
    text=re.sub(r"(<strong>(?:(?!<em).)*?)(</em>@r@</strong>)",lambda match : f"{match.group(1)}</strong></em>" ,text)
    text = re.sub("@r@","",text)

    # Add Phrase tags
    for phrase_re in phrases_re:
        text = phrase_re.sub(phrase_groups, text)


    
    
    # patterns to fix problems with emphasis. these can be removed after current methodd for detecting emphasis is changed.
    text = re.sub(r"(<strong>[^<]*)(<em[^>]*>)([^<]*)(</strong>)([^<]*)(</em>)", r"\1\2\3</em></strong>\2\5\6", text)
    text = re.sub(r"(<span[^>]*>.*?<em[^>]*>.*?)(</span>)(</em>)", r"\1\3\2", text)
    text = fix_em_strong_xml(text)

    return text
