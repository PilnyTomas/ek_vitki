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
    'ŋ': ('ᛜ', 3, 6),  # Ingwaz - Ing, fertility
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
            # Prompt user for phonetic choice
            choice = prompt_for_substitution(text_lower[i], word_context or text, i + 1, substitution_cache)
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
    Converts text to numeric ætt:position scheme (e.g., 'fu' → '1:1 1:2')
    Ignores untranslatable characters.
    """
    text_lower = text.lower()
    result = []
    i = 0
    
    while i < len(text_lower):
        # Check for two-character sequences first
        if i + 1 < len(text_lower) and text_lower[i:i+2] in ELDER_FUTHARK:
            rune, aett, pos = ELDER_FUTHARK[text_lower[i:i+2]]
            if aett is not None and pos is not None:
                result.append(f"{aett}:{pos}")
            i += 2
        elif text_lower[i] in ELDER_FUTHARK:
            rune, aett, pos = ELDER_FUTHARK[text_lower[i]]
            if aett is not None and pos is not None:
                result.append(f"{aett}:{pos}")
            i += 1
        elif interactive and text_lower[i] in AMBIGUOUS_LETTERS:
            # Prompt user for phonetic choice (uses cache)
            choice = prompt_for_substitution(text_lower[i], word_context or text, i + 1, substitution_cache)
            if choice and choice[1] is not None and choice[2] is not None:
                result.append(f"{choice[1]}:{choice[2]}")
            # For multi-rune choices like 'kw', we need to handle differently
            elif choice and choice[0] and len(choice[0]) > 1:
                # Multi-character rune sequence - extract positions
                for rune_char in choice[0]:
                    # Find this rune in ELDER_FUTHARK
                    for key, val in ELDER_FUTHARK.items():
                        if val[0] == rune_char and val[1] is not None:
                            result.append(f"{val[1]}:{val[2]}")
                            break
            i += 1
        else:
            i += 1
    
    return ' '.join(result)

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


# ────────────────────────────────────────────────
# Test section
# ────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Latin to Elder Futhark Translator (with phonetic guidance) ===")
    display_substitution_guide()
    
    while True:
        user_input = input("Enter text (or 'exit' to quit): ").strip()
        if user_input.lower() in ['konec', 'exit', 'q']:
            print("Goodbye!")
            break
        
        # Create shared cache for this translation
        cache = {}
        
        # Unicode runes (with interactive prompts)
        runes = latin_to_elder_futhark(user_input, interactive=True, word_context=user_input, substitution_cache=cache)
        
        # Get substituted text
        substituted = get_substituted_text(user_input, cache)
        
        # Display all forms
        print("\n" + "="*50)
        print("Original:    ", user_input)
        print("Substituted: ", substituted)
        print("Elder Futhark:", runes)
        print("="*50)
        
        # Numeric scheme (reuses cached choices)
        aett_pos = to_aett_pos(user_input, interactive=True, word_context=user_input, substitution_cache=cache)
        print("\nNumeric ætt:position scheme:")
        print(aett_pos)
        
        print("-" * 50)