import pytest
from zulipterminal.cli.run import main
from zulipterminal.model import ServerConnectionFailure


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


def test_valid_zuliprc_but_no_connection(capsys, mocker, tmpdir,
                                         server_connection_error="some_error"):
    mocker.patch('zulipterminal.core.Controller.__init__',
                 side_effect=ServerConnectionFailure(server_connection_error))

    zuliprc_path = str(tmpdir) + "/zuliprc"
    with open(zuliprc_path, "w") as f:
        f.write("[api]")  # minimal to avoid Exception

    with pytest.raises(SystemExit) as e:
        main(["-c", zuliprc_path])
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
