# pixtess_converter.py
import argparse
import os
import sys
import re
import traceback
from collections import defaultdict
from PIL import Image

# Import utilities from the other file
try:
    # Indent level 1 (4 spaces)
    from pixtess_utils import (
        rgb_to_pixtess_code,
        pixtess_code_to_rgb,
        PXT_COLORS_RGB # Optional, for validation/info
    )
# Indent level 0
except ImportError:
    # Indent level 1
    print("Error: Could not import from pixtess_utils.py.", file=sys.stderr)
    print("Ensure both pixtess_converter.py and pixtess_utils.py are in the same directory.", file=sys.stderr)
    sys.exit(1)
# --- End of level 1 ---

# --- Encoding Function ---
# Indent level 0
def encode_image_to_pixtess(image_path, output_path=None):
    """
    Encodes an image file into a Pixtess string and prints or saves it.
    """
    # Indent level 1
    try: # Level 1 try
        # Indent level 2
        abs_image_path = os.path.abspath(image_path)
        if not os.path.exists(abs_image_path):
             # Indent level 3
             raise FileNotFoundError(f"Input image file not found: {abs_image_path}")
             # --- End of level 3 ---

        img = Image.open(abs_image_path).convert("RGB")
        width, height = img.size
        pixels = list(img.getdata())
        print(f"Image loaded: {width}x{height}, {len(pixels)} pixels.", file=sys.stderr)
        # --- End of level 2 ---
    except FileNotFoundError as e: # Level 1 except (matches try)
        # Indent level 2
        print(f"Error: {e}", file=sys.stderr)
        return None
        # --- End of level 2 ---
    except Exception as e: # Level 1 except (matches try)
        # Indent level 2
        print(f"Error loading image '{image_path}': {e}", file=sys.stderr)
        return None
        # --- End of level 2 ---
    # --- End of level 1 try/except block ---

    # Indent level 1 (main function logic continues)
    total_pixels = width * height
    if total_pixels == 0:
        # Indent level 2
        print("Error: Image has no pixels.", file=sys.stderr)
        return None
        # --- End of level 2 ---

    print("Converting pixels to Pixtess codes...", file=sys.stderr)
    pixtess_codes_per_pixel = [rgb_to_pixtess_code(rgb) for rgb in pixels]
    print("Pixel conversion done.", file=sys.stderr)

    print("Building palette...", file=sys.stderr)
    palette_list = sorted(list(set(pixtess_codes_per_pixel)))
    code_to_palette_index = {code: idx for idx, code in enumerate(palette_list)}
    print(f"Palette contains {len(palette_list)} unique codes.", file=sys.stderr)

    print("Generating data ranges...", file=sys.stderr)
    data_ranges = defaultdict(list)
    if pixels: # Check if there are any pixels to process
        # Still inside level 1
        current_run_code_idx = code_to_palette_index[pixtess_codes_per_pixel[0]]
        run_start_pixel_idx = 0
        for i in range(1, total_pixels):
            # Indent level 2 (inside for loop)
            pixel_code_idx = code_to_palette_index[pixtess_codes_per_pixel[i]]
            if pixel_code_idx != current_run_code_idx:
                # Indent level 3 (inside if)
                data_ranges[current_run_code_idx].append((run_start_pixel_idx, i - 1))
                current_run_code_idx = pixel_code_idx
                run_start_pixel_idx = i
                # --- End of level 3 ---
        # Add the last run (Level 1 Indent - after for loop)
        data_ranges[current_run_code_idx].append((run_start_pixel_idx, total_pixels - 1))
        # --- End of level 2 for loop ---
    print("Range generation done.", file=sys.stderr) # Level 1

    print("Formatting Pixtess string...", file=sys.stderr) # Level 1
    metadata_str = f'"RESOLUTION": "{width}x{height}", "TOPIC": "ENCODED_IMAGE", "SUBTOPIC": "{os.path.basename(image_path)}"'
    palette_str = ", ".join([f'"{code}"' for code in palette_list])
    data_items = []
    for idx in sorted(data_ranges.keys()): # Level 1 for loop
        # Indent level 2
        range_str = ", ".join([f'({start},{end})' for start, end in data_ranges[idx]])
        data_items.append(f'{idx}: [ {range_str} ]')
        # --- End of level 2 ---
    data_str = ", ".join(data_items) # Level 1

    pixtess_string = f'''PIXTESS[
  {{ // Metadata
    {metadata_str}
  }},

  PALETTE=[ // Palette Definition
    {palette_str}
  ],

  DATA={{ // Data mapping Palette Index to Coordinate Ranges
    {data_str}
  }}
]''' # Level 1 assignment

    print("Pixtess string formatted.", file=sys.stderr) # Level 1

    # Check if output path is provided
    if output_path: # Level 1 if
        # Indent level 2
        try: # Level 2 try
            # Indent level 3
            with open(output_path, 'w', encoding='utf-8') as f: # Specify encoding
                # Indent level 4
                f.write(pixtess_string)
            # Indent level 2 (after 'with' block)
            print(f"Pixtess string saved to: {output_path}", file=sys.stderr)
        except Exception as e: # Level 2 except (aligns with inner 'try')
            # Indent level 3
            print(f"Error saving Pixtess file '{output_path}': {e}", file=sys.stderr)
    else: # Level 1 else (aligns with 'if')
        # Indent level 2
        print(pixtess_string) # Print to standard output

    # Level 1 return
    return pixtess_string
    # --- End of encode_image_to_pixtess function ---

# --- Decoding Function ---
# Indent level 0
# Corrected decode_pixtess_string_to_image function (Improved Palette Parsing)
def decode_pixtess_string_to_image(pixtess_string, output_path):
    """
    Decodes a Pixtess string into an image object and saves it.
    Uses marker-based parsing and robust palette extraction.
    """
    # Indent level 1
    try: # Level 1 try (Outer)
        # Indent level 2 (Inside outer try)
        # --- Find major sections using markers ---
        pixtess_content = pixtess_string.strip()
        if not pixtess_content.startswith("PIXTESS[") or not pixtess_content.endswith("]"):
            raise ValueError("String does not start/end with PIXTESS[]")

        content_inside_brackets = pixtess_content[len("PIXTESS["):-1].strip()

        # Find Metadata Section {...},
        metadata_start_brace = content_inside_brackets.find('{')
        if metadata_start_brace == -1: raise ValueError("Metadata opening '{' not found.")
        brace_level = 0
        metadata_end_brace = -1
        for i, char in enumerate(content_inside_brackets[metadata_start_brace:]):
             if char == '{': brace_level += 1
             elif char == '}':
                 brace_level -= 1
                 if brace_level == 0:
                     metadata_end_brace = metadata_start_brace + i
                     break
        if metadata_end_brace == -1: raise ValueError("Metadata closing '}' not found.")
        comma_after_metadata = content_inside_brackets.find(',', metadata_end_brace)
        if comma_after_metadata == -1: raise ValueError("Comma after metadata block '},' not found.")
        metadata_block_content = content_inside_brackets[metadata_start_brace + 1 : metadata_end_brace]

        # Find Palette Section PALETTE=[...],
        palette_marker = "PALETTE=["
        palette_start = content_inside_brackets.find(palette_marker, comma_after_metadata)
        if palette_start == -1: raise ValueError("PALETTE=[ marker not found.")
        palette_content_start = palette_start + len(palette_marker)
        palette_end_bracket = -1
        bracket_level = 0
        for i, char in enumerate(content_inside_brackets[palette_content_start:]):
             if char == '[': bracket_level += 1
             elif char == ']':
                 bracket_level -= 1
                 if bracket_level == -1:
                      palette_end_bracket = palette_content_start + i
                      break
        if palette_end_bracket == -1: raise ValueError("Palette closing ']' not found.")
        palette_content_part = content_inside_brackets[palette_content_start:palette_end_bracket].strip() # Includes comments/whitespace now
        comma_after_palette = content_inside_brackets.find(',', palette_end_bracket)
        if comma_after_palette == -1: raise ValueError("Comma after palette block '],' not found.")

        # Find Data Section DATA={...}
        data_marker = "DATA={"
        data_start = content_inside_brackets.find(data_marker, comma_after_palette)
        if data_start == -1: raise ValueError("DATA={ marker not found.")
        data_content_start = data_start + len(data_marker)
        data_end = -1
        brace_level = 0
        for i, char in enumerate(content_inside_brackets[data_content_start:]):
             if char == '{': brace_level += 1
             elif char == '}':
                 brace_level -= 1
                 if brace_level == -1:
                     data_end = data_content_start + i
                     break
        if data_end == -1: raise ValueError("Data closing '}' not found or malformed.")
        data_content = content_inside_brackets[data_content_start:data_end].strip()

        # --- Now parse the extracted content ---
        # Parse Metadata
        width, height = 0, 0
        res_match = re.search(r'"RESOLUTION":\s*"(\d+)x(\d+)"', metadata_block_content)
        if res_match:
            width = int(res_match.group(1))
            height = int(res_match.group(2))
        if width <= 0 or height <= 0:
             raise ValueError("Invalid or missing RESOLUTION in metadata content.")
        print(f"Decoding image: {width}x{height}", file=sys.stderr)

        # Parse Palette using regex findall to extract only quoted "0x..." strings
        palette_list = re.findall(r'"(0x[1-6a-fA-F0-9]+)"', palette_content_part)
        print(f"Palette size: {len(palette_list)}", file=sys.stderr)
        if not palette_list:
             print("Warning: No valid Pixtess codes found in PALETTE section.", file=sys.stderr)
        palette_rgbs = [pixtess_code_to_rgb(code) for code in palette_list]
        print("Palette colors converted to RGB.", file=sys.stderr)

        # Create image
        img = Image.new('RGB', (width, height), color=(0,0,0))
        img_data = img.load()

        # Parse Data and fill pixels
        print("Applying colors based on data ranges...", file=sys.stderr)
        data_entries = re.findall(r'(\d+):\s*\[([^\]]*)\]', data_content)
        processed_pixels = 0
        total_pixels = width * height

        for idx_str, ranges_str in data_entries: # Level 2 for loop
            # Indent level 3
            palette_index = int(idx_str)
            if palette_index >= len(palette_rgbs):
                print(f"Warning: Palette index {palette_index} out of bounds.", file=sys.stderr)
                continue

            rgb_color = palette_rgbs[palette_index]

            range_tuples = re.findall(r"\(\s*(\d+)\s*,\s*(\d+)\s*\)", ranges_str)
            for start_str, end_str in range_tuples: # Level 3 inner for loop
                # Indent level 4
                start_idx = int(start_str)
                end_idx = int(end_str)
                if start_idx > end_idx:
                    print(f"Warning: Invalid range ({start_idx}, {end_idx}) for palette index {palette_index}. Skipping.", file=sys.stderr)
                    continue

                for p_idx in range(start_idx, end_idx + 1): # Level 4 innermost for loop
                    # Indent level 5
                    if p_idx < total_pixels:
                        # Indent level 6
                        y = p_idx // width
                        x = p_idx % width
                        img_data[x, y] = rgb_color
                        processed_pixels +=1
                        # --- End Level 6 ---
                    else:
                        # Indent level 6
                         print(f"Warning: Pixel index {p_idx} out of bounds for {width}x{height}.", file=sys.stderr)
                         # --- End Level 6 ---
                # --- End Level 5 ---
            # --- End Level 4 ---
        # --- End Level 3 ---

        # Level 2 (after outer for loop)
        print(f"Applied colors to {processed_pixels} pixels.", file=sys.stderr)
        if processed_pixels != total_pixels:
            print(f"Warning: Number of pixels processed ({processed_pixels}) does not match expected total ({total_pixels}). Image might be incomplete.", file=sys.stderr)

        # Save the image
        try: # Level 2 try (Inner try for saving)
            # Level 3
            img.save(output_path)
            print(f"Decoded image saved to: {output_path}", file=sys.stderr)
            return True
            # --- End Level 3 ---
        except Exception as e: # Level 2 except (Matches inner try)
            # Level 3
            print(f"Error saving decoded image '{output_path}': {e}", file=sys.stderr)
            return False
            # --- End Level 3 ---
        # --- End Level 2 ---
    # --- Outer except block (Level 1 Indent - matches outer try) ---
    except Exception as e:
        # Indent level 2
        print(f"Error decoding Pixtess string: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return False
        # --- End Level 2 ---
# --- End of decode_pixtess_string_to_image function ---

# --- Main Execution ---
# Indent level 0
def main():
    # Indent level 1
    parser = argparse.ArgumentParser(description="Encode images to PIXTESS format or decode PIXTESS files to images.")
    parser.add_argument('mode', choices=['encode', 'decode'], help="Operation mode: encode or decode.")
    parser.add_argument('-i', '--input', required=True, help="Input file path (image for encode, .pixtess file for decode).")
    parser.add_argument('-o', '--output', help="Output file path (optional). If encoding and omitted, prints to stdout. If decoding and omitted, saves as 'decoded_<input_base>.png'.")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.mode == 'encode':
        print(f"Encoding '{args.input}'...", file=sys.stderr)
        encode_image_to_pixtess(args.input, args.output)

    elif args.mode == 'decode':
        print(f"Decoding '{args.input}'...", file=sys.stderr)
        output_image_path = args.output
        if not output_image_path:
            base_name = os.path.splitext(os.path.basename(args.input))[0]
            # Ensure output is PNG
            if not base_name.lower().endswith(('.pixtess', '.txt')):
                 output_image_path = f"decoded_{base_name}.png"
            else:
                 # Strip potential .pixtess or .txt before adding .png
                 output_image_path = f"decoded_{base_name.rsplit('.', 1)[0]}.png"


        try: # Level 2 try
            # Indent level 3
            # Read file with explicit encoding, handling potential BOMs
            with open(args.input, 'r', encoding='utf-8-sig') as f:
                # Indent level 4
                pixtess_content = f.read()
            if not decode_pixtess_string_to_image(pixtess_content, output_image_path):
                 # Indent level 4
                 print("Decoding process failed.", file=sys.stderr)
                 sys.exit(1)
                 # --- End Level 4 ---
            # --- End Level 3 ---
        except Exception as e: # Level 2 except
            # Indent level 3
            print(f"Error reading or processing Pixtess file '{args.input}': {e}", file=sys.stderr)
            sys.exit(1)
            # --- End Level 3 ---
        # --- End Level 2 ---
    # --- End Level 1 ---
# --- End of main function ---

# --- Script entry point (Level 0 Indent) ---
if __name__ == "__main__":
    # Indent level 1
    main()
    # --- End Level 1 ---