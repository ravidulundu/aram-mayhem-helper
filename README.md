# ARAM Mayhem Helper

Un overlay local pentru League of Legends, mod ARAM Mayhem. Arata tier-ul campionilor la champ select, plus build si augmente in timpul meciului. Fara Overwolf, fara cont, fara instalare de client separat.

## Originea proiectului și documentație

Proiectul original a fost creat de **Joltarise / CyberKird**: [CyberKird/aram-mayhem-helper](https://github.com/CyberKird/aram-mayhem-helper). Această copie de lucru face parte din fork-ul [ravidulundu/aram-mayhem-helper](https://github.com/ravidulundu/aram-mayhem-helper). Arhitectura și funcționalitățile originale rămân atribuite autorului lor; contribuțiile locale sunt prezentate separat mai jos și nu reprezintă o versiune oficială a proiectului original.

README-ul principal rămâne în limba română, limba documentației originale. Documentație suplimentară: [English](README.en.md) · [Türkçe](README.tr.md). Interfața acestei copii de lucru este în engleză.

Motorul Python citește starea jocului și ofertele, iar interfața Electron afișează recomandările. Nu este necesar un cont separat pentru serviciul companion. Pentru fluxul OCR curent, folosește clientul jocului în engleză; obiectele și augmentele sunt afișate în engleză.

<a href="https://ko-fi.com/joltarise"><img src="https://raw.githubusercontent.com/CyberKird/.github/main/assets/ko-fi-button.svg" alt="Susține autorul original pe Ko-fi" width="200"></a>

## Ce face

- **Champ select**: tier-ul campionului tau si al celor de pe bench (reroll), cu cel mai bun marcat. Citeste din LCU, API-ul local al clientului League.
- Cardurile personale din champion select pot fi recunoscute prin OCR; campionul atribuit, cardurile și bench-ul comun intră în selecția celui mai bun candidat.
- **In joc**: roster complet (coechipieri + inamici), build recomandat cu un singur item per slot (nu meniu de alternative), si augmentele oferite, citite prin OCR nativ Windows.
- **Build-ul reactioneaza la itemii reali ai inamicilor** (armura, magic resist, viata, vindecare), nu doar la tipul de campion.
- Planul are cel mult șase obiecte, inclusiv cizmele; verifică grupele exclusive între obiectele planificate, păstrează cerințele augmentelor și excepțiile de quest/cumul acceptate.
- Verificările anti-heal țin cont de obiectele coechipierilor. Contra achizițiilor de rezistență magică se folosesc candidați cu penetrare magică procentuală.
- **Sfat de vandut cizmele** la build complet, daca nu contreaza compozitia inamica.
- **Tier de augment per campion**, nu doar global: acelasi augment poate fi S+ pe un campion si B pe altul.
- **Stat Anvil**: cand cumperi unul, o banda deasupra cardurilor arata care shard e cel mai bun pe campionul tau si contra compozitiei inamice.
- **Augmentele care cer un item anume** ("Upgrade Zhonya's") il urca in capul listei de cumparat. Click pe insigna augmentului ales ca sa-l confirmi; selecția în timp real nu este citită dintr-un API dedicat al integrărilor locale folosite.
- **Statistici per campion**: win rate, pick rate si cum s-au schimbat fata de patch-ul anterior (sageti verzi/rosii, plus schimbarea de tier u.gg), la champ select si in joc.
- **Raport de bug** direct din aplicație (pictograma insectă), trimis la contact@joltarise.com, cu un diagnostic pe care îl verifici înainte de trimitere.
- **Stat Anvil** arata in panou si motivul recomandarii pentru campionul tau.
- **Itemele care evolueaza** (Manamune -> Muramana, Archangel's -> Seraph's etc.) conteaza ca detinute dupa transformare.
- **Indicator pentru poțiunea de 500g** (Elixir of Iron / Sorcery / Wrath, nivel 9, efect de 3 minute): alege elixirul după campion, compozițiile celor două echipe și inventare; momentul cumpărării depinde de nivel, aur, obiectele terminate și timpul de joc. Logica este în `ingame-app/elixir.py`.
- **Headliner** (patch 26.21): jocul nu expune regula meciului, deci o alegi cu un click din panou si vezi efectul si un sfat; click din nou o scoate.
- **Se actualizeaza singur**: exe-ul din Releases, iar tier-urile si statisticile de patch se iau din repo la pornire, fara exe nou.

## Modificări în această copie de lucru

Contribuții locale realizate în fork-ul **ravidulundu**, peste proiectul original:

- Traducerea interfeței și a explicațiilor afișate în engleză; documentație suplimentară în engleză și turcă.
- Acces la panoul principal din bara de activități Windows.
- Planificarea a cel mult șase obiecte, verificări de compatibilitate între obiectele planificate și păstrarea cerințelor augmentelor, a transformărilor și a excepțiilor de cumul acceptate.
- Extinderea opțiunilor situaționale cu obiecte cumpărabile din catalogul Mayhem al aceleiași versiuni de date, în funcție de obiectele deținute și profilul de build. Regulile rămân euristice; nu simulează toate combinațiile de augmente și nu garantează un build optim.
- Explicații mai clare pentru statisticile condiționate de augmente: o medie nu este prezentată drept probabilitatea de victorie a combinației complete.
- Sincronizare atomică a datelor, validarea memoriei cache ETag și corectarea identificării jucătorului/echipei când numele jucătorului activ lipsește din API.
- Verificări locale reproductibile cu Ruff, Pyright, Pytest și selfcheck; reguli de contribuție în [AGENTS.md](AGENTS.md). Detalii și limite: [raportul de calitate](docs/quality-audit.md).

**Starea distribuției:** modificările sunt locale și nu au fost publicate ca release. Numărul de versiune afișat poate fi în continuare cel original, `2.0.7`; acesta nu identifică singur modificările locale. Sursele de actualizare pentru aplicație și date indică încă proiectul original. Pentru testarea acestei copii, `--no-update` dezactivează verificarea actualizărilor binare, dar nu și sincronizarea datelor.

Pe calculatorul de dezvoltare, scurtătura de pe desktop folosește acum motorul local verificat cu `--no-update`; motorul și scurtătura anterioare au fost salvate pentru revenire. Această instalare locală nu modifică instalatoarele originale și nu instalează contribuțiile pe alte calculatoare.

**Validare:** suita locală a trecut 41 de teste și 178 de subteste pe mediul proiectului și pe un mediu separat Python 3.14.6. Selfcheck-ul motorului împachetat a trecut. Aceste verificări nu echivalează cu validarea OCR și a tuturor recomandărilor într-un meci real.

**Suport pentru fork:** problemele specifice contribuțiilor locale se urmăresc în fork-ul ravidulundu. Formularul de raportare existent folosește încă adresa autorului original; existența acestui fork nu implică suport sau aprobare din partea sa.

## Cum functioneaza

Datele despre sesiunea curentă provin din două interfețe locale:

- **LCU** (`127.0.0.1` + port dinamic, citit din argumentele procesului LeagueClientUx.exe) pentru champ select.
- **Live Client Data API** (`127.0.0.1:2999`), oficial de la Riot, pentru roster si itemii jucatorilor in timpul meciului.

Augmentele oferite nu au niciun API. Se citesc prin OCR nativ Windows (`Windows.Media.Ocr`), pe o zona centrala a ferestrei jocului.

Aplicatia are doua bucati: **motorul** (Python, `app.py`), care face toata logica si OCR-ul, si **interfata** (Electron, `ui/`), care il porneste ca proces copil si deseneaza panoul. Vorbesc prin JSON pe stdin/stdout. In meci panoul e o piesa a HUD-ului: rama e taiata din atlasul de texturi al jocului (`ui/assets/make_frame.py`), iar fonturile sunt cele ale jocului (Beaufort, Spiegel), luate o data de pe CommunityDragon la prima pornire. Pozitionarea lucreaza per monitor, deci arata la fel pe 1080p, 1440p si 4K, si cu monitoare cu scalari diferite.

Statisticile (win rate, pick rate, istoric pe patch-uri) sunt preluate din datele publicate de [ARAMKit](https://aramkit.com). `ingame-app/update_aramkit.py` importă statisticile Mayhem, modificatorii de balans, build-urile de obiecte și datele despre augmente, fără browser. `lcu-app/update_tier_list.py` preia tier list-ul u.gg și păstrează patch-ul anterior pentru comparație. Disponibilitatea și actualitatea datelor depind de sursele respective.

Build-urile de itemi, tier-urile de augment (per campion, din win rate real) si summoner spells vin strict din date de ARAM Mayhem, nu din ARAM clasic.

Datele Live Client includ și aurul, nivelul și raza de atac. Regulile de obiecte și cerințele augmentelor sunt configurații JSON și reguli Python locale. Motorul pornește de la build-ul pregătit al campionului, elimină obiectele indisponibile, prioritizează cerințele augmentelor și alege opțiunile situaționale folosind regulile de counter, statisticile condiționate de augmente, preferințele on-hit/crit acceptate și ordinea sursei. Nu este un model antrenat care optimizează toate build-urile posibile.

Exporturile noi păstrează numărul de observații în harta opțională `augment_samples`, fără să schimbe rândurile statistice existente cu trei valori. Când există aceste numere, motorul folosește medii ponderate după eșantion; pentru pachetele vechi păstrează media cu ponderi egale. Datele incluse în prezent nu conțin aceste numere. O medie a statisticilor condiționate nu reprezintă rata măsurată a combinației complete de augmente sau probabilitatea de a câștiga meciul curent.

## Actualizări și utilizare offline

- Actualizările binare și de date folosesc încă **CyberKird/aram-mayhem-helper**. Un binar original mai nou poate înlocui contribuțiile locale. `--no-update` oprește verificarea binară la acea pornire, nu sincronizarea datelor.
- `data_sync.py` verifică datele la pornire și la fiecare 30 de minute. Workflow-ul deja existent programează generarea zilnică a datelor ARAMKit, dacă execuția sa reușește.
- Descărcările sunt validate și scrise atomic; datele mai vechi nu înlocuiesc reviziile locale mai noi, iar un eșec păstrează datele utilizabile.
- Pachetele de build sunt reîncărcate când fișierele se schimbă; nu toate sursele de tier/statistici se reîncarcă în timpul rulării. Extinderea candidaților din catalog se dezactivează când patch-ul pachetului diferă de patch-ul catalogului și al constrângerilor incluse.
- Datele locale pot funcționa offline. Fonturile noi, statisticile actualizate, actualizările aplicației și trimiterea rapoartelor necesită rețea.

Configurează canalele proprii înainte să distribui un fork întreținut. Schimbarea documentației nu schimbă endpoint-urile.

## Instalare (exe)

Versiunile [proiectului original](https://github.com/CyberKird/aram-mayhem-helper/releases) oferă `ARAM-Mayhem-Helper.exe`. Aceste instalatoare pot să nu includă contribuțiile locale; nu a fost publicat un release al fork-ului. Aplicația împachetată păstrează setările, jurnalele și datele sincronizate în `%APPDATA%/ARAM Mayhem Helper`.

## Instalare din sursa (alternativa)

1. Descarcă sau clonează depozitul într-un director în care poți scrie.
2. Rulează `INSTALL.bat`: încearcă să instaleze Python/Node.js lipsă prin winget, pregătește `.venv` și Electron, rulează selfcheck și creează scurtătura de desktop.
3. Pornește cu `START.bat` sau scurtătura. Dacă lipsesc fișierele de rulare, `START.bat` apelează instalatorul.

Instalatorul nu fixează versiunea Python. Păstrează un `.venv` funcțional. Pe acest calculator, mediul proiectului este Python 3.12.14 din runtime-ul Codex, iar PowerShell folosește implicit Python 3.14.6. Mediul separat `dist/quality-py314` este pentru compatibilitate. Numai dacă `.venv` lipsește, creează-l cu Python 3.14 disponibil. Din rădăcina depozitului, în PowerShell:

```powershell
if (-not (Test-Path .venv/Scripts/python.exe)) {
    py -3.14 -m venv .venv
}
.venv/Scripts/python.exe -m pip install -r requirements.txt
Push-Location ui
npm ci
node node_modules/electron/install.js
Pop-Location
./START.bat
```

Comanda explicită de instalare Electron este utilă când politica npm a omis scriptul său de instalare. Windows OCR are nevoie de un motor de limbă engleză disponibil. Mesajele instalatorului pot rămâne în română.

## Verificare

Instalează o dată instrumentele locale, apoi rulează suita completă:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-quality.txt
.\CHECK.bat
```

Comanda rulează Ruff lint, verificarea formatării Ruff, Pyright și Pytest cu interpretorul proiectului. Orice etapă eșuată produce un cod de eroare. Pentru un patch mic: `.\CHECK.bat --files data_sync.py --tests test_data_sync.py`. Pytest colectează și testele unittest existente. [AGENTS.md](AGENTS.md) cere verificările relevante după schimbări și suita completă înainte de finalizarea lucrărilor ample.

Mediul proiectului este Python 3.12.14. Un mediu separat Windows Python 3.14.6 a trecut și el suita completă și selfcheck-ul cu OCR nativ, cu dependențele rezolvate în prezent. Nu a fost retrogradat interpretorul și nu a fost înlocuit mediul existent. Selecția salvată în VS Code a fost verificată ca `.venv/Scripts/python.exe`; o cale implicită singură nu înlocuiește o selecție existentă. Cele două directoare de module locale sunt configurate pentru analiză. Aceste rezultate nu certifică toate versiunile permise de cerințele minime. Detalii: [raportul de calitate](docs/quality-audit.md).

Verificările unittest și selfcheck rămân disponibile:

```powershell
.venv/Scripts/python.exe -m unittest test_data_sync
.venv/Scripts/python.exe -m unittest discover -s ingame-app -p "test_*.py"
.venv/Scripts/python.exe app.py --selfcheck
```

Testele acoperă actualizări atomice eșuate, date invalide/vechi, înlocuirea pachetelor în timpul rulării, limita de șase obiecte, candidați între campioni, inventare, grupe exclusive, countere pentru MR/armură/viață, anti-heal în echipă, vânzări la build complet, conversii de damage, prioritatea questurilor/cumulării și compatibilitatea statisticilor. Selfcheck rulează motorul OCR Windows pe o imagine generată și verifică acoperirea datelor și iconițelor, fără meci pornit.

Validarea locală a trecut **41 de teste Pytest**, inclusiv 29 de recomandări și 3 de sincronizare, **178 de subteste unittest**, șase scenarii de renderer și verificările de identitate a insignelor și formular de raport. Matricea recomandărilor acoperă **173 de campioni în 1.038 de scenarii** de adversari/inventar. Sunt rezultate de verificare, nu o garanție pentru orice stare de joc. Motorul actualizat nu a fost încă validat într-un meci real.

Pentru generarea scenariilor UI și pornirea motorului simulat:

```powershell
.venv/Scripts/python.exe ui/test/make_scenarios.py
$env:ARAM_MOCK = (Resolve-Path ui/test/game1080.json).Path
Push-Location ui
npx electron .
Pop-Location
Remove-Item Env:ARAM_MOCK
```

Motorul simulat nu trimite rapoarte. Fișierele de scenariu generate sunt rezultate de dezvoltare.

## Pentru dezvoltatori: regenerarea datelor

Aceste comenzi suprascriu datele JSON generate; verifică diff-ul și rulează-le în afara unui meci:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe ingame-app/update_aramkit.py
.venv/Scripts/python.exe ingame-app/build_icons.py
```

Actualizarea ARAMKit folosește HTTP și nu necesită browser. Tier list-ul separat u.gg folosește Playwright:

```powershell
.venv/Scripts/python.exe -m playwright install chromium
.venv/Scripts/python.exe lcu-app/update_tier_list.py
```

Utilitarele vechi de scraping u.gg rămân în depozit, dar nu sunt pipeline-ul principal curent pentru build-uri Mayhem. Evită suprascrierea accidentală a datelor Mayhem cu un generator pentru ARAM clasic.

## Pentru dezvoltatori: interfata si build-ul

Rulează mai întâi verificările sursei. Pentru publicare, setează versiunea dorită în `ui/package.json` înainte de build; o verificare locală nu publică automat un release.

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m PyInstaller engine.spec --noconfirm --clean
dist/aram-engine/aram-engine.exe --selfcheck
Push-Location ui
npm ci
npx electron-builder --win nsis --publish never
Pop-Location
```

Oprește-te dacă o comandă eșuează. Motorul este în `dist/aram-engine`, iar instalatorul în `dist/ARAM-Mayhem-Helper.exe`. Spec-ul include fișierul SSL suplimentar al runtime-ului de dezvoltare când există. Pentru publicarea intenționată a unui release cu actualizare automată, instalatorul, `.blockmap` și `latest.yml` trebuie să corespundă aceleiași versiuni și aceluiași canal configurat.

## Ce NU face

- OCR poate omite sau interpreta greșit ofertele. OCR în engleză și scenariile generate au fost verificate; nu se garantează toate limbile sau rezoluțiile.
- Alegerile augmentelor sunt observate/deduse, nu citite dintr-un API dedicat selecției. Confirmarea manuală rămâne importantă.
- Recomandările extind build-ul pregătit cu opțiuni compatibile din catalogul Mayhem al aceluiași patch. Profilul urmărește obiectele deținute/core și conversiile de damage acceptate. Regulile nu simulează fiecare teamfight sau combinație de augmente.
- Lipsa datelor de tier nu este acoperită cu ranguri inventate. Acoperirea și actualitatea surselor publice limitează sistemul.
- Butonul de raport are o iconiță de insectă. Rapoartele merg încă prin FormSubmit la `contact@joltarise.com`. Emailul este opțional, diagnosticul se poate verifica înainte de trimitere, iar la eșec există o alternativă email. Codul de raportare nu atașează capturi de ecran.
- Panoul principal poate primi focus; insignele mici ale overlay-ului nu primesc focus. `Ctrl+Alt+Z` sau `_` restrânge panoul la bara de titlu, `X` închide aplicația, iar butonul romb resetează poziția.

## Limitari legale de stiut

[LICENSE](LICENSE) conține textul GNU GPL versiunea 3; README-ul original declara GPL-3.0-or-later. Metadatele `ui/package.json` au încă valoarea `UNLICENSED`, deci nu sunt aliniate cu declarația originală. Această sincronizare a documentației nu schimbă licența sau atribuirea. Statisticile, fonturile și resursele de joc ale terților rămân supuse condițiilor proprietarilor lor.

Proiectul este neoficial, neafiliat și nu pretinde aprobarea Riot Games. Consultă [documentația și politicile Riot](https://developer.riotgames.com/docs/lol) înainte să distribui un produs derivat.

## Structura

```text
app.py                         Motorul și protocolul de stare JSON
bug_report.py                  Validarea, diagnosticul și trimiterea rapoartelor
data_sync.py                   Descărcări atomice și verificări de revizie
engine.spec                    Împachetarea motorului cu PyInstaller
ui/main.js                     Ferestre Electron, poziționare și actualizări
ui/renderer/                   Panou, insigne, explicații și formular de raport
ui/test/                       Motor simulat și generator de scenarii
lcu-app/                       Acces LCU și date de champion select
ingame-app/live_client.py       Acces la datele meciului în curs
ingame-app/rules_engine.py      Selectarea, cumpărarea și vânzarea obiectelor
ingame-app/bundle.py            Cache validat și reîncărcarea pachetelor de build
ingame-app/update_aramkit.py    Generatorul curent de date Mayhem
ingame-app/test_recommendations.py  Teste de regresie pentru motor și pachete
test_data_sync.py              Teste pentru descărcare și scriere
overwolf-app/                  Implementare alternativă istorică
```

Punctul de intrare desktop activ este `app.py` din rădăcină împreună cu `ui/`.

## Licenta

Autor original: **Joltarise / CyberKird**. [Proiect original](https://github.com/CyberKird/aram-mayhem-helper) · [Susține autorul original](https://ko-fi.com/joltarise).

Atribuirea autorului original și condițiile din [LICENSE](LICENSE) se păstrează pentru acest fork. Diferența dintre declarația GPL-3.0-or-later a README-ului original și metadatele `UNLICENSED` este menționată mai sus; documentația nu modifică drepturile autorului.
