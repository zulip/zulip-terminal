import pytest

from zulipterminal.ui_tools.buttons import TopButton, StreamButton, UserButton

TOPBUTTON = "zulipterminal.ui_tools.buttons.TopButton"
STREAMBUTTON = "zulipterminal.ui_tools.buttons.StreamButton"


class TestTopButton:
    @pytest.mark.parametrize('prefix', [
        None, '\N{BULLET}', '-', ('blue', 'o'),
    ])
    @pytest.mark.parametrize('width, count, short_text', [
        (8, 0, 'c..'),
        (9, 0, 'ca..'),
        (9, -1, 'c..'),
        (9, 1, 'c..'),
        (10, 0, 'cap..'),
        (10, -1, 'ca..'),
        (10, 1, 'ca..'),
        (11, 0, 'capt..'),
        (11, -1, 'cap..'),
        (11, 1, 'cap..'),
        (11, 10, 'ca..'),
        (12, 0, 'caption'),
        (12, -1, 'capt..'),
        (12, 1, 'capt..'),
        (12, 10, 'cap..'),
        (12, 100, 'ca..'),
        (13, 0, 'caption'),
        (13, -1, 'caption'),
        (13, 10, 'capt..'),
        (13, 100, 'cap..'),
        (13, 1000, 'ca..'),
        (15, 0, 'caption'),
        (15, -1, 'caption'),
        (15, 1, 'caption'),
        (15, 10, 'caption'),
        (15, 100, 'caption'),
        (15, 1000, 'capt..'),
        (25, 0, 'caption'),
        (25, -1, 'caption'),
        (25, 1, 'caption'),
        (25, 19, 'caption'),
        (25, 199, 'caption'),
        (25, 1999, 'caption'),
    ])
    def test_text_content(self, mocker,
                          prefix,
                          width, count, short_text, caption='caption'):
        mocker.patch(STREAMBUTTON + ".mark_muted")
        show_function = mocker.Mock()

        if isinstance(prefix, tuple):
            prefix = prefix[1]  # just checking text, not color

        if prefix is None:
            top_button = TopButton(controller=mocker.Mock(),
                                   caption=caption,
                                   show_function=show_function,
                                   width=width,
                                   count=count)
            prefix = '\N{BULLET}'
        else:
            top_button = TopButton(controller=mocker.Mock(),
                                   caption=caption,
                                   show_function=show_function,
                                   prefix_character=prefix,
                                   width=width,
                                   count=count)

        text = top_button._w._original_widget.get_text()
        count_str = '' if count == 0 else str(count)
        if count < 0:
            count_str = 'M'
        expected_text = ' {} {}{}{}'.format(
                prefix, short_text,
                (width - 4 - len(short_text) - len(count_str))*' ',
                count_str)
        assert len(text[0]) == len(expected_text) == (width - 1)
        assert text[0] == expected_text


class TestStreamButton:
    @pytest.mark.parametrize('is_private, expected_prefix', [
        (True, 'P'),
        (False, '#'),
    ], ids=['private', 'not_private'])
    @pytest.mark.parametrize('width, count, short_text', [
        (8, 0, 'c..'),
        (9, 0, 'ca..'),
        (9, 1, 'c..'),
        (10, 0, 'cap..'),
        (10, 1, 'ca..'),
        (11, 0, 'capt..'),
        (11, 1, 'cap..'),
        (11, 10, 'ca..'),
        (12, 0, 'caption'),
        (12, 1, 'capt..'),
        (12, 10, 'cap..'),
        (12, 100, 'ca..'),
        (13, 0, 'caption'),
        (13, 10, 'capt..'),
        (13, 100, 'cap..'),
        (13, 1000, 'ca..'),
        (15, 0, 'caption'),
        (15, 1, 'caption'),
        (15, 10, 'caption'),
        (15, 100, 'caption'),
        (15, 1000, 'capt..'),
        (25, 0, 'caption'),
        (25, 1, 'caption'),
        (25, 19, 'caption'),
        (25, 199, 'caption'),
        (25, 1999, 'caption'),
    ])
    def test_text_content(self, mocker,
                          is_private, expected_prefix,
                          width, count, short_text, caption='caption'):
        mocker.patch(STREAMBUTTON + ".mark_muted")
        controller = mocker.Mock()
        controller.model.muted_streams = {}
        properties = [caption, 5, '#ffffff', is_private]
        view_mock = mocker.Mock()
        view_mock.palette = [(None, 'black', 'white')]
        stream_button = StreamButton(properties,
                                     controller=controller,
                                     view=view_mock,
                                     width=width,
                                     count=count)

        text = stream_button._w._original_widget.get_text()
        count_str = '' if count == 0 else str(count)
        expected_text = ' {} {}{}{}'.format(
                expected_prefix, short_text,
                (width - 4 - len(short_text) - len(count_str))*' ',
                count_str)
        assert len(text[0]) == len(expected_text) == (width - 1)
        assert text[0] == expected_text

    @pytest.mark.parametrize('color', [
        '#ffffff', '#f0f0f0', '#f0f1f2', '#fff'
    ])
    def test_color_formats(self, mocker, color):
        mocker.patch(STREAMBUTTON + ".mark_muted")
        controller = mocker.Mock()
        controller.model.muted_streams = {}
        properties = ["", 1, color, False]  # only color is important
        view_mock = mocker.Mock()
        background = (None, 'white', 'black')
        view_mock.palette = [background]

        stream_button = StreamButton(properties,
                                     controller=controller,
                                     view=view_mock,
                                     width=10,
                                     count=5)

        expected_palette = ([background] +
                            [('#fff', '', '', '', '#fff, bold', 'black')] +
                            [('s#fff', '', '', '', 'black', '#fff')])
        assert view_mock.palette == expected_palette

    @pytest.mark.parametrize('color', [
        '#', '#f', '#ff', '#ffff', '#fffff', '#fffffff'
    ])
    def test_invalid_color_format(self, mocker, color):
        properties = ["", 1, color, False]  # only color is important
        view_mock = mocker.Mock()
        controller = mocker.Mock()
        controller.model.muted_streams = {}
        background = (None, 'white', 'black')
        view_mock.palette = [background]

        with pytest.raises(RuntimeError) as e:
            StreamButton(properties,
                         controller=controller,
                         view=view_mock,
                         width=10,
                         count=5)
        assert str(e.value) == "Unknown color format: '{}'".format(color)

    @pytest.mark.parametrize('stream_id, muted_streams, called_value,\
                             is_action_muting, updated_all_msgs', [
        (86, {}, 204, False, 380),
        (86, {86, 205}, -1, True, 320),
        (205, {14, 99}, 0, False, 350),
    ], ids=[
        'unmuting stream 86 - 204 unreads',
        'muting stream 86',
        'unmuting stream 205 - 0 unreads',
    ])
    def test_mark_stream_muted(self, mocker, stream_button, is_action_muting,
                               stream_id, muted_streams, called_value,
                               updated_all_msgs) -> None:
        stream_button.stream_id = stream_id
        update_count = mocker.patch(TOPBUTTON + ".update_count")
        stream_button.controller.model.unread_counts = {
            'streams': {
                86: 204,
                14: 34,
            }
        }
        stream_button.model.unread_counts['all_msg'] = 350
        stream_button.controller.model.muted_streams = muted_streams
        if is_action_muting:
            stream_button.mark_muted()
        else:
            stream_button.mark_unmuted()
        stream_button.update_count.assert_called_once_with(called_value)
        if called_value:
            stream_button.view.home_button.update_count.\
                assert_called_once_with(updated_all_msgs)
        assert stream_button.model.unread_counts['all_msg'] == updated_all_msgs


class TestUserButton:
    @pytest.mark.parametrize('width, count, short_text', [
        (8, 0, 'c..'),
        (9, 0, 'ca..'),
        (9, 1, 'c..'),
        (10, 0, 'cap..'),
        (10, 1, 'ca..'),
        (11, 0, 'capt..'),
        (11, 1, 'cap..'),
        (11, 10, 'ca..'),
        (12, 0, 'caption'),
        (12, 1, 'capt..'),
        (12, 10, 'cap..'),
        (12, 100, 'ca..'),
        (13, 0, 'caption'),
        (13, 10, 'capt..'),
        (13, 100, 'cap..'),
        (13, 1000, 'ca..'),
        (15, 0, 'caption'),
        (15, 1, 'caption'),
        (15, 10, 'caption'),
        (15, 100, 'caption'),
        (15, 1000, 'capt..'),
        (25, 0, 'caption'),
        (25, 1, 'caption'),
        (25, 19, 'caption'),
        (25, 199, 'caption'),
        (25, 1999, 'caption'),
    ])
    def test_text_content(self, mocker,
                          width, count, short_text, caption='caption'):
        mocker.patch(STREAMBUTTON + ".mark_muted")
        user = {
            'email': 'some_email',  # value unimportant
            'user_id': 5,           # value unimportant
            'full_name': caption,
        }  # type: Dict[str, Any]
        user_button = UserButton(user,
                                 controller=mocker.Mock(),
                                 view=mocker.Mock(),
                                 width=width,
                                 color=None,  # FIXME test elsewhere?
                                 count=count)

        text = user_button._w._original_widget.get_text()
        count_str = '' if count == 0 else str(count)
        expected_text = ' \N{BULLET} {}{}{}'.format(
                short_text,
                (width - 4 - len(short_text) - len(count_str))*' ',
                count_str)
        assert len(text[0]) == len(expected_text) == (width - 1)
        assert text[0] == expected_text
