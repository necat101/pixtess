# Pixtess Image Converter

## Description

This project provides a Python tool to encode standard image files (like PNG, JPG) into the custom Pixtess text-based image format, and decode Pixtess files back into viewable PNG images.

Pixtess is a conceptual format designed to represent image data as structured text, incorporating a color palette and run-length encoding (via coordinate ranges) for compression. It uses an abstract color model based on 6 base components (Blue, Green, Red, Yellow, White, Black) and allows specifying percentage mixes using a modulation system.

## Features

* **Encode:** Convert standard image files (readable by Pillow) into `.pixtess` text files.
* **Decode:** Convert `.pixtess` text files back into viewable `.png` image files.
* **Internal Compression:** Uses Palette encoding and Run-Length Encoding (via coordinate ranges) within the text format itself.
* **Color Model:** Implements the Pixtess color model with 6 bases and percentage modulation (current encoding uses a "Phase 2" heuristic algorithm - see `pixtess_utils.py`).
* **Command-Line Interface:** Simple CLI for encode/decode operations.

## Project Structure

```
pixtess_converter/
├── requirements.txt       # Python dependencies
├── pixtess_utils.py       # Core Pixtess logic (parsing, color conversion)
├── pixtess_converter.py   # Main script with CLI, file I/O
└── README.md              # This file
```

## Setup

1.  **Clone or Download:** Get the project files.
    ```bash
    # Example using git:
    # git clone https://github.com/necat101/pixtess.git
    # cd pixtess_converter
    ```
    (Or simply download `pixtess_converter.py`, `pixtess_utils.py`, and `requirements.txt` into the same folder).

2.  **Install Dependencies:** Navigate to the project folder in your terminal and install the required library (Pillow) using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the converter from your terminal within the project directory.

**Encoding (Image File -> Pixtess File):**

```bash
python pixtess_converter.py encode -i <input_image_path> -o <output_pixtess_path>
```

* Replace `<input_image_path>` with the path to your image (e.g., `my_cat.png`, `photos/landscape.jpg`).
* Replace `<output_pixtess_path>` with the desired name for the output Pixtess file (e.g., `my_cat.pixtess`).
* If `-o` is omitted, the Pixtess string will be printed directly to the console.

**Decoding (Pixtess File -> PNG Image):**

```bash
python pixtess_converter.py decode -i <input_pixtess_path> -o <output_image_path>
```

* Replace `<input_pixtess_path>` with the path to your `.pixtess` file (e.g., `my_cat.pixtess`).
* Replace `<output_image_path>` with the desired name for the output PNG image (e.g., `decoded_cat.png`).
* If `-o` is omitted, the output file will be named `decoded_<input_base_name>.png` (e.g., decoding `my_cat.pixtess` creates `decoded_my_cat.png`).

## Detailed Instructions for Windows 11 Users

If you're using Windows 11 and are less familiar with the command line, follow these steps:

1.  **Install Python:**
    * The easiest way is often via the Microsoft Store. Search for "Python" (choose the latest stable version, e.g., Python 3.11 or 3.12) and install it. This usually sets up `pip` and adds Python to your system PATH automatically.
    * Alternatively, download from [python.org](https://www.python.org/downloads/windows/), run the installer, and **make sure to check the box that says "Add Python to PATH"** during installation.
    * **Verify:** Open Command Prompt (search for `cmd` in the Start menu) and type `python --version` then press Enter. You should see a version number. Type `pip --version` and press Enter. You should see pip's version. If these commands don't work, Python wasn't added to your PATH correctly during installation.

2.  **Download Project Files:**
    * Create a folder for the project, for example, `C:\Users\YourUsername\Documents\PixtessConverter`.
    * Save the three files (`pixtess_converter.py`, `pixtess_utils.py`, `requirements.txt`) into that folder.

3.  **Open Command Prompt in Your Project Folder:**
    * Navigate to your project folder in File Explorer (e.g., `Documents\PixtessConverter`).
    * Click in the address bar at the top of the File Explorer window.
    * Type `cmd` and press Enter. This will open Command Prompt directly in that folder.

4.  **Install Dependencies:**
    * In the Command Prompt window you just opened, type the following command and press Enter:
        ```cmd
        pip install -r requirements.txt
        ```
    * Wait for it to download and install Pillow.

5.  **Run the Converter:**
    * Make sure the image file you want to encode (or the `.pixtess` file you want to decode) is accessible. You can either place it in the same `PixtessConverter` folder or use its full path.
    * **Encoding Example (Saving to a file):**
        ```cmd
        python pixtess_converter.py encode -i "C:\Path\To\Your Pictures\my_image.png" -o "encoded_image.pixtess"
        ```
        *(Replace `"C:\Path\To\Your Pictures\my_image.png"` with the actual path to your image. Use quotes if the path contains spaces. The output file `encoded_image.pixtess` will be saved in your `PixtessConverter` folder unless you specify a different path for `-o`)*.
    * **Encoding Example (Printing to screen):**
        ```cmd
        python pixtess_converter.py encode -i "my_image_in_same_folder.jpg"
        ```
    * **Decoding Example:**
        ```cmd
        python pixtess_converter.py decode -i "encoded_image.pixtess" -o "decoded_image.png"
        ```
        *(This assumes `encoded_image.pixtess` is in the current folder. It will save `decoded_image.png` in the same folder).*
    * **Decoding Example (Default Output Name):**
        ```cmd
        python pixtess_converter.py decode -i "encoded_image.pixtess"
        ```
        *(This will create `decoded_encoded_image.png`)*.

---

## Pixtess Format Summary

The Pixtess format stores image data textually within a `PIXTESS[...]` structure containing:

1.  **Metadata:** A dictionary with image info, including the mandatory `"RESOLUTION": "WxH"`.
2.  **Palette:** An ordered list of all unique Pixtess color codes (`"0x..."`) used in the image.
3.  **Data:** A dictionary mapping each palette index to a list of `(start, end)` pixel coordinate ranges where that color appears (using row-major pixel indexing).

*(See Pixtess Format Specification document for full details on the structure and color code definitions).*

## Current Limitations & Future Work

* The current RGB -> Pixtess encoding algorithm (`rgb_to_pixtess_code` in `pixtess_utils.py`) uses heuristics (based on HSL) to map colors. While better than simple quantization, it may not perfectly represent all complex color mixes or subtle gradients. Further refinement of this algorithm could improve color fidelity.
* Error handling for malformed Pixtess files during decoding could be enhanced.
* Consider adding support for RGBA (handling transparency).

This format was designed for an upcoming update to my MFANN models, where i try to train previously text-only models on pixtess data, and have a handler program run on the frontend to convert back into a standard rgb png/jpg. however, this format can very well be used for other things!

## License


MIT License

Copyright (c) [2025] [Makhi Burroughs]
