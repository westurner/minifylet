# minifylet

A Python tool for minifying JavaScript files into bookmarklets. It strips comments and whitespace, ensures URL safety, checks syntax (optional), and can wrap the code in a standard bookmarklet closures.

## Usage

```console
$ minifylet --help
usage: minifylet [-h] [-v] [-C] [--check-js | --no-check-js]
                 [--wrap | --no-wrap]
                 [input_file] [output_file]

Minify a JavaScript file into a bookmarklet.

positional arguments:
  input_file            Path to the input JavaScript file
  output_file           Path to the output minified file

options:
  -h, --help            show this help message and exit
  -v, --verbose         Enable verbose logging
  -C, --clipboard       Copy the minified bookmarklet to the clipboard
  --check-js, --no-check-js
                        Check syntax using Node.js
  --wrap, --no-wrap     Wrap the bookmarklet code in void((function(){
                        ... })())
```

## Features

- **Minification**: Removes comments and unnecessary whitespace.
- **URL Encoding**: Safely encodes characters for use in `javascript:` URLs.
- **Syntax Checking**: Verify bookmarklet syntax using Node.js (if installed).
- **Clipboard Support**: Copy the result directly to your clipboard.
- **Wrapping**: Automatically wrap code in `void((function(){ ... })())`.

## Development

Install dependencies:

```bash
pip install -e 'git+https://github.com/westurner/minifylet#egg=minifylet[dev]'
```

Run tests:

```bash
make test
```
