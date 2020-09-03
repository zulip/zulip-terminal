import pytest
from urwid import AttrMap, Overlay

from zulipterminal.ui_tools.buttons import MessageLinkButton


BUTTONS = "zulipterminal.ui_tools.buttons"

SERVER_URL = "https://chat.zulip.zulip"


class TestMessageLinkButton:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker):
        self.controller = mocker.Mock()
        self.super_init = mocker.patch(BUTTONS + '.urwid.Button.__init__')
        self.connect_signal = mocker.patch(BUTTONS + '.urwid.connect_signal')

    def message_link_button(self, caption='', link='', display_attr=None):
        self.caption = caption
        self.link = link
        self.display_attr = display_attr
        return MessageLinkButton(self.controller, self.caption, self.link,
                                 self.display_attr)

    def test_init(self, mocker):
        self.update_widget = (
            mocker.patch(BUTTONS + '.MessageLinkButton.update_widget')
        )

        mocked_button = self.message_link_button()

        assert mocked_button.controller == self.controller
        assert mocked_button.model == self.controller.model
        assert mocked_button.view == self.controller.view
        assert mocked_button.link == self.link
        self.super_init.assert_called_once_with('')
        self.update_widget.assert_called_once_with(self.caption,
                                                   self.display_attr)
        assert self.connect_signal.called

    @pytest.mark.parametrize('caption, expected_cursor_position', [
        ('Test', 5),
        ('Check', 6),
    ])
    def test_update_widget(self, mocker, caption, expected_cursor_position,
                           display_attr=None):
        self.selectable_icon = mocker.patch(BUTTONS + '.urwid.SelectableIcon')

        # The method update_widget() is called in MessageLinkButton's init.
        mocked_button = self.message_link_button(caption=caption,
                                                 display_attr=display_attr)

        self.selectable_icon.assert_called_once_with(
            caption, cursor_position=expected_cursor_position
        )
        assert isinstance(mocked_button._w, AttrMap)

    @pytest.mark.parametrize([
            'link',
            'handle_narrow_link_called',
            'process_media_called',
        ],
        [
            (SERVER_URL + '/#narrow/stream/1-Stream-1', True, False),
            (SERVER_URL + '/user_uploads/some/path/image.png', False, True),
            ('https://foo.com', False, False),
        ],
        ids=[
            'internal_narrow_link',
            'internal_media_link',
            'external_link',
        ]
    )
    def test_handle_link(self, mocker, link, handle_narrow_link_called,
                         process_media_called):
        self.controller.model.server_url = SERVER_URL
        self.controller.loop.widget = mocker.Mock(spec=Overlay)
        self.handle_narrow_link = (
            mocker.patch(BUTTONS + '.MessageLinkButton.handle_narrow_link')
        )
        self.process_media = mocker.patch(BUTTONS + '.process_media')
        mocked_button = self.message_link_button(link=link)

        mocked_button.handle_link()

        assert self.handle_narrow_link.called == handle_narrow_link_called
        assert self.process_media.called == process_media_called

    @pytest.mark.parametrize('stream_data, expected_response', [
            ('206-zulip-terminal', dict(stream_id=206, stream_name=None)),
            ('Stream.201', dict(stream_id=None, stream_name='Stream 1')),
        ],
        ids=[
            'stream_data_current_version',
            'stream_data_deprecated_version',
        ]
    )
    def test__decode_stream_data(self, stream_data, expected_response):
        return_value = MessageLinkButton._decode_stream_data(stream_data)

        assert return_value == expected_response

    @pytest.mark.parametrize('message_id, expected_return_value', [
        ('1', 1),
        ('foo', None),
    ])
    def test__decode_message_id(self, message_id, expected_return_value):
        return_value = MessageLinkButton._decode_message_id(message_id)

        assert return_value == expected_return_value

    @pytest.mark.parametrize('link, expected_parsed_link', [
        (SERVER_URL + '/#narrow/stream/1-Stream-1',
         {'narrow': 'stream',
          'stream': {'stream_id': 1, 'stream_name': None}}),
        (SERVER_URL + '/#narrow/stream/Stream.201',
         {'narrow': 'stream',
          'stream': {'stream_id': None, 'stream_name': 'Stream 1'}}),
        (SERVER_URL + '/#narrow/stream/1-Stream-1/topic/foo.20bar',
         {'narrow': 'stream:topic', 'topic_name': 'foo bar',
          'stream': {'stream_id': 1, 'stream_name': None}}),
        (SERVER_URL + '/#narrow/stream/1-Stream-1/near/1',
         {'narrow': 'stream:near',  'message_id': 1,
          'stream': {'stream_id': 1, 'stream_name': None}}),
        (SERVER_URL + '/#narrow/stream/1-Stream-1/topic/foo/near/1',
         {'narrow': 'stream:topic:near', 'topic_name': 'foo', 'message_id': 1,
          'stream': {'stream_id': 1, 'stream_name': None}}),
        (SERVER_URL + '/#narrow/foo',
         {}),
        (SERVER_URL + '/#narrow/stream/',
         {}),
        (SERVER_URL + '/#narrow/stream/1-Stream-1/topic/',
         {}),
        (SERVER_URL + '/#narrow/stream/1-Stream-1//near/',
         {}),
        (SERVER_URL + '/#narrow/stream/1-Stream-1/topic/foo/near/',
         {}),
        ],
        ids=[
            'modern_stream_narrow_link',
            'deprecated_stream_narrow_link',
            'topic_narrow_link',
            'stream_near_narrow_link',
            'topic_near_narrow_link',
            'invalid_narrow_link_1',
            'invalid_narrow_link_2',
            'invalid_narrow_link_3',
            'invalid_narrow_link_4',
            'invalid_narrow_link_5',
        ]
    )
    def test__parse_narrow_link(self, link, expected_parsed_link):
        return_value = MessageLinkButton._parse_narrow_link(link)

        assert return_value == expected_parsed_link

    @pytest.mark.parametrize(
        [
            'parsed_link',
            'is_user_subscribed_to_stream',
            'is_valid_stream',
            'topics_in_stream',
            'expected_error'
        ],
        [
            ({'narrow': 'stream',
              'stream': {'stream_id': 1, 'stream_name': None}},
             True,
             None,
             None,
             ''),
            ({'narrow': 'stream',
              'stream': {'stream_id': 462, 'stream_name': None}},
             False,
             None,
             None,
             'The stream seems to be either unknown or unsubscribed'),
            ({'narrow': 'stream',
              'stream': {'stream_id': None, 'stream_name': 'Stream 1'}},
             None,
             True,
             None,
             ''),
            ({'narrow': 'stream',
              'stream': {'stream_id': None, 'stream_name': 'foo'}},
             None,
             False,
             None,
             'The stream seems to be either unknown or unsubscribed'),
            ({'narrow': 'stream:topic', 'topic_name': 'Valid',
              'stream': {'stream_id': 1, 'stream_name': None}},
             True,
             None,
             ['Valid'],
             ''),
            ({'narrow': 'stream:topic', 'topic_name': 'Invalid',
              'stream': {'stream_id': 1, 'stream_name': None}},
             True,
             None,
             [],
             'Invalid topic name'),
            ({'narrow': 'stream:near', 'message_id': 1,
              'stream': {'stream_id': 1, 'stream_name': None}},
             True,
             None,
             None,
             ''),
            ({'narrow': 'stream:near', 'message_id': None,
              'stream': {'stream_id': 1, 'stream_name': None}},
             True,
             None,
             None,
             'Invalid message ID'),
            ({'narrow': 'stream:topic:near', 'topic_name': 'Valid',
              'message_id': 1,
              'stream': {'stream_id': 1, 'stream_name': None}},
             True,
             None,
             ['Valid'],
             ''),
            ({'narrow': 'stream:topic:near', 'topic_name': 'Valid',
              'message_id': None,
              'stream': {'stream_id': 1, 'stream_name': None}},
             True,
             None,
             ['Valid'],
             'Invalid message ID'),
            ({},
             None,
             None,
             None,
             'The narrow link seems to be either broken or unsupported'),
        ],
        ids=[
            'valid_modern_stream_narrow_parsed_link',
            'invalid_modern_stream_narrow_parsed_link',
            'valid_deprecated_stream_narrow_parsed_link',
            'invalid_deprecated_stream_narrow_parsed_link',
            'valid_topic_narrow_parsed_link',
            'invalid_topic_narrow_parsed_link',
            'valid_stream_near_narrow_parsed_link',
            'invalid_stream_near_narrow_parsed_link',
            'valid_topic_near_narrow_parsed_link',
            'invalid_topic_near_narrow_parsed_link',
            'invalid_narrow_link',
        ]
    )
    def test__validate_narrow_link(self, stream_dict, parsed_link,
                                   is_user_subscribed_to_stream,
                                   is_valid_stream,
                                   topics_in_stream,
                                   expected_error):
        self.controller.model.stream_dict = stream_dict
        self.controller.model.is_user_subscribed_to_stream.return_value = (
            is_user_subscribed_to_stream
        )
        self.controller.model.is_valid_stream.return_value = is_valid_stream
        self.controller.model.topics_in_stream.return_value = topics_in_stream
        mocked_button = self.message_link_button()

        return_value = mocked_button._validate_narrow_link(parsed_link)

        assert return_value == expected_error

    @pytest.mark.parametrize(['parsed_link', 'is_user_subscribed_to_stream',
                              'is_valid_stream',
                              'stream_id_from_name_return_value',
                              'expected_parsed_link',
                              'expected_error'], [
            ({'stream': {'stream_id': 1, 'stream_name': None}},  # ...
             True,
             None,
             None,
             {'stream': {'stream_id': 1, 'stream_name': 'Stream 1'}},
             ''),
            ({'stream': {'stream_id': 462, 'stream_name': None}},  # ...
             False,
             None,
             None,
             {'stream': {'stream_id': 462, 'stream_name': None}},
             'The stream seems to be either unknown or unsubscribed'),
            ({'stream': {'stream_id': None, 'stream_name': 'Stream 1'}},  # ...
             None,
             True,
             1,
             {'stream': {'stream_id': 1, 'stream_name': 'Stream 1'}},
             ''),
            ({'stream': {'stream_id': None, 'stream_name': 'foo'}},  # ...
             None,
             False,
             None,
             {'stream': {'stream_id': None, 'stream_name': 'foo'}},
             'The stream seems to be either unknown or unsubscribed'),
        ],
        ids=[
            'valid_stream_data_with_stream_id',
            'invalid_stream_data_with_stream_id',
            'valid_stream_data_with_stream_name',
            'invalid_stream_data_with_stream_name',
        ]
    )
    def test__validate_and_patch_stream_data(self, stream_dict, parsed_link,
                                             is_user_subscribed_to_stream,
                                             is_valid_stream,
                                             stream_id_from_name_return_value,
                                             expected_parsed_link,
                                             expected_error):
        self.controller.model.stream_dict = stream_dict
        self.controller.model.stream_id_from_name.return_value = (
            stream_id_from_name_return_value
        )
        self.controller.model.is_user_subscribed_to_stream.return_value = (
            is_user_subscribed_to_stream
        )
        self.controller.model.is_valid_stream.return_value = is_valid_stream
        mocked_button = self.message_link_button()

        error = mocked_button._validate_and_patch_stream_data(parsed_link)

        assert parsed_link == expected_parsed_link
        assert error == expected_error

    @pytest.mark.parametrize([
            'parsed_link',
            'narrow_to_stream_called',
            'narrow_to_topic_called',
        ],
        [
            ({'narrow': 'stream',
              'stream': {'stream_id': 1, 'stream_name': 'Stream 1'}},
             True,
             False),
            ({'narrow': 'stream:topic', 'topic_name': 'Foo',
              'stream': {'stream_id': 1, 'stream_name': 'Stream 1'}},
             False,
             True),
            ({'narrow': 'stream:near', 'message_id': 1,
              'stream': {'stream_id': 1, 'stream_name': 'Stream 1'}},
             True,
             False),
            ({'narrow': 'stream:topic:near', 'topic_name': 'Foo',
              'message_id': 1,
              'stream': {'stream_id': 1, 'stream_name': 'Stream 1'}},
             False,
             True),
        ],
        ids=[
            'stream_narrow',
            'topic_narrow',
            'stream_near_narrow',
            'topic_near_narrow',
        ]
    )
    def test__switch_narrow_to(self, parsed_link, narrow_to_stream_called,
                               narrow_to_topic_called,
                               ):
        mocked_button = self.message_link_button()

        mocked_button._switch_narrow_to(parsed_link)

        assert (mocked_button.controller.narrow_to_stream.called
                == narrow_to_stream_called)
        assert (mocked_button.controller.narrow_to_topic.called
                == narrow_to_topic_called)

    @pytest.mark.parametrize(['error', 'set_footer_text_called',
                              '_switch_narrow_to_called',
                              'exit_popup_called'], [
            ('Some Validation Error', True, False, False),
            ('', False, True, True),
        ],
        ids=[
            'successful_narrow',
            'unsuccessful_narrow',
        ]
    )
    def test_handle_narrow_link(self, mocker, error, set_footer_text_called,
                                _switch_narrow_to_called, exit_popup_called):
        self.controller.loop.widget = mocker.Mock(spec=Overlay)
        mocker.patch(BUTTONS + '.MessageLinkButton._parse_narrow_link')
        mocker.patch(BUTTONS + '.MessageLinkButton._validate_narrow_link',
                     return_value=error)
        mocker.patch(BUTTONS + '.MessageLinkButton._switch_narrow_to')
        mocked_button = self.message_link_button()

        mocked_button.handle_narrow_link()

        assert mocked_button._parse_narrow_link.called
        assert mocked_button._validate_narrow_link.called
        assert (mocked_button.view.set_footer_text.called
                == set_footer_text_called)
        assert (mocked_button._switch_narrow_to.called
                == _switch_narrow_to_called)
        assert (mocked_button.controller.exit_popup.called
                == exit_popup_called)
