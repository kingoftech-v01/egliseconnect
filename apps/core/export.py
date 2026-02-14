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


def export_queryset_excel(queryset, fields, filename, headers=None):
    """
    Export a queryset to Excel (.xlsx).

    Args:
        queryset: Django queryset to export
        fields: list of field names or callables
        filename: output filename (without .xlsx)
        headers: optional list of column headers (defaults to field names)

    Returns:
        HttpResponse with Excel content
    """
    try:
        from openpyxl import Workbook
    except ImportError:
        raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")

    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31]  # Excel sheet names max 31 chars

    # Write header row
    if headers:
        ws.append(headers)
    else:
        ws.append([f if isinstance(f, str) else f.__name__ for f in fields])

    # Write data rows
    for obj in queryset:
        row = []
        for field in fields:
            if callable(field):
                val = field(obj)
            elif '__' in field:
                parts = field.split('__')
                val = obj
                for part in parts:
                    val = getattr(val, part, '') if val else ''
            else:
                val = getattr(obj, field, '')
                display_method = f'get_{field}_display'
                if hasattr(obj, display_method):
                    val = getattr(obj, display_method)()
            # Convert non-serializable types to string
            if val is not None and not isinstance(val, (str, int, float, bool)):
                val = str(val)
            row.append(val if val is not None else '')
        ws.append(row)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    return response


def export_queryset_pdf(queryset, fields, filename, headers=None, template_string=None):
    """
    Export a queryset to PDF using xhtml2pdf.

    Args:
        queryset: Django queryset to export
        fields: list of field names or callables
        filename: output filename (without .pdf)
        headers: optional list of column headers
        template_string: optional HTML template string

    Returns:
        HttpResponse with PDF content
    """
    try:
        from xhtml2pdf import pisa
    except ImportError:
        raise ImportError("xhtml2pdf is required for PDF export. Install with: pip install xhtml2pdf")

    if headers is None:
        headers = [f if isinstance(f, str) else f.__name__ for f in fields]

    # Build table rows
    rows = []
    for obj in queryset:
        row = []
        for field in fields:
            if callable(field):
                val = field(obj)
            elif '__' in field:
                parts = field.split('__')
                val = obj
                for part in parts:
                    val = getattr(val, part, '') if val else ''
            else:
                val = getattr(obj, field, '')
                display_method = f'get_{field}_display'
                if hasattr(obj, display_method):
                    val = getattr(obj, display_method)()
            row.append(str(val) if val is not None else '')
        rows.append(row)

    if template_string is None:
        header_cells = ''.join(f'<th style="padding:5px;border:1px solid #ccc;background:#f5f5f5;">{h}</th>' for h in headers)
        body_rows = ''
        for row in rows:
            cells = ''.join(f'<td style="padding:5px;border:1px solid #ccc;">{cell}</td>' for cell in row)
            body_rows += f'<tr>{cells}</tr>'

        template_string = f"""
        <html><head><meta charset="utf-8"></head>
        <body style="font-family:sans-serif;font-size:10px;">
        <h2>{filename}</h2>
        <table style="width:100%;border-collapse:collapse;">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{body_rows}</tbody>
        </table>
        </body></html>
        """

    output = io.BytesIO()
    pisa.CreatePDF(io.StringIO(template_string), dest=output)
    output.seek(0)

    response = HttpResponse(output.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
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
