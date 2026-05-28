# ek_vitki.py
# Convert Latin text → Elder Futhark runes (Unicode) + numeric ætt:pos scheme + ASCII branch art
# For Tomas: Inspiration from kvistrúnar / branch runes

import re
import sys
import unicodedata

# ────────────────────────────────────────────────
# Data: Elder Futhark map and ambiguous letters
# ────────────────────────────────────────────────

# Unified Elder Futhark map: letter → (rune, ætt, position)
# Ordered by Elder Futhark sequence: 3 ættir of 8 runes each
ELDER_FUTHARK = {
    # First ætt (Freyr's ætt)
    'f': ('ᚠ', 1, 1),  # Fehu - cattle, wealth
    'u': ('ᚢ', 1, 2),  # Uruz - aurochs, strength
    'th': ('ᚦ', 1, 3),  # Thurisaz - giant, thorn
    'a': ('ᚨ', 1, 4),  # Ansuz - god, mouth
    'r': ('ᚱ', 1, 5),  # Raidho - journey, wheel
    'k': ('ᚲ', 1, 6),  # Kenaz - torch, knowledge
    'g': ('ᚷ', 1, 7),  # Gebo - gift, partnership
    'w': ('ᚹ', 1, 8),  # Wunjo - joy, pleasure
    # Second ætt (Heimdall's ætt)
    'h': ('ᚺ', 2, 1),  # Hagalaz - hail, disruption
    'n': ('ᚾ', 2, 2),  # Naudiz - need, constraint
    'i': ('ᛁ', 2, 3),  # Isa - ice, stillness
    'j': ('ᛃ', 2, 4),  # Jera - year, harvest
    'e': ('ᛖ', 2, 5),  # Eihwaz - yew, endurance
    'p': ('ᛈ', 2, 6),  # Perthro - fate, mystery
    'z': ('ᛉ', 2, 7),  # Algiz - elk, protection
    's': ('ᛊ', 2, 8),  # Sowilo - sun, victory
    # Third ætt (Tyr's ætt)
    't': ('ᛏ', 3, 1),  # Tiwaz - Tyr, justice
    'b': ('ᛒ', 3, 2),  # Berkano - birch, growth
    'm': ('ᛗ', 3, 4),  # Mannaz - man, humanity
    'l': ('ᛚ', 3, 5),  # Laguz - water, flow
    'ng': ('ᛜ', 3, 6), # 'ŋ' Ingwaz - Ing, fertility
    'd': ('ᛞ', 3, 7),  # Dagaz - day, breakthrough
    'o': ('ᛟ', 3, 8),  # Othala - heritage, homeland
    # Old Norse characters
    'þ': ('ᚦ', 1, 3),  # þ→th (Old Norse thorn)
    'ð': ('ᚦ', 1, 3),  # ð→th (Old Norse eth)
    # Special characters
    ' ': (' ', None, None),
    '.': (' ', None, None),
    ',': (' ', None, None),
}

# Ambiguous Latin letters that can map to different runes depending on phonetic context
AMBIGUOUS_LETTERS = {
    'v': {
        'prompt': "sound like 'F' (as in 'five') or 'W' (as in 'van')?",
        'choices': {
            'f': ('ᚠ', 1, 1),  # Fehu
            'w': ('ᚹ', 1, 8),  # Wunjo
        }
    },
    'c': {
        'prompt': "sound like 'K' (as in 'cat') or 'S' (as in 'city')?",
        'choices': {
            'k': ('ᚲ', 1, 6),  # Kenaz
            's': ('ᛊ', 2, 8),  # Sowilo
        }
    },
    'y': {
        'prompt': "sound like 'I' (as in 'myth'), 'J' (as in 'yes'), or 'E' (as in 'happy')?",
        'choices': {
            'i': ('ᛁ', 2, 3),  # Isa
            'j': ('ᛃ', 2, 4),  # Jera
            'e': ('ᛖ', 2, 5),  # Eihwaz
        }
    },
    'q': {
        'prompt': "sounds like 'K' or 'KW'?",
        'choices': {
            'k': ('ᚲ', 1, 6),  # Kenaz (for 'q' alone)
            'kw': ('ᚲᚹ', None, None),  # Kenaz + Wunjo (returns as special case)
        }
    },
    'x': {
        'prompt': "sound like 'KS' or 'Z'?",
        'choices': {
            'ks': ('ᚲᛊ', None, None),  # Kenaz + Sowilo
            'z': ('ᛉ', 2, 7),  # Algiz
        }
    },
}

# ────────────────────────────────────────────────
# Printable output defaults (override per-call or change here)
# ────────────────────────────────────────────────
PRINT_LONG_MM = 20         # Height of long (ætt) strokes
PRINT_SHORT_MM = 10        # Height of short (position) strokes
PRINT_STROKE_W_MM = 0.1    # Width of each stroke
PRINT_GAP_MM = 1.3         # Gap between strokes (ignored if max_width is set)
PRINT_MAX_WIDTH_MM = None   # If set, gap is auto-computed to fill this width
PRINT_WORD_GAP_MM = 0      # Extra gap at word boundaries (0 = no separator)
PRINT_MARGIN_MM = 2        # Margin around the drawing (SVG only)

# PDF-specific layout
PRINT_LANDSCAPE = True      # PDF: landscape orientation by default
PRINT_PAGE_MARGIN_MM = 10   # PDF: page margin (mm) on all four sides
PRINT_LINE_GAP_MM = 10      # PDF: vertical gap between lines when wrapping

# Paper sizes in mm (width, height) — always stored as portrait
PAPER_SIZES = {
    'a4': (210, 297),
    'a3': (297, 420),
    'a5': (148, 210),
    'letter': (215.9, 279.4),
    'legal': (215.9, 355.6),
}
PRINT_PAPER = 'a4'         # Default paper size


# ────────────────────────────────────────────────
# Utility functions
# ────────────────────────────────────────────────

def _is_prime(n):
    """Simple trial-division primality test."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def normalize_whitespace(text):
    """
    Normalizes all whitespace (spaces, tabs, multiple spaces) to single spaces.
    """
    return re.sub(r'\s+', ' ', text)


def remove_numbers(text):
    """
    Removes all numeric digits from text.
    """
    return re.sub(r'\d', '', text)


def normalize_special_letters(text):
    """
    Strips diacritics / accented characters to their ASCII base form.
    E.g. á→a, č→c, ü→u, ñ→n, etc.
    Preserves Old Norse þ and ð (they have direct rune mappings).
    Also maps ß→ss.
    """
    result = []
    for ch in text:
        if ch in ('þ', 'Þ', 'ð', 'Ð'):
            result.append(ch.lower())
        elif ch == 'ß':
            result.append('ss')
        else:
            # Decompose to base + combining marks, then strip combining marks
            nfkd = unicodedata.normalize('NFKD', ch)
            stripped = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
            result.append(stripped)
    return ''.join(result)


# Utility: Sum all numbers in ætt:pos string pairs (ignoring dashes)
def sum_aett_pos_string_numbers(s):
    """
    Given a string like '2:2 1:4 2:8 - 2:2', sum all numbers in the pairs (e.g. 2+2+1+4+2+8+2+2).
    Ignores dashes and non-pair tokens.
    Returns the total sum as int.
    """
    total = 0
    for token in s.replace('-', ' ').split():
        if ':' in token:
            try:
                a, p = token.split(':')
                total += int(a) + int(p)
            except Exception:
                pass
    return total


def sum_runic_text_value(aett_pos_data):
    """
    Sums the values of the runes in the finished runic text.
    Value is (aett-1)*8 + position_in_aett for each rune.
    Ignores spaces and non-rune items.
    """
    total = 0
    for item in aett_pos_data:
        if isinstance(item, tuple) and len(item) == 2:
            aett, pos = item
            if aett is not None and pos is not None:
                total += (aett - 1) * 8 + pos
    return total


def decompose_rune_sum(sum_value):
    """
    Returns a sorted list of divisors of the rune sum according to magical importance in runic numerology.
    Only numbers are returned.
    Order: [9, 3, 6, 12, 24, 4, 8] (from most to least important).
    """
    if sum_value <= 0:
        return []

    # Order of importance (from strongest)
    candidates = [9, 3, 6, 12, 24, 4, 8]
    result = []
    for divisor in candidates:
        if sum_value % divisor == 0:
            result.append(divisor)
    return result


def print_divisor_descriptions(divisors, rune_sum=0):
    """
    Prints runic numerology meanings for each magical divisor.
    If the rune sum is prime, celebrates that instead.
    """
    descriptions = {
        3: "3 — Three ættir, the sacred triad, completeness of the Futhark structure",
        4: "4 — Four directions, stability, the earthly plane",
        6: "6 — Harmony, balance of opposites (2×3)",
        8: "8 — Eight runes per ætt, the octave of runic cycles",
        9: "9 — The most sacred number in Norse cosmology: 9 worlds, 9 nights of Odin",
        12: "12 — Cosmic order (12 halls of Asgard, yearly cycle)",
        24: "24 — The total number of Elder Futhark runes, full completion",
    }
    if not divisors:
        if rune_sum > 0 and _is_prime(rune_sum):
            print(f"\n  {rune_sum} is a PRIME number — indivisible, a force unto itself.")
        else:
            print("\nNo magical divisors found for this rune sum.")
        return
    print("\nMagical divisors of the rune sum:")
    for d in divisors:
        if d in descriptions:
            print(f"  {descriptions[d]}")


# ────────────────────────────────────────────────
# Interactive prompting for ambiguous letters
# ────────────────────────────────────────────────

def prompt_for_substitution(letter, word, position, substitution_cache=None):
    """
    Prompts user to choose phonetic substitution for ambiguous letters.
    Uses cache to avoid asking the same question twice.
    """
    if letter not in AMBIGUOUS_LETTERS:
        return None

    # Check cache first
    if substitution_cache is not None and (position, letter) in substitution_cache:
        return substitution_cache[(position, letter)]

    config = AMBIGUOUS_LETTERS[letter]
    context = f"'{word}'" if word else "this word"

    print(f"\nIn {context}, letter '{letter.upper()}' at position {position}:")
    print(f"Does it {config['prompt']}")

    choices_list = list(config['choices'].keys())
    print(f"Options: {', '.join(choices_list)}")

    while True:
        choice = input(f"Choose [{'/'.join(choices_list)}]: ").strip().lower()
        if choice in config['choices']:
            result = config['choices'][choice]
            # Store in cache
            if substitution_cache is not None:
                substitution_cache[(position, letter)] = result
            return result
        print(f"Invalid choice. Please enter one of: {', '.join(choices_list)}")


def default_substitution(letter, position, substitution_cache=None):
    """
    Returns the first (default) choice for an ambiguous letter without prompting.
    Used in non-interactive (CLI) mode.
    """
    if letter not in AMBIGUOUS_LETTERS:
        return None

    # Check cache first
    if substitution_cache is not None and (position, letter) in substitution_cache:
        return substitution_cache[(position, letter)]

    config = AMBIGUOUS_LETTERS[letter]
    choices_list = list(config['choices'].keys())
    result = config['choices'][choices_list[0]]

    # Store in cache
    if substitution_cache is not None:
        substitution_cache[(position, letter)] = result
    return result


def get_substituted_text(text, substitution_cache):
    """
    Returns the text with substitutions applied, showing phonetic choices.
    Example: 'victory' with v→w becomes 'wictory'
    """
    text_lower = text.lower()
    result = []
    i = 0

    while i < len(text_lower):
        # Check for two-character sequences first
        if i + 1 < len(text_lower) and text_lower[i:i+2] in ELDER_FUTHARK:
            result.append(text_lower[i:i+2])
            i += 2
        elif text_lower[i] in ELDER_FUTHARK:
            result.append(text_lower[i])
            i += 1
        elif (i + 1, text_lower[i]) in substitution_cache:
            # Use the cached substitution
            choice = substitution_cache[(i + 1, text_lower[i])]
            # Get the substitution key (e.g., 'f', 'w', 'k', etc.)
            for key, val in AMBIGUOUS_LETTERS[text_lower[i]]['choices'].items():
                if val == choice:
                    result.append(key if len(key) == 1 else key)  # Use the choice letter
                    break
            i += 1
        else:
            result.append(text_lower[i])
            i += 1

    return ''.join(result)


# ────────────────────────────────────────────────
# Core translation functions
# ────────────────────────────────────────────────

def latin_to_elder_futhark(text, interactive=True, word_context="", substitution_cache=None):
    text_lower = text.lower()
    result = []
    i = 0

    while i < len(text_lower):
        # Check for two-character sequences first
        if i + 1 < len(text_lower) and text_lower[i:i+2] in ELDER_FUTHARK:
            result.append(ELDER_FUTHARK[text_lower[i:i+2]][0])
            i += 2
        elif text_lower[i] in ELDER_FUTHARK:
            result.append(ELDER_FUTHARK[text_lower[i]][0])
            i += 1
        elif text_lower[i] in AMBIGUOUS_LETTERS:
            # Extract the current word containing this letter
            word_start = i
            while word_start > 0 and text_lower[word_start - 1] not in ' \t\n\r':
                word_start -= 1
            word_end = i
            while word_end < len(text_lower) and text_lower[word_end] not in ' \t\n\r':
                word_end += 1
            current_word = text_lower[word_start:word_end]

            if interactive:
                # Prompt user for phonetic choice
                choice = prompt_for_substitution(text_lower[i], current_word, i + 1, substitution_cache)
            else:
                # Use default (first) choice
                choice = default_substitution(text_lower[i], i + 1, substitution_cache)

            if choice:
                rune_str = choice[0]
                result.append(rune_str)
            else:
                result.append(text_lower[i])
            i += 1
        else:
            result.append(text_lower[i])
            i += 1

    return ''.join(result)


def to_aett_pos(text, interactive=True, word_context="", substitution_cache=None):
    """
    Converts text to structured data with numeric ætt:position pairs.
    Returns list of tuples: [(aett, pos), 'SPACE', (aett, pos), ...]
    SPACE markers indicate word boundaries.
    """
    text_lower = text.lower()
    result = []
    i = 0

    while i < len(text_lower):
        # Check for space/whitespace
        if text_lower[i] in ' \t\n\r':
            # Add space marker if not already at boundary
            if result and result[-1] != 'SPACE':
                result.append('SPACE')
            i += 1
        # Check for two-character sequences first
        elif i + 1 < len(text_lower) and text_lower[i:i+2] in ELDER_FUTHARK:
            rune, aett, pos = ELDER_FUTHARK[text_lower[i:i+2]]
            if aett is not None and pos is not None:
                result.append((aett, pos))
            i += 2
        elif text_lower[i] in ELDER_FUTHARK:
            rune, aett, pos = ELDER_FUTHARK[text_lower[i]]
            if aett is not None and pos is not None:
                result.append((aett, pos))
            i += 1
        elif text_lower[i] in AMBIGUOUS_LETTERS:
            # Extract the current word containing this letter
            word_start = i
            while word_start > 0 and text_lower[word_start - 1] not in ' \t\n\r':
                word_start -= 1
            word_end = i
            while word_end < len(text_lower) and text_lower[word_end] not in ' \t\n\r':
                word_end += 1
            current_word = text_lower[word_start:word_end]

            if interactive:
                # Prompt user for phonetic choice (uses cache)
                choice = prompt_for_substitution(text_lower[i], current_word, i + 1, substitution_cache)
            else:
                # Use default (first) choice
                choice = default_substitution(text_lower[i], i + 1, substitution_cache)

            if choice and choice[1] is not None and choice[2] is not None:
                result.append((choice[1], choice[2]))
            # For multi-rune choices like 'kw', we need to handle differently
            elif choice and choice[0] and len(choice[0]) > 1:
                # Multi-character rune sequence - extract positions
                for rune_char in choice[0]:
                    # Find this rune in ELDER_FUTHARK
                    for key, val in ELDER_FUTHARK.items():
                        if val[0] == rune_char and val[1] is not None:
                            result.append((val[1], val[2]))
                            break
            i += 1
        else:
            i += 1

    return result


# ────────────────────────────────────────────────
# Visual representations
# ────────────────────────────────────────────────

def generate_branch_ascii(aett_pos_data):
    """
    Generates ASCII art for branch runes (kvistrúnar).
    - 8 lines tall (positions 1-8 in an ætt)
    - Left branches encode ætt number (number of \\ from top)
    - Right branches encode position number (number of / from top)
    - Example: 3:8 shows \\ on first 3 rows (left), / on all 8 rows (right)
    - Words alternate direction (swap left/right branches)

    Args:
        aett_pos_data: List of tuples [(aett, pos), 'SPACE', ...]
    """
    if not aett_pos_data:
        return ""

    # Create 8 rows (for positions 8 down to 1)
    rows = [[] for _ in range(8)]

    word_index = 0  # Track which word we're in

    for item in aett_pos_data:
        if item == 'SPACE':
            # Word boundary - increment word counter
            word_index += 1
            # Add visual separator between words
            for row in rows:
                row.append("  ")  # Double space for word boundary
            continue

        aett, pos = item

        # Determine if we swap left/right based on word
        swap = word_index % 2 == 1

        # For each row (position 1 to 8 from top to bottom)
        for row_idx in range(8):
            row_position = row_idx + 1  # Row 0 = position 1, row 7 = position 8

            # Determine what appears on left and right
            if swap:
                # Odd word: swap sides
                left = '/' if row_position <= pos else ' '
                right = '\\' if row_position <= aett else ' '
            else:
                # Even word: normal
                left = '\\' if row_position <= aett else ' '
                right = '/' if row_position <= pos else ' '

            # Build the pattern
            rows[row_idx].append(f"{left}|{right}")

    # Join each row with spaces between columns
    result = []
    for row in rows:
        result.append(" ".join(row))

    return '\n'.join(result)


def generate_line_notation(aett_pos_data):
    """
    Generates a two-row 'line notation' (isrunir) for rune data.
    - Long lines (tall '|') span both rows  -> encode the aett number.
    - Short lines (short '|') appear only on the bottom row -> encode the position.
    - Within one rune: aett strokes, one space, position strokes.
    - Double space between runes inside a word.
    - Quadruple space between words.

    Example  1:4 -> top:  |
                   bot:  | ||||

    Example  3:2 1:5  ->  top:  |||        |
                         bot:  ||| ||  | |||||
    """
    if not aett_pos_data:
        return ""

    # Build groups: a list of "words", each word is a list of (aett, pos) tuples
    words = [[]]
    for item in aett_pos_data:
        if item == 'SPACE':
            words.append([])
        else:
            words[-1].append(item)

    top_parts = []
    bot_parts = []

    for w_idx, word in enumerate(words):
        if w_idx > 0:
            # Word separator — quadruple space
            top_parts.append("    ")
            bot_parts.append("    ")

        for r_idx, (aett, pos) in enumerate(word):
            if r_idx > 0:
                # Rune separator within a word — double space
                top_parts.append("  ")
                bot_parts.append("  ")

            # Aett strokes (tall — appear on both rows)
            aett_top = "|" * aett
            aett_bot = "|" * aett

            # Position strokes (short — bottom row only, top row padded)
            pos_top = " " * pos
            pos_bot = "|" * pos

            # Combine: aett block + one space + position block
            top_parts.append(aett_top + " " + pos_top)
            bot_parts.append(aett_bot + " " + pos_bot)

    return "\n".join(["".join(top_parts), "".join(bot_parts)])


# ────────────────────────────────────────────────
# Shared helpers for printable output (SVG & PDF)
# ────────────────────────────────────────────────

def _flatten_strokes(aett_pos_data):
    """
    Flattens aett_pos_data into a flat list of stroke descriptors.

    Each rune (aett, pos) becomes `aett` long strokes followed by `pos` short strokes.
    No extra gap between the aett and position strokes of the same rune — they are
    just consecutive strokes separated by the regular gap.

    'SPACE' items mark word boundaries: the *next* stroke gets word_boundary_before=True.

    Returns:
        list of dicts: [{'kind': 'long'|'short', 'word_boundary_before': bool}, ...]
    """
    strokes = []
    pending_word_boundary = False

    for item in aett_pos_data:
        if item == 'SPACE':
            pending_word_boundary = True
            continue

        aett, pos = item

        # Aett strokes (long)
        for s in range(aett):
            strokes.append({
                'kind': 'long',
                'word_boundary_before': pending_word_boundary and s == 0,
            })
            if s == 0:
                pending_word_boundary = False

        # Position strokes (short) — immediately follow, no extra gap
        for s in range(pos):
            strokes.append({
                'kind': 'short',
                'word_boundary_before': pending_word_boundary and s == 0,
            })
            if s == 0:
                pending_word_boundary = False

    return strokes


def _compute_layout(strokes, long_mm, short_mm, stroke_w_mm, gap_mm,
                    max_width_mm, word_gap_mm):
    """
    Computes exact x-positions and sizes for every stroke.

    Two sizing modes:
      * Fixed gap   — gap_mm is used as-is, total width is computed.
      * Fixed width — max_width_mm is given, gap_mm is auto-computed so that all
        strokes + word gaps fit exactly within that width.

    Returns dict:
        'content_width_mm':  total width of the stroke area (no SVG margin)
        'content_height_mm': long_mm  (tallest stroke)
        'gap_mm':            effective gap (given or computed)
        'num_strokes':       int
        'num_word_gaps':     int
        'rects':             [(x, y, w, h), ...] where x/y are relative to content origin,
                              y=0 is the TOP of the long stroke.
    """
    n = len(strokes)
    if n == 0:
        return {
            'content_width_mm': 0, 'content_height_mm': 0, 'gap_mm': 0,
            'num_strokes': 0, 'num_word_gaps': 0, 'rects': [],
        }

    num_word_gaps = sum(1 for s in strokes if s['word_boundary_before'])

    # ── Resolve gap / total width ──────────────────────────────────
    if max_width_mm is not None:
        usable = max_width_mm - n * stroke_w_mm - num_word_gaps * word_gap_mm
        n_gaps = n - 1
        effective_gap = usable / n_gaps if n_gaps > 0 else 0
        content_width = max_width_mm
    else:
        effective_gap = gap_mm
        content_width = (n * stroke_w_mm
                         + max(0, n - 1) * effective_gap
                         + num_word_gaps * word_gap_mm)

    # ── Place strokes ──────────────────────────────────────────────
    rects = []
    x = 0.0
    for idx, stroke in enumerate(strokes):
        if idx > 0:
            x += effective_gap
        if stroke['word_boundary_before']:
            x += word_gap_mm

        if stroke['kind'] == 'long':
            y = 0.0
            h = long_mm
        else:
            y = long_mm - short_mm
            h = short_mm

        rects.append((x, y, stroke_w_mm, h))
        x += stroke_w_mm

    return {
        'content_width_mm': round(content_width, 4),
        'content_height_mm': long_mm,
        'gap_mm': round(effective_gap, 4),
        'num_strokes': n,
        'num_word_gaps': num_word_gaps,
        'rects': rects,
    }


# ────────────────────────────────────────────────
# SVG export
# ────────────────────────────────────────────────

def generate_printable_svg(aett_pos_data,
                           long_mm=None,
                           short_mm=None,
                           stroke_w_mm=None,
                           gap_mm=None,
                           max_width_mm=None,
                           word_gap_mm=None,
                           margin_mm=None,
                           output_file="runes.svg"):
    """
    Generates a printable SVG file with precise dimensions (in mm) for line-notation runes.

    Returns:
        dict with: total_width_mm, svg_height_mm, gap_mm, num_strokes, num_word_gaps
    """
    # Apply defaults
    if long_mm is None:       long_mm = PRINT_LONG_MM
    if short_mm is None:      short_mm = PRINT_SHORT_MM
    if stroke_w_mm is None:   stroke_w_mm = PRINT_STROKE_W_MM
    if gap_mm is None and max_width_mm is None and PRINT_MAX_WIDTH_MM is None:
        gap_mm = PRINT_GAP_MM
    if max_width_mm is None and PRINT_MAX_WIDTH_MM is not None:
        max_width_mm = PRINT_MAX_WIDTH_MM
    if word_gap_mm is None:   word_gap_mm = PRINT_WORD_GAP_MM
    if margin_mm is None:     margin_mm = PRINT_MARGIN_MM

    strokes = _flatten_strokes(aett_pos_data)
    layout = _compute_layout(strokes, long_mm, short_mm, stroke_w_mm,
                             gap_mm if gap_mm is not None else 0,
                             max_width_mm, word_gap_mm)

    total_w = layout['content_width_mm'] + 2 * margin_mm
    total_h = layout['content_height_mm'] + 2 * margin_mm

    svg_lines = []
    svg_lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    svg_lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_w:.3f}mm" height="{total_h:.3f}mm" '
        f'viewBox="0 0 {total_w:.3f} {total_h:.3f}">'
    )
    svg_lines.append(
        f'  <!-- Printable rune line notation: {layout["num_strokes"]} strokes, '
        f'gap={layout["gap_mm"]:.3f}mm, total={total_w:.2f}x{total_h:.2f}mm -->'
    )

    for (rx, ry, rw, rh) in layout['rects']:
        svg_lines.append(
            f'  <rect x="{rx + margin_mm:.3f}" y="{ry + margin_mm:.3f}" '
            f'width="{rw:.3f}" height="{rh:.3f}" fill="black"/>'
        )

    svg_lines.append('</svg>')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg_lines) + '\n')

    return {
        'total_width_mm': round(total_w, 3),
        'svg_height_mm': round(total_h, 3),
        'gap_mm': layout['gap_mm'],
        'num_strokes': layout['num_strokes'],
        'num_word_gaps': layout['num_word_gaps'],
    }


# ────────────────────────────────────────────────
# PDF helpers: multi-line word-wrap layout
# ────────────────────────────────────────────────

def _group_into_words(strokes):
    """
    Splits flat stroke list into a list of word groups (list of lists).
    A new word starts at any stroke with word_boundary_before=True.
    """
    if not strokes:
        return []
    words = [[]]
    for stroke in strokes:
        if stroke['word_boundary_before'] and words[-1]:
            words.append([])
        words[-1].append(stroke)
    return [w for w in words if w]  # drop empty


def _word_width(word_strokes, stroke_w_mm, gap_mm):
    """Width of one word: n*stroke_w + (n-1)*gap."""
    n = len(word_strokes)
    if n == 0:
        return 0
    return n * stroke_w_mm + max(0, n - 1) * gap_mm


def _split_into_lines(words, stroke_w_mm, gap_mm, word_gap_mm, max_line_width_mm):
    """
    Greedy word-wrap: pack words into lines not exceeding max_line_width_mm.
    Gap between words on the same line = gap_mm + word_gap_mm.
    If a single word exceeds the line width, put it alone on its own line.
    Returns list of lines, each line is a list of word groups.
    """
    if not words:
        return []

    inter_word = gap_mm + word_gap_mm  # gap between last stroke of prev word and first of next
    lines = []
    current_line = []
    current_width = 0.0

    for word in words:
        ww = _word_width(word, stroke_w_mm, gap_mm)
        if not current_line:
            # First word on line — always fits
            current_line.append(word)
            current_width = ww
        else:
            needed = current_width + inter_word + ww
            if needed <= max_line_width_mm + 0.001:  # small epsilon for float
                current_line.append(word)
                current_width = needed
            else:
                # Start new line
                lines.append(current_line)
                current_line = [word]
                current_width = ww

    if current_line:
        lines.append(current_line)

    return lines


def _layout_line(words, stroke_w_mm, gap_mm, word_gap_mm, long_mm, short_mm):
    """
    Compute rects for one line of words.
    Returns (rects, line_width) where rects = [(x, y, w, h), ...].
    x starts at 0. Between strokes within a word: gap_mm.
    Between words: gap_mm + word_gap_mm (one inter-stroke gap + the word gap).
    """
    rects = []
    x = 0.0
    inter_word = gap_mm + word_gap_mm

    for w_idx, word_strokes in enumerate(words):
        if w_idx > 0:
            x += inter_word  # gap between last stroke of prev word and first of this word

        for s_idx, stroke in enumerate(word_strokes):
            if s_idx > 0:
                x += gap_mm

            if stroke['kind'] == 'long':
                y = 0.0
                h = long_mm
            else:
                y = long_mm - short_mm
                h = short_mm

            rects.append((x, y, stroke_w_mm, h))
            x += stroke_w_mm

    line_width = x  # total width to the right edge of the last stroke
    return rects, line_width


# ────────────────────────────────────────────────
# PDF export (exact mm dimensions on paper, landscape, multi-line, multi-page)
# ────────────────────────────────────────────────

def generate_printable_pdf(aett_pos_data,
                           long_mm=None,
                           short_mm=None,
                           stroke_w_mm=None,
                           gap_mm=None,
                           max_width_mm=None,
                           word_gap_mm=None,
                           paper=None,
                           landscape=None,
                           page_margin_mm=None,
                           line_gap_mm=None,
                           output_file="runes.pdf"):
    """
    Generates a print-ready PDF with rune line notation at exact mm dimensions.

    The page size matches the chosen paper (default A4). If landscape is True
    (default), the page is rotated so the long edge is horizontal.

    Content is word-wrapped into lines that fit within the printable area.
    If it doesn't fit on one page, multiple pages are generated.

    When printed at 100% scale (no fit-to-page!) the measurements will be exact.

    Args:
        aett_pos_data:  List from to_aett_pos(): [(aett, pos), 'SPACE', ...]
        long_mm:        Height of long (aett) strokes.
        short_mm:       Height of short (position) strokes.
        stroke_w_mm:    Width of each stroke rectangle.
        gap_mm:         Gap between consecutive strokes.
        max_width_mm:   (Unused in multi-line mode — kept for API compat.)
        word_gap_mm:    Extra gap at word boundaries.
        paper:          Paper name (key in PAPER_SIZES) or (w_mm, h_mm) tuple.
        landscape:      If True, rotate page to landscape. Default: PRINT_LANDSCAPE.
        page_margin_mm: Margin on all four sides of the page.
        line_gap_mm:    Vertical gap between lines.
        output_file:    Path to the output PDF file.

    Returns:
        dict with layout info.
    """
    from reportlab.lib.units import mm as RL_MM
    from reportlab.pdfgen import canvas

    # Apply defaults
    if long_mm is None:         long_mm = PRINT_LONG_MM
    if short_mm is None:        short_mm = PRINT_SHORT_MM
    if stroke_w_mm is None:     stroke_w_mm = PRINT_STROKE_W_MM
    if gap_mm is None:          gap_mm = PRINT_GAP_MM
    if word_gap_mm is None:     word_gap_mm = PRINT_WORD_GAP_MM
    if landscape is None:       landscape = PRINT_LANDSCAPE
    if page_margin_mm is None:  page_margin_mm = PRINT_PAGE_MARGIN_MM
    if line_gap_mm is None:     line_gap_mm = PRINT_LINE_GAP_MM

    # Resolve paper size
    if paper is None:
        paper = PRINT_PAPER
    if isinstance(paper, str):
        paper_key = paper.lower()
        if paper_key not in PAPER_SIZES:
            raise ValueError(f"Unknown paper size '{paper}'. "
                             f"Available: {', '.join(PAPER_SIZES.keys())}")
        page_w_mm, page_h_mm = PAPER_SIZES[paper_key]
    else:
        page_w_mm, page_h_mm = paper  # custom (w, h) tuple in mm

    # Apply landscape
    if landscape:
        page_w_mm, page_h_mm = max(page_w_mm, page_h_mm), min(page_w_mm, page_h_mm)

    # Printable area
    area_w = page_w_mm - 2 * page_margin_mm
    area_h = page_h_mm - 2 * page_margin_mm

    # Flatten strokes and group into words
    strokes = _flatten_strokes(aett_pos_data)
    words = _group_into_words(strokes)

    # Word-wrap into lines
    lines = _split_into_lines(words, stroke_w_mm, gap_mm, word_gap_mm, area_w)

    # How many lines fit per page?
    if long_mm + line_gap_mm > 0:
        lines_per_page = max(1, int((area_h + line_gap_mm) / (long_mm + line_gap_mm)))
    else:
        lines_per_page = 1

    # Split lines into page groups
    pages = []
    for i in range(0, len(lines), lines_per_page):
        pages.append(lines[i:i + lines_per_page])

    num_pages = len(pages)
    num_lines = len(lines)

    # Create PDF
    c = canvas.Canvas(output_file, pagesize=(page_w_mm * RL_MM, page_h_mm * RL_MM))

    max_line_width = 0.0

    for page_idx, page_lines in enumerate(pages):
        if page_idx > 0:
            c.showPage()

        for line_idx, line_words in enumerate(page_lines):
            # Compute rects for this line
            rects, line_width = _layout_line(line_words, stroke_w_mm, gap_mm,
                                              word_gap_mm, long_mm, short_mm)
            max_line_width = max(max_line_width, line_width)

            # Centre line horizontally
            line_origin_x = page_margin_mm + (area_w - line_width) / 2.0

            # Vertical position: first line at top of printable area, going down.
            # reportlab y=0 is page bottom.
            # Top of printable area = page_h - page_margin
            # Top of line i = page_h - page_margin - i*(long_mm + line_gap)
            # reportlab y for bottom of long stroke = top_of_line - long_mm
            # But we want bottom-aligned strokes, so:
            #   baseline (bottom of all strokes) = page_h - page_margin - long_mm - i*(long_mm + line_gap)
            baseline_y = page_h_mm - page_margin_mm - long_mm - line_idx * (long_mm + line_gap_mm)

            for (rx, ry, rw, rh) in rects:
                # ry=0 for long (full height), ry=long-short for short
                # Both bottom-aligned: pdf_y = baseline_y for all
                pdf_x = (line_origin_x + rx) * RL_MM
                pdf_y = baseline_y * RL_MM
                pdf_w = rw * RL_MM
                pdf_h = rh * RL_MM
                c.rect(pdf_x, pdf_y, pdf_w, pdf_h, stroke=0, fill=1)

    c.save()

    total_content_h = num_lines * long_mm + max(0, num_lines - 1) * line_gap_mm

    return {
        'page_w_mm': page_w_mm,
        'page_h_mm': page_h_mm,
        'content_width_mm': round(max_line_width, 3),
        'content_height_mm': round(total_content_h, 3),
        'gap_mm': round(gap_mm, 4),
        'num_strokes': len(strokes),
        'num_word_gaps': len(words) - 1 if len(words) > 1 else 0,
        'num_lines': num_lines,
        'num_pages': num_pages,
        'landscape': landscape,
    }


def display_substitution_guide():
    """
    Displays a guide for ambiguous letter substitutions.
    """
    print("\n" + "="*60)
    print("AMBIGUOUS LETTERS - Substitution Guide")
    print("="*60)
    print("For these letters, you'll be asked to choose the sound:")
    print()
    print("  V -> F (as in 'five') or W (as in 'van')")
    print("  C -> K (as in 'cat') or S (as in 'city')")
    print("  Y -> I (as in 'myth'), J (as in 'yes'), or E (as in 'happy')")
    print("  Q -> K (as in 'queen') or KW (as in 'quake')")
    print("  X -> KS (as in 'box') or Z (as in 'xylophone')")
    print()
    print("TIP: You can pre-substitute these in your input for direct conversion:")
    print("     'victory' -> 'wiktory' (v->w, c->k)")
    print("     'city' -> 'sity', 'cat' -> 'kat', 'xbox' -> 'iksboks'")
    print("="*60 + "\n")


# ────────────────────────────────────────────────
# Shared processing logic (used by both CLI and interactive modes)
# ────────────────────────────────────────────────

def process_text(user_input, interactive=True):
    """
    Processes a single text input through the full translation pipeline:
    normalization -> rune translation -> numeric scheme -> ASCII art ->
    line notation -> SVG -> PDF -> numerology.

    Args:
        user_input:   Raw text to translate.
        interactive:  If True, prompts user for ambiguous letter choices.
                      If False, uses the first (default) choice automatically.
    """
    # Remove numbers
    user_input = remove_numbers(user_input)

    # Normalize special/accented letters
    user_input = normalize_special_letters(user_input)

    # Normalize whitespace
    normalized_input = normalize_whitespace(user_input)

    # Create shared cache for this translation
    cache = {}

    # Unicode runes
    runes = latin_to_elder_futhark(normalized_input, interactive=interactive,
                                    word_context=normalized_input, substitution_cache=cache)

    # Get substituted text
    substituted = get_substituted_text(normalized_input, cache)

    # Display all forms
    print("\n" + "="*50)
    print("Original:    ", user_input)
    if normalized_input != user_input:
        print("Normalized:  ", normalized_input)
    print("Substituted: ", substituted)
    print("Elder Futhark:", runes)
    print("="*50)

    # Numeric scheme (reuses cached choices) - now returns structured data
    aett_pos_data = to_aett_pos(normalized_input, interactive=interactive,
                                 word_context=normalized_input, substitution_cache=cache)

    # Convert to string for display with word separators
    parts = []
    for item in aett_pos_data:
        if item == 'SPACE':
            parts.append('-')
        else:
            a, p = item
            parts.append(f"{a}:{p}")
    aett_pos_str = ' '.join(parts)

    print("\nNumeric aett:position scheme:")
    print(aett_pos_str)
    sum_all = sum_aett_pos_string_numbers(aett_pos_str)
    print(f"\nSum of all numbers in aett:pos string: {sum_all}")

    # ASCII branch art (if aett_pos_data exists)
    if aett_pos_data:
        ascii_art = generate_branch_ascii(aett_pos_data)
        print("\nASCII art approximation of branch runes:")
        print(ascii_art)

    # Line notation (isrunir)
    if aett_pos_data:
        line_art = generate_line_notation(aett_pos_data)
        print("\nLine notation (isrunir):")
        print(line_art)

    # Printable SVG
    if aett_pos_data:
        svg_info = generate_printable_svg(aett_pos_data)
        print(f"\nPrintable SVG saved: runes.svg")
        print(f"  Dimensions: {svg_info['total_width_mm']:.1f} x {svg_info['svg_height_mm']:.1f} mm")
        print(f"  Strokes: {svg_info['num_strokes']}, gap: {svg_info['gap_mm']:.2f} mm")
        if svg_info['num_word_gaps'] > 0:
            print(f"  Word gaps: {svg_info['num_word_gaps']}")

    # Printable PDF
    if aett_pos_data:
        pdf_info = generate_printable_pdf(aett_pos_data)
        print(f"\nPrintable PDF saved: runes.pdf")
        print(f"  Paper: {pdf_info['page_w_mm']:.0f} x {pdf_info['page_h_mm']:.0f} mm"
              f" ({'landscape' if pdf_info['landscape'] else 'portrait'})")
        print(f"  Content: {pdf_info['content_width_mm']:.1f} x {pdf_info['content_height_mm']:.1f} mm")
        print(f"  Strokes: {pdf_info['num_strokes']}, gap: {pdf_info['gap_mm']:.2f} mm")
        print(f"  Lines: {pdf_info['num_lines']}, pages: {pdf_info['num_pages']}")
        if pdf_info['num_word_gaps'] > 0:
            print(f"  Word gaps: {pdf_info['num_word_gaps']}")

    rune_sum = sum_runic_text_value(aett_pos_data)
    print(f"\nSum of rune values ((aett-1)*8+pos): {rune_sum}")

    # Show magical divisors of the rune sum
    divisors = decompose_rune_sum(rune_sum)
    print_divisor_descriptions(divisors, rune_sum=rune_sum)


# ────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # CLI mode: join all arguments as input text, non-interactive
        text = ' '.join(sys.argv[1:])
        process_text(text, interactive=False)
    else:
        # Interactive mode
        print("=== Latin to Elder Futhark Translator (with phonetic guidance) ===")
        display_substitution_guide()

        while True:
            user_input = input("Enter text (or 'exit' to quit): ").strip()
            if user_input.lower() in ['konec', 'exit', 'q']:
                print("Goodbye!")
                break

            process_text(user_input, interactive=True)
