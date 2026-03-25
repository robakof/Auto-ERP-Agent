# Research: Prompt engineering dla spójnej identyfikacji wizualnej — mapowanie obszarów wiedzy

Data: 2026-03-25

Legenda siły dowodów:
- **empiryczne** — peer-reviewed paper, benchmark, badanie z ewaluacją
- **praktyczne** — oficjalna dokumentacja, cookbook, działające repo, oficjalne zasady platform
- **spekulacja** — inferencja, hipoteza, rekomendacja nieprzetestowana lub słabo sformalizowana

## TL;DR — 7 najważniejszych kierunków

1. **Anatomia skutecznego promptu wizualnego jest względnie ustalona, ale składnia i mechanizmy kontroli silnie zależą od rodziny modelu.** W modelach API-first rośnie znaczenie jasnych opisów i jawnych inwariantów; w Midjourney i części open-source nadal ważne są parametry, wagi i referencje stylu; w diffusion/open-weight mocniejsze pozostają negative prompts, weighting i workflow control. **Siła dowodów: praktyczne**

2. **Spójność stylu między generacjami dziś najczęściej utrzymuje się nie jednym trikiem, tylko pakietem kontroli: referencje stylu/obrazu, jawne inwarianty, kontrola edycji, czasem personalizacja lub fine-tuning.** Sam seed bywa przydatny do eksperymentów, ale oficjalne źródła nie pokazują go jako głównego narzędzia trwałej spójności. **Siła dowodów: praktyczne**

3. **Dla brand identity rynek enterprise przesuwa się od „promptów” do „systemów sterowania marką”: style kits, custom models, DAM, governance, approvals, provenance.** To już istnieje komercyjnie, ale niezależna literatura naukowa opisująca skuteczność takich systemów jest skromna. **Siła dowodów: praktyczne + spekulacja**

4. **Zdjęcia produktowe to obszar najbardziej dojrzały proceduralnie, ale niekoniecznie najbardziej „promptowalny” czysto z tekstu.** Standardy marketplace’ów są sztywne (białe tło, wypełnienie kadru, wierna reprezentacja), więc przy dużej skali lepiej wyglądają workflow oparte o reference images, editing, recontext i batch templates niż „czyste” text-to-image od zera. **Siła dowodów: praktyczne + spekulacja**

5. **Największa luka badawcza i operacyjna: brak jednego uznanego frameworku do mierzenia „brand consistency” oraz regresji promptów po zmianie modelu.** Istnieją metryki jakości i alignmentu (CLIPScore, TIFA, PickScore, ImageReward, benchmarki identity/style), ale nie ma wspólnego standardu odpowiadającego wprost na pytanie: „czy nowa generacja nadal jest zgodna z brand bookiem?”. **Siła dowodów: empiryczne + praktyczne**

6. **Landscape narzędzi 2025–2026 jest bardzo ruchomy: modele i endpointy zmieniają się szybciej niż trwałe wzorce pracy.** Najbardziej stabilne poznawczo są nie nazwy modeli, lecz kategorie: closed/managed, open/open-weight, wyspecjalizowane produktowo, workflow/node-based, DAM/governance oraz post-processing/QA. **Siła dowodów: praktyczne**

7. **Kompetencje agenta Art Director leżą na styku pięciu domen: visual prompting, design fundamentals, brand governance, pipeline/asset operations oraz QA/evaluation.** Dwie pierwsze są dobrze opisane; trzy ostatnie są szybciej zmienne i słabiej sformalizowane. **Siła dowodów: synteza z wielu źródeł, praktyczne + empiryczne**

---

## Wyniki per obszar badawczy

## A. Fundamenty prompt engineeringu wizualnego

### A1. Jak zbudowany jest skuteczny prompt do generowania obrazów?

**Wprost ze źródeł**
- [OpenAI: Gpt-image-1.5 Prompting Guide](https://cookbook.openai.com/examples/generate_images_with_gpt_image) zaleca opisywać kadr, punkt widzenia, oświetlenie, zachowanie literalnego tekstu, ograniczenia typu „nie zmieniaj układu”, a przy kolejnych iteracjach powtarzać inwarianty i zmieniać mało naraz. **Siła dowodów: praktyczne**
- [Google Vertex AI / Imagen prompt guide](https://cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide) pokazuje podobną anatomię promptu, ale zachęca do prostego języka naturalnego, iteracyjnego doprecyzania i używania słów opisujących fotografię, obiektyw, styl i scenę. **Siła dowodów: praktyczne**
- [Stability AI SD3.5 prompt guide](https://platform.stability.ai/docs/generate/sd3-5) również rozbija prompt na subject, composition/framing, lighting/color, technical parameters i literal text. **Siła dowodów: praktyczne**
- [Midjourney docs](https://docs.midjourney.com/hc/en-us/articles/32859204029709-Parameter-List) formalizują sporą część sterowania przez parametry (`--stylize`, `--sref`, `--seed`, `--raw`, proporcje, warianty), a nie wyłącznie sam tekst opisu. **Siła dowodów: praktyczne**

**Synteza**
- **Względnie stabilny „szkielet” promptu** to: **subject / action-context / composition / camera / lighting / style / mood / explicit constraints / text / references**. To powtarza się w dokumentacji OpenAI, Google i Stability, mimo różnic produktowych. **Siła dowodów: praktyczne**
- **Największa różnica nie dotyczy tego „co opisać”, tylko „jak sterować”.**
  - **API-first / multimodal**: lepiej działają pełne, semantyczne opisy i jawne inwarianty.
  - **Midjourney**: większą rolę mają parametry, referencje stylu, personalizacja i prompt permutations.
  - **Diffusion / open-weight**: większa rola negative prompts, weighting, LoRA, node workflows.
  **Siła dowodów: praktyczne**
- **Kolejność elementów ma znaczenie mniejsze niż kompletność constraintów i zgodność z natywnym interfejsem modelu.** W nowszych modelach wysoka prompt adherence częściowo zmniejsza potrzebę „hacków składniowych”, ale ich nie eliminuje w całym ekosystemie. **Siła dowodów: praktyczne + spekulacja**

### A2. Negative prompts — kiedy i jak stosować

**Wprost ze źródeł**
- [Imagen prompt guide](https://cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide) ma osobną sekcję negative prompts; rekomenduje opisywanie niechcianych elementów wprost, ale bez nadmiaru instrukcji typu „don’t / no” w zwykłym tekście promptu. **Siła dowodów: praktyczne**
- [Stability SD3.5 guide](https://platform.stability.ai/docs/generate/sd3-5) i [Stability Seconds prompt weighting](https://platform.stability.ai/docs/feature-guides/prompt-weighting) traktują negative prompting i weighting jako podstawowe narzędzia korekty wyniku. **Siła dowodów: praktyczne**
- [Hugging Face Diffusers](https://huggingface.co/docs/diffusers/main/en/using-diffusers/weighted_prompts) pokazuje weighting i negative prompt embeddings jako standard workflow w diffusion pipelines. **Siła dowodów: praktyczne**

**Synteza**
- **Negative prompts są najbardziej „natywne” w rodzinie diffusion/open-source oraz w systemach explicite wspierających osobne pole negative prompt.** **Siła dowodów: praktyczne**
- **W systemach typu GPT-image większe znaczenie ma zamiana negacji na pozytywnie sformułowane constraints i inwarianty** („zachowaj produkt bez zmian”, „bez watermarków”, „nie zmieniaj kompozycji”), a nie osobna „lista zakazów”. **Siła dowodów: praktyczne**
- **Trade-off:** negative prompts pomagają usuwać artefakty i zawężać wynik, ale mogą zwiększać kruchość promptu i utrudniać przenoszenie workflow między modelami. **Siła dowodów: praktyczne + spekulacja**

### A3. Techniki utrzymywania spójności stylu między generacjami

**Wprost ze źródeł**
- [Midjourney Style Reference](https://docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference) służy do utrzymywania ogólnego stylu (kolor, medium, tekstury, lighting), a [Character Reference](https://docs.midjourney.com/hc/en-us/articles/32099348346765-Character-Reference) do spójności postaci. **Siła dowodów: praktyczne**
- [Midjourney Seeds](https://docs.midjourney.com/hc/en-us/articles/32819538148365-Seeds) wprost zaznaczają, że seed jest dobry do testowania zmian promptu, ale nie jest najlepszym narzędziem do zachowywania stylu/postaci na dłuższą metę; do tego lepsze są referencje i personalizacja. **Siła dowodów: praktyczne**
- [OpenAI prompting guide](https://cookbook.openai.com/examples/generate_images_with_gpt_image) pokazuje utrzymywanie spójności przez powtarzanie cech postaci/obiektu i explicit invariants („Do not redesign the character”). **Siła dowodów: praktyczne**
- [Adobe Style Kits](https://www.adobe.com/products/firefly/features/style-kits.html) i [Firefly Custom Models](https://www.adobe.com/products/firefly/enterprise/custom-models.html) komercjalizują spójność stylu jako współdzielony zasób lub model trenowany na własnych assetach. **Siła dowodów: praktyczne**
- [FLUX.2 image editing](https://docs.bfl.ai/api-reference/flux-kontext) wspiera multi-reference editing, a [FLUX.2 text-to-image](https://docs.bfl.ai/api-reference/flux) deklaruje sterowanie kolorami także przez wartości hex, co jest szczególnie ciekawe dla compliance brandowego. **Siła dowodów: praktyczne**

**Synteza**
- **Najsilniejsze praktyczne wzorce spójności to dziś:**
  1. reference-based control (styl, postać, produkt, layout),
  2. jawne inwarianty promptowe,
  3. edycja istniejącego obrazu zamiast generacji od zera,
  4. personalizacja lub custom model przy dużym reuse.
  **Siła dowodów: praktyczne**
- **Fine-tuning (LoRA, DreamBooth, textual inversion, custom models)** ma sens, gdy styl/produkt/postać mają wracać wielokrotnie i koszt „ręcznego pilnowania” promptem staje się większy niż koszt utrzymania modelu. **Siła dowodów: praktyczne + spekulacja**
- **Overkill**: przy jednorazowych kampaniach, krótkich seriach lub tam, gdzie wystarcza referencja + edycja, fine-tuning może być cięższy organizacyjnie niż korzyść jakościowa. **Siła dowodów: spekulacja**

### A4. Ograniczenia i pułapki

**Wprost ze źródeł**
- Oficjalne przewodniki OpenAI, Google i Stability mocno akcentują iterację, co pośrednio potwierdza, że wynik nie jest deterministyczny ani idealnie stabilny między próbami. **Siła dowodów: praktyczne**
- [Qwen-Image](https://github.com/QwenLM/Qwen-Image) i [Seedream 4.5](https://www.volcengine.com/docs/85128/1813145) mocno promują text rendering i editing consistency, ale to w dużej mierze twierdzenia dostawców; niezależne benchmarki porównawcze są rzadsze. **Siła dowodów: praktyczne**
- Badania nad style consistency, identity preservation i compositional alignment rosną, ale nadal są to osobne benchmarki i metryki, a nie zamknięty standard produkcyjny. Przykłady: [Only-Style](https://arxiv.org/abs/2503.22251), [DSH-Bench / SICS](https://arxiv.org/abs/2508.14652), [VLM-based identity preservation evaluation](https://arxiv.org/abs/2504.18283). **Siła dowodów: empiryczne**

**Synteza**
- **Prompt drift** jest realnym problemem workflow, zwłaszcza przy wielu iteracjach, przejściach między modelami i „łataniu” promptu kolejnymi wyjątkami. **Siła dowodów: praktyczne + empiryczne**
- **Najbardziej uporczywe błędy pozostają zbliżone w całej branży:** tekst w obrazach, drobna geometria/anatomia, lokalna fizyka, niekontrolowana stylizacja, nadmierna „upiększająca” homogenizacja. **Siła dowodów: praktyczne + empiryczne**
- **Model-specific biases** nadal są ważne, ale źródła oficjalne zwykle opisują je pośrednio (przez funkcje i ograniczenia), nie jako formalną listę biasów. To pozostaje obszarem słabiej jawnie udokumentowanym. **Siła dowodów: praktyczne + luka**

---

## B. Brand identity w kontekście generatywnym

### B1. Jak definiować i utrzymywać visual brand guidelines dla AI?

**Wprost ze źródeł**
- [Adobe Style Kits](https://www.adobe.com/products/firefly/features/style-kits.html) pozwalają budować udostępniane szablony stylu do generowania wariantów w ramach jednego estetycznego systemu. **Siła dowodów: praktyczne**
- [Adobe Firefly Custom Models](https://www.adobe.com/products/firefly/enterprise/custom-models.html) i [Firefly Foundry](https://business.adobe.com/products/firefly/enterprise.html) opisują model trenowany na własnych assetach jako sposób na utrzymanie zgodności z marką i IP. **Siła dowodów: praktyczne**
- [Frontify: DAM + governance guide](https://www.frontify.com/en/guides/the-governance-driven-dam) argumentuje, że DAM ma nie tylko przechowywać assety, ale egzekwować standardy marki i governance. **Siła dowodów: praktyczne**

**Synteza**
- **Tradycyjny brand book w generatywnym AI przestaje wystarczać jako PDF do czytania; musi być tłumaczony na zestaw egzekwowalnych sterowników.** Praktycznie oznacza to: referencje stylu, wzorce promptów, dopuszczalne palety, constraints, approved assets, custom models, workflow approvals i provenance. **Siła dowodów: praktyczne + spekulacja**
- **Color palette enforcement** jest dziś częściowo osiągalne promptem, ale lepiej działa, gdy model lub workflow wspiera jawne sterowanie kolorem (np. [FLUX.2 hex-code steering](https://docs.bfl.ai/api-reference/flux)) albo gdy człowiek/QA sprawdza odchylenie od brand palette po generacji. **Siła dowodów: praktyczne + spekulacja**
- **Moodboard → prompt translation** nie ma jednego standardu. W praktyce rynek korzysta z referencji obrazowych, inspiration boards i template prompts; badania HCI pokazują, że strukturyzowane interfejsy z panelami „branding / audience / inspiration” pomagają projektantom wydobywać wymagania marki. Zob. [ACAI](https://arxiv.org/abs/2502.12344). **Siła dowodów: empiryczne + praktyczne**

### B2. Firmy/projekty, które wdrożyły spójną identyfikację z AI na skalę

**Wprost ze źródeł**
- [Newell Brands x Adobe](https://business.adobe.com/customer-success-stories/newell-brands-case-study.html): Adobe opisuje użycie custom models i governance do generowania brand-aligned materiałów dla marek takich jak Paper Mate i Elmer’s. **Siła dowodów: praktyczne**
- [Versuni x Adobe](https://business.adobe.com/customer-success-stories/versuni-case-study.html): deklarowane 63% skrócenia time-to-market produktów, 60% oszczędności kosztów creative/photoshoot i 50% szybsze pozyskiwanie obrazów. **Siła dowodów: praktyczne**
- [Currys x Adobe](https://business.adobe.com/customer-success-stories/currys-case-study.html): case opisuje przyspieszenie konceptowania kampanii przy zachowaniu kontroli nad marką. **Siła dowodów: praktyczne**
- [Frontify + SCENAR.IO](https://www.frontify.com/en/blog/elastic-branding-with-frontify-and-scenar-io) pozycjonują AI jako narzędzie do szybkiego tworzenia on-brand visuals z pojedynczego reference image. **Siła dowodów: praktyczne**

**Synteza**
- **Case studies istnieją i są już „enterprise-grade”, ale prawie zawsze pochodzą od vendorów wdrożeniowych.** To oznacza, że są cenne jako dowód istnienia wzorca rynkowego, ale słabsze jako niezależny dowód porównawczej skuteczności. **Siła dowodów: praktyczne**
- **Najsilniej udokumentowany wzorzec wdrożeniowy** nie jest „promptujemy lepiej”, tylko „łączymy generację z systemem brand assetów, approvals i reuse”. **Siła dowodów: praktyczne**

### B3. QA generowanych materiałów

**Wprost ze źródeł**
- [Survey on quality metrics for text-to-image generation](https://arxiv.org/abs/2503.18198) pokazuje, że klasyczne metryki rekonstrukcyjne (SSIM, PSNR) są niewystarczające dla T2I; potrzebne są metryki alignmentu i jakości kompozycyjnej. **Siła dowodów: empiryczne**
- Badania i benchmarki wskazują na rolę metryk takich jak **CLIPScore, TIFA, VQA Score, PickScore, ImageReward**, ale z różną przydatnością zależnie od zadania; np. [Metrics for compositional T2I: a systematic evaluation](https://arxiv.org/abs/2504.17814) oraz benchmarki typu [Generate Any Scene](https://arxiv.org/abs/2505.19579). **Siła dowodów: empiryczne**
- [NTIRE 2025 Generated Image QA Challenge](https://arxiv.org/abs/2504.11677) przesuwa nacisk na fine-grained alignment i structural fidelity. **Siła dowodów: empiryczne**
- [NIST GenAI Image 2025](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Resources/GenAI_Image) pokazuje, że ocena obrazów generatywnych jest traktowana jako osobny program ewaluacyjny. **Siła dowodów: praktyczne**

**Synteza**
- **Nie ma jednej metryki jakości „dla marki”.** Dostępny stan wiedzy to raczej **stack ewaluacyjny**: alignment prompt–obraz, jakość percepcyjna, identity/style consistency, kontrola tekstu, zgodność z paletą/układem oraz human review. **Siła dowodów: empiryczne + praktyczne**
- **Human-in-the-loop pozostaje standardem w wątkach brandowych i reklamowych**, bo obecne metryki dobrze mierzą fragmenty jakości, ale słabo chwytają „czy to nadal brzmi jak nasza marka?”. **Siła dowodów: empiryczne + praktyczne**
- **A/B testing** jest bardziej dojrzały jako praktyka marketingowa niż jako specjalny „AI-native” framework; w źródłach dla generatywnego designu częściej pojawia się jako domyślna praktyka growth/creative teams niż jako odrębny standard naukowy. **Siła dowodów: praktyczne + luka**

---

## C. Zdjęcia produktowe — specifics

### C1. Przyjęte standardy zdjęć produktowych

**Wprost ze źródeł**
- [Amazon image requirements](https://sellercentral.amazon.com/help/hub/reference/G200309320) (main image): biały background, sam produkt, bez dodatkowego tekstu/watermarków, produkt powinien wypełniać większość kadru. **Siła dowodów: praktyczne**
- [Walmart image requirements](https://marketplace.walmart.com/guides/fulfillment-shipping/setting-up-your-items/spec-sheet-and-image-upload/) wymagają m.in. białego tła, formatu 1:1 i wysokiej rozdzielczości. **Siła dowodów: praktyczne**
- [eBay picture policy](https://www.ebay.com/help/policies/listing-policies/picture-policy?id=4370) oraz wytyczne dla obrazów produktowych akcentują ostrość, wierną reprezentację i prosty kadr. **Siła dowodów: praktyczne**
- [Shopify product photography guide](https://www.shopify.com/blog/product-photography) rekomenduje wiele ujęć, w tym close-upy i kąty prostolinijne. **Siła dowodów: praktyczne**
- [Etsy listing image recommendations](https://help.etsy.com/hc/en-us/articles/115015663107-How-to-Upload-and-Adjust-Listing-Images) podaje minimalne rozdzielczości i praktyki prezentacyjne. **Siła dowodów: praktyczne**

**Synteza**
- **Packshot / katalog / marketplace** to obszar o wysokiej dojrzałości standardów: neutralne tło, wysoka czytelność, wierna reprezentacja wariantu, powtarzalny kadr, brak dekoracyjnego chaosu. **Siła dowodów: praktyczne**
- **Lifestyle i in-context** są dużo bardziej elastyczne estetycznie, ale nadal muszą zachować rozpoznawalność produktu i nie przekroczyć granicy „misrepresentation”. **Siła dowodów: praktyczne + spekulacja**
- **Z perspektywy generatywnej** oznacza to, że zdjęcia produktowe są mniej polem dla „wolnej kreacji”, a bardziej dla kontrolowanego przetwarzania i standaryzacji. **Siła dowodów: praktyczne + spekulacja**

### C2. Jak generować spójne zdjęcia produktowe seryjnie?

**Wprost ze źródeł**
- [Google Product Recontext](https://cloud.google.com/vertex-ai/generative-ai/docs/image/product-recontext) wspiera edycję zdjęć produktów do nowych scenerii i tła, także z wieloma widokami tego samego produktu. **Siła dowodów: praktyczne**
- [Vertex AI Virtual Try-On](https://cloud.google.com/vertex-ai/generative-ai/docs/image/virtual-try-on) formalizuje osobny workflow dla branży odzieżowej. **Siła dowodów: praktyczne**
- [Midjourney Editor](https://docs.midjourney.com/hc/en-us/articles/32073762846733-Editor) oferuje vary region / remix / pan / zoom jako workflow edycyjny. **Siła dowodów: praktyczne**
- [FLUX.2 Image Editing](https://docs.bfl.ai/api-reference/flux-kontext) wspiera wieloobrazowe referencje i bardziej kontrolowane edit workflows. **Siła dowodów: praktyczne**

**Synteza**
- **Najbardziej obiecujący wzorzec seryjnego product imaging** to:
  1. template prompt z polami zmiennymi,
  2. reference image jako źródło prawdy o produkcie,
  3. editing/recontext zamiast generacji od zera,
  4. batch orchestration,
  5. QA pod kątem zgodności z listing rules.
  **Siła dowodów: praktyczne + spekulacja**
- **Inpainting / outpainting / img2img** są ważniejsze dla packshotów niż sama „poetyka promptu”, bo pozwalają zachować geometrię, etykietę i cechy SKU. **Siła dowodów: praktyczne**
- **Reference/control mechanisms** są krytyczne tam, gdzie warianty produktu różnią się subtelnie (kolor, tekstura, nadruk, etykieta, materiał). **Siła dowodów: praktyczne + spekulacja**

### C3. Granice realności i uncanny valley dla produktów

**Synteza**
- **AI-generated jest najbardziej wystarczające tam, gdzie liczy się scena, tło, atmosfera i ogólny marketingowy „look”, a mniej drobna prawda o powierzchni obiektu.** **Siła dowodów: spekulacja**
- **Najbardziej ryzykowne są produkty, gdzie zakup zależy od detalu materialnego:** wykończenie, połysk, transparentność, mikro-tekst, etykieta, skala, dopasowanie części, refleksy. **Siła dowodów: spekulacja**
- **Praktyczna granica realności** przebiega zwykle nie między „AI vs nie-AI”, tylko między:
  - generacją tła/sceny,
  - edycją istniejącego zdjęcia,
  - pełną syntezą produktu od zera.
  Im bliżej pełnej syntezy od zera, tym większe ryzyko błędu reprezentacyjnego. **Siła dowodów: praktyczne + spekulacja**

**Luka**
- Nie udało się potwierdzić jednego szeroko cytowanego, branżowego progu „uncanny valley dla packshotów” ani standardowego benchmarku „AI product realism acceptance”. To wygląda na obszar bardziej praktyczny niż sformalizowany naukowo. **Nie udało się potwierdzić.**

---

## D. Narzędzia i systemy — aktualny landscape (2025–2026)

### D1. Kategorie modeli generatywnych — aktualny stan

#### 1) Closed / managed / komercyjne
- [OpenAI image generation guide](https://platform.openai.com/docs/guides/image-generation) + [cookbook GPT-image-1.5](https://cookbook.openai.com/examples/generate_images_with_gpt_image): nacisk na controllable production workflows, wieloobrazowe wejścia, edycję konwersacyjną, identity preservation, literal text rendering. **Siła dowodów: praktyczne**
- [Google Vertex AI image generation](https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images) / [models](https://cloud.google.com/vertex-ai/generative-ai/docs/models): Imagen/Gemini image stack, product recontext, virtual try-on, provisioned throughput, Content Credentials. **Siła dowodów: praktyczne**
- [Adobe Firefly enterprise](https://business.adobe.com/products/firefly/enterprise.html): brand/IP-safe positioning, custom models, style kits, enterprise governance. **Siła dowodów: praktyczne**
- [Midjourney docs](https://docs.midjourney.com/): bardzo mocne narzędzia stylowe i art direction, ale słabsza pozycja jako klasycznie „API-first enterprise platform”. **Siła dowodów: praktyczne**

#### 2) Open-source / open-weight / self-hosted
- [Black Forest Labs FLUX.2](https://docs.bfl.ai/): rodzina od real-time do quality-first; część workflow wspiera open weights / LoRA / finetuning. **Siła dowodów: praktyczne**
- [Qwen-Image](https://github.com/QwenLM/Qwen-Image): 20B open model z mocnym naciskiem na text rendering i editing. **Siła dowodów: praktyczne**
- [Stability AI / Stable Image / SD3.5](https://platform.stability.ai/docs/getting-started): nadal ważna rodzina dla workflow, weighting i custom pipelines. **Siła dowodów: praktyczne**
- [ComfyUI](https://docs.comfy.org/) jako node-based open-source inference engine stał się warstwą orkiestracji, nie tylko pojedynczym narzędziem UI. **Siła dowodów: praktyczne**

#### 3) Wyspecjalizowane
- [Product Recontext](https://cloud.google.com/vertex-ai/generative-ai/docs/image/product-recontext), [Virtual Try-On](https://cloud.google.com/vertex-ai/generative-ai/docs/image/virtual-try-on) — silne specjalizacje produktowo-modowe. **Siła dowodów: praktyczne**
- [Adobe custom/brand models](https://www.adobe.com/products/firefly/enterprise/custom-models.html) — specjalizacja brandowa. **Siła dowodów: praktyczne**
- Część dostawców wyspecjalizowanych (moda, wnętrza, architektura) istnieje rynkowo, ale nie zawsze ma stabilną i przejrzystą dokumentację publiczną na poziomie porównywalnym z Big Tech / open-weight. **Siła dowodów: praktyczne + luka**

### D2. Porównanie podejść: jakość vs kontrola vs koszt vs customizacja

**Synteza**
- **Closed/managed**: najwyższa wygoda operacyjna, szybki start, często najlepsza użyteczność dla zespołów bez własnego ML stacku; trade-off to zależność od roadmapy dostawcy i zmienność endpointów/produktów. **Siła dowodów: praktyczne**
- **Open/open-weight**: najwyższa elastyczność, możliwość własnej kontroli, dostrajania i integracji z pipeline’em; trade-off to koszt operacyjny, MLOps i odpowiedzialność za ewaluację. **Siła dowodów: praktyczne**
- **Wyspecjalizowane produktowo/brandowo**: często najlepszy „fit” dla jednego use case’u, ale większe ryzyko lock-in i mniejszej przenaszalności kompetencji promptowych. **Siła dowodów: praktyczne + spekulacja**

### D3. Systemy do pracy na skalę

**Wprost ze źródeł**
- [ComfyUI docs](https://docs.comfy.org/) i [server routes / queue](https://docs.comfy.org/development/comfyui-server/comms_routes) pokazują dojrzały mechanizm workflow submission, queue i execution tracking. **Siła dowodów: praktyczne**
- [fal platform](https://fal.ai/models/fal-ai/flux-pro/v2.1) + [async queue docs](https://fal.ai/models/docs/concepts/queue): asynchroniczne kolejki, webhooks, retries, skalowanie inferencji. **Siła dowodów: praktyczne**
- [Replicate model versions](https://replicate.com/docs/topics/models/versions) i [How Replicate works](https://replicate.com/docs/reference/how-does-replicate-work) podkreślają versioning modeli jako warunek reprodukowalności. **Siła dowodów: praktyczne**
- [Frontify guide](https://www.frontify.com/en/guides/the-governance-driven-dam) i [Bynder State of DAM 2025](https://www.bynder.com/en/resources/state-of-dam-report-2025/) opisują DAM jako warstwę skalowania asset operations i governance. **Siła dowodów: praktyczne**

**Synteza**
- **Dwa dojrzałe wzorce skalowania to:**
  1. **workflow/node-based** (np. ComfyUI + modele + custom nodes) — większa kontrola i powtarzalność,
  2. **API-first inference platforms** (fal, Replicate, Vertex) — większa prostota wdrożenia i elastyczność ruchu.
  **Siła dowodów: praktyczne**
- **Brand management i DAM** nie zastępują generacji, ale stają się niezbędne przy większej skali, bo rozwiązują approved assets, reuse, governance, expiry, rights i odnajdywalność. **Siła dowodów: praktyczne**

### D4. Narzędzia wspomagające

**Wprost ze źródeł**
- [LangSmith prompt management](https://docs.langchain.com/langsmith/manage-prompts) i [programmatic management](https://docs.langchain.com/langsmith/manage-prompts-programmatically) formalizują prompt versioning, tagi, webhooki i centralne zarządzanie promptami. **Siła dowodów: praktyczne**
- [Replicate versions](https://replicate.com/docs/topics/models/versions) pokazuje znaczenie wersji modeli dla powtarzalności. **Siła dowodów: praktyczne**
- [Midjourney search/folders/manage creations](https://docs.midjourney.com/hc/en-us/articles/34523360642189-Organize-Your-Creations) wspiera organizację promptów, parametrów i referencji po stronie assetów. **Siła dowodów: praktyczne**

**Synteza**
- **Prompt management jako dyscyplina jest dojrzały po stronie tekstowej/LLM, ale w wizualach dopiero się „dopieszcza” o referencje obrazowe, parametry modeli, seed, asset lineage i QA outputs.** **Siła dowodów: praktyczne + spekulacja**
- **Version control dla assetów wizualnych** powinien obejmować nie tylko prompt, ale też model version, wejściowe referencje, workflow graph, post-processing i decyzję QA. **Siła dowodów: praktyczne + spekulacja**

### D5. Ekonomia skalowania

**Wprost ze źródeł**
- [OpenAI API pricing](https://openai.com/api/pricing/) rozlicza GPT-image-1.5 tokenowo dla input/output obrazowych i tekstowych. **Siła dowodów: praktyczne**
- [Google Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) rozlicza wiele image modeli per obraz (np. Imagen 4, Fast, Ultra, Product Recontext, Virtual Try-On). **Siła dowodów: praktyczne**
- [fal FLUX.2 pricing](https://fal.ai/models/fal-ai/flux-pro/v2.1) pokazuje rozliczanie per megapixel/output w modelu inference-as-a-service. **Siła dowodów: praktyczne**

**Synteza**
- **Nie istnieje jeden prosty „koszt za obraz” porównywalny między dostawcami** — zależy od modelu, rozdzielczości, liczby wejściowych obrazów, trybu edycji, throughput modelu i warstwy hostingowej. **Siła dowodów: praktyczne**
- **Przy 1000+ obrazów/mies.** ograniczeniem często przestaje być sama inferencja, a zaczynają być: przygotowanie referencji, kontrola wariantów, kolejki, ręczny QA, odrzuty oraz zmiany wersji modeli. **Siła dowodów: praktyczne + spekulacja**
- **API vs self-hosted vs managed** to głównie trade-off między prostotą i przewidywalnością ops a maksymalną customizacją i kontrolą kosztu jednostkowego. Brakuje jednego uniwersalnego zwycięzcy; zależy od wolumenu, stabilności use case’u i kompetencji operacyjnych. **Siła dowodów: praktyczne + spekulacja**

---

## E. Metodyki i frameworki

### E1. Czy istnieją uznane metodyki/systematyczne frameworki do promptingu wizualnego?

**Wprost ze źródeł**
- Dokumentacje OpenAI, Google, Stability i Midjourney dostarczają **praktycznych playbooków**, ale nie wspólnego międzybranżowego standardu. **Siła dowodów: praktyczne**
- Badania HCI, jak [GenTune](https://arxiv.org/abs/2502.12338) i [ACAI](https://arxiv.org/abs/2502.12344), próbują systematyzować proces projektowania promptów i externalizacji intencji wizualnej. **Siła dowodów: empiryczne**
- Badania jakości/metryk (np. [survey T2I metrics](https://arxiv.org/abs/2503.18198)) systematyzują ewaluację, ale nie tworzą jednego workflow operacyjnego dla brandingu. **Siła dowodów: empiryczne**

**Synteza**
- **Tak, istnieją metodyki cząstkowe; nie, nie istnieje dziś jeden uznany „visual prompting framework” dla spójnej identyfikacji brandowej.** **Siła dowodów: empiryczne + praktyczne**
- Najbardziej dojrzały wspólny schemat roboczy wygląda raczej jak: **brief → references/moodboard → prompt set → controlled tests → selection → edit/refine → batch → QA → approval → asset governance**. **Siła dowodów: praktyczne + empiryczne**
- **Emerging standards** bardziej dotyczą provenance i accessibility niż samego promptingu. [C2PA](https://c2pa.org/specifications/specifications/1.3/specs/C2PA_Specification.html) i [Content Credentials](https://contentcredentials.org/) dojrzewają jako warstwa pochodzenia treści. **Siła dowodów: praktyczne**

### E2. Workflow profesjonalnego AI art directora / vibe designera

**Synteza**
- Ze źródeł produktowych, case studies i badań HCI wyłania się dość spójny workflow:
  1. **Brief i constraints** (co wolno / czego nie wolno),
  2. **Moodboard / references / brand anchors**,
  3. **Eksploracja promptów**,
  4. **Refinement przez edit workflows**,
  5. **Batch generation z template’ów**,
  6. **QA i odrzuty**,
  7. **Approval, wersjonowanie, publikacja i governance**.
  **Siła dowodów: praktyczne + empiryczne**
- **Granica automatyzacji** dziś przebiega zwykle w miejscach o wysokiej semantycznej subtelności: brand fit, „czy to wygląda jak my”, zgodność z kampanią, ocena drobnych błędów produktu. Tam nadal dominuje człowiek. **Siła dowodów: empiryczne + praktyczne**
- **To, co można automatyzować skuteczniej**, to generacja wariantów, tła, recontext, techniczna walidacja formatu, podstawowe scoringi jakości i organizacja assetów. **Siła dowodów: praktyczne + spekulacja**

### E3. Dokumentacja i wersjonowanie visual prompt library

**Wprost ze źródeł**
- [LangSmith prompt management](https://docs.langchain.com/langsmith/manage-prompts) i podobne systemy pokazują dojrzałość w wersjonowaniu promptów, tagach i webhookach. **Siła dowodów: praktyczne**
- [Replicate versions](https://replicate.com/docs/topics/models/versions) podkreśla potrzebę spinania promptu z wersją modelu dla reprodukowalności. **Siła dowodów: praktyczne**
- [ComfyUI queue / workflows](https://docs.comfy.org/development/comfyui-server/comms_routes) pokazuje, że workflow graph może być pierwszorzędnym artefaktem, nie tylko prompt text. **Siła dowodów: praktyczne**

**Synteza**
- **Prompt library dla wizuali nie powinna być tylko bazą tekstów.** Powinna przechowywać co najmniej:
  - prompt template,
  - model/version,
  - parametry sterujące,
  - reference assets,
  - przykłady wejście/wyjście,
  - decyzję QA,
  - zastosowanie biznesowe,
  - datę i powód zmiany.
  **Siła dowodów: praktyczne + spekulacja**
- **Regression testing** jest dziś bardziej potrzebą niż standardem. Da się testować stare prompty na nowych modelach, ale brak wspólnego protokołu „pass/fail” dla stylu marki. **Siła dowodów: praktyczne + luka**

---

## F. Mapa wiedzy — meta-poziom

### F1. Które obszary są dobrze zbadane i mają ustalone wzorce?

#### Established
- **Fundamenty kompozycji, światła, koloru i fotografii produktowej** — starsze, stabilne, nie-AI-native zasady nadal obowiązują. **Siła dowodów: praktyczne**
- **Anatomia promptu i podstawowe praktyki controllable prompting** w głównych rodzinach modeli. **Siła dowodów: praktyczne**
- **Reference-based consistency** (style refs, image refs, edit-first workflows) jako główny wzorzec utrzymywania spójności. **Siła dowodów: praktyczne**
- **Marketplace rules dla packshotów** i techniczne standardy listing images. **Siła dowodów: praktyczne**
- **Need for prompt/model versioning** i reprodukowalność workflow. **Siła dowodów: praktyczne**

### F2. Które obszary są emerging?

#### Emerging
- **AI-native brand systems**: style kits, custom brand models, governance-first DAM. Rynek już jest, ale wiedza naukowa jest płytsza niż marketing vendorów. **Siła dowodów: praktyczne + luka**
- **Metryki spójności stylu i tożsamości** (identity preservation, style fidelity, compositional fidelity). **Siła dowodów: empiryczne**
- **Specjalizowane workflow produktowe** (recontext, try-on, controlled editing). **Siła dowodów: praktyczne**
- **Agentic/assisted design review** i narzędzia tłumaczące prompt na elementy obrazu (np. GenTune, Agentic-DRS). **Siła dowodów: empiryczne**
- **Provenance / Content Credentials / C2PA w pipeline’ach generatywnych.** **Siła dowodów: praktyczne**

### F3. Które to białe plamy?

#### White spots
- **Brak uznanego benchmarku „brand consistency”** łączącego styl, kolor, layout, ton marki i użyteczność biznesową. **Nie udało się potwierdzić.**
- **Brak powszechnego standardu regresji promptów wizualnych** po zmianie modelu lub wersji endpointu. **Nie udało się potwierdzić.**
- **Mało niezależnych, porównawczych case studies enterprise** pokazujących jakość, koszt i trwałość różnych strategii brand control. **Nie udało się potwierdzić.**
- **Słaba formalizacja granicy akceptowalności AI packshotów** w zależności od kategorii produktu i ryzyka reprezentacyjnego. **Nie udało się potwierdzić.**
- **Niewiele otwartych standardów accessibility specyficznych dla AI-generated images**; praktyka opiera się głównie na istniejących standardach WCAG/W3C. **Siła dowodów: praktyczne + luka**

### F4. Kompetencje, które powinien mieć agent Art Director

**Synteza**
To nie jest jeszcze rekomendacja architektury, tylko mapa kompetencji wynikająca z researchu:

1. **Visual prompting i multimodal control**
   - prompt anatomy
   - edit workflows
   - reference handling
   - model-specific syntax/control
   **Siła dowodów: praktyczne**

2. **Graphic design / art direction fundamentals**
   - kompozycja, światło, kolor, typografia, fotografia produktowa
   **Siła dowodów: praktyczne**

3. **Brand systems literacy**
   - rozumienie brand books, moodboardów, anchors, color enforcement, governance
   **Siła dowodów: praktyczne**

4. **Asset and pipeline operations**
   - batching, template variables, wersjonowanie, provenance, DAM, approvals
   **Siła dowodów: praktyczne**

5. **Evaluation / QA literacy**
   - metryki alignmentu
   - rozpoznawanie driftu
   - human review handoff
   - rozumienie ograniczeń benchmarków
   **Siła dowodów: empiryczne + praktyczne**

6. **Product representation awareness**
   - kiedy generacja od zera jest ryzykowna
   - kiedy lepsza jest edycja lub recontext
   **Siła dowodów: praktyczne + spekulacja**

---

## Mapa obszarów wiedzy

### Established
- Zasady kompozycji, oświetlenia, koloru, moodu i fotografii produktowej
- Prompt anatomy: subject / scene / composition / camera / lighting / style / constraints / text / references
- Reference-based consistency jako podstawowy mechanizm spójności
- Negative prompts / weighting w diffusion i open-source
- Packshot rules dla marketplace’ów
- Potrzeba wersjonowania promptów i modeli

### Emerging
- AI-native brand systems (style kits, custom models, DAM-governance)
- Metryki identity/style consistency
- Product recontext, virtual try-on i workflow produktowe
- Agentic design review i assisted prompt refinement
- Provenance / Content Credentials / C2PA w produkcyjnych pipeline’ach
- Prompt libraries rozszerzone o asset lineage i workflow graphs

### White spots
- Automatyczna, wiarygodna ocena zgodności z brand identity
- Standard regresji promptów wizualnych przy aktualizacjach modelu
- Niezależne benchmarki koszt–jakość–spójność dla wdrożeń enterprise
- Formalne kryteria „AI-realism acceptance” dla packshotów produktowych
- Uniwersalne, model-agnostyczne playbooki dla spójnej identyfikacji wizualnej na skali

---

## Otwarte pytania / luki w wiedzy

- **Nie udało się potwierdzić** jednego uznanego, przekrojowego frameworku do prompt engineeringu wizualnego dla brand consistency. Są playbooki vendorów, badania HCI i benchmarki cząstkowe, ale brak jednego standardu.
- **Nie udało się potwierdzić** branżowego benchmarku „brand consistency regression” po zmianie modelu lub endpointu.
- **Źródła rozjeżdżają się** co do realnej siły najnowszych modeli open-weight, bo część twierdzeń pochodzi głównie od dostawców (np. Qwen/Seedream) i ma słabszą niezależną triangulację niż dokumentacja Big Tech + peer-reviewed benchmarki.
- **Case studies enterprise** są obiecujące, ale często vendor-authored; trudno z nich wyciągać mocne wnioski porównawcze.
- **Accessibility dla AI-generated images** nie ma jeszcze wyraźnie wyodrębnionego, AI-specyficznego standardu; praktyka opiera się głównie na istniejących zasadach W3C/WCAG.
- **Specjalizowane workflow produktowe** szybko się zmieniają produktowo (migracje endpointów, nowe modele, deprecations), więc ich ocena ma krótszy termin ważności niż fundamenty projektowe.

---

## Źródła / odniesienia

### Oficjalna dokumentacja modeli i promptingu
- [OpenAI — Image generation guide](https://platform.openai.com/docs/guides/image-generation) — oficjalny opis API, edycji, workflow i aktualnego pozycjonowania produktu.
- [OpenAI Cookbook — Gpt-image-1.5 Prompting Guide](https://cookbook.openai.com/examples/generate_images_with_gpt_image) — najbardziej praktyczne źródło o anatomii promptu, inwariantach, stylu, tekstach i consistency.
- [Google Vertex AI — Imagen prompt guide](https://cloud.google.com/vertex-ai/generative-ai/docs/image/img-gen-prompt-guide) — oficjalne zasady promptingu, negative prompts i słownik fotograficzny.
- [Google Vertex AI — Generate images](https://cloud.google.com/vertex-ai/generative-ai/docs/image/generate-images) — oficjalny punkt wejścia do image generation na Vertex AI.
- [Google Vertex AI — Models](https://cloud.google.com/vertex-ai/generative-ai/docs/models) — aktualny krajobraz modeli obrazowych, wyspecjalizowanych i zarządzanych.
- [Google Vertex AI — Product Recontext](https://cloud.google.com/vertex-ai/generative-ai/docs/image/product-recontext) — oficjalny workflow dla przekształcania zdjęć produktów do nowych scenerii.
- [Google Vertex AI — Virtual Try-On](https://cloud.google.com/vertex-ai/generative-ai/docs/image/virtual-try-on) — oficjalny workflow dla mody i odzieży.
- [Stability AI — SD3.5 / prompt guide](https://platform.stability.ai/docs/generate/sd3-5) — oficjalna dokumentacja prompt anatomy i negative prompting.
- [Stability AI — Prompt weighting](https://platform.stability.ai/docs/feature-guides/prompt-weighting) — praktyczne użycie weighting i de-emphasis.
- [Hugging Face Diffusers — Weighted prompts](https://huggingface.co/docs/diffusers/main/en/using-diffusers/weighted_prompts) — dokumentacja ekosystemu diffusion, ważna dla open-source workflows.
- [Midjourney — Style Reference](https://docs.midjourney.com/hc/en-us/articles/32180011136653-Style-Reference) — oficjalny mechanizm spójności stylu.
- [Midjourney — Character Reference](https://docs.midjourney.com/hc/en-us/articles/32099348346765-Character-Reference) — oficjalny mechanizm spójności postaci.
- [Midjourney — Seeds](https://docs.midjourney.com/hc/en-us/articles/32819538148365-Seeds) — ograniczenia seeda i jego właściwe zastosowanie.
- [Midjourney — Multi Prompts & Weights](https://docs.midjourney.com/hc/en-us/articles/32023408776205-Multi-Prompts-Weights) — składnia wag i negacji.
- [Midjourney — Permutations](https://docs.midjourney.com/hc/en-us/articles/32568480625933-Permutations) — generowanie wariantów promptów.
- [Midjourney — Editor](https://docs.midjourney.com/hc/en-us/articles/32073762846733-Editor) — edycyjne workflow dla maintain/refine.
- [Black Forest Labs — FLUX API reference](https://docs.bfl.ai/api-reference/flux) — oficjalne możliwości rodziny FLUX, w tym sterowanie kolorem.
- [Black Forest Labs — FLUX image editing](https://docs.bfl.ai/api-reference/flux-kontext) — multi-reference i edycja obrazów.
- [Black Forest Labs — FLUX open weights / training](https://docs.bfl.ai/flux/model-overview) — informacje o wariantach, open weights i treningu/LoRA.
- [Qwen-Image GitHub](https://github.com/QwenLM/Qwen-Image) — oficjalne repo modelu open-weight.
- [ByteDance / Volcengine — Seedream 4.5](https://www.volcengine.com/docs/85128/1813145) — aktualny opis modelu i jego możliwości z perspektywy dostawcy.

### Brand, governance, DAM, enterprise cases
- [Adobe — Style Kits](https://www.adobe.com/products/firefly/features/style-kits.html) — AI-native mechanizm współdzielenia stylu.
- [Adobe — Firefly Custom Models](https://www.adobe.com/products/firefly/enterprise/custom-models.html) — custom brand models.
- [Adobe — Firefly Enterprise / Foundry](https://business.adobe.com/products/firefly/enterprise.html) — governance, IP, enterprise positioning.
- [Newell Brands x Adobe case study](https://business.adobe.com/customer-success-stories/newell-brands-case-study.html) — przykład skalowania spójnych treści brandowych z custom models.
- [Versuni x Adobe case study](https://business.adobe.com/customer-success-stories/versuni-case-study.html) — case z metrykami time-to-market i kosztów.
- [Currys x Adobe case study](https://business.adobe.com/customer-success-stories/currys-case-study.html) — case dotyczący kampanii i creative workflow.
- [Frontify — Governance-driven DAM](https://www.frontify.com/en/guides/the-governance-driven-dam) — rola DAM jako warstwy egzekwowania standardów marki.
- [Frontify + SCENAR.IO](https://www.frontify.com/en/blog/elastic-branding-with-frontify-and-scenar-io) — przykład AI zintegrowanego z brand management.
- [Bynder — State of DAM 2025](https://www.bynder.com/en/resources/state-of-dam-report-2025/) — raport vendorowy o AI w DAM i content ops.

### Zdjęcia produktowe i standardy marketplace
- [Amazon Seller Central — Image requirements](https://sellercentral.amazon.com/help/hub/reference/G200309320) — główne reguły dla main image i listingów.
- [Walmart Marketplace — Image upload requirements](https://marketplace.walmart.com/guides/fulfillment-shipping/setting-up-your-items/spec-sheet-and-image-upload/) — wymogi techniczne i tło.
- [eBay — Picture policy](https://www.ebay.com/help/policies/listing-policies/picture-policy?id=4370) — oficjalne zasady zdjęć w listingach.
- [Shopify — Product photography guide](https://www.shopify.com/blog/product-photography) — dobre praktyki e-commerce.
- [Etsy — Listing images help](https://help.etsy.com/hc/en-us/articles/115015663107-How-to-Upload-and-Adjust-Listing-Images) — rozdzielczość i praktyka listingowa.

### QA, benchmarki, badania
- [A Survey of Quality Metrics for Text-to-Image Generation](https://arxiv.org/abs/2503.18198) — szeroki przegląd metryk i ich ograniczeń.
- [Metrics for compositional text-to-image generation: a systematic evaluation](https://arxiv.org/abs/2504.17814) — porównanie metryk alignmentu i kompozycji.
- [Generate Any Scene](https://arxiv.org/abs/2505.19579) — benchmark i zestaw metryk dla kontroli sceny.
- [NTIRE 2025 Challenge on Fine-Grained Generated Image Quality Assessment](https://arxiv.org/abs/2504.11677) — przesunięcie w stronę fine-grained alignment i structural fidelity.
- [NIST — GenAI Image 2025](https://airc.nist.gov/AI_RMF_Knowledge_Base/AI_RMF/Resources/GenAI_Image) — program ewaluacji generowanych obrazów.
- [Only-Style: Style-Consistent Image Generation with Large Visual Models](https://arxiv.org/abs/2503.22251) — przykład badań nad style consistency.
- [Evaluating Identity-Preserving Image Generation with VLMs](https://arxiv.org/abs/2504.18283) — benchmark i ewaluacja identity preservation.
- [DSH-Bench: Subject Identity Consistency Score](https://arxiv.org/abs/2508.14652) — benchmark i metryka spójności tożsamości.
- [Agentic-DRS](https://arxiv.org/abs/2508.00462) — agentowa ewaluacja jakości graphic design.
- [GenTune](https://arxiv.org/abs/2502.12338) — badanie nad śledzeniem prompt labels i refinem designu.
- [ACAI](https://arxiv.org/abs/2502.12344) — strukturyzowany interfejs dla brand-aligned AI ad design.

### Provenance, accessibility, prompt/version ops
- [C2PA Specification](https://c2pa.org/specifications/specifications/1.3/specs/C2PA_Specification.html) — otwarty standard pochodzenia i zmian w treściach cyfrowych.
- [Content Credentials](https://contentcredentials.org/) — warstwa praktycznej adopcji provenance.
- [W3C Images Tutorial](https://www.w3.org/WAI/tutorials/images/) — aktualne podstawy accessibility dla obrazów.
- [W3C Understanding SC 1.4.5 Images of Text](https://www.w3.org/WAI/WCAG22/Understanding/images-of-text) — ważne dla ograniczania tekstu „zaszytego” w obrazie tam, gdzie powinien istnieć jako tekst.
- [ComfyUI documentation](https://docs.comfy.org/) — node-based workflow/inference engine i API/queue.
- [ComfyUI server routes](https://docs.comfy.org/development/comfyui-server/comms_routes) — techniczne podstawy workflow queue.
- [fal queue concepts](https://fal.ai/models/docs/concepts/queue) — skalowanie inferencji, kolejki, webhooki.
- [Replicate — model versions](https://replicate.com/docs/topics/models/versions) — wersjonowanie jako warunek reprodukowalności.
- [Replicate — how it works](https://replicate.com/docs/reference/how-does-replicate-work) — reprodukowalność i wersjonowanie.
- [LangSmith — manage prompts](https://docs.langchain.com/langsmith/manage-prompts) — prompt versioning i zarządzanie promptami.
- [LangSmith — manage prompts programmatically](https://docs.langchain.com/langsmith/manage-prompts-programmatically) — automatyzacja i workflow around prompt assets.

### Pricing / ekonomia (stan na 2026-03-25; wysoka zmienność)
- [OpenAI API Pricing](https://openai.com/api/pricing/) — aktualny model cenowy dla GPT-image-1.5.
- [Google Vertex AI Pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) — ceny modeli obrazowych, recontext i try-on.
- [fal — FLUX Pro pricing](https://fal.ai/models/fal-ai/flux-pro/v2.1) — przykład modelu kosztowego inference-as-a-service.
