"""
minifylet.tests.test_cli
"""
import pytest
import urllib.parse
import sys
import shutil
import os
import glob
import subprocess
import argparse
from minifylet.cli import (
    minify_code,
    copy_to_clipboard,
    check_syntax,
    minify_bookmarklet,
    main,
    SAFE_CHARS,
)


@pytest.fixture
def mock_open_file(mocker):
    return mocker.patch("builtins.open", mocker.mock_open(read_data="var x = 1;"))


@pytest.fixture
def mock_exit(mocker):
    return mocker.patch("sys.exit")


@pytest.mark.parametrize(
    "js_code, expected_inner, wrap",
    [
        ("var x = 1; // comment", "var x=1;", False),
        (
            "var x = 1; /* comment \n more comment */ var y = 2;",
            "var x=1;var y=2;",
            False,
        ),
        ("  var   x   =   1;  ", "var x=1;", False),
        ("if ( x == 1 ) { y = 2; }", "if(x==1){y=2;}", False),
        (
            """
    (function() {
        // This is a comment
        var x = 10;
        /* Multi-line
           comment */
        if (x > 5) {
            alert('Hello');
        }
    })();
    """,
            "(function(){var x=10;if(x>5){alert('Hello');}})();",
            False,
        ),
        ("javascript:(function(){})();", "(function(){})();", False),
        ("var color = '#fff';", "var color='#fff';", False),
        ('var url = "https://google.com";', 'var url="https://google.com";', False),
        ("alert(1);", "void((function(){alert(1);})())", True),
    ],
)
def test_minify_code_scenarios(js_code, expected_inner, wrap):
    """Test various code minification scenarios."""
    expected = "javascript:" + urllib.parse.quote(expected_inner, safe=SAFE_CHARS)
    assert minify_code(js_code, wrap=wrap) == expected
    if "'#fff'" in expected_inner:
        assert "%23" in minify_code(js_code, wrap=wrap)


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js not installed")
@pytest.mark.parametrize(
    "filepath",
    glob.glob(os.path.join(os.path.dirname(__file__), "data", "*-bookmarklet.js")),
)
def test_bookmarklet_syntax(filepath):
    """Integration test: Verify minified bookmarklets are valid JS syntax using Node.js."""
    with open(filepath, "r") as f:
        js_code = f.read()

    minified_url = minify_code(js_code)
    code_to_check = (
        urllib.parse.unquote(minified_url[11:])
        if minified_url.startswith("javascript:")
        else minified_url
    )
    assert check_syntax(code_to_check), f"Syntax error for {os.path.basename(filepath)}"


def test_check_syntax_tempfile_cleanup(mocker):
    """Verify check_syntax creates/removes temp files correctly."""
    mocker.patch("shutil.which", return_value="/usr/bin/node")
    mock_run = mocker.patch("subprocess.run")

    check_syntax("code")

    # Verify subprocess called with a temp file ending in .js
    assert mock_run.called
    args = mock_run.call_args[0][0]
    assert args[0] == "node"
    assert args[1] == "--check"
    temp_path = args[2]
    assert temp_path.endswith(".js")
    # File should be deleted by the time check_syntax returns
    assert not os.path.exists(temp_path)


def test_check_syntax_node_missing(mocker):
    """Should return False if node is missing."""
    mocker.patch("shutil.which", return_value=None)
    assert check_syntax("var x=1;") is False


def test_check_syntax_error(mocker):
    """Should return False on node syntax check failure."""
    mocker.patch("shutil.which", return_value="/usr/bin/node")
    mocker.patch(
        "subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "node", stderr="Syntax Error"),
    )
    assert check_syntax("invalid code") is False


def test_copy_to_clipboard_integration():
    """Integration test using actual system clipboard tools."""
    # Simple check if any supported tool exists
    tools = ["pbcopy", "clip", "xclip", "xsel", "wl-copy"]
    if not any(shutil.which(t) for t in tools):
        pytest.skip("No supported clipboard tool found")

    if sys.platform == "linux" and not (
        shutil.which("xclip") or shutil.which("xsel") or shutil.which("wl-copy")
    ):
        pytest.skip("No linux clipboard tool")

    try:
        copy_to_clipboard("test")
    except Exception:
        pytest.fail("copy_to_clipboard crashed integration test")


@pytest.mark.parametrize(
    "platform, tool, cmd",
    [
        ("darwin", None, ["pbcopy"]),
        ("win32", None, ["clip"]),
        ("linux", "xclip", ["xclip", "-selection", "clipboard"]),
        ("linux", "xsel", ["xsel", "--clipboard", "--input"]),
        ("linux", "wl-copy", ["wl-copy"]),
    ],
)
def test_copy_to_clipboard_success(mocker, platform, tool, cmd):
    """Test clipboard command invocation for different platforms."""
    mocker.patch("sys.platform", platform)
    mocker.patch("shutil.which", side_effect=lambda x: x == tool)
    mock_run = mocker.patch("subprocess.run")

    assert copy_to_clipboard("text") is True
    mock_run.assert_called_with(cmd, input="text", text=True, check=True)


def test_copy_to_clipboard_failure(mocker):
    """Should return False upon exception."""
    mocker.patch("sys.platform", "darwin")
    mocker.patch("subprocess.run", side_effect=Exception("Copy failed"))
    assert copy_to_clipboard("text") is False


@pytest.mark.parametrize(
    "to_clipboard, copy_result, expect_warning",
    [
        (False, None, False),  # Standard success (no clipboard)
        (True, True, False),  # Clipboard success
        (True, False, True),  # Clipboard failure
    ],
)
def test_minify_bookmarklet_execution(
    mocker, mock_open_file, to_clipboard, copy_result, expect_warning
):
    """Verify minify_bookmarklet workflow, including file I/O and clipboard logic."""
    mocker.patch("minifylet.cli.check_syntax", return_value=True)
    mock_copy = mocker.patch(
        "minifylet.cli.copy_to_clipboard", return_value=copy_result
    )
    mock_logger = mocker.patch("minifylet.cli.logger")
    mocker.patch("minifylet.cli.sys.stderr")

    minify_bookmarklet(
        "in.js", "out.js", to_clipboard=to_clipboard, check_js=True, wrap=True
    )

    mock_open_file.assert_called_with("out.js", "w")
    if to_clipboard:
        mock_copy.assert_called()
    else:
        mock_copy.assert_not_called()

    if expect_warning:
        mock_logger.warning.assert_called()


@pytest.mark.parametrize(
    "exception, expected_exit",
    [
        (FileNotFoundError, 1),
        (Exception("Disk error"), 1),
    ],
)
def test_minify_bookmarklet_exceptions(mock_exit, mocker, exception, expected_exit):
    """Verify correct exit codes on file/disk errors."""
    mocker.patch("builtins.open", side_effect=exception)
    mocker.patch("minifylet.cli.logger")
    minify_bookmarklet("in.js", "out.js")
    mock_exit.assert_called_with(expected_exit)


def test_minify_bookmarklet_syntax_fail(mock_exit, mocker):
    """Should exit if syntax check fails."""
    mocker.patch("builtins.open", mocker.mock_open(read_data="bad code"))
    mocker.patch("minifylet.cli.check_syntax", return_value=False)

    minify_bookmarklet("in.js", "out.js", check_js=True)
    mock_exit.assert_called_with(1)


def test_minify_bookmarklet_no_javascript_prefix(mocker):
    """Verify logic for extracting code to check when 'javascript:' prefix differs."""
    mocker.patch("builtins.open", mocker.mock_open(read_data="var x = 1;"))
    mock_check = mocker.patch("minifylet.cli.check_syntax", return_value=True)
    mocker.patch("minifylet.cli.minify_code", return_value="raw_code")
    mocker.patch("minifylet.cli.sys.stderr")

    minify_bookmarklet("in.js", "out.js", check_js=True)
    mock_check.assert_called_with("raw_code")


@pytest.mark.parametrize(
    "verbose, set_level_called",
    [
        (False, False),
        (True, True),
    ],
)
def test_main(mocker, verbose, set_level_called):
    """Verify main argument parsing and logging setup."""
    mock_args = mocker.patch("argparse.ArgumentParser.parse_args")
    mock_minify = mocker.patch("minifylet.cli.minify_bookmarklet")
    mock_logger = mocker.patch("minifylet.cli.logger")

    mock_args.return_value = argparse.Namespace(
        input_file="in.js",
        output_file="out.js",
        verbose=verbose,
        clipboard=False,
        check_js=True,
        wrap=True,
    )
    main()
    mock_minify.assert_called_with("in.js", "out.js", False, True, True)
    if set_level_called:
        mock_logger.setLevel.assert_called()
    else:
        mock_logger.setLevel.assert_not_called()
