#!/usr/bin/env python3
"""
minifylet.cli -- Minify bookmarklet JS

Usage:

.. code:: sh

    minifylet --help
    minifylet bookmarket.js bookmarket.min.js

"""
import urllib.parse
import re
import argparse
import logging
import sys
import subprocess
import shutil
import os
import tempfile


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Safe chars: All printable ASCII except space, %, and # (which starts a fragment)
SAFE_CHARS = "".join(
    [chr(i) for i in range(33, 127) if chr(i) not in ["%", " ", "#"]]
)


def check_syntax(js_code):
    """
    Checks the syntax of the JavaScript code using Node.js.
    """
    if not shutil.which("node"):
        logger.error("Node.js is not installed. Cannot check syntax.")
        return False

    with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as tmp:
        tmp.write(js_code)
        tmp_path = tmp.name
        
    try:
        subprocess.run(['node', '--check', tmp_path], capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Syntax error in minified code:\n{e.stderr}")
        return False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def minify_code(js_code, wrap=True):
    """
    Minifies JavaScript code and converts it to a bookmarklet string.
    """
    # 1. Basic Minification: Remove single-line comments
    # Use lookbehind to ensure // is not preceded by : (to avoid matching URLs like https://)
    minified = re.sub(r"(?<!:)//.*", "", js_code)

    # 2. Remove multi-line comments
    minified = re.sub(r"/\*[\s\S]*?\*/", "", minified)

    # 3. Collapse multiple whitespaces and newlines into a single space
    minified = re.sub(r"\s+", " ", minified)

    # 4. Remove spaces around structural characters
    minified = re.sub(r"\s*([\{\}\(\)\[\]\=\+\-\*\/\;\:\,\<\>])\s*", r"\1", minified)

    # Remove 'javascript:' prefix if present, to avoid double prefixing
    minified = minified.strip()
    if minified.startswith("javascript:"):
        minified = minified[11:]

    if wrap:
        minified = f"void((function(){{{minified}}})())"

    # 5. URL Encode special characters (keeping essential JS safe)
    # We use quote to ensure characters like '#' or ' ' are browser-safe
    # We preserve common JS characters to keep the bookmarklet readable and shorter
    bookmarklet = "javascript:" + urllib.parse.quote(minified.strip(), safe=SAFE_CHARS)
    return bookmarklet


def copy_to_clipboard(text):
    """
    Copies text to the clipboard using available system tools.
    """
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return True
        elif sys.platform == "win32":
            subprocess.run(["clip"], input=text, text=True, check=True)
            return True
        elif sys.platform.startswith("linux"):
            if shutil.which("xclip"):
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text,
                    text=True,
                    check=True,
                )
                return True
            elif shutil.which("xsel"):
                subprocess.run(
                    ["xsel", "--clipboard", "--input"],
                    input=text,
                    text=True,
                    check=True,
                )
                return True
            elif shutil.which("wl-copy"):
                subprocess.run(["wl-copy"], input=text, text=True, check=True)
                return True
    except Exception as e:
        logger.warning(f"Could not copy to clipboard: {e}")
    return False


def minify_bookmarklet(input_file, output_file, to_clipboard=False, check_js=True, wrap=True):
    try:
        logger.info(f"Reading from {input_file}")
        with open(input_file, "r") as f:
            js_code = f.read()

        bookmarklet = minify_code(js_code, wrap=wrap)

        if check_js:
            # Extract code to check
            if bookmarklet.startswith("javascript:"):
                code_to_check = urllib.parse.unquote(bookmarklet[11:])
            else:
                code_to_check = bookmarklet
            
            if not check_syntax(code_to_check):
                sys.exit(1)

        logger.info(f"Writing to {output_file}")
        with open(output_file, "w") as f:
            f.write(bookmarklet)

        logger.info(f"Success! Minified bookmarklet saved to {output_file}")

        if to_clipboard:
            if copy_to_clipboard(bookmarklet):
                logger.info("Copied bookmarklet to clipboard!")
            else:
                logger.warning(
                    "Failed to copy to clipboard. Please copy it manually below."
                )

        print("\nCopy the content below into your bookmark URL:", file=sys.stderr)
        print("-" * 20, file=sys.stderr)
        print(bookmarklet)
        print("-" * 20, file=sys.stderr)

    except FileNotFoundError:
        logger.error(f"File not found: {input_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Minify a JavaScript file into a bookmarklet."
    )
    parser.add_argument(
        "input_file",
        help="Path to the input JavaScript file",
        nargs="?",
        default="srchq-bookmarklet.js",
    )
    parser.add_argument(
        "output_file",
        help="Path to the output minified file",
        nargs="?",
        default="srchq-bookmarklet.min.js",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "-C",
        "--clipboard",
        action="store_true",
        help="Copy the minified bookmarklet to the clipboard",
    )
    parser.add_argument(
        "--check-js",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Check syntax using Node.js",
    )
    parser.add_argument(
        "--wrap",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Wrap the bookmarklet code in void((function(){ ... })())",
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    minify_bookmarklet(
        args.input_file, args.output_file, args.clipboard, args.check_js, args.wrap
    )


if __name__ == "__main__":  # pragma: no cover
    main()
