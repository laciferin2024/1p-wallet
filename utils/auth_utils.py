import random
import hashlib
import secrets
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

from utils.helpers import generate_nonce, keccak256, generate_entropy_layers

class OneRoundVerifier:
    """
    A simplified, one-round version of the 1P authentication system.
    Use this for quick challenges where a full multi-round authentication is not needed.
    """
    def __init__(self, secret: str, direction_mapping: Dict[str, str],
                 colors: List[str], direction_map: Dict[str, str], domains: Dict[str, str]):
        self.secret = secret
        self.direction_mapping = direction_mapping
        self.colors = colors
        self.direction_map = direction_map
        self.domains = domains
        self.nonce = None
        self.color_map = {}

    def generate_challenge(self) -> Tuple[str, str]:
        """
        Generates a one-round challenge grid.

        Returns:
            Tuple containing (grid_html, expected_direction_code)
        """
        self.nonce = generate_nonce()
        entropy = generate_entropy_layers(self.nonce, 1)[0]

        # Build combined alphabet from all domains
        alphabet = ""
        for domain_chars in self.domains.values():
            alphabet += domain_chars
        alphabet = ''.join(set(alphabet))  # Remove duplicates

        # Create rotated alphabet based on entropy
        offset = entropy % len(alphabet)
        rotated = alphabet[offset:] + alphabet[:offset]

        # Create color mapping
        self.color_map = {rotated[i]: self.colors[i % len(self.colors)] for i in range(len(rotated))}

        # Determine expected solution
        assigned_color = self.color_map.get(self.secret, None)
        if assigned_color is None:
            expected = "S"  # Skip if secret character not in grid
        else:
            direction = self.direction_mapping.get(assigned_color, "Skip")
            expected = self.direction_map[direction]

        # Generate the grid HTML
        grid_html = self._generate_grid_html()

        return grid_html, expected

    def _generate_grid_html(self) -> str:
        """Generate HTML for the challenge grid."""
        chars_by_color = defaultdict(list)
        for ch, color in self.color_map.items():
            chars_by_color[color].append(ch)

        grid_html = """
        <div style="border: 2px solid #333; padding: 15px; margin: 10px; background: #f8f9fa; border-radius: 8px;">
        <h4>🎯 One-Round Authentication</h4>
        <p><strong>Find your secret character and note its color!</strong></p>
        """

        color_hex_map = {"red": "#FF0000", "green": "#00AA00", "blue": "#0066FF", "yellow": "#FFD700"}

        for color in self.colors:
            chars = chars_by_color[color]
            if chars:
                grid_html += f'<div style="margin: 8px 0;"><strong style="color: {color_hex_map[color]};">{color.upper()}:</strong> '
                for char in chars:
                    grid_html += f'<span style="color: {color_hex_map[color]}; font-size: 18px; margin: 2px; padding: 4px; background: white; border-radius: 4px;">{char}</span> '
                grid_html += '</div>'

        grid_html += '</div>'
        return grid_html

    def verify_solution(self, user_input: str, expected: str) -> bool:
        """
        Verify if the user's solution matches the expected direction.

        Args:
            user_input: User's input direction code ("U", "D", "L", "R", "S")
            expected: Expected direction code

        Returns:
            True if the authentication is successful, False otherwise
        """
        return user_input == expected

def run_one_round_authentication(secret: str, direction_mapping: Dict[str, str],
                               colors: List[str], direction_map: Dict[str, str],
                               domains: Dict[str, str]) -> Tuple[str, str]:
    """
    Helper function to run a single round of authentication.

    Args:
        secret: The user's secret character
        direction_mapping: Mapping of colors to directions
        colors: List of available colors
        direction_map: Mapping of direction names to codes
        domains: Available character domains

    Returns:
        Tuple containing (grid_html, expected_direction_code)
    """
    verifier = OneRoundVerifier(secret, direction_mapping, colors, direction_map, domains)
    return verifier.generate_challenge()