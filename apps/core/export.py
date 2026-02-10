"""Shared CSV and PDF export utilities."""
import csv
import io

from django.http import HttpResponse


def export_queryset_csv(queryset, fields, filename, headers=None):
    """
    Export a queryset to CSV.

    Args:
        queryset: Django queryset to export
        fields: list of field names or callables
        filename: output filename (without .csv)
        headers: optional list of column headers (defaults to field names)

    Returns:
        HttpResponse with CSV content
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    response.write('\ufeff')  # BOM for Excel UTF-8

    writer = csv.writer(response)

    if headers:
        writer.writerow(headers)
    else:
        writer.writerow([f if isinstance(f, str) else f.__name__ for f in fields])

    for obj in queryset:
        row = []
        for field in fields:
            if callable(field):
                row.append(field(obj))
            elif '__' in field:
                # Handle related field lookups
                parts = field.split('__')
                val = obj
                for part in parts:
                    val = getattr(val, part, '') if val else ''
                row.append(val)
            else:
                val = getattr(obj, field, '')
                # Use get_FOO_display() for choice fields if available
                display_method = f'get_{field}_display'
                if hasattr(obj, display_method):
                    val = getattr(obj, display_method)()
                row.append(val)
        writer.writerow(row)

    return response


def export_list_csv(data, headers, filename):
    """
    Export a list of dicts to CSV.

    Args:
        data: list of dicts
        headers: list of (key, label) tuples
        filename: output filename (without .csv)

    Returns:
        HttpResponse with CSV content
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    response.write('\ufeff')  # BOM for Excel UTF-8

    writer = csv.writer(response)
    writer.writerow([label for _, label in headers])

    for row_data in data:
        writer.writerow([row_data.get(key, '') for key, _ in headers])

    return response
