# ek_vitki.py
# Convert Latin text → Elder Futhark runes (Unicode) + numeric ætt:pos scheme + ASCII branch art
# For Tomas: Inspiration from kvistrúnar / branch runes

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
    ' ': ('  ', None, None),
    '.': ('.', None, None),
    ',': (',', None, None),
}

divisor_mapping = {
    9:  "Nine - Most sacred number: 9 worlds, Odin’s sacrifice, highest magical potency",
    3:  "Three - Core principle: the three ættir of the runes",
    6:  "Six - Hagalaz structure, crystallization, balance",
    12: "Twelve - Half of the full rune row, cosmic order",
    24: "Twenty-four - Complete Elder Futhark, full systemic power",
    4:  "Four - Four directions, stability, foundation",
    8:  "Eight - Sleipnir’s eight legs, movement between worlds"
}

def print_divisor_descriptions(divisors):
    """
    Prints magical divisors and their descriptions.
    """
    if divisors:
        print(f"Magically important divisors of the sum: {divisors}")
        for divisor in divisors:
            desc = divisor_mapping.get(divisor)
            if desc:
                print(f"  {divisor}: {desc}")
    else:
        print("No magically important divisors found for the sum.")

# Ambiguous letters requiring phonetic choice
AMBIGUOUS_LETTERS = {
    'v': {
        'prompt': "sound like 'F' (as in 'of') or 'W' (as in 'van')?",
        'choices': {
            'f': ('ᚠ', 1, 1),  # Fehu
            'w': ('ᚹ', 1, 8),  # Wunjo
        }
    },
    'c': {
        'prompt': "sound like hard 'K' (as in 'cat') or soft 'S' (as in 'city')?",
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

def normalize_whitespace(text):
    """
    Normalizes all whitespace (spaces, tabs, multiple spaces) to single spaces.
    """
    import re
    return re.sub(r'\s+', ' ', text)


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
        elif interactive and text_lower[i] in AMBIGUOUS_LETTERS:
            # Extract the current word containing this letter
            word_start = i
            while word_start > 0 and text_lower[word_start - 1] not in ' \t\n\r':
                word_start -= 1
            word_end = i
            while word_end < len(text_lower) and text_lower[word_end] not in ' \t\n\r':
                word_end += 1
            current_word = text_lower[word_start:word_end]
            
            # Prompt user for phonetic choice
            choice = prompt_for_substitution(text_lower[i], current_word, i + 1, substitution_cache)
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
        elif interactive and text_lower[i] in AMBIGUOUS_LETTERS:
            # Extract the current word containing this letter
            word_start = i
            while word_start > 0 and text_lower[word_start - 1] not in ' \t\n\r':
                word_start -= 1
            word_end = i
            while word_end < len(text_lower) and text_lower[word_end] not in ' \t\n\r':
                word_end += 1
            current_word = text_lower[word_start:word_end]
            
            # Prompt user for phonetic choice (uses cache)
            choice = prompt_for_substitution(text_lower[i], current_word, i + 1, substitution_cache)
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

def display_substitution_guide():
    """
    Displays a guide for ambiguous letter substitutions.
    """
    print("\n" + "="*60)
    print("AMBIGUOUS LETTERS - Substitution Guide")
    print("="*60)
    print("For these letters, you'll be asked to choose the sound:")
    print()
    print("  V → F (as in 'five') or W (as in 'van')")
    print("  C → K (as in 'cat') or S (as in 'city')")
    print("  Y → I (as in 'myth'), J (as in 'yes'), or E (as in 'happy')")
    print("  Q → K (as in 'queen') or KW (as in 'quake')")
    print("  X → KS (as in 'box') or Z (as in 'xylophone')")
    print()
    print("TIP: You can pre-substitute these in your input for direct conversion:")
    print("     'victory' → 'wiktory' (v→w, c→k)")
    print("     'city' → 'sity', 'cat' → 'kat', 'xbox' → 'iksboks'")
    print("="*60 + "\n")


def normalize_whitespace(text):
    """
    Normalizes all whitespace (spaces, tabs, multiple spaces) to single spaces.
    """
    import re
    return re.sub(r'\s+', ' ', text)


def remove_numbers(text):
    """
    Removes all numeric digits from text.
    """
    import re
    return re.sub(r'\d', '', text)

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
    

# ────────────────────────────────────────────────
# Test section
# ────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    # Check if text was provided as command line arguments
    if len(sys.argv) > 1:
        # Join all arguments as input text
        user_input = ' '.join(sys.argv[1:])
        
        # Remove numbers
        user_input = remove_numbers(user_input)
        
        # Normalize whitespace
        normalized_input = normalize_whitespace(user_input)
        
        # Create shared cache for this translation
        cache = {}
        
        # Unicode runes (with interactive prompts)
        runes = latin_to_elder_futhark(normalized_input, interactive=True, word_context=normalized_input, substitution_cache=cache)
        
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
        aett_pos_data = to_aett_pos(normalized_input, interactive=True, word_context=normalized_input, substitution_cache=cache)
        
        # Convert to string for display with word separators
        parts = []
        for item in aett_pos_data:
            if item == 'SPACE':
                parts.append('-')
            else:
                a, p = item
                parts.append(f"{a}:{p}")
        aett_pos_str = ' '.join(parts)
        print("\nNumeric ætt:position scheme:")
        print(aett_pos_str)
        
        # ASCII branch art (if aett_pos_data exists)
        if aett_pos_data:
            ascii_art = generate_branch_ascii(aett_pos_data)
            print("\nASCII art approximation of branch runes:")
            print(ascii_art)

        rune_sum = sum_runic_text_value(aett_pos_data)
        print(f"\nSum of rune values ((aett-1)*8+pos): {rune_sum}")

        # Show magical divisors of the rune sum
        divisors = decompose_rune_sum(rune_sum)
        print_divisor_descriptions(divisors)
        
        sys.exit(0)
    
    # Interactive mode
    print("=== Latin to Elder Futhark Translator (with phonetic guidance) ===")
    display_substitution_guide()
    
    while True:
        user_input = input("Enter text (or 'exit' to quit): ").strip()
        if user_input.lower() in ['konec', 'exit', 'q']:
            print("Goodbye!")
            break
        
        # Remove numbers
        user_input = remove_numbers(user_input)
        
        # Normalize whitespace
        normalized_input = normalize_whitespace(user_input)
        
        # Create shared cache for this translation
        cache = {}
        
        # Unicode runes (with interactive prompts)
        runes = latin_to_elder_futhark(normalized_input, interactive=True, word_context=normalized_input, substitution_cache=cache)
        
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
        aett_pos_data = to_aett_pos(normalized_input, interactive=True, word_context=normalized_input, substitution_cache=cache)
        
        # Convert to string for display with word separators
        parts = []
        for item in aett_pos_data:
            if item == 'SPACE':
                parts.append('-')
            else:
                a, p = item
                parts.append(f"{a}:{p}")
        aett_pos_str = ' '.join(parts)
        print("\nNumeric ætt:position scheme:")
        print(aett_pos_str)
        
        # ASCII branch art (if aett_pos_data exists)
        if aett_pos_data:
            ascii_art = generate_branch_ascii(aett_pos_data)
            print("\nASCII art branch runes:")
            print(ascii_art)

        rune_sum = sum_runic_text_value(aett_pos_data)
        print(f"\nSum of rune values: {rune_sum}")

        # Show magical divisors of the rune sum
        divisors = decompose_rune_sum(rune_sum)
        print_divisor_descriptions(divisors)
        