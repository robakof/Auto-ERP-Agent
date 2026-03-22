"""
Core repositories — persystencja encji do bazy danych.

Moduły:
- base: Repository[T] — abstrakcja repozytorium
- suggestion_repo: SuggestionRepository
- backlog_repo: BacklogRepository (M2 part 2)
- message_repo: MessageRepository (M2 part 2)
"""

# Milestone 2 part 1 exports
from .base import Repository
from .suggestion_repo import SuggestionRepository

__all__ = [
    "Repository",
    "SuggestionRepository",
]
