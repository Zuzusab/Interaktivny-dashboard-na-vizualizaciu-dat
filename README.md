# Vizualizačný dashboard 

Interaktívny nástroj na porovnávanie a analýzu dát naprieč piatimi najpoužívanejšími Python knižnicami na vizualizáciu – navrhnutý pre začínajúcich dátových analytikov a každého, kto rád experimentuje s dátami.

**Python 3.10** · **Licencia: MIT** · **Postavené na Streamlit**

🔗 **[Vyskúšať dashboard](https://interaktivny-dashboard-na-vizualizaciu-dat.streamlit.app/)**

## O projekte

Dashboard vznikol v rámci mojej bakalárskej práce, ktorá sa venovala porovnávaniu vizualizačných knižníc v Pythone. Namiesto teoretického porovnania som chcela vytvoriť nástroj, ktorý umožní priamo si vyskúšať a vizuálne porovnať, ako rovnaké dáta vyzerajú naprieč piatimi najpoužívanejšími knižnicami. Zároveň poskytuje aj základnú štatistickú analýzu, aby bol užitočný nielen na porovnávanie knižníc, ale aj na reálnu prácu s dátami.

<img width="800" alt="Snímka obrazovky 2026-04-30 151838" src="https://github.com/user-attachments/assets/83826371-52da-4f4d-99dd-36fc95cfdace" />

## Kľúčové funkcie

### Automatický profil datasetu
Po nahratí dát dashboard automaticky:
- Rozpozná typ jednotlivých stĺpcov (numerické / kategoriálne)
- Zobrazí náhľad prvých 10 riadkov datasetu
- Vypíše celkový počet riadkov a stĺpcov
- Navrhne vhodné typy grafov na základe štruktúry dát
- Upozorní na základné problémy v dátach (napr. chýbajúce hodnoty, duplicity, odľahlé hodnoty)
- Umožňuje vygenerovať základný EDA report

### Štandardný režim
Vhodný na prácu s jednou knižnicou:
1. Výber knižnice a typu grafu
2. Výber premenných na vizualizáciu
3. Vygenerovanie grafu na kliknutie

<img width="1362" height="1489" alt="Snímka obrazovky 2026-04-30 153021" src="https://github.com/user-attachments/assets/c67d089a-a5db-43f0-90fb-da262f260858" />

Grafy sú doplnené o štatistickú analýzu (len tam, kde to dáva zmysel vzhľadom na typ grafu):
- Test normality
- Detekcia štatisticky významných korelácií medzi premennými
- Cohen's d pre porovnanie skupín
- Štatistické porovnanie skupín

Grafy je možné exportovať podľa možností, ktoré daná knižnica podporuje.


<img width="800" alt="Snímka obrazovky 2026-04-30 153052" src="https://github.com/user-attachments/assets/db51e310-cce3-4ced-a87b-14889d66a8cb" />

###  Porovnávací režim
Umožňuje priamo porovnať, ako rovnaké dáta vyzerajú naprieč rôznymi knižnicami:
1. Výber viacerých knižníc naraz
2. Dashboard automaticky ponúkne len typy grafov, ktoré sú spoločné pre všetky vybrané knižnice
3. Výber premenných a vygenerovanie grafov vedľa seba na priame porovnanie

<img width="800" alt="Snímka obrazovky 2026-03-23 161133" src="https://github.com/user-attachments/assets/7a69dd12-b351-4ffa-bf9c-8dabc18c94d7" />
