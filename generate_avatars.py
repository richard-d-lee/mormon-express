"""
Generate placeholder SVG avatars for all characters.
Run this script to create avatar images in the static/images folder.
"""

import os

# Character definitions with colors
CHARACTERS = {
    # Book of Mormon
    "nephi": {"name": "Nephi", "color": "#1e3a5f", "initials": "N"},
    "alma_younger": {"name": "Alma", "color": "#8b0000", "initials": "A"},
    "moroni_captain": {"name": "Moroni", "color": "#2e4a1c", "initials": "CM"},
    "mormon": {"name": "Mormon", "color": "#4a4a4a", "initials": "M"},
    "moroni_prophet": {"name": "Moroni", "color": "#c9a227", "initials": "M"},
    "abinadi": {"name": "Abinadi", "color": "#8b4513", "initials": "AB"},
    "king_benjamin": {"name": "Benjamin", "color": "#5c4033", "initials": "KB"},
    "enos": {"name": "Enos", "color": "#2f4f4f", "initials": "E"},
    "ammon": {"name": "Ammon", "color": "#006400", "initials": "AM"},
    "samuel_lamanite": {"name": "Samuel", "color": "#654321", "initials": "SL"},

    # Old Testament
    "moses": {"name": "Moses", "color": "#8b4513", "initials": "MO"},
    "abraham": {"name": "Abraham", "color": "#d4af37", "initials": "AB"},
    "joseph_egypt": {"name": "Joseph", "color": "#9932cc", "initials": "JE"},
    "elijah": {"name": "Elijah", "color": "#ff4500", "initials": "EL"},
    "ruth": {"name": "Ruth", "color": "#daa520", "initials": "R"},
    "david": {"name": "David", "color": "#000080", "initials": "D"},
    "isaiah": {"name": "Isaiah", "color": "#4b0082", "initials": "IS"},
    "daniel": {"name": "Daniel", "color": "#483d8b", "initials": "DN"},
    "eve": {"name": "Eve", "color": "#228b22", "initials": "EV"},
    "job": {"name": "Job", "color": "#696969", "initials": "JB"},
    "noah_ot": {"name": "Noah", "color": "#4682b4", "initials": "NO"},

    # New Testament
    "peter": {"name": "Peter", "color": "#b8860b", "initials": "P"},
    "paul": {"name": "Paul", "color": "#800020", "initials": "PA"},
    "mary_mother": {"name": "Mary", "color": "#4169e1", "initials": "MA"},
    "john_beloved": {"name": "John", "color": "#9400d3", "initials": "JN"},
    "martha": {"name": "Martha", "color": "#cd853f", "initials": "MT"},
    "john_baptist": {"name": "John B.", "color": "#8b7355", "initials": "JB"},
    "thomas": {"name": "Thomas", "color": "#556b2f", "initials": "TH"},
    "luke": {"name": "Luke", "color": "#2f4f4f", "initials": "LK"},
    "mary_magdalene": {"name": "Mary M.", "color": "#dc143c", "initials": "MM"},
    "stephen": {"name": "Stephen", "color": "#8b0000", "initials": "ST"},
}

SVG_TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="200" height="200">
  <circle cx="50" cy="50" r="50" fill="{color}"/>
  <text x="50" y="50" font-family="Georgia, serif" font-size="{font_size}" fill="white" text-anchor="middle" dominant-baseline="central" font-weight="bold">{initials}</text>
</svg>'''

def generate_avatars():
    output_dir = os.path.join(os.path.dirname(__file__), "src", "static", "images")
    os.makedirs(output_dir, exist_ok=True)

    for char_id, char_info in CHARACTERS.items():
        initials = char_info["initials"]
        font_size = 32 if len(initials) <= 2 else 24

        svg_content = SVG_TEMPLATE.format(
            color=char_info["color"],
            initials=initials,
            font_size=font_size
        )

        # Save as SVG (browsers can display these)
        filepath = os.path.join(output_dir, f"{char_id}.svg")
        with open(filepath, "w") as f:
            f.write(svg_content)
        print(f"Created: {filepath}")

    # Create default avatar
    default_svg = SVG_TEMPLATE.format(color="#888888", initials="?", font_size=40)
    with open(os.path.join(output_dir, "default-avatar.svg"), "w") as f:
        f.write(default_svg)
    print("Created: default-avatar.svg")

    # Create logo
    logo_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="200" height="200">
  <circle cx="50" cy="50" r="48" fill="#1e4d6b" stroke="#c4a44a" stroke-width="4"/>
  <text x="50" y="45" font-family="Georgia, serif" font-size="28" fill="white" text-anchor="middle" font-weight="bold">ME</text>
  <text x="50" y="68" font-family="Georgia, serif" font-size="12" fill="#c4a44a" text-anchor="middle">Scripture</text>
</svg>'''
    with open(os.path.join(output_dir, "logo.svg"), "w") as f:
        f.write(logo_svg)
    print("Created: logo.svg")

    # Create favicon
    favicon_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <circle cx="16" cy="16" r="16" fill="#1e4d6b"/>
  <text x="16" y="16" font-family="Georgia, serif" font-size="14" fill="white" text-anchor="middle" dominant-baseline="central" font-weight="bold">M</text>
</svg>'''
    with open(os.path.join(output_dir, "favicon.svg"), "w") as f:
        f.write(favicon_svg)
    print("Created: favicon.svg")

if __name__ == "__main__":
    generate_avatars()
    print("\nAll avatars generated! Note: These are SVG placeholders.")
    print("For production, consider replacing with actual character illustrations.")
