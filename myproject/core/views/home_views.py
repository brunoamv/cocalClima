"""
Home and navigation views.

Extracted from core/views.py following Single Responsibility Principle.
Handles homepage and basic navigation.
"""

from django.shortcuts import render


def home(request):
    """Render the main homepage."""
    return render(request, "index.html")