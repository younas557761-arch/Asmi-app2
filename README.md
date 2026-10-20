# ASMI — Artificial School Management Intelligent

A multi-tenant school management platform with an AI software builder.
Phase 1 (Foundation) is complete. There is NO demo data — every school
starts empty and the owner adds everything himself.

## Stack
- Frontend: Next.js (App Router), React, TypeScript
- Backend: Python, FastAPI, SQLAlchemy 2, Pydantic
- Database: PostgreSQL (own database, own server — no Supabase/Firebase)
- Auth: Argon2id password hashing, server-side sessions, HttpOnly cookies
- Tests: pytest
- Deploy: Docker Compose, or split hosting (frontend anywhere + backend anywhere)

## Quick start
