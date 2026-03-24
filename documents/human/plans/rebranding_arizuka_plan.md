# Plan Rebrandingu: Mrowisko → Arizuka

**Data:** 2026-03-24
**Autor:** Prompt Engineer
**Status:** Proposal (czeka na user approval)

---

## Executive Summary

**Obecna nazwa:** Mrowisko (polska, dosłowna, funkcjonalna)
**Proponowana:** Arizuka (蟻塚, japońska, symboliczna, międzynarodowa)

**Rationale:**
- **Trwałość:** 塚 (tsuka) = kopiec/kurhan → konotacja budowania czegoś monumentalnego, dziedzictwa
- **Międzynarodowość:** Łatwiejsze do wymówienia globalnie niż "Mrowisko"
- **Filozoficzne dopasowanie:** Mrówki budują struktury trwające pokolenia (jak kurhan) — fitting dla projektu budującego long-term architecture
- **Unikalność:** "Arizuka" rzadko używane w tech (unique branding)

---

## Analiza Nazw — Porównanie

| Aspekt | Mrowisko | Arizuka |
|--------|----------|---------|
| **Znaczenie** | Mrowisko (dosłowne) | Kopiec mrówek / Kurhan mrówek |
| **Konotacja** | Aktywność, ruch, chaos | Trwałość, budowanie, dziedzictwo |
| **Wymowa międzynarodowa** | Trudna (6+ sylab: "mro-vis-ko") | Łatwiejsza (4 sylaby: "a-ri-zu-ka") |
| **Tech branding** | Folklorystyczne, polskie | Eksotyczne, tech-friendly |
| **Domain availability** | mrowisko.ai/io (sprawdzić) | arizuka.ai/io (prawdopodobnie dostępne) |
| **SEO uniqueness** | Średnia (istnieje w polskim internecie) | Wysoka (rzadko używane) |
| **Alignment z SPIRIT.md** | Emergencja, autonomia | **Trwałość, legacy, budowanie fundamentów** |

---

## Branding Strategy

### Tagline Proposals

**Option 1 (Legacy-focused):**
> "Arizuka — where agents build legacy"

**Option 2 (Emergence-focused):**
> "Arizuka — autonomous agents, emergent architecture"

**Option 3 (Philosophy-focused):**
> "Arizuka — 蟻塚 — collective intelligence, enduring systems"

### Visual Identity

**Logo concept:**
- Stylizowany kopiec (kurhan shape) zbudowany z geometrycznych elementów (reprezentuje agentów)
- Minimalistyczny, monochrome lub earth tones (brown/gray — jak rzeczywisty kopiec)
- Kanji 蟻塚 jako secondary mark (optional, dla tech-savvy audiences)

**Color palette:**
- Primary: Earth brown (#8B4513) — kopiec, trwałość
- Secondary: Deep gray (#4A4A4A) — kamień, fundament
- Accent: Emerald green (#50C878) — życie, emergencja

---

## Technical Migration Checklist

### Phase 1: Code & Infrastructure (Week 1-2)

**Database:**
- [ ] Rename database: `mrowisko.db` → `arizuka.db`
- [ ] Update connection strings w wszystkich tools/
- [ ] Migration script: `tools/migration_rebranding.py` (copy + verify)

**Repository:**
- [ ] GitHub repo rename: `mrowisko` → `arizuka` (settings → rename)
- [ ] Update README.md (nazwa, opis, branding)
- [ ] Update all internal references (grep "Mrowisko" → replace "Arizuka")

**File paths:**
- [ ] Rename root folder: `Mrowisko/` → `Arizuka/`
- [ ] Update all absolute paths w code (grep "Mrowisko" case-sensitive)
- [ ] Update `.git/config` remote URLs (if affected)

**Environment variables:**
- [ ] Update `.env` files (if any reference project name)
- [ ] Update shell aliases / shortcuts

### Phase 2: Documentation (Week 2-3)

**Core documents:**
- [ ] `CLAUDE.md` — header + nazwa projektu
- [ ] `documents/methodology/SPIRIT.md` — replace "Mrowisko" → "Arizuka"
- [ ] `documents/architecture/PATTERNS.md` — examples w kontekście Arizuka
- [ ] All role documents (DEVELOPER.md, ARCHITECT.md, etc.) — project references

**External docs:**
- [ ] README.md (główny)
- [ ] Contributing guide (if exists)
- [ ] License file (copyright holder name)

**Comments in code:**
- [ ] Python docstrings (grep "Mrowisko")
- [ ] SQL comments
- [ ] Config file comments

### Phase 3: Branding Assets (Week 3-4)

**Domain:**
- [ ] Check availability: arizuka.ai, arizuka.io, arizuka.dev
- [ ] Purchase preferred domain
- [ ] Setup redirect: mrowisko.* → arizuka.* (if old domains exist)

**Visual:**
- [ ] Logo design (kurhan/kopiec motif)
- [ ] Favicon (minimalist 蟻 or kopiec shape)
- [ ] Social media graphics (if applicable)

**Marketing:**
- [ ] Update project description (GitHub, social media)
- [ ] Announcement post (blog/Twitter) — "Mrowisko rebrands to Arizuka"
- [ ] Press kit (logo, tagline, boilerplate description)

### Phase 4: Communication (Week 4)

**Internal:**
- [ ] Update all agent prompts (role documents) — "projekt Arizuka" consistency
- [ ] Session logs — note rebranding (for future context)

**External (if public project):**
- [ ] GitHub announcement (pinned issue or discussion)
- [ ] Social media posts
- [ ] Email to stakeholders (if any)

---

## Philosophy Alignment — Arizuka vs Spirit

**SPIRIT.md core tenets:**

| Tenet | Mrowisko fit | Arizuka fit |
|-------|--------------|-------------|
| **Emergencja > Planowanie** | ✓ Mrówki = emergent behavior | ✓ Kopiec = emergent structure |
| **Autonomia agentów** | ✓ Mrówki = autonomiczne | ✓ Każda mrówka niezależna |
| **Trwałość architektury** | ~ Mrowisko = aktywność (ruch) | ✓✓ Kopiec/kurhan = **trwałość, legacy** |
| **Budowanie fundamentów** | ~ Mrowisko = powierzchnia | ✓✓ 塚 (tsuka) = **monumentalna struktura** |
| **Long-term thinking** | ~ Neutral | ✓✓ Kurhan = pokoleniowa trwałość |

**Verdict:** **Arizuka lepiej odzwierciedla long-term vision** (budowanie trwałych fundamentów, nie tylko emergent chaos).

---

## Risks & Mitigations

### Risk 1: Breaking Changes (Internal)

**Problem:** All absolute paths, DB references break
**Mitigation:**
- Migration script (automated rename + verify)
- Comprehensive grep (find all "Mrowisko" references)
- Testing phase (run all tools post-rename, verify DB access)

### Risk 2: Loss of Polish Identity

**Problem:** "Mrowisko" was uniquely Polish, "Arizuka" is Japanese
**Mitigation:**
- Keep Polish as primary language (docs, prompts remain PL)
- Arizuka = branding layer (external), internal culture unchanged
- Optional: secondary tagline in Polish ("Arizuka — budujemy dziedzictwo AI")

### Risk 3: Pronunciation Confusion

**Problem:** Non-Japanese speakers may mispronounce "Arizuka"
**Mitigation:**
- Phonetic guide: "ah-ree-ZOO-kah" (4 sylaby, akcent na 3)
- Shorter alias: "Ari" (informal, internal)
- Logo pronunciation guide (website footer)

### Risk 4: Cultural Appropriation Perception

**Problem:** Using Japanese name without cultural connection
**Mitigation:**
- Transparent rationale (symbolism, not fetishization)
- Respect: use correct kanji 蟻塚, not random characters
- Educational: explain meaning (kopiec/kurhan, not just "sounds cool")

---

## Timeline

**Total: 4 weeks**

| Week | Phase | Effort | Owner |
|------|-------|--------|-------|
| 1-2 | Code & Infrastructure migration | High (10-15h) | Developer |
| 2-3 | Documentation update | Medium (8-10h) | Prompt Engineer + Architect |
| 3-4 | Branding assets | Medium (8-10h) | External (designer) or PE |
| 4 | Communication & launch | Low (3-5h) | All roles |

**Critical path:**
1. Database rename (Week 1) — blocker for all else
2. Code references (Week 1-2) — must complete before docs
3. Domain purchase (Week 3) — parallel, non-blocking
4. Announcement (Week 4) — after all technical complete

---

## Cost Estimate

**Domain:**
- arizuka.ai: ~$30-50/year (premium .ai TLD)
- arizuka.io: ~$15-25/year
- Total: ~$50-75/year

**Design (optional):**
- DIY (PE/Developer): $0 (time only)
- Freelance logo: $100-300 (Fiverr/99designs)
- Professional branding: $500-1500 (agency)

**Development time:**
- Internal: 30-40h (Developer + PE + Architect)
- Cost: $0 (volunteer) or ~$1500-2000 (if valued at $50/h)

**Total:** ~$50-2000 depending on design choice

---

## Decision Framework

**Go/No-Go criteria:**

**Go (rebranding makes sense) if:**
- ✓ Project going public (international audience)
- ✓ Long-term vision (5+ years)
- ✓ Philosophical alignment matters (trwałość > emergent chaos)
- ✓ Resources available (30-40h developer time)

**No-Go (stay with Mrowisko) if:**
- ✗ Project remains private/Polish-only
- ✗ Short-term experiment (<2 years horizon)
- ✗ Limited resources (can't afford 30-40h migration)
- ✗ Strong attachment to Polish identity (Mrowisko = cultural anchor)

---

## Recommendation (Prompt Engineer perspective)

**Verdict: Conditional GO**

**Why:**
- **Philosophical fit:** "Kopiec/kurhan" lepiej oddaje long-term vision (budowanie dziedzictwa) niż "mrowisko" (ruch, aktywność)
- **International potential:** Jeśli projekt ma ambicje globalne (publikacja, open-source), "Arizuka" łatwiejsze do brandowania
- **Unique positioning:** Rzadko używane w tech, strong SEO uniqueness

**Conditions:**
1. **User approval:** To fundamentalna zmiana (nazwa = tożsamość projektu)
2. **Resource commitment:** 30-40h to significant investment (czy warto teraz?)
3. **Timeline flexibility:** 4 weeks to minimum (nie rush)

**Alternative:** **Soft rebrand** (Arizuka jako external name, Mrowisko jako internal codename) — best of both worlds?

---

## Next Steps

**If approved:**
1. **Week 0:** User decision (go/no-go + timeline confirmation)
2. **Week 1:** Developer starts DB migration (critical path)
3. **Week 2:** PE updates docs (parallel with code)
4. **Week 3:** Domain purchase + branding design
5. **Week 4:** Announcement + launch

**If deferred:**
- Save plan for future (revisit in 6-12 months)
- Alternative: use "Arizuka" as subtitle/tagline ("Mrowisko (Arizuka) — budujemy dziedzictwo AI")

---

## Appendix: Name Alternatives (if Arizuka rejected)

**If "Arizuka" doesn't resonate, consider:**

1. **Myrmexis** (gr. myrmex = mrówka + -is suffix) — tech-elegant
2. **Formic.ai** (łac. formicarium) — .ai natural fit
3. **Anthive** (ant + hive) — hybrid concept
4. **Emergis** (emergence + -is) — philosophical
5. **Stay Mrowisko** — embrace Polish uniqueness

---

**Plan prepared by:** Prompt Engineer
**Reviewed by:** (pending — Architect, Developer, User)
**Status:** Draft — czeka na user decision

---

**User question:** Czy idziemy z rebrandingiem Arizuka, czy zostajemy przy Mrowisko? Albo soft rebrand (oba nazwy)?
