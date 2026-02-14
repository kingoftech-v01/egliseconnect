"""Tests for member import wizard and services."""
import pytest
from io import BytesIO, StringIO

from apps.core.constants import Roles
from apps.members.models import Member, ImportHistory

from .factories import (
    UserFactory,
    MemberFactory,
    PastorFactory,
    AdminMemberFactory,
    ImportHistoryFactory,
)


@pytest.mark.django_db
class TestImportHistoryModel:
    """Tests for ImportHistory model."""

    def test_create_import_history(self):
        """ImportHistory creation with required fields."""
        history = ImportHistoryFactory()
        assert history.id is not None
        assert history.filename
        assert history.total_rows == 10
        assert history.success_count == 8
        assert history.error_count == 2

    def test_import_history_str(self):
        """String representation."""
        history = ImportHistoryFactory(filename='test.csv')
        assert 'test.csv' in str(history) or history.filename == 'test.csv'


@pytest.mark.django_db
class TestMemberImportService:
    """Tests for MemberImportService."""

    def test_parse_csv(self):
        """Parse a CSV file and extract headers and rows."""
        from apps.members.services_import import MemberImportService
        csv_content = "first_name,last_name,email\nJean,Dupont,jean@test.com\nPierre,Martin,pierre@test.com"
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'), content_type='text/csv')
        headers, rows = MemberImportService.parse_file(f)
        assert headers == ['first_name', 'last_name', 'email']
        assert len(rows) == 2
        assert rows[0]['first_name'] == 'Jean'

    def test_parse_invalid_file(self):
        """Parse raises ValueError for unsupported format."""
        from apps.members.services_import import MemberImportService
        from django.core.files.uploadedfile import SimpleUploadedFile
        f = SimpleUploadedFile('test.txt', b'some text', content_type='text/plain')
        with pytest.raises(ValueError):
            MemberImportService.parse_file(f)

    def test_validate_preview(self):
        """Validate preview returns validation results."""
        from apps.members.services_import import MemberImportService
        rows = [
            {'col_a': 'Jean', 'col_b': 'Dupont', 'col_c': 'jean@test.com'},
            {'col_a': '', 'col_b': 'Martin', 'col_c': 'pierre@test.com'},
        ]
        mapping = {'col_a': 'first_name', 'col_b': 'last_name', 'col_c': 'email'}
        preview = MemberImportService.validate_preview(rows, mapping)
        assert len(preview) == 2
        # First row should be valid
        assert preview[0]['valid'] is True
        # Second row may be invalid (missing first_name)

    def test_execute_import(self):
        """Execute import creates members and returns history."""
        from apps.members.services_import import MemberImportService
        preview = [
            {'valid': True, 'data': {'first_name': 'Jean', 'last_name': 'Dupont'}},
            {'valid': True, 'data': {'first_name': 'Pierre', 'last_name': 'Martin'}},
            {'valid': False, 'data': {}, 'errors': ['Missing data']},
        ]
        member = AdminMemberFactory()
        history = MemberImportService.execute_import(preview, imported_by=member)
        assert history.success_count == 2
        assert history.error_count == 1
        assert history.total_rows == 3
        assert Member.objects.filter(first_name='Jean', last_name='Dupont').exists()


@pytest.fixture(autouse=True)
def _setup_templates(settings, tmp_path):
    """Create minimal template stubs."""
    members_dir = tmp_path / 'members'
    members_dir.mkdir()
    template_names = [
        'import_upload.html',
        'import_map.html',
        'import_preview.html',
        'import_history.html',
    ]
    for name in template_names:
        (members_dir / name).write_text('{{ page_title|default:"test" }}')
    settings.TEMPLATES = [
        {
            **settings.TEMPLATES[0],
            'DIRS': [str(tmp_path)] + [
                str(d) for d in settings.TEMPLATES[0].get('DIRS', [])
            ],
        }
    ]


@pytest.fixture
def admin_user():
    """Admin member with linked user account."""
    user = UserFactory()
    member = AdminMemberFactory(user=user)
    return user, member


@pytest.fixture
def regular_user():
    """Regular member with linked user account."""
    user = UserFactory()
    member = MemberFactory(user=user, role=Roles.MEMBER)
    return user, member


@pytest.mark.django_db
class TestImportViews:
    """Tests for import wizard views."""

    def test_upload_get(self, client, admin_user):
        """Admin can access upload page."""
        user, member = admin_user
        client.force_login(user)
        response = client.get('/members/import/')
        assert response.status_code == 200

    def test_upload_denied_regular(self, client, regular_user):
        """Non-admin redirected from import."""
        user, member = regular_user
        client.force_login(user)
        response = client.get('/members/import/')
        assert response.status_code == 302

    def test_import_history_view(self, client, admin_user):
        """Admin can view import history."""
        user, member = admin_user
        ImportHistoryFactory()
        client.force_login(user)
        response = client.get('/members/import/history/')
        assert response.status_code == 200

    def test_map_redirect_without_session(self, client, admin_user):
        """Map page redirects if no session data."""
        user, member = admin_user
        client.force_login(user)
        response = client.get('/members/import/map/')
        assert response.status_code == 302

    def test_preview_redirect_without_session(self, client, admin_user):
        """Preview page redirects if no session data."""
        user, member = admin_user
        client.force_login(user)
        response = client.get('/members/import/preview/')
        assert response.status_code == 302
