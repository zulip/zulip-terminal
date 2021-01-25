import pytest
from pytest import param

from zulipterminal.config.keys import keys_for_command, primary_key_for_command
from zulipterminal.config.symbols import (
    STREAM_MARKER_INVALID,
    STREAM_MARKER_PRIVATE,
    STREAM_MARKER_PUBLIC,
)
from zulipterminal.ui_tools.boxes import PanelSearchBox, WriteBox


BOXES = "zulipterminal.ui_tools.boxes"


class TestWriteBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, initial_index):
        self.view = mocker.Mock()
        self.view.model = mocker.Mock()

    @pytest.fixture()
    def write_box(self, mocker, users_fixture, user_groups_fixture,
                  streams_fixture, unicode_emojis):
        self.view.model.active_emoji_data = unicode_emojis
        write_box = WriteBox(self.view)
        write_box.view.users = users_fixture
        write_box.model.user_group_names = [
            groups['name'] for groups in user_groups_fixture]

        write_box.view.pinned_streams = []
        write_box.view.unpinned_streams = sorted([
            {'name': stream['name']} for stream in
            streams_fixture], key=lambda stream: stream['name'].lower())

        return write_box

    def test_init(self, write_box):
        assert write_box.model == self.view.model
        assert write_box.view == self.view
        assert write_box.msg_edit_id is None

    @pytest.mark.parametrize('text, state', [
        ('Plain Text', 0),
        ('Plain Text', 1),
    ])
    def test_generic_autocomplete_no_prefix(self, mocker, write_box, text,
                                            state):
        return_val = write_box.generic_autocomplete(text, state)
        assert return_val == text
        write_box.view.set_typeahead_footer.assert_not_called()

    @pytest.mark.parametrize('text, state, footer_text', [
        # no-text mentions
        ('@', 0,
            ['Human Myself', 'Human 1', 'Human 2',
             'Group 1', 'Group 2', 'Group 3', 'Group 4']),
        ('@*', 0, ['Group 1', 'Group 2', 'Group 3', 'Group 4']),
        ('@**', 0, ['Human Myself', 'Human 1', 'Human 2']),
        # mentions
        ('@Human', 0, ['Human Myself', 'Human 1', 'Human 2']),
        ('@**Human', 0, ['Human Myself', 'Human 1', 'Human 2']),
        ('@_Human', 0, ['Human Myself', 'Human 1', 'Human 2']),
        ('@_*Human', None, []),  # NOTE: Optional single star fails
        ('@_**Human', 0, ['Human Myself', 'Human 1', 'Human 2']),
        ('@Human', None, ['Human Myself', 'Human 1', 'Human 2']),
        ('@NoMatch', None, []),
        # streams
        ('#Stream', 0, ['Stream 1', 'Stream 2', 'Secret stream',
                        'Some general stream']),
        ('#*Stream', None, []),  # NOTE: Optional single star fails
        ('#**Stream', 0, ['Stream 1', 'Stream 2', 'Secret stream',
                          'Some general stream']),  # Optional 2-stars
        ('#Stream', None, ['Stream 1', 'Stream 2', 'Secret stream',
                           'Some general stream']),
        ('#NoMatch', None, []),
        # emojis
        (':smi', 0, ['smile', 'smiley', 'smirk']),
        (':smi', None, ['smile', 'smiley', 'smirk']),
        (':NoMatch', None, []),
    ])
    def test_generic_autocomplete_set_footer(self, mocker, write_box,
                                             state, footer_text, text):
        write_box.view.set_typeahead_footer = mocker.patch(
                                'zulipterminal.ui.View.set_typeahead_footer')
        write_box.generic_autocomplete(text, state)

        write_box.view.set_typeahead_footer.assert_called_once_with(
                                                    footer_text,
                                                    state,
                                                    False)

    @pytest.mark.parametrize('text, state, required_typeahead', [
        ('@Human', 0, '@**Human Myself**'),
        ('@Human', 1, '@**Human 1**'),
        ('@Human', 2, '@**Human 2**'),
        ('@Human', -1, '@**Human 2**'),
        ('@Human', -2, '@**Human 1**'),
        ('@Human', -3, '@**Human Myself**'),
        ('@Human', -4, None),
        ('@_Human', 0, '@_**Human Myself**'),
        ('@_Human', 1, '@_**Human 1**'),
        ('@_Human', 2, '@_**Human 2**'),
        ('@H', 1, '@**Human 1**'),
        ('@Hu', 1, '@**Human 1**'),
        ('@Hum', 1, '@**Human 1**'),
        ('@Huma', 1, '@**Human 1**'),
        ('@Human', 1, '@**Human 1**'),
        ('@Human 1', 0, '@**Human 1**'),
        ('@_H', 1, '@_**Human 1**'),
        ('@_Hu', 1, '@_**Human 1**'),
        ('@_Hum', 1, '@_**Human 1**'),
        ('@_Huma', 1, '@_**Human 1**'),
        ('@_Human', 1, '@_**Human 1**'),
        ('@_Human 1', 0, '@_**Human 1**'),
        ('@Group', 0, '@*Group 1*'),
        ('@Group', 1, '@*Group 2*'),
        ('@G', 0, '@*Group 1*'),
        ('@Gr', 0, '@*Group 1*'),
        ('@Gro', 0, '@*Group 1*'),
        ('@Grou', 0, '@*Group 1*'),
        ('@G', 1, '@*Group 2*'),
        ('@Gr', 1, '@*Group 2*'),
        ('@Gro', 1, '@*Group 2*'),
        ('@Grou', 1, '@*Group 2*'),
        # Expected sequence of autocompletes from '@'
        ('@', 0, '@**Human Myself**'),
        ('@', 1, '@**Human 1**'),
        ('@', 2, '@**Human 2**'),
        ('@', 3, '@*Group 1*'),
        ('@', 4, '@*Group 2*'),
        ('@', 5, '@*Group 3*'),
        ('@', 6, '@*Group 4*'),
        ('@', 7, None),  # Reached last match
        ('@', 8, None),  # Beyond end
        # Expected sequence of autocompletes from '@**' (no groups)
        ('@**', 0, '@**Human Myself**'),
        ('@**', 1, '@**Human 1**'),
        ('@**', 2, '@**Human 2**'),
        ('@**', 3, None),  # Reached last match
        ('@**', 4, None),  # Beyond end
        # Expected sequence of autocompletes from '@*' (only groups)
        ('@*', 0, '@*Group 1*'),
        ('@*', 1, '@*Group 2*'),
        ('@*', 2, '@*Group 3*'),
        ('@*', 3, '@*Group 4*'),
        ('@*', 4, None),  # Reached last match
        ('@*', 5, None),  # Beyond end
        # Expected sequence of autocompletes from '@_'
        ('@_', 0, '@_**Human Myself**'),  # NOTE: No silent group mention
        ('@_', 1, '@_**Human 1**'),
        ('@_', 2, '@_**Human 2**'),
        ('@_', 3, None),  # Reached last match
        ('@_', 4, None),  # Beyond end
        ('@_', -1, '@_**Human 2**'),
        # Complex autocomplete prefixes.
        ('(@H', 0, '(@**Human Myself**'),
        ('(@H', 1, '(@**Human 1**'),
        ('-@G', 0, '-@*Group 1*'),
        ('-@G', 1, '-@*Group 2*'),
        ('_@H', 0, '_@**Human Myself**'),
        ('_@G', 0, '_@*Group 1*'),
        ('@@H', 0, '@@**Human Myself**'),
        (':@H', 0, ':@**Human Myself**'),
        ('#@H', 0, '#@**Human Myself**'),
        ('@_@H', 0, '@_@**Human Myself**'),
        ('>@_H', 0, '>@_**Human Myself**'),
        ('>@_H', 1, '>@_**Human 1**'),
        ('@_@_H', 0, '@_@_**Human Myself**'),
        ('@@_H', 0, '@@_**Human Myself**'),
        (':@_H', 0, ':@_**Human Myself**'),
        ('#@_H', 0, '#@_**Human Myself**'),
        ('@@_H', 0, '@@_**Human Myself**'),
        ('@@_*H', 0, None),  # Optional single star fails
        ('@@_**H', 0, '@@_**Human Myself**'),  # Optional stars
    ])
    def test_generic_autocomplete_mentions(self, write_box, text,
                                           required_typeahead, state):
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize('text, state, required_typeahead, recipients', [
        ('@', 0, '@**Human 2**', [12]),
        ('@', 1, '@**Human Myself**', [12]),
        ('@', 2, '@**Human 1**', [12]),
        ('@', -1, '@*Group 4*', [12]),
        ('@', 0, '@**Human 1**', [11, 12]),
        ('@', 1, '@**Human 2**', [11, 12]),
        ('@', 2, '@**Human Myself**', [11, 12]),
        ('@', -1, '@*Group 4*', [11, 12]),
    ])
    def test_generic_autocomplete_mentions_subscribers(self, write_box, text,
                                                       required_typeahead,
                                                       state, recipients):
        write_box.recipient_user_ids = recipients
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize('text, state, required_typeahead, to_pin', [
        # With no streams pinned.
        ('#Stream', 0, '#**Stream 1**', []),  # 1st-word startswith match.
        ('#Stream', 1, '#**Stream 2**', []),  # 1st-word startswith match.
        ('#Stream', 2, '#**Secret stream**', []),  # 2nd-word startswith match.
        ('#Stream', 3, '#**Some general stream**', []),  # 3rd-word startswith.
        ('#S', 0, '#**Secret stream**', []),  # 1st-word startswith match.
        ('#S', 1, '#**Some general stream**', []),  # 1st-word startswith.
        ('#S', 2, '#**Stream 1**', []),  # 1st-word startswith match.
        ('#S', 3, '#**Stream 2**', []),  # 1st-word startswith match.
        ('#S', -1, '#**Stream 2**', []),
        ('#S', -2, '#**Stream 1**', []),
        ('#S', -3, '#**Some general stream**', []),
        ('#S', -4, '#**Secret stream**', []),
        ('#S', -5, None, []),
        ('#So', 0, '#**Some general stream**', []),
        ('#So', 1, None, []),
        ('#Se', 0, '#**Secret stream**', []),
        ('#Se', 1, None, []),
        ('#St', 0, '#**Stream 1**', []),
        ('#St', 1, '#**Stream 2**', []),
        ('#g', 0, '#**Some general stream**', []),
        ('#g', 1, None, []),
        ('#Stream 1', 0, '#**Stream 1**', []),  # Complete match.
        ('#nomatch', 0, None, []),
        ('#ene', 0, None, []),
        # Complex autocomplete prefixes.
        ('[#Stream', 0, '[#**Stream 1**', []),
        ('(#Stream', 1, '(#**Stream 2**', []),
        ('@#Stream', 0, '@#**Stream 1**', []),
        ('@_#Stream', 0, '@_#**Stream 1**', []),
        (':#Stream', 0, ':#**Stream 1**', []),
        ('##Stream', 0, '##**Stream 1**', []),
        ('##*Stream', 0, None, []),  # NOTE: Optional single star fails
        ('##**Stream', 0, '##**Stream 1**', []),  # Optional 2-stars
        # With 'Secret stream' pinned.
        ('#Stream', 0, '#**Secret stream**',
         ['Secret stream', ]),  # 2nd-word startswith match (pinned).
        ('#Stream', 1, '#**Stream 1**',
         ['Secret stream', ]),  # 1st-word startswith match (unpinned).
        ('#Stream', 2, '#**Stream 2**',
         ['Secret stream', ]),  # 1st-word startswith match (unpinned).
        ('#Stream', 3, '#**Some general stream**',
         ['Secret stream', ]),  # 3rd-word starstwith match (unpinned).
        # With 'Stream 1' and 'Secret stream' pinned.
        ('#Stream', 0, '#**Stream 1**', ['Secret stream', 'Stream 1', ]),
        ('#Stream', 1, '#**Secret stream**', ['Secret stream',
                                              'Stream 1', ]),
        ('#Stream', 2, '#**Stream 2**', ['Secret stream', 'Stream 1', ]),
        ('#Stream', 3, '#**Some general stream**', ['Secret stream',
                                                    'Stream 1', ]),
    ])
    def test_generic_autocomplete_streams(self, write_box, text,
                                          state, required_typeahead, to_pin):
        streams_to_pin = [{'name': stream_name} for stream_name in to_pin]
        for stream in streams_to_pin:
            write_box.view.unpinned_streams.remove(stream)
        write_box.view.pinned_streams = streams_to_pin
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize('text, state, required_typeahead', [
        (':rock_o', 0, ':rock_on:'),
        (':rock_o', 1, None),
        (':rock_o', -1, ':rock_on:'),
        (':rock_o', -2, None),
        (':smi', 0, ':smile:'),
        (':smi', 1, ':smiley:'),
        (':smi', 2, ':smirk:'),
        (':jo', 0, ':joker:'),
        (':jo', 1, ':joy_cat:'),
        (':jok', 0, ':joker:'),
        (':', 0, ':happy:'),
        (':', 1, ':joker:'),
        (':', -2, ':smiley:'),
        (':', -1, ':smirk:'),
        (':nomatch', 0, None),
        (':nomatch', -1, None),
        # Complex autocomplete prefixes.
        ('(:smi', 0, '(:smile:'),
        ('&:smi', 1, '&:smiley:'),
        ('@:smi', 0, '@:smile:'),
        ('@_:smi', 0, '@_:smile:'),
        ('#:smi', 0, '#:smile:'),
        ])
    def test_generic_autocomplete_emojis(self, write_box, text,
                                         mocker, state, required_typeahead):
        typeahead_string = write_box.generic_autocomplete(text, state)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize(['text', 'state', 'to_pin', 'matching_streams'], [
        ('', 1, [], ['Secret stream', 'Some general stream',
                     'Stream 1', 'Stream 2']),
        ('', 1, ['Stream 2'], ['Stream 2', 'Secret stream',
                               'Some general stream', 'Stream 1']),
        ('St', 1, [], ['Stream 1', 'Stream 2', 'Secret stream',
                       'Some general stream']),
        ('St', 1, ['Stream 2'], ['Stream 2', 'Stream 1',
                                 'Secret stream', 'Some general stream']),
    ], ids=[
        'no_search_text',
        'no_search_text_with_pinned_stream',
        'single_word_search_text',
        'single_word_search_text_with_pinned_stream',
    ])
    def test__stream_box_autocomplete(self, mocker, write_box, text, state,
                                      to_pin, matching_streams):
        streams_to_pin = [{'name': stream_name} for stream_name in to_pin]
        for stream in streams_to_pin:
            write_box.view.unpinned_streams.remove(stream)
        write_box.view.pinned_streams = streams_to_pin
        _process_typeaheads = mocker.patch(BOXES
                                           + '.WriteBox._process_typeaheads')

        write_box._stream_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(matching_streams, state,
                                                    matching_streams)

    @pytest.mark.parametrize([
        'stream_name',
        'stream_id',
        'is_valid_stream',
        'expected_marker',
        'expected_color'
    ], [
      ('Secret stream', 99, True,  STREAM_MARKER_PRIVATE, '#ccc'),
      ('Stream 1',       1, True,  STREAM_MARKER_PUBLIC,  '#b0a5fd'),
      ('Stream 0',       0, False, STREAM_MARKER_INVALID, 'general_bar'),
    ], ids=[
        'private_stream',
        'public_stream',
        'invalid_stream_name',
    ])
    def test__set_stream_write_box_style_markers(self, write_box, stream_id,
                                                 stream_name, is_valid_stream,
                                                 expected_marker, stream_dict,
                                                 mocker, expected_color):
        # FIXME: Refactor when we have ~ Model.is_private_stream
        write_box.model.stream_dict = stream_dict
        write_box.model.is_valid_stream.return_value = is_valid_stream
        write_box.model.stream_id_from_name.return_value = stream_id

        write_box.stream_box_view(stream_id)

        write_box._set_stream_write_box_style(write_box, stream_name)

        stream_marker = (write_box.header_write_box
                         [write_box.FOCUS_HEADER_PREFIX_STREAM])

        assert stream_marker.text == expected_marker
        assert stream_marker.attrib[0][0] == expected_color

    @pytest.mark.parametrize('text, expected_text', [
        ('Som', 'Some general stream'),
        ('Some gen', 'Some general stream'),
    ])
    def test__stream_box_autocomplete_with_spaces(self, mocker, write_box,
                                                  widget_size,
                                                  text, expected_text):
        mocker.patch(BOXES + '.WriteBox._set_stream_write_box_style')
        write_box.stream_box_view(1000)
        stream_focus = write_box.FOCUS_HEADER_BOX_STREAM
        write_box.header_write_box[stream_focus].set_edit_text(text)
        write_box.header_write_box[stream_focus].set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = stream_focus
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command('AUTOCOMPLETE'))

        assert (write_box.header_write_box[stream_focus].edit_text
                == expected_text)

    @pytest.mark.parametrize(['text', 'matching_topics'], [
        ('', ['Topic 1', 'This is a topic', 'Hello there!']),
        ('Th', ['This is a topic']),
    ], ids=[
        'no_search_text',
        'single_word_search_text',
    ])
    def test__topic_box_autocomplete(self, mocker, write_box, text, topics,
                                     matching_topics, state=1):
        write_box.model.topics_in_stream.return_value = topics
        _process_typeaheads = mocker.patch(BOXES
                                           + '.WriteBox._process_typeaheads')

        write_box._topic_box_autocomplete(text, state)

        _process_typeaheads.assert_called_once_with(matching_topics, state,
                                                    matching_topics)

    @pytest.mark.parametrize('text, expected_text', [
        ('Th', 'This is a topic'),
        ('This i', 'This is a topic'),
    ])
    def test__topic_box_autocomplete_with_spaces(self, mocker, write_box,
                                                 widget_size,
                                                 text, expected_text,
                                                 topics):
        mocker.patch(BOXES + '.WriteBox._set_stream_write_box_style')
        write_box.stream_box_view(1000)
        write_box.model.topics_in_stream.return_value = topics
        topic_focus = write_box.FOCUS_HEADER_BOX_TOPIC
        write_box.header_write_box[topic_focus].set_edit_text(text)
        write_box.header_write_box[topic_focus].set_edit_pos(len(text))
        write_box.focus_position = write_box.FOCUS_CONTAINER_HEADER
        write_box.header_write_box.focus_col = topic_focus
        size = widget_size(write_box)

        write_box.keypress(size, primary_key_for_command('AUTOCOMPLETE'))

        assert (write_box.header_write_box[topic_focus].edit_text
                == expected_text)

    @pytest.mark.parametrize(['suggestions', 'state', 'expected_state',
                              'expected_typeahead', 'is_truncated'], [
      (['zero', 'one', 'two'], 1, 1, '*one*', False),
      (['zero', 'one', 'two'] * 4, 1, 1, '*one*', True),
      (['zero', 'one', 'two'], None, None, None, False),
      (['zero', 'one', 'two'], 5, None, None, False),
      (['zero', 'one', 'two'], -5, None, None, False),
     ], ids=[
        'fewer_than_10_typeaheads',
        'more_than_10_typeaheads',
        'invalid_state-None',
        'invalid_state-greater_than_possible_index',
        'invalid_state-less_than_possible_index',
    ])
    def test__process_typeaheads(self, write_box, suggestions, state,
                                 expected_state, expected_typeahead,
                                 is_truncated, mocker):
        write_box.view.set_typeahead_footer = mocker.patch(
                                'zulipterminal.ui.View.set_typeahead_footer')
        # Use an example formatting to differentiate between
        # typeaheads and suggestions.
        typeaheads = ['*{}*'.format(s) for s in suggestions]

        typeahead = write_box._process_typeaheads(typeaheads, state,
                                                  suggestions)

        assert typeahead == expected_typeahead
        write_box.view.set_typeahead_footer.assert_called_once_with(
                            suggestions[:10], expected_state, is_truncated)

    @pytest.mark.parametrize('topic_entered_by_user, topic_sent_to_server', [
        ('', '(no topic)'),
        ('hello', 'hello'),
        ('  ', '(no topic)'),
    ], ids=[
        'empty_topic',
        'non_empty_topic',
        'topic_with_whitespace',
    ])
    @pytest.mark.parametrize('msg_edit_id', [10, None], ids=[
        'update_message',
        'send_message',
    ])
    @pytest.mark.parametrize('key', keys_for_command('SEND_MESSAGE'))
    def test_keypress_SEND_MESSAGE_no_topic(self, mocker, write_box,
                                            msg_edit_id, topic_entered_by_user,
                                            topic_sent_to_server, key,
                                            widget_size,
                                            propagate_mode='change_one'):
        write_box.stream_write_box = mocker.Mock()
        write_box.msg_write_box = mocker.Mock(edit_text='')
        write_box.title_write_box = mocker.Mock(
            edit_text=topic_entered_by_user
        )
        write_box.to_write_box = None
        size = widget_size(write_box)
        write_box.msg_edit_id = msg_edit_id
        write_box.edit_mode_button = mocker.Mock(mode=propagate_mode)

        write_box.keypress(size, key)

        if msg_edit_id:
            write_box.model.update_stream_message.assert_called_once_with(
                        topic=topic_sent_to_server,
                        content=write_box.msg_write_box.edit_text,
                        message_id=msg_edit_id,
                        propagate_mode=propagate_mode,
                    )
        else:
            write_box.model.send_stream_message.assert_called_once_with(
                        stream=write_box.stream_write_box.edit_text,
                        topic=topic_sent_to_server,
                        content=write_box.msg_write_box.edit_text,
                    )

    @pytest.mark.parametrize(['key', 'current_typeahead_mode',
                              'expected_typeahead_mode',
                              'expect_footer_was_reset'], [
        # footer does not reset
        (primary_key_for_command('AUTOCOMPLETE'), False, False, False),
        (primary_key_for_command('AUTOCOMPLETE_REVERSE'), False, False, False),
        (primary_key_for_command('AUTOCOMPLETE'), True, True, False),
        (primary_key_for_command('AUTOCOMPLETE_REVERSE'), True, True, False),
        # footer resets
        (primary_key_for_command('GO_BACK'), True, False, True),
        ('space', True, False, True),
        ('k', True, False, True),
    ])
    def test_keypress_typeahead_mode_autocomplete_key(self, mocker, write_box,
                                                      widget_size,
                                                      current_typeahead_mode,
                                                      expected_typeahead_mode,
                                                      expect_footer_was_reset,
                                                      key):
        write_box.is_in_typeahead_mode = current_typeahead_mode
        size = widget_size(write_box)

        write_box.keypress(size, key)

        assert write_box.is_in_typeahead_mode == expected_typeahead_mode
        if expect_footer_was_reset:
            self.view.set_footer_text.assert_called_once_with()
        else:
            self.view.set_footer_text.assert_not_called()

    @pytest.mark.parametrize(["initial_focus_name",
                              "initial_focus_col_name",
                              "box_type",
                              "msg_body_edit_enabled",
                              "message_being_edited",
                              "expected_focus_name",
                              "expected_focus_col_name"], [
        ('CONTAINER_HEADER', 'HEADER_BOX_STREAM', "stream", True, False,
         'CONTAINER_HEADER', 'HEADER_BOX_TOPIC'),
        ('CONTAINER_HEADER', 'HEADER_BOX_TOPIC', "stream", True, False,
         'CONTAINER_MESSAGE', 'MESSAGE_BOX_BODY'),
        ('CONTAINER_HEADER', 'HEADER_BOX_TOPIC', "stream", False, True,
         'CONTAINER_HEADER', 'HEADER_BOX_EDIT'),
        ('CONTAINER_HEADER', 'HEADER_BOX_EDIT', "stream", False, True,
         'CONTAINER_HEADER', 'HEADER_BOX_TOPIC'),
        ('CONTAINER_MESSAGE', 'MESSAGE_BOX_BODY', "stream", True, False,
         'CONTAINER_HEADER', 'HEADER_BOX_STREAM'),
        ('CONTAINER_HEADER', 'HEADER_BOX_STREAM', "stream", True, True,
         'CONTAINER_HEADER', 'HEADER_BOX_TOPIC'),
        ('CONTAINER_HEADER', 'HEADER_BOX_TOPIC', "stream", True, True,
         'CONTAINER_HEADER', 'HEADER_BOX_EDIT'),
        ('CONTAINER_HEADER', 'HEADER_BOX_EDIT', "stream", True, True,
         'CONTAINER_MESSAGE', 'MESSAGE_BOX_BODY'),
        ('CONTAINER_MESSAGE', 'MESSAGE_BOX_BODY', "stream", True, True,
         'CONTAINER_HEADER', 'HEADER_BOX_STREAM'),
        ('CONTAINER_HEADER', 'HEADER_BOX_RECIPIENT', "private", True, False,
         'CONTAINER_MESSAGE', 'MESSAGE_BOX_BODY'),
        ('CONTAINER_MESSAGE', 'MESSAGE_BOX_BODY', "private", True, False,
         'CONTAINER_HEADER', 'HEADER_BOX_RECIPIENT'),
    ], ids=[
        'stream_name_to_topic_box',
        'topic_to_message_box',
        'topic_edit_only-topic_to_edit_mode_box',
        'topic_edit_only-edit_mode_to_topic_box',
        'message_to_stream_name_box',
        'edit_box-stream_name_to_topic_box',
        'edit_box-topic_to_edit_mode_box',
        'edit_box-edit_mode_to_message_box',
        'edit_box-message_to_stream_name_box',
        'recipient_to_message_box',
        'message_to_recipient_box',
    ])
    @pytest.mark.parametrize("tab_key",
                             keys_for_command("CYCLE_COMPOSE_FOCUS"))
    def test_keypress_CYCLE_COMPOSE_FOCUS(self, write_box, tab_key,
                                          initial_focus_name,
                                          expected_focus_name,
                                          initial_focus_col_name,
                                          expected_focus_col_name, box_type,
                                          msg_body_edit_enabled,
                                          message_being_edited,
                                          widget_size,
                                          mocker, stream_id=10):
        mocker.patch(BOXES + '.WriteBox._set_stream_write_box_style')

        if box_type == "stream":
            if message_being_edited:
                mocker.patch(BOXES + ".EditModeButton")
                write_box.stream_box_edit_view(stream_id)
                write_box.msg_edit_id = 10
            else:
                write_box.stream_box_view(stream_id)
        else:
            write_box.private_box_view()
        size = widget_size(write_box)

        def focus_val(x: str) -> int:
            return getattr(write_box, 'FOCUS_' + x)
        write_box.focus_position = focus_val(initial_focus_name)
        write_box.msg_body_edit_enabled = msg_body_edit_enabled
        if write_box.focus_position == write_box.FOCUS_CONTAINER_HEADER:
            write_box.header_write_box.focus_col = (focus_val(
                                                    initial_focus_col_name))
        write_box.model.get_invalid_recipient_emails.return_value = []
        write_box.model.user_dict = mocker.MagicMock()

        write_box.keypress(size, tab_key)

        assert write_box.focus_position == focus_val(expected_focus_name)
        # FIXME: Needs refactoring?
        if write_box.focus_position == write_box.FOCUS_CONTAINER_HEADER:
            assert (write_box.header_write_box.focus_col
                    == focus_val(expected_focus_col_name))
        else:
            assert (write_box.FOCUS_MESSAGE_BOX_BODY
                    == focus_val(expected_focus_col_name))

    @pytest.mark.parametrize(["msg_type", "expected_box_size"], [
        ('private',     1),
        ('stream',      4),
        ('stream_edit', 5),
    ], ids=[
        'private_message',
        'stream_message',
        'stream_edit_message',
    ])
    def test_write_box_header_contents(self, write_box, expected_box_size,
                                       mocker, msg_type):
        mocker.patch(BOXES + '.WriteBox._set_stream_write_box_style')
        mocker.patch(BOXES + '.WriteBox.set_editor_mode')
        if msg_type == 'stream':
            write_box.stream_box_view(1000)
        elif msg_type == 'stream_edit':
            write_box.stream_box_edit_view(1000)
        else:
            write_box.private_box_view(email='foo@gmail.com',
                                       recipient_user_ids=[1])

        assert len(write_box.header_write_box.widget_list) == expected_box_size


class TestPanelSearchBox:
    search_caption = "Search Results "

    @pytest.fixture
    def panel_search_box(self, mocker):
        # X is the return from keys_for_command("UNTESTED_TOKEN")
        mocker.patch(BOXES + ".keys_for_command", return_value="X")
        panel_view = mocker.Mock()
        update_func = mocker.Mock()
        return PanelSearchBox(panel_view, "UNTESTED_TOKEN", update_func)

    def test_init(self, panel_search_box):
        assert panel_search_box.search_text == "Search [X]: "
        assert panel_search_box.caption == ""
        assert panel_search_box.edit_text == panel_search_box.search_text

    def test_reset_search_text(self, panel_search_box):
        panel_search_box.set_caption(self.search_caption)
        panel_search_box.edit_text = "key words"

        panel_search_box.reset_search_text()

        assert panel_search_box.caption == ""
        assert panel_search_box.edit_text == panel_search_box.search_text

    @pytest.mark.parametrize("search_text, entered_string, expected_result", [
        # NOTE: In both backspace cases it is not validated (backspace is not
        #       shown), but still is handled during editing as normal
        # NOTE: Unicode backspace case likely doesn't get triggered
        param('', 'backspace', False, id="no_text-disallow_urwid_backspace"),
        param('', '\u0008', False, id="no_text-disallow_unicode_backspace"),
        param('', '\u2003', False, id="no_text-disallow_unicode_em_space"),
        param('', 'x', True, id="no_text-allow_entry_of_x"),
        param('', '\u0394', True, id="no_text-allow_entry_of_delta"),
        param('', ' ', False, id="no_text-disallow_entry_of_space"),
        param('x', ' ', True, id="text-allow_entry_of_space"),
        param('x', 'backspace', False, id="text-disallow_urwid_backspace"),
    ])
    def test_valid_char(self, panel_search_box,
                        search_text, entered_string, expected_result):
        panel_search_box.edit_text = search_text

        result = panel_search_box.valid_char(entered_string)

        assert result == expected_result

    @pytest.mark.parametrize("log, expect_body_focus_set", [
        ([], False),
        (["SOMETHING"], True)
    ])
    @pytest.mark.parametrize("enter_key", keys_for_command("ENTER"))
    def test_keypress_ENTER(self, panel_search_box, widget_size,
                            enter_key, log, expect_body_focus_set):
        size = widget_size(panel_search_box)
        panel_search_box.panel_view.view.controller.is_in_editor_mode = (
            lambda: True
        )
        panel_search_box.panel_view.log = log
        panel_search_box.set_caption("")
        panel_search_box.edit_text = "key words"

        panel_search_box.keypress(size, enter_key)

        # Update this display
        # FIXME We can't test for the styled version?
        # We'd compare to [('filter_results', 'Search Results'), ' ']
        assert panel_search_box.caption == self.search_caption
        assert panel_search_box.edit_text == "key words"

        # Leave editor mode
        (panel_search_box.panel_view.view.controller.exit_editor_mode
         .assert_called_once_with())

        # Switch focus to body; if have results, move to them
        panel_search_box.panel_view.set_focus.assert_called_once_with("body")
        if expect_body_focus_set:
            (panel_search_box.panel_view.body.set_focus
             .assert_called_once_with(0))
        else:
            (panel_search_box.panel_view.body.set_focus
             .assert_not_called())

    @pytest.mark.parametrize("back_key", keys_for_command("GO_BACK"))
    def test_keypress_GO_BACK(self, panel_search_box, back_key, widget_size):
        size = widget_size(panel_search_box)
        panel_search_box.panel_view.view.controller.is_in_editor_mode = (
            lambda: True
        )
        panel_search_box.set_caption(self.search_caption)
        panel_search_box.edit_text = "key words"

        panel_search_box.keypress(size, back_key)

        # Reset display
        assert panel_search_box.caption == ""
        assert panel_search_box.edit_text == panel_search_box.search_text

        # Leave editor mode
        (panel_search_box.panel_view.view.controller.exit_editor_mode
         .assert_called_once_with())

        # Switch focus to body; focus should return to previous in body
        panel_search_box.panel_view.set_focus.assert_called_once_with("body")

        # pass keypress back
        # FIXME This feels hacky to call keypress (with hardcoded 'esc' too)
        #       - should we add a second callback to update the panel?
        (panel_search_box.panel_view.keypress
         .assert_called_once_with(size, 'esc'))
