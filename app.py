#!/usr/bin/env python3
"""
Web interface for Elder Futhark translator
"""

from flask import Flask, render_template, request, jsonify
import sys
import os

# Import the translation functions from ek_vitki.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ek_vitki import (
    normalize_whitespace,
    remove_numbers,
    latin_to_elder_futhark,
    get_substituted_text,
    to_aett_pos,
    generate_branch_ascii,
    AMBIGUOUS_LETTERS
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text', '')
    substitutions = data.get('substitutions', {})
    
    print(f"Received text: {text}")
    print(f"Received substitutions: {substitutions}")
    
    # Remove numbers and normalize
    text = remove_numbers(text)
    normalized_input = normalize_whitespace(text)
    
    print(f"Normalized input: {normalized_input}")
    
    # Create cache with user's choices
    cache = {}
    for pos_key, choice in substitutions.items():
        pos = int(pos_key)
        letter = None
        # Find the letter at this position
        if pos <= len(normalized_input):
            letter = normalized_input[pos - 1].lower()
            if letter in AMBIGUOUS_LETTERS:
                # Get the rune tuple for this choice
                config = AMBIGUOUS_LETTERS[letter]
                if choice in config['choices']:
                    cache[(pos, letter)] = config['choices'][choice]
                    print(f"Added to cache: position {pos}, letter {letter}, choice {choice}")
    
    print(f"Cache: {cache}")
    
    # Translate
    runes = latin_to_elder_futhark(normalized_input, interactive=False, substitution_cache=cache)
    substituted = get_substituted_text(normalized_input, cache)
    
    # Get numeric scheme
    aett_pos_data = to_aett_pos(normalized_input, interactive=False, substitution_cache=cache)
    
    # Convert to string for display
    parts = []
    for item in aett_pos_data:
        if item == 'SPACE':
            parts.append('-')
        else:
            a, p = item
            parts.append(f"{a}:{p}")
    numeric_scheme = ' '.join(parts)
    
    # Generate ASCII art
    ascii_art = generate_branch_ascii(aett_pos_data) if aett_pos_data else ""
    
    return jsonify({
        'original': text,
        'normalized': normalized_input,
        'substituted': substituted,
        'runes': runes,
        'numeric': numeric_scheme,
        'ascii_art': ascii_art
    })

@app.route('/get_ambiguous', methods=['POST'])
def get_ambiguous():
    """Returns positions and choices for ambiguous letters"""
    data = request.json
    text = data.get('text', '')
    
    # Remove numbers and normalize
    text = remove_numbers(text)
    normalized_input = normalize_whitespace(text)
    
    ambiguous_positions = []
    
    for i, char in enumerate(normalized_input.lower()):
        if char in AMBIGUOUS_LETTERS:
            # Extract the word
            word_start = i
            while word_start > 0 and normalized_input[word_start - 1] not in ' \t\n\r':
                word_start -= 1
            word_end = i
            while word_end < len(normalized_input) and normalized_input[word_end] not in ' \t\n\r':
                word_end += 1
            current_word = normalized_input[word_start:word_end]
            
            config = AMBIGUOUS_LETTERS[char]
            ambiguous_positions.append({
                'position': i + 1,
                'letter': char.upper(),
                'word': current_word,
                'prompt': config['prompt'],
                'choices': list(config['choices'].keys())
            })
    
    return jsonify({'ambiguous': ambiguous_positions})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
