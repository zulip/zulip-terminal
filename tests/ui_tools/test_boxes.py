import pytest

from zulipterminal.ui_tools.boxes import WriteBox

WRITEBOX = "zulipterminal.ui_tools.boxes.WriteBox"


class TestWriteBox:
    @pytest.fixture(autouse=True)
    def mock_external_classes(self, mocker, initial_index):
        self.view = mocker.Mock()
        self.view.model = mocker.Mock()

    @pytest.fixture()
    def write_box(self, mocker):
        write_box = WriteBox(self.view)
        return write_box

    def test_init(self, write_box):
        assert write_box.model == self.view.model
        assert write_box.view == self.view
        assert write_box.msg_edit_id is None

    @pytest.mark.parametrize('text, prefix_string, state', [
        ('@Boo', '@', 0),
        ('@Boo', '@', 1),
        ('@_Boo', '@_', 0),
        ('@_Boo', '@_', 1),
        ('Plain Text', '', 0),
        ('Plain Text', '', 1),
    ])
    def test_generic_autocomplete(self, mocker, write_box, text,
                                  prefix_string, state):
        autocomplete_mentions = mocker.patch(WRITEBOX+'.autocomplete_mentions')
        return_val = write_box.generic_autocomplete(text, state)
        if prefix_string == '':
            assert return_val == text
        else:
            autocomplete_mentions.assert_called_once_with(text, state,
                                                          prefix_string)

    @pytest.mark.parametrize('text, state, prefix_string,\
                              required_typeahead', [
        ('@Human', 0, '@', '@**Human Myself**'),
        ('@Human', 1, '@', '@**Human 1**'),
        ('@Human', 2, '@', '@**Human 2**'),
        ('@_Human', 0, '@_', '@_**Human Myself**'),
        ('@_Human', 1, '@_', '@_**Human 1**'),
        ('@_Human', 2, '@_', '@_**Human 2**'),
        ('@H', 1, '@', '@**Human 1**'),
        ('@Hu', 1, '@', '@**Human 1**'),
        ('@Hum', 1, '@', '@**Human 1**'),
        ('@Huma', 1, '@', '@**Human 1**'),
        ('@Human', 1, '@', '@**Human 1**'),
        ('@Human 1', 0, '@', '@**Human 1**'),
        ('@_H', 1, '@_', '@_**Human 1**'),
        ('@_Hu', 1, '@_', '@_**Human 1**'),
        ('@_Hum', 1, '@_', '@_**Human 1**'),
        ('@_Huma', 1, '@_', '@_**Human 1**'),
        ('@_Human', 1, '@_', '@_**Human 1**'),
        ('@_Human 1', 0, '@_', '@_**Human 1**'),
        ('@Group', 0, '@', '@*Group 1*'),
        ('@Group', 1, '@', '@*Group 2*'),
        ('@G', 0, '@', '@*Group 1*'),
        ('@Gr', 0, '@', '@*Group 1*'),
        ('@Gro', 0, '@', '@*Group 1*'),
        ('@Grou', 0, '@', '@*Group 1*'),
        ('@G', 1, '@', '@*Group 2*'),
        ('@Gr', 1, '@', '@*Group 2*'),
        ('@Gro', 1, '@', '@*Group 2*'),
        ('@Grou', 1, '@', '@*Group 2*'),
        ('No match', 1, '', None),
    ])
    def test_autocomplete_mentions(self, write_box, users_fixture,
                                   text, state, prefix_string,
                                   required_typeahead, user_groups_fixture):
        write_box.view.users = users_fixture
        write_box.model.user_group_names = [
            groups['name'] for groups in user_groups_fixture]
        typeahead_string = write_box.autocomplete_mentions(
            text, state, prefix_string)
        assert typeahead_string == required_typeahead

    @pytest.mark.parametrize('text, state, required_typeahead', [
        ('#Stream', 0, '#**Stream 1**'),
        ('#Stream', 1, '#**Stream 2**'),
        ('#S', 0, '#**Some general stream**'),
        ('#S', 1, '#**Secret stream**'),
        ('#S', 2, '#**Stream 1**'),
        ('#S', 3, '#**Stream 2**'),
        ('#So', 0, '#**Some general stream**'),
        ('#So', 1, None),
        ('#Se', 0, '#**Secret stream**'),
        ('#Se', 1, None),
        ('#St', 0, '#**Stream 1**'),
        ('#St', 1, '#**Stream 2**'),
        ('#Stream 1', 0, '#**Stream 1**'),
        ('No match', 0, None)
    ])
    def test_autocomplete_streams(self, write_box, streams_fixture,
                                  text, state, required_typeahead):
        write_box.view.pinned_streams = [
            [stream['name']] for stream in
            streams_fixture[:len(streams_fixture)//2]]
        write_box.view.unpinned_streams = [
            [stream['name']] for stream in
            streams_fixture[len(streams_fixture)//2:]]
        typeahead_string = write_box.autocomplete_streams(text, state)
        assert typeahead_string == required_typeahead
