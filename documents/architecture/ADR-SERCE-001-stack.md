# ADR-SERCE-001: Stack technologiczny projektu Serce

Date: 2026-04-09
Status: Proposed

---

## Context

Projekt Serce to platforma wzajemnej pomocy — web + mobile, backend z logiką
transferów walutowych (serca), geografia PL (województwa/miasta).

Wymagania:
- Transakcje ACID (transfer serc musi być atomowy)
- Web + mobile z jednym backendem
- Python jako preferowany język backendu
- Małe koszty startowe, łatwy onboarding Developera

---

## Decision

**Backend:** FastAPI (Python 3.12) + PostgreSQL 16 + SQLAlchemy 2.x + Alembic

**Frontend web:** Next.js 14 (React, TypeScript)

**Mobile:** React Native + Expo

**Auth:** JWT (access token 15min, refresh 30 dni, httpOnly cookie)

**Konteneryzacja:** Docker + docker-compose

---

## Consequences

### Zyskujemy

- FastAPI: natywny async, automatyczne OpenAPI docs, typowany przez Pydantic — szybki development, łatwe testy
- PostgreSQL: ACID transactions, CHECK constraints (heart_balance >= 0), JSON columns jeśli potrzeba, FTS wbudowany
- Next.js: SSR dla SEO (feed próśb powinien być indeksowany), duży ekosystem, TypeScript first
- React Native + Expo: współdzielony API client i logika z frontendem — jeden team obsługuje web + mobile
- Docker: identyczne środowisko dev/prod, łatwy onboarding

### Tracimy / ryzykujemy

- React Native: nie jest natywny (performance gorszy niż Swift/Kotlin) — akceptowalne dla v1
- SQLAlchemy: ORM overhead dla złożonych queries — używamy raw SQL przez SQLAlchemy Core gdy potrzeba
- FastAPI bez cache (Redis): przy dużym ruchu feedu może być wolny — Redis dodajemy gdy manifestuje się potrzeba

### Odwracalność

- Backend: FastAPI → Django REST Framework / Flask — łatwa migracja (Python, podobna struktura)
- Frontend: Next.js → inne React framework — łatwa migracja
- Mobile: React Native → Flutter — trudna (przepisanie), ale v1 to dopiero weryfikacja rynku
- DB: PostgreSQL → inna relacyjna — trudna, ale nie planujemy

---

## Alternatywy odrzucone

**Node.js (Express/NestJS) zamiast FastAPI:**
Odrzucone — Python preferowany, FastAPI nie ustępuje Node.js pod względem performance
dla tego use case.

**Django zamiast FastAPI:**
Odrzucone — Django zbyt ciężki dla API-first projektu. FastAPI daje pełną kontrolę.

**Flutter zamiast React Native:**
Odrzucone — brak współdzielonego kodu z Next.js frontend. React Native + Expo daje
re-use API client i hooks.

**SQLite:**
Odrzucone — brak row-level locking, nie nadaje się do równoległych transferów serc.
