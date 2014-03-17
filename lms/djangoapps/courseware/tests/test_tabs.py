from django.test import TestCase
from mock import MagicMock
from mock import patch

import xmodule.tabs as tabs

from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from .helpers import LoginEnrollmentTestCase

class TabTestCase(TestCase):
    """Base class for Tab-related test cases."""
    def setUp(self):

        self.course = MagicMock()
        self.course.id = 'edX/toy/2012_Fall'

    def check_tab(
            self,
            tab_class,
            dict_tab,
            expected_link,
            expected_tab_id,
            expected_name='same',
            invalid_dict_tab={'fake_tab_key': 'fake_tab_value'},
            expected_can_display_value=True
    ):
        # create tab
        tab = tab_class(dict_tab)

        # takes name from given tab
        self.assertEqual(tab.name, expected_name)

        # link is as expected
        self.assertEqual(tab.link_func(self.course), expected_link)

        # verify active page name
        self.assertEqual(tab.tab_id, expected_tab_id)

        # verify that the return value from can_display is as expected
        self.assertEqual(
            tab.can_display(self.course, is_user_authenticated=True, is_user_staff=True),
            expected_can_display_value
        )

        # validate tab
        self.assertTrue(tab.validate(dict_tab))
        if invalid_dict_tab:
            with self.assertRaises(tabs.InvalidTabsException):
                tab.validate(invalid_dict_tab)

        # return tab for any additional tests
        return tab


    def check_can_display_results(self, tab, for_authenticated_users_only=False, for_staff_only=False):
        """Check can display results for various users"""
        if for_staff_only:
            self.assertTrue(tab.can_display(self.course, is_user_authenticated=False, is_user_staff=True))
        if for_authenticated_users_only:
            self.assertTrue(tab.can_display(self.course, is_user_authenticated=True, is_user_staff=False))
        if not for_authenticated_users_only and not for_staff_only:
            self.assertTrue(tab.can_display(self.course, is_user_authenticated=False, is_user_staff=False))


class TabEqualityTestCase(TestCase):
    """Test cases for tab equality - especially for tabs that override the __eq__ method."""

    def test_courseware_tab_equality(self):
        tab1 = tabs.CoursewareTab()
        tab2 = tabs.CoursewareTab()
        self.assertEqual(tab1, tab1)
        self.assertEqual(tab1, tab2)
        self.assertEqual(tab1, {'type': tabs.CoursewareTab.type})
        self.assertEqual(tab1, {'type': tabs.CoursewareTab.type, 'name': tab1.name})
        self.assertNotEqual(tab1, {'type': tabs.CoursewareTab.type, 'name': 'fake_name'})
        self.assertNotEqual(tab1, {'type': 'fake_type', 'name': tab1.name})

    def test_static_tab_equality(self):
        tab1 = tabs.StaticTab(name="name1", url_slug="url1")
        tab2 = tabs.StaticTab(name="name1", url_slug="url1")
        tab3 = tabs.StaticTab(name="name3", url_slug="url3")
        self.assertEqual(tab1, tab1)
        self.assertEqual(tab1, tab2)
        self.assertNotEqual(tab1, tab3)
        self.assertEqual(tab1, {'type': tabs.StaticTab.type, 'name': tab1.name, 'url_slug': tab1.url_slug})
        self.assertNotEqual(tab1, {'type': tabs.StaticTab.type})
        self.assertNotEqual(tab1, {'type': tabs.StaticTab.type, 'name': tab1.name})
        self.assertNotEqual(tab1, {'type': 'fake_type', 'name': tab1.name, 'url_slug': tab1.url_slug})
        self.assertNotEqual(tab1, {'type': tabs.StaticTab.type, 'name': 'fake_name', 'url_slug': tab1.url_slug})
        self.assertNotEqual(tab1, {'type': tabs.StaticTab.type, 'name': tab1.name, 'url_slug': 'else'})


class ProgressTestCase(TabTestCase):
    """Test cases for Progress Tab."""

    def check_progress_tab(self, expected_can_display_value):
        return self.check_tab(
            tab_class=tabs.ProgressTab,
            dict_tab={'name': 'same'},
            expected_link=reverse('progress', args=[self.course.id]),
            expected_tab_id=tabs.ProgressTab.type,
            invalid_dict_tab=None,
            expected_can_display_value=expected_can_display_value,
        )

    def test_progress(self):

        self.course.hide_progress_tab = False
        tab = self.check_progress_tab(True)
        self.check_can_display_results(tab, for_authenticated_users_only=True)

        self.course.hide_progress_tab = True
        self.check_progress_tab(False)


class WikiTestCase(TabTestCase):
    """Test cases for Wiki Tab."""

    def check_wiki_tab(self, expected_can_display_value):

        self.check_tab(
            tab_class=tabs.WikiTab,
            dict_tab={'name': 'same'},
            expected_link=reverse('course_wiki', args=[self.course.id]),
            expected_tab_id=tabs.WikiTab.type,
            expected_can_display_value=expected_can_display_value,
        )

    @override_settings(WIKI_ENABLED=True)
    def test_wiki_enabled(self):

        self.check_wiki_tab(True)

    @override_settings(WIKI_ENABLED=False)
    def test_wiki_enabled_false(self):

        self.check_wiki_tab(False)


class ExternalLinkTestCase(TabTestCase):
    """Test cases for External Link Tab."""

    def test_external_link(self):

        self.check_tab(
            tab_class=tabs.ExternalLinkTab,
            dict_tab={'name': 'same', 'link': 'blink'},
            expected_link='blink',
            expected_tab_id=None,
            expected_can_display_value=True,
        )

class StaticTabTestCase(TabTestCase):

    def test_static_tab(self):

        url_slug = 'schmug'

        self.check_tab(
            tab_class=tabs.StaticTab,
            dict_tab={'name': 'same', 'url_slug': url_slug},
            expected_link=reverse('static_tab', args=[self.course.id, url_slug]),
            expected_tab_id='static_tab_schmug',
            expected_can_display_value=True
        )

@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class StaticTabDateTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):

    def setUp(self):
        self.course = CourseFactory.create()
        self.page = ItemFactory.create(
            category="static_tab", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="new_tab"
        )
        # The following XML course is closed; we're testing that
        # static tabs still appear when the course is already closed
        self.xml_data = "static 463139"
        self.xml_url = "8e4cce2b4aaf4ba28b1220804619e41f"
        self.xml_course_id = 'edX/detached_pages/2014'

    def test_logged_in(self):
        self.setup_user()
        url = reverse('static_tab', args=[self.course.id, 'new_tab'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    def test_anonymous_user(self):
        url = reverse('static_tab', args=[self.course.id, 'new_tab'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_logged_in_xml(self):
        self.setup_user()
        url = reverse('static_tab', args=[self.xml_course_id, self.xml_url])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)

    @patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_anonymous_user_xml(self):
        url = reverse('static_tab', args=[self.xml_course_id, self.xml_url])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)


class TextbooksTestCase(TabTestCase):
    """Test cases for Textbook Tab."""

    def setUp(self):
        super(TextbooksTestCase, self).setUp()

        self.dict_tab = MagicMock()
        textbook_a = MagicMock()
        textbook_t = MagicMock()
        textbook_a.title = 'Book1: Algebra'
        textbook_t.title = 'Book2: Topology'
        self.course.textbooks = [textbook_a, textbook_t]

    @override_settings(FEATURES={'ENABLE_TEXTBOOK': True})
    def test_textbooks1(self):

        tab = tabs.TextbookTabs(self.dict_tab)
        self.check_can_display_results(tab, for_authenticated_users_only=True)
        for i, book in enumerate(tab.books(self.course)):
            expected_link = reverse('book', args=[self.course.id, i])
            self.assertEqual(book.link_func(self.course), expected_link)
            self.assertEqual(book.tab_id, 'textbook/{0}'.format(i))
            self.assertTrue(book.name.startswith('Book{0}:'.format(i+1)))

    @override_settings(FEATURES={'ENABLE_TEXTBOOK': False})
    def test_textbooks0(self):

        tab = tabs.TextbookTabs(self.dict_tab)
        self.assertFalse(tab.can_display(self.course, is_user_authenticated=True, is_user_staff=True))


class GradingTestCase(TabTestCase):
    """Test cases for Grading related Tabs."""

    def check_grading_tab(self, tab_class, name, link_value):
        return self.check_tab(
            tab_class=tab_class,
            dict_tab={'name': name},
            expected_name=name,
            expected_link=reverse(link_value, args=[self.course.id]),
            expected_tab_id=tab_class.type,
            expected_can_display_value=True,
            invalid_dict_tab=None,
        )

    def test_grading_tabs(self):

        peer_grading_tab = self.check_grading_tab(
            tabs.PeerGradingTab,
            'Peer grading',
            'peer_grading'
        )
        self.check_can_display_results(peer_grading_tab, for_authenticated_users_only=True)
        open_ended_grading_tab = self.check_grading_tab(
            tabs.OpenEndedGradingTab,
            'Open Ended Panel',
            'open_ended_notifications'
        )
        self.check_can_display_results(open_ended_grading_tab, for_authenticated_users_only=True)
        staff_grading_tab = self.check_grading_tab(
            tabs.StaffGradingTab,
            'Staff grading',
            'staff_grading'
        )
        self.check_can_display_results(staff_grading_tab, for_staff_only=True)


class NotesTestCase(TabTestCase):
    """Test cases for Notes Tab."""

    def check_notes_tab(self, expected_can_display_value):

        return self.check_tab(
            tab_class=tabs.NotesTab,
            dict_tab={'name': 'same'},
            expected_link=reverse('notes', args=[self.course.id]),
            expected_tab_id=tabs.NotesTab.type,
            expected_can_display_value=expected_can_display_value,
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_STUDENT_NOTES": True})
    def test_notes_tabs_enabled(self):
        tab = self.check_notes_tab(True)
        self.check_can_display_results(tab, for_authenticated_users_only=True)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_STUDENT_NOTES": False})
    def test_notes_tabs_disabled(self):
        self.check_notes_tab(False)


class SyllabusTestCase(TabTestCase):
    """Test cases for Syllabus Tab."""

    def check_syllabus_tab(self, expected_can_display_value):

        name = 'Syllabus'
        self.check_tab(
            tab_class=tabs.SyllabusTab,
            dict_tab={'name': name},
            expected_name=name,
            expected_link=reverse('syllabus', args=[self.course.id]),
            expected_tab_id=tabs.SyllabusTab.type,
            expected_can_display_value=expected_can_display_value,
            invalid_dict_tab=None,
        )

    def test_syllabus_tab_enabled(self):
        self.course.syllabus_present = True
        self.check_syllabus_tab(True)

    def test_syllabus_tab_disabled(self):
        self.course.syllabus_present = False
        self.check_syllabus_tab(False)


class InstructorTestCase(TabTestCase):
    """Test cases for Instructor Tab."""

    def test_instructor_tab(self):
        name = 'Instructor'
        tab = self.check_tab(
            tab_class=tabs.InstructorTab,
            dict_tab={'name': name},
            expected_name=name,
            expected_link=reverse('instructor_dashboard', args=[self.course.id]),
            expected_tab_id=tabs.InstructorTab.type,
            expected_can_display_value=True,
            invalid_dict_tab=None,
        )
        self.check_can_display_results(tab, for_staff_only=True)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class DiscussionLinkTestCase(ModuleStoreTestCase):
    """Test cases for discussion link tab."""

    def setUp(self):
        self.tabs_with_discussion = [
            tabs.CoursewareTab(),
            tabs.CourseInfoTab(),
            tabs.DiscussionTab(),
            tabs.TextbookTabs(),
        ]
        self.tabs_without_discussion = [
            tabs.CoursewareTab(),
            tabs.CourseInfoTab(),
            tabs.TextbookTabs(),
        ]

    @staticmethod
    def _patch_reverse(course):
        """Allows tests to override the reverse function"""
        def patched_reverse(viewname, args):
            """Function to override the reverse function"""
            if viewname == "django_comment_client.forum.views.forum_form_discussion" and args == [course.id]:
                return "default_discussion_link"
            else:
                return None
        return patch("xmodule.tabs.reverse", patched_reverse)

    def check_discussion(self, course, expected_discussion_link, expected_can_display_value):
        """
        Helper function to verify that the discussion tab exists and can be displayed
        """
        discussion = tabs.CourseTabList.get_discussion(course)
        with self._patch_reverse(course):
            self.assertEquals((
                    discussion is not None and
                    discussion.can_display(course, True, True) and
                    (discussion.link_func(course) == expected_discussion_link)
                ),
                expected_can_display_value
            )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": False})
    def test_explicit_discussion_link(self):
        """Test that setting discussion_link overrides everything else"""
        self.check_discussion(
            CourseFactory.create(discussion_link="other_discussion_link", tabs=self.tabs_with_discussion),
            expected_discussion_link="other_discussion_link",
            expected_can_display_value=True
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": False})
    def test_discussions_disabled(self):
        """Test that other cases return None with discussions disabled"""
        for i, t in enumerate([[], self.tabs_with_discussion, self.tabs_without_discussion]):
            self.check_discussion(
                CourseFactory.create(tabs=t, number=str(i)),
                expected_discussion_link=not None,
                expected_can_display_value=False,
            )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_no_tabs(self):
        """Test a course without tabs configured"""
        self.check_discussion(
            CourseFactory.create(),
            expected_discussion_link="default_discussion_link",
            expected_can_display_value=True
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_tabs_with_discussion(self):
        """Test a course with a discussion tab configured"""
        self.check_discussion(
            CourseFactory.create(tabs=self.tabs_with_discussion),
            expected_discussion_link="default_discussion_link",
            expected_can_display_value=True
        )

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_tabs_without_discussion(self):
        """Test a course with tabs configured but without a discussion tab"""
        self.check_discussion(
            CourseFactory.create(tabs=self.tabs_without_discussion),
            expected_discussion_link=not None,
            expected_can_display_value=False,
        )


class KeyCheckerTestCase(TestCase):
    """Test cases for KeyChecker class"""

    def setUp(self):

        self.valid_keys = ['a', 'b']
        self.invalid_keys = ['a', 'v', 'g']
        self.dict_value = {'a': 1, 'b': 2, 'c': 3}

    def test_key_checker(self):

        self.assertTrue(tabs.key_checker(self.valid_keys)(self.dict_value, raise_error=False))
        with self.assertRaises(tabs.InvalidTabsException):
            tabs.key_checker(self.invalid_keys)(self.dict_value)


class NeedNameTestCase(TestCase):
    """Test cases for NeedName validator"""

    def setUp(self):

        self.valid_dict1 = {'a': 1, 'name': 2}
        self.valid_dict2 = {'name': 1}
        self.valid_dict3 = {'a': 1, 'name': 2, 'b': 3}
        self.invalid_dict = {'a': 1, 'b': 2}

    def test_need_name(self):
        self.assertTrue(tabs.need_name(self.valid_dict1))
        self.assertTrue(tabs.need_name(self.valid_dict2))
        self.assertTrue(tabs.need_name(self.valid_dict3))
        with self.assertRaises(tabs.InvalidTabsException):
            tabs.need_name(self.invalid_dict)


class ValidateTabsTestCase(TestCase):
    """Test cases for validating tabs."""

    def setUp(self):

        self.courses = [MagicMock() for i in range(0, 7)]  # pylint: disable=unused-variable

        # invalid tabs
        self.invalid_tabs = [
            # invalid type and missing course_info
            [{'type': tabs.CoursewareTab.type}, {'type': 'fake_type'}],
            # invalid type and incorrect order
            [{'type': 'fake_type'}, {'type': tabs.CourseInfoTab.type}],
            # invalid type
            [{'type': tabs.CoursewareTab.type}, {'type': tabs.CourseInfoTab.type}, {'type': 'fake_type'}],
            # incorrect order
            [{'type': tabs.CourseInfoTab.type}, {'type': tabs.CoursewareTab.type}],
        ]

        # tab types that should appear only once
        unique_tab_types = [
            tabs.CourseInfoTab.type,
            tabs.CoursewareTab.type,
            tabs.NotesTab.type,
            tabs.TextbookTabs.type,
            tabs.PDFTextbookTabs.type,
            tabs.HtmlTextbookTabs.type,
        ]

        for unique_tab_type in unique_tab_types:
            self.invalid_tabs.append([
                {'type': tabs.CourseInfoTab.type},
                {'type': tabs.CoursewareTab.type},
                # add the unique tab multiple times
                {'type': unique_tab_type},
                {'type': unique_tab_type},
            ])

        # valid tabs
        self.valid_tabs = [
            # empty list
            [],
            # all valid tabs
            [
                {'type': tabs.CoursewareTab.type},
                {'type': tabs.CourseInfoTab.type, 'name': 'alice'},
                {'type': tabs.WikiTab.type, 'name': 'alice'},
                {'type': tabs.DiscussionTab.type, 'name': 'alice'},
                {'type': tabs.ExternalLinkTab.type, 'name': 'alice', 'link': 'blink'},
                {'type': tabs.TextbookTabs.type},
                {'type': tabs.PDFTextbookTabs.type},
                {'type': tabs.HtmlTextbookTabs.type},
                {'type': tabs.ProgressTab.type, 'name': 'alice'},
                {'type': tabs.StaticTab.type, 'name': 'alice', 'url_slug': 'schlug'},
                {'type': tabs.PeerGradingTab.type},
                {'type': tabs.StaffGradingTab.type},
                {'type': tabs.OpenEndedGradingTab.type},
                {'type': tabs.NotesTab.type, 'name': 'alice'},
                {'type': tabs.SyllabusTab.type},
            ],
            # with external discussion
            [
                {'type': tabs.CoursewareTab.type},
                {'type': tabs.CourseInfoTab.type, 'name': 'alice'},
                {'type': tabs.ExternalDiscussionTab.type, 'name': 'alice', 'link': 'blink'}
            ],
        ]

    def test_validate_tabs(self):
        tab_list = tabs.CourseTabList()
        for invalid_tab_list in self.invalid_tabs:
            with self.assertRaises(tabs.InvalidTabsException):
                tab_list.from_json(invalid_tab_list)

        for valid_tab_list in self.valid_tabs:
            from_json_result = tab_list.from_json(valid_tab_list)
            self.assertEquals(len(from_json_result), len(valid_tab_list))

