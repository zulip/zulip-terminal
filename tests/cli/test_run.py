import pytest
from zulipterminal.cli.run import main, in_color, THEMES
from zulipterminal.model import ServerConnectionFailure


@pytest.mark.parametrize('color, code', [
    ('red', '\x1b[91m'),
    ('green', '\x1b[92m'),
    ('yellow', '\x1b[93m'),
    ('blue', '\x1b[94m'),
    ('purple', '\x1b[95m'),
    ('cyan', '\x1b[96m'),
])
def test_in_color(color, code, text="some text"):
    assert in_color(color, text) == code + text + "\x1b[0m"


@pytest.mark.parametrize('options', ['-h', '--help'])
def test_main_help(capsys, options):
    with pytest.raises(SystemExit):
        main([options])

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")

    assert lines[0].startswith('usage: ')

    required_arguments = {
        '--theme THEME, -t THEME',
        '-h, --help',
        '-d, --debug',
        '--profile',
        '--config-file CONFIG_FILE, -c CONFIG_FILE'
    }
    optional_argument_lines = {line[2:] for line in lines
                               if len(line) > 2 and line[2] == '-'}
    for line in optional_argument_lines:
        assert any(line.startswith(arg) for arg in required_arguments)

    assert captured.err == ""


@pytest.fixture
def minimal_zuliprc(tmpdir):
    zuliprc_path = str(tmpdir) + "/zuliprc"
    with open(zuliprc_path, "w") as f:
        f.write("[api]")  # minimal to avoid Exception
    return zuliprc_path


def test_valid_zuliprc_but_no_connection(capsys, mocker, minimal_zuliprc,
                                         server_connection_error="some_error"):
    mocker.patch('zulipterminal.core.Controller.__init__',
                 side_effect=ServerConnectionFailure(server_connection_error))

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc])
        assert str(e.value) == '1'

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        "Loading with:",
        "   theme 'default' specified with no config.",
        "   autohide setting 'autohide' specified with no config.",
        "\x1b[91m",
        ("Error connecting to Zulip server: {}.\x1b[0m".
            format(server_connection_error)),
    ]
    assert lines == expected_lines

    assert captured.err == ""


@pytest.mark.parametrize('bad_theme', ['c', 'd'])
def test_warning_regarding_incomplete_theme(capsys, mocker, monkeypatch,
                                            minimal_zuliprc, bad_theme,
                                            server_connection_error="sce"):
    mocker.patch('zulipterminal.core.Controller.__init__',
                 side_effect=ServerConnectionFailure(server_connection_error))

    monkeypatch.setitem(THEMES, bad_theme, [])
    mocker.patch('zulipterminal.cli.run.all_themes',
                 return_value=('a', 'b', 'c', 'd'))
    mocker.patch('zulipterminal.cli.run.complete_and_incomplete_themes',
                 return_value=(['a', 'b'], ['c', 'd']))

    with pytest.raises(SystemExit) as e:
        main(["-c", minimal_zuliprc, "-t", bad_theme])
        assert str(e.value) == '1'

    captured = capsys.readouterr()

    lines = captured.out.strip().split("\n")
    expected_lines = [
        "Loading with:",
        "   theme '{}' specified on command line.".format(bad_theme),
        "\x1b[93m"
        "   WARNING: Incomplete theme; results may vary!",
        "      (you could try: {}, {})"
        "\x1b[0m".format('a', 'b'),
        "   autohide setting 'autohide' specified with no config.",
        "\x1b[91m",
        ("Error connecting to Zulip server: {}.\x1b[0m".
            format(server_connection_error)),
    ]
    assert lines == expected_lines

    assert captured.err == ""
