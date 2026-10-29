"""Transcript and report card PDFs (Vaishnavi): issue #14. Details in docs/TEAM_GUIDE.md.

  GET /reports/transcript/<studentId>             own student, admin   PDF (unofficial)
  GET /reports/report-card?studentId=&termId=     admin                PDF (official)
  GET /ui/admin/report-cards                      admin page: pick student + term
"""
from flask import Blueprint

bp = Blueprint("reports", __name__)
