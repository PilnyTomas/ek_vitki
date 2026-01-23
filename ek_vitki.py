# rune_translator.py (verze 0.2)
# Převod latinského textu → Elder Futhark runy (Unicode) + numerické schéma ætt:pos + ASCII branch art
# Pro Tomas: Inspirace z kvistrúnar / branch runes

# Unicode mapa (stejná jako předtím)
ELDER_FUTHARK_MAP = {
    'a': 'ᚨ', 'b': 'ᛒ', 'c': 'ᚲ', 'd': 'ᛞ', 'e': 'ᛖ', 'f': 'ᚠ', 'g': 'ᚷ', 'h': 'ᚺ',
    'i': 'ᛁ', 'j': 'ᛃ', 'k': 'ᚲ', 'l': 'ᛚ', 'm': 'ᛗ', 'n': 'ᚾ', 'o': 'ᛟ', 'p': 'ᛈ',
    'q': 'ᚲ', 'r': 'ᚱ', 's': 'ᛊ', 't': 'ᛏ', 'u': 'ᚢ', 'v': 'ᚠ', 'w': 'ᚹ', 'x': 'ᛉ',
    'y': 'ᛇ', 'z': 'ᛉ', 'þ': 'ᚦ', 'ð': 'ᚦ', ' ': '  ', '.': '.', ',': ',',
}

# Mapa pro ætt:pozice (Elder Futhark: 3 ættir po 8)
# Aproximace pro chybějící: v→f, c→k, q→k, x→z, y→j/e, atd.
LETTER_TO_AETT_POS = {
    'f': (1,1), 'u': (1,2), 'þ': (1,3), 'a': (1,4), 'r': (1,5), 'k': (1,6), 'g': (1,7), 'w': (1,8),
    'h': (2,1), 'n': (2,2), 'i': (2,3), 'j': (2,4), 'e': (2,5), 'p': (2,6), 'z': (2,7), 's': (2,8),
    't': (3,1), 'b': (3,2), 'e': (3,3), 'm': (3,4), 'l': (3,5), 'ŋ': (3,6), 'd': (3,7), 'o': (3,8),
    # Aproximace
    'v': (1,1), 'c': (1,6), 'q': (1,6), 'x': (2,7), 'y': (2,4), 'ð': (1,3),
}

def latin_to_elder_futhark(text):
    text = text.lower()
    result = []
    for char in text:
        result.append(ELDER_FUTHARK_MAP.get(char, char))
    return ''.join(result)

def to_aett_pos(text):
    """
    Převede text na numerické schéma ætt:pozice (např. 'fu' → '1:1 1:2')
    Nepřeložené znaky ignoruje.
    """
    text = text.lower()
    result = []
    for char in text:
        if char in LETTER_TO_AETT_POS:
            aett, pos = LETTER_TO_AETT_POS[char]
            result.append(f"{aett}:{pos}")
    return ' '.join(result)

def generate_branch_ascii(aett_pos_list):
    """
    Generuje jednoduchý ASCII art pro branch runes.
    - Vertikální osa: |
    - Větve: Vlevo dolů (\---) pro ætt 1 (nižší), vpravo nahoru (---/) pro ætt 2+, délka = pos.
    - Každá runa na novém "levelu" osy.
    """
    lines = []
    height = len(aett_pos_list) * 2  # Mezery mezi větvemi
    axis = [' '] * height + ['|'] * (height + 1)  # Základní osa dole

    for idx, pos_str in enumerate(aett_pos_list):
        aett, pos = map(int, pos_str.split(':'))
        branch_len = '-' * pos
        level = idx * 2  # Rozestup

        if aett == 1:  # Dolů vlevo
            branch = '\\' + branch_len
            for i, char in enumerate(branch):
                axis[level + i] = char + axis[level + i]
        else:  # Nahoru vpravo (pro ætt 2/3)
            branch = branch_len + '/'
            for i, char in enumerate(branch):
                axis[level + i] = axis[level + i] + char

    # Sestav řádky (obráceně pro "nahoru")
    ascii_art = '\n'.join(''.join(axis[::-1]))  # Obrátit pro vertikální
    return ascii_art

# ────────────────────────────────────────────────
# Testovací část
# ────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Elder Futhark Translator v0.2 (s ætt:pos + ASCII branch) ===\n")
    
    while True:
        vstup = input("Zadej text (nebo 'konec' pro ukončení): ").strip()
        if vstup.lower() in ['konec', 'exit', 'q']:
            print("Nashledanou!")
            break
        
        # Unicode runy
        runy = latin_to_elder_futhark(vstup)
        print("\nVýsledek v Elder Futhark Unicode:")
        print(runy)
        
        # Numerické schéma
        aett_pos = to_aett_pos(vstup)
        print("\nNumerické schéma ætt:pozice:")
        print(aett_pos)
        
        # ASCII branch art (pokud je aett_pos)
        if aett_pos:
            aett_pos_list = aett_pos.split()
            ascii_art = generate_branch_ascii(aett_pos_list)
            print("\nASCII art aproximace branch runes:")
            print(ascii_art)
        
        print("-" * 50)