"""
Wyjątki domenowe dla core/.

Hierarchia:
- DomainError (bazowy)
  - InvalidStateError (próba niedozwolonej zmiany stanu)
  - NotFoundError (encja nie znaleziona)
  - ValidationError (błąd walidacji danych)
"""


class DomainError(Exception):
    """
    Bazowy wyjątek domenowy.

    Wszystkie wyjątki rzucane przez logikę biznesową dziedziczą z tej klasy.
    """
    pass


class InvalidStateError(DomainError):
    """
    Próba niedozwolonej zmiany stanu encji.

    Przykład:
        >>> suggestion = Suggestion(status=SuggestionStatus.IMPLEMENTED)
        >>> suggestion.reject()  # raises InvalidStateError
        InvalidStateError: Cannot reject suggestion in status IMPLEMENTED
    """
    pass


class NotFoundError(DomainError):
    """
    Encja nie znaleziona w bazie danych.

    Przykład:
        >>> repo.get(999)  # raises NotFoundError
        NotFoundError: Suggestion with id=999 not found
    """
    pass


class ValidationError(DomainError):
    """
    Błąd walidacji danych wejściowych.

    Przykład:
        >>> BacklogItem(title="", content="...")  # raises ValidationError
        ValidationError: Title cannot be empty
    """
    pass
