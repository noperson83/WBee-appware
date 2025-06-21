from io import BytesIO

from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML


class Render:

    @staticmethod
    def render(path: str, params: dict):
        template = get_template(path)
        html = template.render(params)

        # Use WeasyPrint to generate the PDF
        pdf_bytes = HTML(string=html, base_url=".").write_pdf()

        return HttpResponse(pdf_bytes, content_type="application/pdf")
