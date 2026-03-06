"""Tests for CSV/PDF export utilities."""
import pytest
from django.test import TestCase

from apps.core.export import export_queryset_csv, export_list_csv


class TestExportListCSV:
    def test_returns_csv_response(self):
        data = [{'name': 'Jean', 'age': '30'}, {'name': 'Marie', 'age': '25'}]
        headers = [('name', 'Nom'), ('age', 'Âge')]
        response = export_list_csv(data, headers, 'test_export')

        assert response['Content-Type'] == 'text/csv'
        assert 'test_export.csv' in response['Content-Disposition']

    def test_csv_content(self):
        data = [{'name': 'Jean', 'age': '30'}]
        headers = [('name', 'Nom'), ('age', 'Âge')]
        response = export_list_csv(data, headers, 'test')

        content = response.content.decode('utf-8')
        assert 'Nom' in content
        assert 'Jean' in content
        assert '30' in content

    def test_empty_data(self):
        data = []
        headers = [('name', 'Nom')]
        response = export_list_csv(data, headers, 'empty')

        content = response.content.decode('utf-8')
        assert 'Nom' in content


@pytest.mark.django_db
class TestExportQuerysetCSV:
    def test_export_members(self):
        from apps.members.tests.factories import MemberFactory

        member = MemberFactory(first_name='Jean', last_name='Test')
        from apps.members.models import Member
        qs = Member.objects.filter(pk=member.pk)

        response = export_queryset_csv(
            qs,
            ['first_name', 'last_name', 'email'],
            'members_export',
            headers=['Prénom', 'Nom', 'Courriel'],
        )

        assert response['Content-Type'] == 'text/csv'
        content = response.content.decode('utf-8')
        assert 'Jean' in content
        assert 'Test' in content
