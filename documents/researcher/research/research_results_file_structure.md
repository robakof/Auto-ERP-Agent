# Research: Struktura plików i katalogów w monorepo wieloagentowym

Data: 2026-03-30

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana

## TL;DR — 5-7 najważniejszych kierunków

1. **W dużych monorepo dominują granice per-project / per-package / per-bounded-context, a nie czysty podział „katalog per zespół”.** Zespoły i role są zwykle modelowane metadanymi (owners, tags, visibility, CODEOWNERS), a nie jako główna oś drzewa katalogów. Potwierdzają to oficjalne wzorce Nx (`apps/`, `packages/`, projekty auto-discover), Turborepo (`apps/`, `packages/`) oraz Bazel (repo jako hierarchia pakietów z `BUILD`). **Siła dowodów: praktyczne.**  
   Źródła: [Nx – Crafting Your Workspace](https://nx.dev/docs/getting-started/tutorials/crafting-your-workspace), [Turborepo – Structuring a repository](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository), [Bazel – Repositories, workspaces, packages, and targets](https://bazel.build/concepts/build-ref)

2. **Przy skali 10+ zespołów / 100+ kontrybutorów kluczowy problem to nie samo „gdzie leżą pliki”, lecz jak egzekwować granice zależności, własność i blast radius zmian.** W praktyce dochodzi do dryfu architektury, nadmiarowych zależności, ciężkiego CI i niejasnej odpowiedzialności; narzędzia odpowiadają na to graph-based analysis, selective execution, cache i rules-as-code. **Siła dowodów: praktyczne + empiryczne.**  
   Źródła: [Nx vs Turborepo](https://nx.dev/docs/guides/adopting-nx/why-nx#nx-vs-turborepo), [Pants – Effective monorepos with Pants](https://www.pantsbuild.org/blog/2022/03/15/effective-monorepos-with-pants), [Why Google Stores Billions of Lines of Code in a Single Repository](https://research.google/pubs/pub45424/)

3. **Najbardziej dojrzały model ownership w repo to hybryda: struktura per-project + CODEOWNERS / owners metadata + reguły review/CI.** Sam folder ownership rzadko wystarcza. GitHub/GitLab pozwalają wymuszać approvale właścicieli, a Nx idzie dalej, modelując ownerów na poziomie projektów i tagów. **Siła dowodów: praktyczne.**  
   Źródła: [GitHub Docs – About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [GitHub Docs – Branch protection rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches), [Nx Powerpack / Owners](https://nx.dev/blog/introducing-nx-powerpack)

4. **W multi-agent AI nie widać jeszcze jednego ustalonego standardu „per-agent filesystem isolation” porównywalnego z dojrzałymi praktykami monorepo.** Dominują pragmatyczne wzorce: `thread_id`, katalog sesji, `work_dir`, tymczasowy workspace, pamięć per-agent/per-project lub sandbox backend. To raczej operacyjny pattern niż stabilny standard. **Siła dowodów: praktyczne.**  
   Źródła: [LangGraph – Persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [LangChain – Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview), [AutoGen – Command Line Code Executors](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/components/command-line-code-executors.html), [ChatDev memory docs](https://github.com/OpenBMB/ChatDev/blob/main/docs/user_guide/en/modules/memory.md), [MetaGPT repo](https://github.com/FoundationAgents/MetaGPT)

5. **Pliki współdzielone i artefakty cross-team zwykle nie są rozwiązywane przez „wspólny folder bez zasad”, tylko przez jawne wyjątki governance: shared/core packages, visibility rules, wymagane review, publishing pipelines, albo synchronizację do downstream repo.** **Siła dowodów: praktyczne + empiryczne.**  
   Źródła: [Bazel visibility](https://bazel.build/concepts/visibility), [Kubernetes staging/publishing-bot](https://github.com/kubernetes/kubernetes/tree/master/staging), [Hybrid Organizational Structure for OSS Communities](https://arxiv.org/abs/2407.09498)

6. **Nazewnictwo przy skali działa najlepiej, gdy opiera się o hierarchię i namespace’y (np. scope pakietu, nazwa projektu, tag domeny), a nie o płaskie zbiory podobnych plików.** Dla samych nazw plików mocne, bezpośrednie badania porównawcze są skąpe; praktyka jest zgodna co do: spójności, machine-readable names, unikania kolizji i dodawania dat/wersji tylko tam, gdzie artefakt jest czasowy lub raportowy. **Siła dowodów: praktyczne; bezpośrednie porównania — nie udało się potwierdzić.**  
   Źródła: [npm package scopes](https://docs.npmjs.com/cli/v10/using-npm/scope), [Stanford file naming best practices](https://library.stanford.edu/data-management-services/data-best-practices/best-practices-file-naming), [CESSDA file naming convention](https://www.cessda.eu/Training/Training-Resources/Library/Data-Management-Expert-Guide/3.-Process/3.4.-File-name-conventions)

7. **Najstabilniejszy wzorzec dla „temporary vs persistent” to: trwałe artefakty w repo lub artifact store; cache, scratch, debug i intermediate outputs poza ścieżką źródłową, ignorowane przez Git i objęte retencją/TTL.** W praktyce wspierają to `gitignore`, `git clean -X`, task outputs/caches w build tools i polityki retencji artefaktów CI. **Siła dowodów: praktyczne.**  
   Źródła: [gitignore](https://git-scm.com/docs/gitignore), [git clean](https://git-scm.com/docs/git-clean), [Turborepo configuration / outputs](https://turborepo.dev/docs/reference/configuration), [GitHub Actions artifact retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)

## Wyniki per obszar badawczy

### A. Monorepo structure patterns

**1) Dominujący wzorzec struktury to „repo root orchestration + wiele projektów/pakietów”, nie jeden uniwersalny podział per-team.**  
Nx opisuje workspace, w którym projekty są wykrywane z package-manager workspaces i często lądują pod `apps/*` oraz `packages/*`; Turborepo rekomenduje analogiczny układ z `apps/` dla aplikacji/usług i `packages/` dla współdzielonych bibliotek/narzędzi; Bazel traktuje repo jako hierarchię pakietów, gdzie podstawową jednostką organizacyjną jest katalog z plikiem `BUILD`. **Siła dowodów: praktyczne.**  
**Synteza:** przy tych narzędziach pierwszorzędną osią organizacji jest „co buduje się i wersjonuje razem”, a nie „kto nad tym pracuje”.  
Źródła: [Nx – Crafting Your Workspace](https://nx.dev/docs/getting-started/tutorials/crafting-your-workspace), [Turborepo – Structuring a repository](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository), [Bazel – build concepts](https://bazel.build/concepts/build-ref)

**2) Per-team folders występują częściej jako warstwa ownership/governance niż jako główny model topologii kodu.**  
W oficjalnych narzędziach granice architektoniczne są wyrażane przez projekty, pakiety, visibility, tags i dependency rules. Nx dodaje `enforce-module-boundaries`, Turborepo ma `boundaries` oparte o tagi, Bazel ma visibility, Yarn ma workspace constraints, a Pants opiera selekcję i invalidation na zależnościach wykrytych do poziomu pliku. **Siła dowodów: praktyczne.**  
**Trade-off:**  
- **Per-feature / per-domain / per-package** lepiej odpowiada „co zmienia się razem” i ułatwia dependency analysis.  
- **Per-team** upraszcza ownership, ale zwykle gorzej odwzorowuje zależności między produktami i zwiększa liczbę wyjątków/shared areas.  
Źródła: [Nx – Enforce Module Boundaries](https://nx.dev/docs/technologies/eslint/eslint-plugin/guides/enforce-module-boundaries), [Turborepo – configuration / boundaries](https://turborepo.dev/docs/reference/configuration), [Yarn – Workspaces / Constraints](https://yarnpkg.com/features/workspaces), [Pants – Effective monorepos with Pants](https://www.pantsbuild.org/blog/2022/03/15/effective-monorepos-with-pants)

**3) Przy skali 10+ zespołów problemem staje się architektoniczny drift i blast radius zmian.**  
Nx wprost argumentuje, że w dużym workspace „który utracił strukturę” powstaje dryf zależności i potrzebne są tags / lint rules / conformance. Uber opisuje wyzwanie polegające na tym, że pojedynczy commit może dotykać tysiące usług, więc kluczowe staje się ograniczanie blast radius. Google opisuje monorepo na ogromną skalę jako trade-off między spójnością a kosztami narzędzi i workflow. **Siła dowodów: praktyczne + empiryczne.**  
**Typowe problemy przy skali:**  
- nadmiarowe zależności i importy „na skróty”,  
- wzrost kosztu CI/build/test,  
- trudna identyfikacja właściciela zmiany,  
- coraz większe shared areas,  
- zbyt duże / zbyt skomplikowane reguły CODEOWNERS.  
Źródła: [Nx vs Turborepo](https://nx.dev/docs/guides/adopting-nx/why-nx#nx-vs-turborepo), [Uber Engineering – Monorepo at scale](https://www.uber.com/en-PL/blog/building-uber-with-monorepo/), [Google monorepo paper](https://research.google/pubs/pub45424/)

**4) Narzędzia nie tylko „obsługują” strukturę — one ją współtworzą i egzekwują.**  
- **Nx:** project graph, affected execution, module boundaries, owners, conformance, TypeScript solution-style project references.  
- **Turborepo:** workspaces + `turbo.json`, task `outputs`, `boundaries`, cache i concurrency controls.  
- **Bazel:** packages + visibility + query + zdalny cache.  
- **Pants:** source roots, inference zależności na poziomie pliku, uruchamianie po changed files / dependees.  
- **Yarn:** constraints do repo-wide zasad dla workspace’ów.  
**Siła dowodów: praktyczne.**  
**Wniosek syntetyczny:** „struktura katalogów” bez odpowiadających jej reguł narzędziowych nie skaluje się dobrze.  
Źródła: [Nx docs](https://nx.dev/docs), [Turborepo configuration](https://turborepo.dev/docs/reference/configuration), [Bazel concepts](https://bazel.build/concepts/build-ref), [Pants monorepo guide](https://www.pantsbuild.org/blog/2022/03/15/effective-monorepos-with-pants), [Yarn workspaces](https://yarnpkg.com/features/workspaces)

### B. Agent workspace conventions

**1) Nie udało się potwierdzić istnienia jednego dominującego standardu „per-agent isolation na poziomie drzewa repo”.**  
W oficjalnych frameworkach agentowych izolacja częściej jest modelowana przez stan wykonania, sesję, pamięć lub roboczy katalog niż przez trwały, dojrzały model ownership katalogów w repo. **Siła dowodów: praktyczne.**  
**To jest ważny negatywny wynik:** brak jednego stabilnego, szeroko przyjętego wzorca porównywalnego z `apps/packages` w monorepo tooling.

**2) Dominują cztery praktyczne wzorce izolacji pracy agentów.**  
- **Thread/session isolation** — LangGraph zapisuje checkpointy per krok i organizuje je przez `thread_id`.  
- **Working directory / sandbox isolation** — AutoGen wykonuje wygenerowany kod w `work_dir`; Deep Agents wspiera różne backendy filesystemu i subagentów dla izolacji kontekstu.  
- **Session artifact folders** — ChatDev zapisuje kontekst i artefakty do katalogu sesji w `WareHouse/...`; MetaGPT tworzy repo projektu w `./workspace`.  
- **Scoped memory** — CrewAI dokumentuje współdzieloną pamięć crew oraz scope’y typu `/project/...` i `/agent/...`.  
**Siła dowodów: praktyczne.**  
Źródła: [LangGraph – Persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview), [AutoGen code executors](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/components/command-line-code-executors.html), [ChatDev memory docs](https://github.com/OpenBMB/ChatDev/blob/main/docs/user_guide/en/modules/memory.md), [MetaGPT repo](https://github.com/FoundationAgents/MetaGPT), [CrewAI docs](https://docs.crewai.com)

**3) Frameworki częściej rozdzielają „kontekst roboczy agenta” od „kanonicznych artefaktów projektu” niż implementują pełny file-locking model.**  
To widać szczególnie w Deep Agents (filesystem jako backend kontekstu), LangGraph (`thread_id` jako klucz stanu) i AutoGen (`work_dir` dla kodu). **Siła dowodów: praktyczne.**  
**Trade-off:**  
- izolacja sesji/work_dir jest prosta i bezpieczna operacyjnie,  
- ale nie rozwiązuje sama z siebie konfliktów wokół trwałych, współdzielonych plików w repo.

**4) Kolizje równoczesnego zapisu do wspólnego repo są częściej adresowane przez workflow Git/CI niż przez agent framework.**  
Najbliższe standardowym mechanizmom są: CODEOWNERS, review gates, branch protection, osobne worktree/branch per zadanie, a dla plików binarnych — Git LFS locking. **Siła dowodów: praktyczne.**  
Źródła: [GitHub CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [Git worktree](https://git-scm.com/docs/git-worktree), [Git LFS locking](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-lock.adoc)

### C. Document ownership models

**1) Ownership na dużą skalę jest zwykle przypisywany do projektu/pakietu/ścieżki, a nie do pojedynczego pliku „ad hoc”.**  
GitHub CODEOWNERS mapuje ścieżki do właścicieli; GitLab pozwala wymuszać code-owner approvals; Nx Owners modeluje własność na poziomie projektów i tagów, a następnie kompiluje to do polityk repo. **Siła dowodów: praktyczne.**  
**Wniosek syntetyczny:** decyzja „ten katalog należy do tej roli” jest najczęściej narzędziowo implementowana jako reguła ścieżek lub metadanych projektu, nie jako nieformalna konwencja w README.  
Źródła: [GitHub – About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners), [GitLab – Code Owners / approvals](https://docs.gitlab.com/user/project/codeowners/), [Nx Powerpack / Owners](https://nx.dev/blog/introducing-nx-powerpack)

**2) Enforcement jest skuteczne dopiero wtedy, gdy ownership łączy się z review i CI.**  
Samo istnienie pliku CODEOWNERS nie rozwiązuje problemu, jeśli review nie jest wymagane przez branch protection albo merge rules. GitHub i GitLab pozwalają wymuszać approvale właścicieli i blokować merge do czasu spełnienia reguł. Nx Conformance/Owners idzie dalej, sprawdzając polityki jako część narzędziowego governance. **Siła dowodów: praktyczne.**  
Źródła: [GitHub branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches), [GitLab merge request approvals](https://docs.gitlab.com/user/project/merge_requests/approvals/), [Nx Conformance](https://nx.dev/docs/enterprise/conformance)

**3) Shared documents i cross-team artifacts wymagają jawnego modelu „shared/core”.**  
Źródła praktyczne pokazują, że zamiast próbować przypisać wszystko do jednej roli, dojrzałe repo mają obszary współdzielone z wyższym poziomem kontroli: wspólne pakiety, `visibility`/`package_group`, staging/publishing pipelines, albo wielu właścicieli. Kubernetes jest tu czytelnym przykładem: staging w monorepo synchronizowany do downstream repo przez publishing-bot. **Siła dowodów: praktyczne.**  
**Trade-off:**  
- obszary współdzielone zwiększają reuse,  
- ale wymagają ostrzejszego governance i często bardziej kosztownego review.  
Źródła: [Bazel visibility](https://bazel.build/concepts/visibility), [Kubernetes staging](https://github.com/kubernetes/kubernetes/tree/master/staging)

**4) Struktura ownership w dużych wspólnotach kodu bywa hybrydowa.**  
Badanie 20 projektów OSS wskazuje, że hierarchia organizacyjna i role współwystępują z bardziej elastycznymi, hybrydowymi strukturami. To wspiera tezę, że czysty model „każdy katalog ma jednego właściciela” często nie wytrzymuje rzeczywistej złożoności. **Siła dowodów: empiryczne.**  
Źródło: [Hybrid Organizational Structure for OSS Communities](https://arxiv.org/abs/2407.09498)

### D. Naming conventions at scale

**1) Najsilniej potwierdzony wzorzec to namespace w strukturze, a nie „sprytne nazwy pojedynczych plików”.**  
npm scopes pokazują, że namespace w nazwie pakietu rozwiązuje kolizje i jasno komunikuje przynależność. W monorepo analogicznie działają nazwy projektów, package names, source roots i tagi domenowe. **Siła dowodów: praktyczne.**  
Źródła: [npm scope](https://docs.npmjs.com/cli/v10/using-npm/scope), [Pants monorepo guide](https://www.pantsbuild.org/blog/2022/03/15/effective-monorepos-with-pants), [Nx docs](https://nx.dev/docs)

**2) Przy 100+ plikach tego samego typu lepiej skaluje hierarchia + stabilny identyfikator projektu niż długie prefiksy w każdej nazwie pliku.**  
To nie jest wprost sformalizowane przez jedno źródło, ale wynika spójnie z praktyk workspaces/packages/projects w Nx/Turbo/Bazel/Pants. **Siła dowodów: spekulacja oparta na wielu źródłach praktycznych.**  
**Alternatywy i trade-offy:**  
- **Prefix per rola** pomaga w płaskich katalogach, ale źle skaluje się przy plikach współdzielonych i zmianie odpowiedzialności.  
- **Hierarchical path + krótka nazwa pliku** lepiej redukuje kolizje i poprawia discoverability.  
- **Data w nazwie** jest użyteczna dla raportów/dumpów/artefaktów sesyjnych, ale zwykle szkodzi stabilnym dokumentom referencyjnym i modułom.

**3) Ogólne best practices dla nazw plików są dobrze udokumentowane, ale nie są to bezpośrednie badania monorepo.**  
Źródła z bibliotek i data management konsekwentnie zalecają: spójność, przewidywalność, brak spacji i znaków specjalnych, nazwy machine-readable, sensowne daty/versioning tylko gdy faktycznie niosą informację. **Siła dowodów: praktyczne (adjacent evidence).**  
Źródła: [Stanford file naming best practices](https://library.stanford.edu/data-management-services/data-best-practices/best-practices-file-naming), [CESSDA file naming convention](https://www.cessda.eu/Training/Training-Resources/Library/Data-Management-Expert-Guide/3.-Process/3.4.-File-name-conventions)

**4) Nie udało się potwierdzić mocnych, aktualnych badań porównawczych typu „kebab-case vs snake_case”, „flat vs hierarchical” albo „z datą vs bez” specyficznie dla dużych monorepo i efektywności zespołów.**  
Znalezione materiały są głównie normatywne (guidelines), a nie ewaluacyjne. **Siła dowodów: brak bezpośredniego potwierdzenia — wynik negatywny.**

### E. Temporary vs persistent artifacts

**1) Dojrzałe repo oddzielają źródła kanoniczne od cache/scratch/build outputs.**  
Turborepo jawnie definiuje `outputs` z możliwością wykluczania cache subdirs; Git jasno rozróżnia ignorowane pliki (`gitignore`) od wersjonowanych źródeł. **Siła dowodów: praktyczne.**  
Źródła: [Turborepo configuration / outputs](https://turborepo.dev/docs/reference/configuration), [gitignore](https://git-scm.com/docs/gitignore)

**2) Cleanup jest zwykle realizowany przez polityki narzędziowe, nie przez ręczne porządki w repo.**  
Przykłady: `git clean -X` dla usuwania tylko ignorowanych plików, cache retention/LRU po stronie build tools, `retention-days` dla artefaktów GitHub Actions. **Siła dowodów: praktyczne.**  
Źródła: [git clean](https://git-scm.com/docs/git-clean), [GitHub Actions artifact retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository), [Nx local cache](https://nx.dev/docs/reference/nx-cloud/config)

**3) W praktyce są trzy różne klasy artefaktów i warto je konceptualnie rozdzielać.**  
- **Persistent / canonical** — kod źródłowy, trwała dokumentacja, definicje interfejsów, konfiguracje projektu.  
- **Build/cache** — kompilaty, cache tasków, vendorized/generated outputs możliwe do odtworzenia.  
- **Scratch/session/intermediate** — eksperymenty, debug files, drafty, logi sesji agentów, tymczasowe raporty.  
To jest synteza z praktyk Git/Turbo/Nx i frameworków agentowych. **Siła dowodów: spekulacja oparta na wielu źródłach praktycznych.**

**4) Frameworki agentowe zwykle trzymają intermediate outputs w sesjach/workspace’ach, a nie w „kanonicznym” drzewie repo.**  
ChatDev zapisuje artefakty i kontekst w katalogu sesji, MetaGPT tworzy `workspace`, AutoGen używa `work_dir`, a Deep Agents może podmieniać backend filesystemu. **Siła dowodów: praktyczne.**  
**Wniosek syntetyczny:** w ekosystemie agentowym najbardziej naturalny jest podział `repo canonical` vs `agent workspace/session store`.  
Źródła: [ChatDev memory docs](https://github.com/OpenBMB/ChatDev/blob/main/docs/user_guide/en/modules/memory.md), [MetaGPT repo](https://github.com/FoundationAgents/MetaGPT), [AutoGen code executors](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/components/command-line-code-executors.html), [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)

## Otwarte pytania / luki w wiedzy

- **Nie udało się potwierdzić** istnienia szeroko przyjętego, dojrzałego standardu organizacji katalogów *specyficznie* dla projektów multi-agent AI, porównywalnego z dojrzałością Nx/Bazel/Turbo/Pants.
- **Nie udało się potwierdzić** mocnych badań porównawczych oceniających skuteczność naming conventions typu `kebab-case` vs `snake_case`, `flat` vs `hierarchical`, `z datą` vs `bez daty` w dużych monorepo.
- Frameworki agentowe są mocne w orkiestracji ról, pamięci i sesji, ale słabiej opisują governance współdzielonych plików w jednym repo; ten obszar wygląda na praktykę emergentną, nie ustalony standard.
- Źródła monorepo są bardzo silne dla kodu, buildów i ownership, ale słabsze dla dokumentów i promptów jako first-class citizens; część wniosków dla dokumentów to ekstrapolacja z governance kodu.
- Własność współdzielonych artefaktów (`shared`, `core`, `staging`) jest dobrze obsłużona przez visibility/review, ale mniej przez proste reguły „jedna rola = jeden katalog”; tu częściej pojawia się model hybrydowy.
- Dane o cleanup/retention są dobrze opisane dla CI artifacts i cache, ale słabiej dla długowiecznych artefaktów sesji agentów przechowywanych lokalnie lub poza repo.

## Źródła / odniesienia

- [Nx – Crafting Your Workspace](https://nx.dev/docs/getting-started/tutorials/crafting-your-workspace) — oficjalny opis struktury workspace, auto-discovery projektów, relacji z package manager workspaces.
- [Nx – Enforce Module Boundaries](https://nx.dev/docs/technologies/eslint/eslint-plugin/guides/enforce-module-boundaries) — oficjalny mechanizm egzekwowania granic zależności.
- [Nx vs Turborepo](https://nx.dev/docs/guides/adopting-nx/why-nx#nx-vs-turborepo) — porównanie użyte do potwierdzenia problemu architectural drift i roli tags/conformance.
- [Nx Powerpack / Owners](https://nx.dev/blog/introducing-nx-powerpack) — materiał o owners/conformance jako governance w monorepo.
- [Turborepo – Structuring a repository](https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository) — oficjalny wzorzec `apps/` + `packages/`.
- [Turborepo – Configuration](https://turborepo.dev/docs/reference/configuration) — źródło dla `outputs`, `boundaries`, concurrency i reguł tasków.
- [Yarn – Workspaces](https://yarnpkg.com/features/workspaces) — oficjalne źródło dla workspace constraints.
- [Bazel – Repositories, workspaces, packages, and targets](https://bazel.build/concepts/build-ref) — oficjalne pojęcia pakietów i `BUILD` jako jednostek struktury.
- [Bazel – Visibility](https://bazel.build/concepts/visibility) — oficjalny mechanizm ograniczania zależności i dostępu między pakietami/targetami.
- [Pants – Effective monorepos with Pants](https://www.pantsbuild.org/blog/2022/03/15/effective-monorepos-with-pants) — praktyka monorepo przy skali, dependency inference, selective execution.
- [Why Google Stores Billions of Lines of Code in a Single Repository](https://research.google/pubs/pub45424/) — klasyczne źródło empiryczne o monorepo na ogromną skalę i trade-offach.
- [Uber Engineering – Building Uber with Monorepo](https://www.uber.com/en-PL/blog/building-uber-with-monorepo/) — case study skali, commit volume i blast radius.
- [GitHub Docs – About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) — definicja i ograniczenia CODEOWNERS, użyte do ownership enforcement.
- [GitHub Docs – Managing protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches) — wymagane review/status checks dla egzekwowania governance.
- [GitLab – Code Owners](https://docs.gitlab.com/user/project/codeowners/) — code owner approvals w merge requestach.
- [GitLab – Merge request approvals](https://docs.gitlab.com/user/project/merge_requests/approvals/) — merge gates i approval rules.
- [gitignore](https://git-scm.com/docs/gitignore) — oficjalne rozróżnienie plików ignorowanych od wersjonowanych.
- [git clean](https://git-scm.com/docs/git-clean) — cleanup tylko ignorowanych plików, użyte dla cleanup patterns.
- [git worktree](https://git-scm.com/docs/git-worktree) — izolacja pracy przez osobne worktrees.
- [Git LFS lock](https://github.com/git-lfs/git-lfs/blob/main/docs/man/git-lfs-lock.adoc) — file locking dla kolizyjnych assetów binarnych.
- [GitHub Actions artifact retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) — polityki retencji artefaktów CI.
- [LangGraph – Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) — `thread_id` i checkpointy per krok jako wzorzec izolacji stanu.
- [LangChain – Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) — filesystem backends, subagents i context isolation.
- [AutoGen – Command Line Code Executors](https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/components/command-line-code-executors.html) — `work_dir` i zapis kodu do plików przed wykonaniem.
- [CrewAI Documentation](https://docs.crewai.com) — struktura scaffoldingu projektu, knowledge folder, shared/private memory scopes.
- [ChatDev – Memory module docs](https://github.com/OpenBMB/ChatDev/blob/main/docs/user_guide/en/modules/memory.md) — session folders, `WareHouse`, kontekst sesji.
- [MetaGPT repository](https://github.com/FoundationAgents/MetaGPT) — `workspace`/`ProjectRepo` i organizacja artefaktów projektu.
- [Kubernetes – staging](https://github.com/kubernetes/kubernetes/tree/master/staging) — przykład shared/staging artifacts synchronizowanych do osobnych repo.
- [Hybrid Organizational Structure for OSS Communities](https://arxiv.org/abs/2407.09498) — empiryczne wsparcie dla hybrydowej struktury ownership/governance.
- [npm package scope](https://docs.npmjs.com/cli/v10/using-npm/scope) — namespacing pakietów jako mechanizm redukcji kolizji.
- [Stanford – Best practices for file naming](https://library.stanford.edu/data-management-services/data-best-practices/best-practices-file-naming) — adjacent evidence dla spójnego, machine-readable naming.
- [CESSDA – File name conventions](https://www.cessda.eu/Training/Training-Resources/Library/Data-Management-Expert-Guide/3.-Process/3.4.-File-name-conventions) — dodatkowe praktyczne zasady nazewnictwa plików.
