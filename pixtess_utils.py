# pixtess_utils.py
import colorsys
import math
import re
import sys
from collections import defaultdict

# --- Configuration ---
PXT_COLORS_RGB = { # Used mainly for decoding, but useful reference
    1: (0, 0, 255),    # Blue
    2: (0, 255, 0),    # Green
    3: (255, 0, 0),    # Red
    4: (255, 255, 0),  # Yellow
    5: (255, 255, 255),# White
    6: (0, 0, 0)       # Black
}

# --- Thresholds for Phase 2 Encoding ---
SAT_THRESHOLD_LOW = 0.10       # Below this, it's grayscale
LIGHTNESS_THRESHOLD_HIGH = 0.80 # Above this, add White
LIGHTNESS_THRESHOLD_LOW = 0.20  # Below this, add Black

# --- Helper Functions ---

def get_modulator(percentage_first_component):
    """Calculates the Pixtess modulator string for a component's percentage."""
    p = max(0.0, min(100.0, percentage_first_component))
    if math.isclose(p, 50.0): return "f0"
    diff = p - 50.0
    value = min(9, max(0, int(round(abs(diff) / 5.0))))
    char = 'f' if diff >= 0 else 'a'
    return f"{char}{value}"

def parse_pixtess_code(pxt_code):
    """Parses a Pixtess code string."""
    if not isinstance(pxt_code, str) or not pxt_code.startswith("0x"):
         raise ValueError(f"Invalid Pixtess code format: {pxt_code}")
    hex_part = pxt_code[2:]
    component_str = ""
    modulator_str = ""
    for i, char in enumerate(hex_part):
        if char.isdigit() and 1 <= int(char) <= 6: component_str += char
        else: modulator_str = hex_part[i:]; break
    if not component_str: raise ValueError(f"No valid components: {pxt_code}")
    components = [int(c) for c in component_str]
    modulators = []
    if modulator_str:
        if len(modulator_str) % 2 != 0: raise ValueError(f"Invalid modulator length: {pxt_code}")
        try:
            for i in range(0, len(modulator_str), 2):
                mod_char = modulator_str[i]
                mod_val = int(modulator_str[i+1])
                if mod_char not in ('a', 'f') or not (0 <= mod_val <= 9): raise ValueError("Invalid modulator char/value")
                modulators.append((mod_char, mod_val))
        except (ValueError, IndexError): raise ValueError(f"Invalid modulator format: {pxt_code}")
    n_colors = len(components)
    if n_colors > 1 and modulator_str and len(modulators) != n_colors - 1: raise ValueError(f"Expected {n_colors - 1} modulators, found {len(modulators)}: {pxt_code}")
    if n_colors == 1 and modulator_str: raise ValueError(f"Modulators not allowed for single component: {pxt_code}")
    return components, modulators

def get_pixtess_percentages(components, modulators):
    """Calculates percentages from components and modulators."""
    percentages = defaultdict(float)
    n_colors = len(components)
    if n_colors == 0: raise ValueError("Empty components list.")
    if not modulators:
        if n_colors > 0:
             default_perc = 1.0 / n_colors
             for comp in components: percentages[comp] = default_perc
        return percentages
    if len(modulators) != n_colors - 1: raise ValueError(f"Mismatch modulators ({len(modulators)}) vs components ({n_colors})")
    total_percentage_so_far = 0
    for i in range(n_colors - 1):
        comp = components[i]
        mod_char, mod_val = modulators[i]
        percentage = 50.0 + (5.0 * mod_val) if mod_char == 'f' else 50.0 - (5.0 * mod_val)
        percentage = max(0.0, min(100.0, percentage))
        current_p = percentage / 100.0
        if total_percentage_so_far + current_p > 1.0: current_p = max(0.0, 1.0 - total_percentage_so_far)
        percentages[comp] = current_p
        total_percentage_so_far += current_p
    last_comp = components[-1]
    percentages[last_comp] = max(0.0, 1.0 - total_percentage_so_far)
    return percentages

# --- Color Conversion Functions ---

def pixtess_code_to_rgb(pxt_code):
    """Converts a Pixtess code string into an RGB tuple."""
    try:
        components, modulators = parse_pixtess_code(pxt_code)
        percentages = get_pixtess_percentages(components, modulators)
    except ValueError as e:
        print(f"Warning: Could not parse Pixtess code '{pxt_code}'. Using Black. Error: {e}", file=sys.stderr)
        return (0, 0, 0)
    r_final, g_final, b_final = 0.0, 0.0, 0.0
    for comp, percentage in percentages.items():
         if comp in PXT_COLORS_RGB:
             base_rgb = PXT_COLORS_RGB[comp]
             r_final += percentage * base_rgb[0]
             g_final += percentage * base_rgb[1]
             b_final += percentage * base_rgb[2]
    rgb_color = (int(max(0, min(255, r_final))),
                 int(max(0, min(255, g_final))),
                 int(max(0, min(255, b_final))))
    return rgb_color

# --- Updated Phase 2 Encoding Function ---
def rgb_to_pixtess_code(rgb):
    """
    Converts an RGB tuple into a Pixtess code string (Phase 2).
    Handles primary hues, simple mixes, basic W/B shading, up to 3 components.
    """
    r, g, b = rgb
    try:
        r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
        h, l, s = colorsys.rgb_to_hls(r_norm, g_norm, b_norm)
        hue_deg = h * 360
    except (TypeError, ValueError):
        print(f"Warning: Invalid RGB {rgb} or HLS conversion failed. Defaulting to Black.", file=sys.stderr)
        return "0x6"

    # 1. Grayscale Check
    if s < SAT_THRESHOLD_LOW:
        if l >= LIGHTNESS_THRESHOLD_HIGH: return "0x5" # White
        elif l <= LIGHTNESS_THRESHOLD_LOW: return "0x6" # Black
        else:
            pW = l * 100.0
            mod = get_modulator(pW)
            return f"0x56{mod}"

    # 2. Color: Identify Hue Component(s)
    hue_components = []
    # Define hue ranges carefully to cover 0-360
    if 0 <= hue_deg < 15:       hue_components = [3]       # Red start
    elif 15 <= hue_deg < 45:    hue_components = [3, 4]    # Orange -> R+Y
    elif 45 <= hue_deg < 75:    hue_components = [4]       # Yellow
    elif 75 <= hue_deg < 105:   hue_components = [2, 4]    # Lime -> G+Y
    elif 105 <= hue_deg < 150:  hue_components = [2]       # Green
    elif 150 <= hue_deg < 210:  hue_components = [1, 2]    # Cyan -> B+G
    elif 210 <= hue_deg < 270:  hue_components = [1]       # Blue
    elif 270 <= hue_deg < 330:  hue_components = [1, 3]    # Magenta -> B+R
    elif 330 <= hue_deg < 345:  hue_components = [3]       # Red end part 1
    elif 345 <= hue_deg <= 360: hue_components = [3]       # Red end part 2 (includes 360)
    # --- Add a final else for robustness ---
    else:
        print(f"Warning: Hue {hue_deg:.2f} from HLS({h:.2f}, {l:.2f}, {s:.2f}) fell outside defined ranges (0-360). Defaulting to Black.", file=sys.stderr)
        hue_components = [6] # Fallback to Black

    # --- The separate check 'if not hue_components:' is now removed ---

    # 3. Add White/Black Component?
    shade_component = None
    pShade = 0.0
    if l > LIGHTNESS_THRESHOLD_HIGH:
        shade_component = 5 # White
        denominator = (1.0 - LIGHTNESS_THRESHOLD_HIGH)
        pShade = 50.0 + 50.0 * ((l - LIGHTNESS_THRESHOLD_HIGH) / denominator) if denominator > 0 else 100.0
        pShade = min(99.9, pShade)
    elif l < LIGHTNESS_THRESHOLD_LOW:
        shade_component = 6 # Black
        denominator = LIGHTNESS_THRESHOLD_LOW
        pShade = 50.0 + 50.0 * ((LIGHTNESS_THRESHOLD_LOW - l) / denominator) if denominator > 0 else 100.0
        pShade = min(99.9, pShade)

    final_components = list(hue_components)
    if shade_component is not None and shade_component not in final_components:
        final_components.append(shade_component)

    # 4. Order and Calculate Percentages/Modulators
    final_components.sort()
    n_final = len(final_components)
    percentages = {} # Stores percentage (0-100)

    if n_final == 1:
        percentages[final_components[0]] = 100.0
    elif n_final == 2:
        c1, c2 = final_components
        if c2 == 5: # Hue + White
            pW = pShade; pHue = 100.0 - pW
            percentages[c1] = pHue; percentages[c2] = pW
        elif c2 == 6: # Hue + Black
            pBk = pShade; pHue = 100.0 - pBk
            percentages[c1] = pHue; percentages[c2] = pBk
        else: # Hue1 + Hue2
            percentages[c1] = 50.0; percentages[c2] = 50.0
    elif n_final == 3: # Hue1 + Hue2 + (W or Bk)
        c1, c2, c3 = final_components
        pColor = max(0.0, 100.0 - pShade)
        if c3 == 5: percentages[c3] = pShade
        elif c3 == 6: percentages[c3] = pShade
        else: # Fallback if c3 is not 5 or 6 (shouldn't happen)
            percentages[c1] = 100.0; n_final = 1; final_components = [c1]

        if n_final == 3:
            percentages[c1] = pColor / 2.0
            percentages[c2] = pColor / 2.0
            # Normalize
            current_sum = percentages[c1] + percentages[c2] + percentages[c3]
            if current_sum > 0 and not math.isclose(current_sum, 100.0):
                norm_factor = 100.0 / current_sum
                percentages[c1] *= norm_factor
                percentages[c2] *= norm_factor
                percentages[c3] *= norm_factor

    # 5. Build final code string
    base_code_str = "0x" + "".join(map(str, final_components))
    modulators_str = ""
    if n_final > 1:
        for i in range(n_final - 1):
            comp_to_modulate = final_components[i]
            percent = percentages.get(comp_to_modulate, 0.0)
            modulators_str += get_modulator(percent)

    return base_code_str + modulators_str