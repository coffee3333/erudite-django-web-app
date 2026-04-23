# Builder pattern for generating certificate PDFs.
# Instead of passing 5 positional args to generate_certificate_pdf(),
# we use a step-by-step builder so it's clear what each value is.
from core.utils.certificate_pdf import generate_certificate_pdf


class CertificateBuilder:

    def __init__(self):
        self._user = None
        self._course = None
        self._certificate_id = None
        self._issued_at = None
        self._score_pct = None

    def set_recipient(self, user) -> "CertificateBuilder":
        self._user = user
        return self

    def set_course(self, course) -> "CertificateBuilder":
        self._course = course
        return self

    def set_certificate_id(self, certificate_id) -> "CertificateBuilder":
        self._certificate_id = certificate_id
        return self

    def set_issued_at(self, issued_at) -> "CertificateBuilder":
        self._issued_at = issued_at
        return self

    def set_score(self, score_pct: float) -> "CertificateBuilder":
        self._score_pct = score_pct
        return self

    def build(self) -> bytes:
        # make sure nothing was forgotten before generating the PDF
        missing = [
            name for name, val in [
                ("recipient", self._user),
                ("course", self._course),
                ("certificate_id", self._certificate_id),
                ("issued_at", self._issued_at),
                ("score_pct", self._score_pct),
            ] if val is None
        ]
        if missing:
            raise ValueError(f"CertificateBuilder missing fields: {missing}")
        return generate_certificate_pdf(
            self._user,
            self._course,
            self._certificate_id,
            self._issued_at,
            self._score_pct,
        )
