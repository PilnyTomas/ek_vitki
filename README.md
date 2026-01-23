# ek_vitki
Latin to Elder Futhark rune translator with phonetic guidance

## Features
- Converts Latin text to Elder Futhark runes
- Interactive phonetic substitution for ambiguous letters (v, c, y, q, x)
- Multiple output formats:
  - Unicode runes
  - Numeric ætt:position scheme
  - ASCII branch runes (kvistrúnar)
- Command-line and web interface

## Usage

### Command Line
```bash
python ek_vitki.py <text>
```

### Interactive Mode
```bash
python ek_vitki.py
```

### Web Interface
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the web server:
```bash
python app.py
```

3. Open your browser to: `http://localhost:5000`

## How It Works
- Automatic whitespace normalization
- Numbers are removed from input
- Multi-character sequences supported (e.g., 'th' → Thurisaz)
- Phonetic disambiguation for ambiguous letters
- Branch runes encode ætt and position through branch counts

