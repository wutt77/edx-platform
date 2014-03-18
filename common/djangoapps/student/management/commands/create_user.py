from optparse import make_option
from django.core.management.base import BaseCommand
from student.models import CourseEnrollment, Registration, create_comments_service_user
from student.views import _do_create_account, AccountValidationError
from django.contrib.auth.models import User

from track.management.tracked_command import TrackedCommand


class Command(TrackedCommand):
    help = """
    This command creates and registers a user in a given course
    as "audit", "verified" or "honor".

    example:
        # Enroll a user test@example.com into the demo course
        # The username and name will default to "test"
        manage.py ... create_user -e test@example.com -p insecure -c edX/Open_DemoX/edx_demo_course -m verified
    """

    option_list = BaseCommand.option_list + (
        make_option('-m', '--mode',
                    metavar='ENROLLMENT_MODE',
                    dest='mode',
                    default='honor',
                    choices=('audit', 'verified', 'honor'),
                    help='Enrollment type for user for a specific course'),
        make_option('-u', '--username',
                    metavar='USERNAME',
                    dest='username',
                    default=None,
                    help='Username, defaults to "user" in the email'),
        make_option('-n', '--name',
                    metavar='NAME',
                    dest='name',
                    default=None,
                    help='Name, defaults to "user" in the email'),
        make_option('-p', '--password',
                    metavar='NAME',
                    dest='password',
                    default=None,
                    help='Password for user'),
        make_option('-e', '--email',
                    metavar='EMAIL',
                    dest='email',
                    default=None,
                    help='Email for user'),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=None,
                    help='course to enroll the user in (optional)'),
        make_option('-s', '--staff',
                    metavar='COURSE_ID',
                    dest='staff',
                    default=False,
                    action='store_true',
                    help='give user the staff bit'),
    )

    def handle(self, *args, **options):
        username = options['username']
        name = options['name']
        if not username:
            username = options['email'].split('@')[0]
        if not name:
            name = options['email'].split('@')[0]

        post_data = {
            'username': username,
            'email': options['email'],
            'password': options['password'],
            'name': name,
            'honor_code': u'true',
            'terms_of_service': u'true',
        }
        try:
            user, profile, reg = _do_create_account(post_data)
            if options['staff']:
                user.is_staff = True
                user.save()
            reg.activate()
            reg.save()
            create_comments_service_user(user)
        except AccountValidationError as e:
            print e.message
            user = User.objects.get(email=options['email'])
        if options['course']:
            CourseEnrollment.enroll(user, options['course'], mode=options['mode'])
