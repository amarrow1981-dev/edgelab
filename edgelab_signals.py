#!/usr/bin/env python3
"""
EdgeLab External Signal Layer — Phase 1
-----------------------------------------
Static / derivable signals that require no external API.
All signals are pre-match — available before kickoff, usable for prediction.

Signals built here:
  1. Referee stats       — home win rate, card rate, foul tendency per referee
  2. Ground coordinates  — static table, enables travel distance calculation
  3. Travel load         — away team travel distance → normalised signal (0-1)
  4. Fixture timing      — day of week, time of day, bank holiday, festive period
  5. Public holidays     — English bank holiday calendar
  6. Motivation index    — derived from standings: dead rubber / must-win / relegation

Each signal produces a normalised float (0.0–1.0) or a flag.
Each signal has a DPOL param slot at 0.0 in LeagueParams/EngineParams.
DPOL validates which signals actually correlate with outcomes.

Every signal also feeds Gary's MatchFlagsBlock so he can reason in plain English.

Usage:
    from edgelab_signals import (
        compute_referee_stats,
        compute_travel_load,
        get_fixture_timing_flags,
        compute_motivation_index,
        GROUND_COORDS,
    )

    # During engine feature computation (per-match, on full dataframe):
    df = compute_referee_stats(df)     # adds ref_home_rate, ref_card_rate columns
    df = compute_travel_load(df)       # adds travel_km, travel_load columns
    df = compute_fixture_timing(df)    # adds day_of_week_flag, bank_holiday_flag etc.
    df = compute_motivation(df)        # adds motivation_index column

    # For Gary — single fixture context:
    from edgelab_signals import get_signal_context
    ctx = get_signal_context("Wigan Athletic", "Leyton Orient", "2026-04-12", "E2", df_history)
"""

import os
import math
import logging
from datetime import date, datetime
from typing import Optional, Dict, Tuple

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. GROUND COORDINATES — static table
#    Format: "Team Name": (latitude, longitude)
#    Source: approximate ground locations, accurate enough for distance calc.
#    Covers all clubs likely to appear in E0–EC.
# ---------------------------------------------------------------------------

GROUND_COORDS: Dict[str, Tuple[float, float]] = {
    # Premier League (E0)
    "Arsenal":            (51.5549,  -0.1084),
    "Aston Villa":        (52.5090,  -1.8847),
    "Bournemouth":        (50.7352,  -1.8381),
    "Brentford":          (51.4882,  -0.3088),
    "Brighton":           (50.8617,  -0.0837),
    "Chelsea":            (51.4816,  -0.1910),
    "Crystal Palace":     (51.3983,  -0.0855),
    "Everton":            (53.4388,  -2.9662),
    "Fulham":             (51.4749,  -0.2217),
    "Ipswich":            (52.0551,   1.1447),
    "Leeds":              (53.7775,  -1.5724),
    "Leicester":          (52.6204,  -1.1421),
    "Liverpool":          (53.4308,  -2.9608),
    "Man City":           (53.4831,  -2.2004),
    "Man United":         (53.4631,  -2.2913),
    "Middlesbrough":      (54.5784,  -1.2175),
    "Newcastle":          (54.9756,  -1.6217),
    "Norwich":            (52.6218,   1.3094),
    "Nott'm Forest":      (52.9399,  -1.1328),
    "Sheffield Utd":      (53.3703,  -1.4705),
    "Sheffield United":   (53.3703,  -1.4705),   # alias — CSV uses full name
    "Southampton":        (50.9058,  -1.3912),
    "Sunderland":         (54.9148,  -1.3879),
    "Tottenham":          (51.6042,  -0.0665),
    "Watford":            (51.6498,  -0.4017),
    "West Brom":          (52.5092,  -1.9642),
    "West Ham":           (51.5386,   0.0164),
    "Wolves":             (52.5903,  -2.1303),
    # Championship (E1)
    "Barnsley":           (53.5523,  -1.4670),
    "Birmingham":         (52.4753,  -1.7869),
    "Blackburn":          (53.7286,  -2.4894),
    "Blackpool":          (53.8058,  -3.0478),
    "Bolton":             (53.5805,  -2.5353),
    "Bristol City":       (51.4400,  -2.6200),
    "Burnley":            (53.7893,  -2.2306),
    "Cardiff":            (51.4732,  -3.2027),
    "Charlton":           (51.4865,   0.0366),
    "Coventry":           (52.4454,  -1.5396),
    "Derby":              (52.9157,  -1.4472),
    "Huddersfield":       (53.6539,  -1.7683),
    "Hull":               (53.7457,  -0.3672),
    "Luton":              (51.8841,  -0.4317),
    "Middlesbrough":      (54.5784,  -1.2175),
    "Millwall":           (51.4860,  -0.0503),
    "Oxford Utd":         (51.7174,  -1.2162),
    "Plymouth":           (50.3882,  -4.1272),
    "Portsmouth":         (50.8060,  -1.0672),
    "Preston":            (53.7719,  -2.6862),
    "QPR":                (51.5093,  -0.2322),
    "Reading":            (51.4539,  -0.9865),
    "Rotherham":          (53.4280,  -1.3624),
    "Sheffield Weds":     (53.4111,  -1.5006),
    "Stoke":              (53.0003,  -2.1750),
    "Swansea":            (51.6430,  -3.9350),
    "Swindon":            (51.5590,  -1.7707),
    "Wigan":              (53.5494,  -2.6375),
    "Wigan Athletic":     (53.5494,  -2.6375),
    "Wrexham":            (53.0464,  -2.9902),
    # League One (E2)
    "Accrington":         (53.7540,  -2.3640),
    "Barnsley":           (53.5523,  -1.4670),
    "Bradford":           (53.8039,  -1.7776),
    "Bristol Rovers":     (51.5126,  -2.5402),
    "Burton":             (52.8127,  -1.6349),
    "Cambridge":          (52.2000,   0.1174),
    "Charlton":           (51.4865,   0.0366),
    "Chesterfield":       (53.2526,  -1.4270),
    "Doncaster":          (53.5226,  -1.0858),
    "Exeter":             (50.7274,  -3.5193),
    "Fleetwood":          (53.9217,  -3.0127),
    "Leyton Orient":      (51.5607,  -0.0142),
    "Lincoln":            (53.1666,  -0.5394),
    "Mansfield":          (53.1498,  -1.1901),
    "MK Dons":            (52.0138,  -0.7337),
    "Milton Keynes Dons": (52.0138,  -0.7337),
    "Northampton":        (52.2319,  -0.8899),
    "Peterborough":       (52.5651,  -0.2404),
    "Port Vale":          (53.0500,  -2.1750),
    "Shrewsbury":         (52.7215,  -2.7471),
    "Stevenage":          (51.8824,  -0.2119),
    "Stockport":          (53.4069,  -2.1593),
    "Wycombe":            (51.6305,  -0.7993),
    # League Two (E3)
    "Barnet":             (51.6500,  -0.1890),
    "Barrow":             (54.1094,  -3.2275),
    "Bradford City":      (53.8039,  -1.7776),
    "Bromley":            (51.4005,   0.0223),
    "Cheltenham":         (51.9008,  -2.0784),
    "Colchester":         (51.8894,   0.9097),
    "Crawley":            (51.1188,  -0.1888),
    "Crewe":              (53.0942,  -2.4317),
    "Gillingham":         (51.3883,   0.5492),
    "Grimsby":            (53.5679,  -0.1046),
    "Harrogate":          (53.9894,  -1.5408),
    "Morecambe":          (54.0701,  -2.8478),
    "Newport County":     (51.5879,  -2.9880),
    "Oldham":             (53.5455,  -2.1286),
    "Rochdale":           (53.6140,  -2.1548),
    "Salford":            (53.4831,  -2.2925),
    "Tranmere":           (53.3986,  -3.0305),
    "Walsall":            (52.5637,  -1.9866),
    # National League (EC)
    "Aldershot":          (51.2465,  -0.7831),
    "Altrincham":         (53.3864,  -2.3525),
    "Boreham Wood":       (51.6671,  -0.2737),
    "Boston Utd":         (52.9826,  -0.0228),
    "Chesterfield":       (53.2526,  -1.4270),
    "Dag and Red":        (51.5429,   0.1299),
    "Dagenham":           (51.5429,   0.1299),
    "Dover":              (51.1279,   1.3134),
    "Eastleigh":          (50.9626,  -1.3585),
    "FC Halifax":         (53.7234,  -1.8580),
    "Gateshead":          (54.9604,  -1.6200),
    "Guiseley":           (53.8727,  -1.7063),
    "Hartlepool":         (54.6880,  -1.2122),
    "King's Lynn":        (52.7549,   0.3984),
    "Maidstone":          (51.2820,   0.5217),
    "Notts County":       (52.9434,  -1.1358),
    "Scunthorpe":         (53.5881,  -0.6569),
    "Solihull Moors":     (52.4250,  -1.7677),
    "Southend":           (51.5403,   0.7082),
    "Sutton Utd":         (51.3656,  -0.1975),
    "Torquay":            (50.4747,  -3.5241),
    "Wealdstone":         (51.5925,  -0.3373),
    "Woking":             (51.3230,  -0.5566),
    "Wrexham":            (53.0464,  -2.9902),
    "York":               (53.9508,  -1.0826),
    "Yeovil":             (50.9436,  -2.6374),
    # ---------------------------------------------------------------------------
    # EUROPEAN GROUNDS
    # ---------------------------------------------------------------------------

    # Belgian First Division A (B1)
    "Anderlecht":           (50.8344,   4.3352),
    "Antwerp":              (51.2100,   4.4200),
    "Beerschot VA":         (51.1965,   4.3817),
    "Beveren":              (51.2100,   4.2600),
    "Cercle Brugge":        (51.1942,   3.2032),
    "Charleroi":            (50.4011,   4.4444),
    "Club Brugge":          (51.1942,   3.2032),
    "Dender":               (50.9000,   4.0300),
    "Eupen":                (50.6280,   6.0350),
    "FC Brussels":          (50.8503,   4.3517),
    "Genk":                 (50.9550,   5.5100),
    "Gent":                 (51.0425,   3.7250),
    "Germinal":             (51.0500,   4.2800),
    "Heusden Zolder":       (51.0500,   5.3300),
    "Kortrijk":             (50.8200,   3.2700),
    "Lierse":               (51.1200,   4.5500),
    "Lokeren":              (51.0970,   3.9890),
    "Lommel":               (51.2300,   5.3100),
    "Louvieroise":          (50.4700,   4.1700),
    "Mechelen":             (51.0300,   4.4800),
    "Molenbeek":            (50.8600,   4.3200),
    "RWD Molenbeek":        (50.8600,   4.3200),
    "Mouscron":             (50.7400,   3.2100),
    "Mouscron-Peruwelz":    (50.7400,   3.2100),
    "Aalst":                (50.9400,   4.0400),
    "Bergen":               (50.4700,   3.9600),
    "Oostende":             (51.2300,   2.9100),
    "Oud-Heverlee Leuven":  (50.8800,   4.7000),
    "Roeselare":            (50.9400,   3.1200),
    "Seraing":              (50.5900,   5.5100),
    "St Truiden":           (50.8100,   5.1800),
    "St. Gilloise":         (50.8200,   4.3400),
    "Standard":             (50.6100,   5.5300),
    "Tubize":               (50.6900,   4.2000),
    "Waasland-Beveren":     (51.2100,   4.2600),
    "Waregem":              (50.8900,   3.4300),
    "Westerlo":             (51.1000,   4.9100),

    # Bundesliga (D1) + 2. Bundesliga (D2)
    "Aachen":               (50.7753,   6.0839),
    "Aalen":                (48.8370,  10.0933),
    "Ahlen":                (51.7600,   7.8900),
    "Augsburg":             (48.3235,  10.8864),
    "Bayern Munich":        (48.2188,  11.6248),
    "Bielefeld":            (52.0250,   8.5320),
    "Bochum":               (51.4900,   7.2300),
    "Braunschweig":         (52.2700,  10.5200),
    "Burghausen":           (48.1700,  12.8300),
    "CZ Jena":              (50.9300,  11.5900),
    "Cottbus":              (51.7600,  14.3200),
    "Darmstadt":            (49.8600,   8.6500),
    "Dortmund":             (51.4926,   7.4518),
    "Dresden":              (51.0600,  13.7400),
    "Duisburg":             (51.4900,   6.7800),
    "Ein Frankfurt":        (50.0686,   8.6456),
    "Ein Trier":            (49.7600,   6.6400),
    "Elversberg":           (49.3800,   7.1000),
    "Erfurt":               (50.9700,  11.0300),
    "Erzgebirge Aue":       (50.5900,  12.7000),
    "Essen":                (51.4900,   6.9900),
    "FC Koln":              (50.9338,   6.8750),
    "Fortuna Dusseldorf":   (51.2700,   6.7900),
    "Frankfurt FSV":        (50.0686,   8.6456),
    "Freiburg":             (48.0219,   7.8839),
    "Greuther Furth":       (49.5000,  10.9900),
    "Hamburg":              (53.5872,   9.9986),
    "Hannover":             (52.3607,   9.7383),
    "Hansa Rostock":        (54.0887,  12.1319),
    "Heidenheim":           (48.7000,  10.1600),
    "Hertha":               (52.5147,  13.2397),
    "Hoffenheim":           (49.2400,   8.8900),
    "Holstein Kiel":        (54.3764,  10.1320),
    "Ingolstadt":           (48.7500,  11.3900),
    "Kaiserslautern":       (49.4344,   7.7769),
    "Karlsruhe":            (49.0300,   8.4100),
    "Koblenz":              (50.3600,   7.5700),
    "Leverkusen":           (51.0383,   7.0022),
    "Lubeck":               (53.8800,  10.6800),
    "M'gladbach":           (51.1742,   6.3853),
    "Magdeburg":            (52.1500,  11.5900),
    "Mainz":                (49.9843,   8.2241),
    "Mannheim":             (49.4700,   8.4900),
    "Munich 1860":          (48.2188,  11.6248),
    "Nurnberg":             (49.4267,  11.1330),
    "Oberhausen":           (51.4700,   6.8600),
    "Offenbach":            (50.1100,   8.7600),
    "Osnabruck":            (52.2700,   8.0500),
    "Paderborn":            (51.7200,   8.7500),
    "Preußen Münster":      (51.9600,   7.6300),
    "RB Leipzig":           (51.3458,  12.3483),
    "Regensburg":           (49.0100,  12.1000),
    "Reutlingen":           (48.4900,   9.2100),
    "Saarbrucken":          (49.2300,   7.0100),
    "Sandhausen":           (49.3400,   8.6600),
    "Schalke 04":           (51.5543,   7.0678),
    "Siegen":               (50.8700,   8.0200),
    "St Pauli":             (53.5544,   9.9681),
    "Stuttgart":            (48.7925,   9.2325),
    "Ulm":                  (48.4000,   9.9900),
    "Union Berlin":         (52.4575,  13.5683),
    "Unterhaching":         (48.0700,  11.6100),
    "Wehen":                (50.0600,   8.1300),
    "Werder Bremen":        (53.0661,   8.8376),
    "Wolfsburg":            (52.4317,  10.8042),
    "Wurzburger Kickers":   (49.7900,   9.9300),

    # Serie A (I1) + Serie B (I2)
    "Albinoleffe":          (45.8000,   9.8500),
    "Alessandria":          (44.9100,   8.6100),
    "Ancona":               (43.6000,  13.5100),
    "Arezzo":               (43.4700,  11.8800),
    "Ascoli":               (42.8500,  13.5700),
    "Atalanta":             (45.7090,   9.6800),
    "Avellino":             (40.9100,  14.7900),
    "Bari":                 (41.0850,  16.8710),
    "Benevento":            (41.1300,  14.7800),
    "Bologna":              (44.4939,  11.3119),
    "Brescia":              (45.5190,  10.2200),
    "Cagliari":             (39.2250,   9.1340),
    "Carpi":                (44.7800,  10.8800),
    "Carrarese":            (44.0800,  10.0900),
    "Catania":              (37.5000,  15.0900),
    "Catanzaro":            (38.9000,  16.5900),
    "Cesena":               (44.1300,  12.2400),
    "Chievo":               (45.4400,  11.0000),
    "Cittadella":           (45.6500,  11.7800),
    "Como":                 (45.8100,   9.0800),
    "Cosenza":              (39.3000,  16.2500),
    "Cremonese":            (45.1300,  10.0300),
    "Crotone":              (39.0800,  17.1300),
    "Empoli":               (43.7200,  10.9500),
    "FeralpiSalo":          (45.6000,  10.5300),
    "Fiorentina":           (43.7806,  11.2822),
    "Foggia":               (41.4600,  15.5500),
    "Frosinone":            (41.6400,  13.3600),
    "Gallipoli":            (40.0600,  17.9900),
    "Genoa":                (44.4164,   8.9511),
    "Grosseto":             (42.7600,  11.1100),
    "Gubbio":               (43.3500,  12.5700),
    "Inter":                (45.4781,   9.1240),
    "Juve Stabia":          (40.7000,  14.4700),
    "Juventus":             (45.1096,   7.6413),
    "Latina":               (41.4700,  12.9000),
    "Lazio":                (41.9340,  12.4547),
    "Lecce":                (40.3600,  18.1700),
    "Lecco":                (45.8600,   9.3900),
    "Livorno":              (43.5500,  10.3100),
    "Mantova":              (45.1600,  10.7900),
    "Messina":              (38.1900,  15.5500),
    "Milan":                (45.4781,   9.1240),
    "Modena":               (44.6400,  10.9300),
    "Monza":                (45.5900,   9.2700),
    "Napoli":               (40.8280,  14.1930),
    "Nocerina":             (40.7400,  14.6200),
    "Novara":               (45.4500,   8.6200),
    "Padova":               (45.4100,  11.8800),
    "Palermo":              (38.1400,  13.3700),
    "Parma":                (44.8000,  10.3300),
    "Perugia":              (43.1100,  12.3900),
    "Pescara":              (42.4600,  14.2000),
    "Piacenza":             (45.0500,   9.7000),
    "Pisa":                 (43.7100,  10.4000),
    "Pistoiese":            (43.9300,  10.9100),
    "Pordenone":            (45.9600,  12.6600),
    "Portogruaro":          (45.7800,  12.8400),
    "Pro Vercelli":         (45.3300,   8.4200),
    "Ravenna":              (44.4200,  12.2000),
    "Reggiana":             (44.7000,  10.6300),
    "Reggina":              (38.1100,  15.6500),
    "Rimini":               (44.0600,  12.5700),
    "Roma":                 (41.9340,  12.4547),
    "Salernitana":          (40.6800,  14.7600),
    "Sampdoria":            (44.4164,   8.9511),
    "Sassuolo":             (44.5400,  10.7800),
    "Siena":                (43.3100,  11.3300),
    "Spal":                 (44.8600,  11.6100),
    "Spezia":               (44.1100,   9.8300),
    "Sudtirol":             (46.5000,  11.3500),
    "Ternana":              (42.5600,  12.6400),
    "Torino":               (45.0408,   7.6500),
    "Trapani":              (38.0200,  12.5200),
    "Treviso":              (45.6700,  12.2400),
    "Triestina":            (45.6500,  13.7800),
    "Udinese":              (46.0800,  13.2000),
    "Varese":               (45.8200,   8.8300),
    "Venezia":              (45.4380,  12.3155),
    "Verona":               (45.4300,  10.9800),
    "Vicenza":              (45.5400,  11.5500),
    "Virtus Entella":       (44.3100,   9.3300),
    "Virtus Lanciano":      (42.2300,  14.3800),

    # Eredivisie (N1)
    "AZ Alkmaar":           (52.6200,   4.7400),
    "Ajax":                 (52.3143,   4.9419),
    "Almere City":          (52.3600,   5.2200),
    "Cambuur":              (53.2200,   5.8000),
    "Den Bosch":            (51.7000,   5.3000),
    "Den Haag":             (52.0589,   4.3247),
    "Dordrecht":            (51.8100,   4.6700),
    "Excelsior":            (51.9200,   4.5000),
    "FC Emmen":             (52.7800,   6.9100),
    "Feyenoord":            (51.8939,   4.5228),
    "For Sittard":          (50.9200,   5.8700),
    "Go Ahead Eagles":      (52.2600,   6.1500),
    "Graafschap":           (51.9600,   6.2900),
    "Groningen":            (53.2100,   6.5800),
    "Heerenveen":           (52.9600,   5.9200),
    "Heracles":             (52.3100,   6.6700),
    "NAC Breda":            (51.5900,   4.7800),
    "Nijmegen":             (51.8400,   5.8700),
    "PSV Eindhoven":        (51.4416,   5.4672),
    "Roda":                 (50.8900,   5.9300),
    "Roda JC":              (50.8900,   5.9300),
    "Roosendaal":           (51.5300,   4.4600),
    "Sparta":               (51.9200,   4.4700),
    "Sparta Rotterdam":     (51.9200,   4.4700),
    "Telstar":              (52.4600,   4.6200),
    "Twente":               (52.2367,   6.8564),
    "Utrecht":              (52.0786,   5.1447),
    "VVV Venlo":            (51.3700,   6.1700),
    "Vitesse":              (51.9700,   5.9400),
    "Volendam":             (52.5000,   5.0700),
    "Waalwijk":             (51.6900,   5.0700),
    "Willem II":            (51.5600,   5.0800),
    "Zwolle":               (52.5100,   6.0900),

    # Scottish Premiership + lower (SC0–SC3)
    "Aberdeen":             (57.1497,  -2.0943),
    "Airdrie":              (55.8600,  -3.9900),
    "Airdrie Utd":          (55.8600,  -3.9900),
    "Albion Rvs":           (55.7700,  -4.0600),
    "Alloa":                (56.1100,  -3.7900),
    "Annan Athletic":       (54.9900,  -3.2600),
    "Arbroath":             (56.5600,  -2.5900),
    "Ayr":                  (55.4700,  -4.6200),
    "Berwick":              (55.7700,  -2.0000),
    "Bonnyrigg Rose":       (55.8700,  -3.1000),
    "Brechin":              (56.7300,  -2.6600),
    "Celtic":               (55.8497,  -4.2058),
    "Clyde":                (55.8300,  -4.1200),
    "Clydebank":            (55.9000,  -4.4000),
    "Cove Rangers":         (57.0900,  -2.0800),
    "Cowdenbeath":          (56.1100,  -3.3500),
    "Dumbarton":            (55.9400,  -4.5700),
    "Dundee":               (56.4620,  -3.0000),
    "Dundee United":        (56.4620,  -3.0000),
    "Dunfermline":          (56.0700,  -3.4600),
    "East Fife":            (56.1900,  -2.9900),
    "East Kilbride":        (55.7600,  -4.1600),
    "East Stirling":        (56.0000,  -3.7800),
    "Edinburgh City":       (55.9500,  -3.1900),
    "FC Edinburgh":         (55.9500,  -3.1900),
    "Elgin":                (57.6500,  -3.3400),
    "Falkirk":              (56.0000,  -3.7800),
    "Forfar":               (56.6400,  -2.8900),
    "Gretna":               (54.9900,  -3.0600),
    "Hamilton":             (55.7700,  -4.0300),
    "Hearts":               (55.9389,  -3.2311),
    "Hibernian":            (55.9611,  -3.1650),
    "Inverness C":          (57.4800,  -4.2300),
    "Kelty Hearts":         (56.1200,  -3.4000),
    "Kilmarnock":           (55.6100,  -4.4900),
    "Livingston":           (55.8800,  -3.5200),
    "Montrose":             (56.7100,  -2.4700),
    "Morton":               (55.8700,  -4.6900),
    "Motherwell":           (55.7800,  -3.9900),
    "Partick":              (55.8800,  -4.3200),
    "Peterhead":            (57.5100,  -1.7800),
    "Queen of Sth":         (55.0700,  -3.6100),
    "Queens Park":          (55.8300,  -4.2500),
    "Raith":                (56.1100,  -3.1600),
    "Raith Rvs":            (56.1100,  -3.1600),
    "Rangers":              (55.8508,  -4.3094),
    "Ross County":          (57.5900,  -4.4200),
    "Spartans":             (55.9700,  -3.2400),
    "St Johnstone":         (56.4000,  -3.4300),
    "St Mirren":            (55.8400,  -4.4300),
    "Stenhousemuir":        (56.0500,  -3.8000),
    "Stirling":             (56.1200,  -3.9400),
    "Stranraer":            (54.9000,  -5.0200),

    # La Liga (SP1) + La Liga 2 (SP2)
    "Alaves":               (42.8500,  -2.6700),
    "Albacete":             (38.9900,  -1.8600),
    "Alcorcon":             (40.3500,  -3.8300),
    "Alcoyano":             (38.6900,  -0.4700),
    "Algeciras":            (36.1300,  -5.4600),
    "Alicante":             (38.3700,  -0.4800),
    "Almeria":              (36.8380,  -2.4510),
    "Amorebieta":           (43.2200,  -2.7300),
    "Andorra":              (42.5700,   1.5200),
    "Ath Bilbao":           (43.2642,  -2.9494),
    "Ath Bilbao B":         (43.2642,  -2.9494),
    "Ath Madrid":           (40.4361,  -3.5994),
    "Badajoz":              (38.8800,  -6.9700),
    "Barcelona":            (41.3809,   2.1228),
    "Barcelona B":          (41.3809,   2.1228),
    "Betis":                (37.3567,  -5.9811),
    "Burgos":               (42.3500,  -3.6900),
    "Cadiz":                (36.5000,  -6.2700),
    "Cartagena":            (37.6000,  -0.9800),
    "Castellon":            (39.9800,  -0.0500),
    "Celta":                (42.2117,  -8.7384),
    "Ceuta":                (35.8900,  -5.3200),
    "Ciudad de Murcia":     (37.9700,  -1.1300),
    "Compostela":           (42.8800,  -8.5500),
    "Cordoba":              (37.8690,  -4.7840),
    "Cultural Leonesa":     (42.6000,  -5.5700),
    "Eibar":                (43.1800,  -2.4700),
    "Elche":                (38.2700,  -0.6900),
    "Eldense":              (38.4800,  -0.7900),
    "Espanol":              (41.3471,   2.0749),
    "Extremadura":          (38.9200,  -6.3400),
    "Extremadura UD":       (38.9200,  -6.3400),
    "Ferrol":               (43.4800,  -8.2300),
    "Fuenlabrada":          (40.2800,  -3.8000),
    "Getafe":               (40.3239,  -3.7139),
    "Gimnastic":            (41.1200,   1.2400),
    "Girona":               (41.9615,   2.8361),
    "Granada":              (37.1500,  -3.5900),
    "Granada 74":           (37.1500,  -3.5900),
    "Guadalajara":          (40.6300,  -3.1700),
    "Hercules":             (38.3600,  -0.4900),
    "Huesca":               (42.1400,  -0.4100),
    "Ibiza":                (38.9100,   1.4300),
    "Jaen":                 (37.7700,  -3.7900),
    "La Coruna":            (43.3650,  -8.4100),
    "Las Palmas":           (28.1000, -15.4300),
    "Leganes":              (40.3300,  -3.7600),
    "Leonesa":              (42.6000,  -5.5700),
    "Levante":              (39.4764,  -0.3581),
    "Llagostera":           (41.8300,   2.9500),
    "Lleida":               (41.6200,   0.6200),
    "Logrones":             (42.4600,  -2.4500),
    "Lorca":                (37.6700,  -1.7000),
    "Lugo":                 (43.0100,  -7.5600),
    "Malaga":               (36.7200,  -4.4200),
    "Malaga B":             (36.7200,  -4.4200),
    "Mallorca":             (39.5900,   2.6500),
    "Mirandes":             (42.6900,  -2.9300),
    "Murcia":               (37.9700,  -1.1300),
    "Numancia":             (41.7800,  -2.4600),
    "Osasuna":              (42.7967,  -1.6369),
    "Oviedo":               (43.3614,  -5.8597),
    "Poli Ejido":           (36.7700,  -2.8100),
    "Ponferradina":         (42.5500,  -6.5900),
    "Pontevedra":           (42.4300,  -8.6500),
    "Rayo Majadahonda":     (40.4700,  -3.8700),
    "Real Madrid":          (40.4530,  -3.6883),
    "Real Madrid B":        (40.4530,  -3.6883),
    "Real Union":           (43.3500,  -1.8000),
    "Recreativo":           (37.2700,  -6.9400),
    "Reus Deportiu":        (41.1600,   1.1100),
    "Sabadell":             (41.5500,   2.1000),
    "Salamanca":            (40.9600,  -5.6600),
    "Santander":            (43.4500,  -3.8200),
    "Sevilla":              (37.3841,  -5.9706),
    "Sevilla B":            (37.3841,  -5.9706),
    "Sociedad":             (43.3014,  -1.9736),
    "Sociedad B":           (43.3014,  -1.9736),
    "Sp Gijon":             (43.5300,  -5.6400),
    "Tenerife":             (28.4700, -16.2600),
    "Terrassa":             (41.5700,   2.0100),
    "UCAM Murcia":          (37.9700,  -1.1300),
    "Valencia":             (39.4753,  -0.3583),
    "Valladolid":           (41.6522,  -4.7264),
    "Vallecano":            (40.3922,  -3.6617),
    "Vecindario":           (27.8600, -15.4200),
    "Villarreal":           (39.9444,  -0.1036),
    "Villarreal B":         (39.9444,  -0.1036),
    "Xerez":                (36.6900,  -6.1400),
    "Zaragoza":             (41.6560,  -0.8773),

    # ── CSV name aliases — exact names used in weather_cache.csv ────────────
    # These differ from canonical names already in the dict above.
    # Added S31 after weather retry identified mismatches.
    "Bristol Rvs":          (51.5126,  -2.5402),
    "Oxford":               (51.7174,  -1.2162),
    "Peterboro":            (52.5651,  -0.2404),
    "Crawley Town":         (51.1188,  -0.1888),
    "Forest Green":         (51.6996,  -2.2399),
    "AFC Wimbledon":        (51.4249,  -0.1879),
    "Fleetwood Town":       (53.9217,  -3.0127),
    "Bury":                 (53.5800,  -2.2983),
    "Macclesfield":         (53.2607,  -2.1244),
    "Kidderminster":        (52.3938,  -2.2505),
    "Halifax":              (53.7234,  -1.8580),
    "Hereford":             (52.0497,  -2.7164),
    "Ebbsfleet":            (51.4249,   0.3162),
    "Tamworth":             (52.6340,  -1.6892),
    "Darlington":           (54.5225,  -1.5696),
    "Chester":              (53.1876,  -2.8860),
    "Southport":            (53.6478,  -3.0057),
    "Rushden & D":          (52.2872,  -0.6011),
    "Braintree Town":       (51.8786,   0.5650),
    "Sutton":               (51.3656,  -0.1975),
    "Solihull":             (52.4250,  -1.7677),
    "Maidenhead":           (51.5237,  -0.7189),
    "Grays":                (51.4757,   0.3258),
    "Alfreton Town":        (53.0970,  -1.3830),
    "Salisbury":            (51.0693,  -1.7940),
    "Kettering Town":       (52.3935,  -0.7198),
    "Histon":               (52.2399,   0.1135),
    "Dover Athletic":       (51.1279,   1.3134),
    "Fylde":                (53.8264,  -2.9860),
    "Welling United":       (51.4454,   0.1049),
    "Nuneaton Town":        (52.5190,  -1.4617),
    "Dartford":             (51.4457,   0.2167),
    "Weymouth":             (50.6136,  -2.4597),
    "Northwich":            (53.2587,  -2.5134),
    "Hayes & Yeading":      (51.5237,  -0.4279),
    "Eastbourne Borough":   (50.7668,   0.2824),
    "Wimbledon":            (51.3983,  -0.0855),
    "Boston":               (52.9826,  -0.0228),
    "Telford United":       (52.6860,  -2.4470),
    "Hyde United":          (53.4529,  -2.0725),
    "Bath City":            (51.3694,  -2.3556),
    "Stafford Rangers":     (52.8073,  -2.1168),
    "Dorking":              (51.2322,  -0.3327),
    "Gravesend":            (51.4249,   0.3162),
    "AFC Telford United":   (52.6860,  -2.4470),
    "Lewes":                (50.8740,   0.0147),
    "Droylsden":            (53.4855,  -2.1575),
    "Farsley":              (53.8106,  -1.6601),
    "St. Albans":           (51.7526,  -0.3335),
    "Oxford City":          (51.7174,  -1.2162),
    "Scarborough":          (54.2739,  -0.3996),
    "Canvey Island":        (51.5167,   0.5833),
    "Brackley Town":        (52.0318,  -1.1434),
    "Truro":                (50.2632,  -5.0510),
    "Chorley":              (53.6531,  -2.6322),
    "Carlisle":             (54.8929,  -2.9358),
    # Dutch/German/Italian trailing space variants
    "Ajax ":                (52.3143,   4.9419),
    "Feyenoord ":           (51.8939,   4.5228),
    "Groningen ":           (53.2100,   6.5800),
    "Heracles ":            (52.3100,   6.6700),
    "Utrecht ":             (52.0786,   5.1447),
    "Vitesse ":             (51.9700,   5.9400),
    "Willem II ":           (51.5600,   5.0800),
    "Roda ":                (50.8900,   5.9300),
    "Graafschap ":          (51.9600,   6.2900),
    "Kaiserslautern ":      (49.4344,   7.7769),
    "Piacenza ":            (45.0500,   9.7000),
}


# ---------------------------------------------------------------------------
# 2. UK BANK HOLIDAYS — static table
#    English bank holidays. Festive period defined as Dec 20 – Jan 3.
#    These are the key fixtures that behave differently (midweek, big crowds,
#    away support patterns change, tired squads).
# ---------------------------------------------------------------------------

# Key English bank holidays (date strings YYYY-MM-DD)
# Extend as needed. Covers the full historical dataset period.
BANK_HOLIDAYS = {
    # 2018-19
    "2018-12-25", "2018-12-26", "2019-01-01", "2019-04-19", "2019-04-22",
    "2019-05-06", "2019-05-27", "2019-08-26",
    # 2019-20
    "2019-12-25", "2019-12-26", "2020-01-01", "2020-04-10", "2020-04-13",
    "2020-05-08", "2020-05-25", "2020-08-31",
    # 2020-21
    "2020-12-25", "2020-12-28", "2021-01-01", "2021-04-02", "2021-04-05",
    "2021-05-03", "2021-05-31", "2021-08-30",
    # 2021-22
    "2021-12-27", "2021-12-28", "2022-01-03", "2022-04-15", "2022-04-18",
    "2022-05-02", "2022-06-02", "2022-06-03", "2022-08-29",
    # 2022-23
    "2022-12-26", "2022-12-27", "2023-01-02", "2023-04-07", "2023-04-10",
    "2023-05-01", "2023-05-08", "2023-05-29", "2023-08-28",
    # 2023-24
    "2023-12-25", "2023-12-26", "2024-01-01", "2024-03-29", "2024-04-01",
    "2024-05-06", "2024-05-27", "2024-08-26",
    # 2024-25
    "2024-12-25", "2024-12-26", "2025-01-01", "2025-04-18", "2025-04-21",
    "2025-05-05", "2025-05-26", "2025-08-25",
    # 2025-26
    "2025-12-25", "2025-12-26", "2026-01-01", "2026-04-03", "2026-04-06",
    "2026-05-04", "2026-05-25", "2026-08-31",
}


def is_bank_holiday(dt: pd.Timestamp) -> bool:
    return dt.strftime("%Y-%m-%d") in BANK_HOLIDAYS


def is_festive_period(dt: pd.Timestamp) -> bool:
    """Dec 20 to Jan 3 — the congested Christmas/NY fixture run."""
    m, d = dt.month, dt.day
    return (m == 12 and d >= 20) or (m == 1 and d <= 3)


# ---------------------------------------------------------------------------
# 3. REFEREE STATS — computed from historical CSV data
# ---------------------------------------------------------------------------

def compute_referee_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute per-referee statistics and add signal columns to df.

    Reads the 'Referee' column (retained in session 12 CSV audit).
    Uses only history BEFORE each match — no lookahead.

    Columns added:
        ref_home_rate    — referee's historical home win rate (0-1)
                           1.0 = always gives home wins, 0.5 = neutral
        ref_card_rate    — average total yellow cards per game for this ref
        ref_foul_rate    — average total fouls per game for this ref
        ref_signal       — normalised combined signal (0-1). 0.5 = neutral ref.
                           >0.5 = ref with high home bias. <0.5 = lower home bias.

    If 'Referee' column absent or ref not seen before, uses global averages.
    """
    if "Referee" not in df.columns:
        logger.info("[Signals] No Referee column — skipping referee stats")
        df["ref_home_rate"]  = 0.5
        df["ref_card_rate"]  = np.nan
        df["ref_foul_rate"]  = np.nan
        df["ref_signal"]     = 0.5
        return df

    df = df.copy().reset_index(drop=True)

    # Global averages — used as prior when ref has < MIN_MATCHES
    MIN_MATCHES  = 10   # minimum matches before we trust a ref's stats
    global_h_rate = (df["FTR"] == "H").mean() if len(df) > 0 else 0.45

    has_cards = "HY" in df.columns and "AY" in df.columns
    has_fouls = "HF" in df.columns and "AF" in df.columns
    global_card_rate  = (df["HY"].fillna(0) + df["AY"].fillna(0)).mean() if has_cards else np.nan
    global_foul_rate  = (df["HF"].fillna(0) + df["AF"].fillna(0)).mean() if has_fouls else np.nan

    ref_home_rates  = []
    ref_card_rates  = []
    ref_foul_rates  = []
    ref_signals     = []

    # Referee cumulative state — rolling, no lookahead
    ref_stats: Dict[str, dict] = {}

    refs       = df["Referee"].tolist()
    ftrs       = df["FTR"].tolist()
    hys        = df["HY"].tolist()  if has_cards else [np.nan] * len(df)
    ays        = df["AY"].tolist()  if has_cards else [np.nan] * len(df)
    hfs        = df["HF"].tolist()  if has_fouls else [np.nan] * len(df)
    afs        = df["AF"].tolist()  if has_fouls else [np.nan] * len(df)

    for i in range(len(df)):
        ref = refs[i]
        if pd.isna(ref) or ref == "":
            ref_home_rates.append(global_h_rate)
            ref_card_rates.append(global_card_rate)
            ref_foul_rates.append(global_foul_rate)
            ref_signals.append(0.5)
            continue

        if ref not in ref_stats:
            ref_stats[ref] = {"n": 0, "h_wins": 0, "cards": 0, "fouls": 0}

        s = ref_stats[ref]

        # Stats BEFORE this match
        if s["n"] >= MIN_MATCHES:
            h_rate   = s["h_wins"] / s["n"]
            c_rate   = s["cards"]  / s["n"]
            f_rate   = s["fouls"]  / s["n"]
            # Normalise home rate to a signal: ref home_rate vs global baseline
            # 0.5 = exactly at baseline, 1.0 = extreme home bias, 0.0 = never home
            ref_signal = np.clip(h_rate / (global_h_rate * 2), 0.0, 1.0)
        else:
            # Not enough data — use global averages, neutral signal
            h_rate   = global_h_rate
            c_rate   = global_card_rate
            f_rate   = global_foul_rate
            ref_signal = 0.5

        ref_home_rates.append(round(h_rate, 4))
        ref_card_rates.append(round(c_rate, 4) if not np.isnan(c_rate) else np.nan)
        ref_foul_rates.append(round(f_rate, 4) if not np.isnan(f_rate) else np.nan)
        ref_signals.append(round(ref_signal, 4))

        # Update stats with this match's result
        s["n"]      += 1
        s["h_wins"] += 1 if ftrs[i] == "H" else 0
        hy = hys[i] if not pd.isna(hys[i]) else 0
        ay = ays[i] if not pd.isna(ays[i]) else 0
        hf = hfs[i] if not pd.isna(hfs[i]) else 0
        af = afs[i] if not pd.isna(afs[i]) else 0
        s["cards"]  += hy + ay
        s["fouls"]  += hf + af

    df["ref_home_rate"] = ref_home_rates
    df["ref_card_rate"] = ref_card_rates
    df["ref_foul_rate"] = ref_foul_rates
    df["ref_signal"]    = ref_signals

    return df


# ---------------------------------------------------------------------------
# 4. TRAVEL DISTANCE — ground coordinates → km → normalised load
# ---------------------------------------------------------------------------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_travel_km(home_team: str, away_team: str) -> Optional[float]:
    """
    Return travel distance for away team in km.
    Returns None if either team not in GROUND_COORDS.
    """
    home_coords = GROUND_COORDS.get(home_team)
    away_coords = GROUND_COORDS.get(away_team)
    if home_coords is None or away_coords is None:
        return None
    return round(haversine_km(away_coords[0], away_coords[1],
                              home_coords[0], home_coords[1]), 1)


def compute_travel_load(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add travel_km and travel_load columns to df.

    travel_km    — distance away team travels to the ground (km)
    travel_load  — normalised 0-1 signal.
                   0 = local derby (<30km), 1 = longest possible journey (>400km)

    Short journeys: London derbies, Lancashire derbies etc. ~ 10-20km
    Long journeys: Exeter to Newcastle, Plymouth to Hartlepool etc. ~ 400km+

    The signal is designed as an away team disadvantage:
    a long journey on limited rest is a genuine handicap.
    """
    df = df.copy()

    kms   = []
    loads = []

    # Normalisation thresholds
    MIN_KM  = 30    # below this = essentially neutral (London derby)
    MAX_KM  = 400   # above this = max travel burden

    for _, row in df.iterrows():
        km = get_travel_km(str(row["HomeTeam"]), str(row["AwayTeam"]))
        if km is None:
            kms.append(np.nan)
            loads.append(np.nan)
        else:
            kms.append(km)
            load = np.clip((km - MIN_KM) / (MAX_KM - MIN_KM), 0.0, 1.0)
            loads.append(round(float(load), 4))

    df["travel_km"]   = kms
    df["travel_load"] = loads
    return df


# ---------------------------------------------------------------------------
# 5. FIXTURE TIMING FLAGS
# ---------------------------------------------------------------------------

def compute_fixture_timing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add fixture timing signal columns to df.

    Columns added:
        day_of_week      — 0=Mon ... 6=Sun
        is_weekend       — True if Sat/Sun
        is_midweek       — True if Tue/Wed/Thu
        bank_holiday_flag — True if English bank holiday
        festive_flag     — True if Dec 20 – Jan 3 festive period
        timing_signal    — combined 0-1 signal. Higher = more disruptive timing.
                           0 = normal Saturday kickoff
                           1 = bank holiday / festive / unusual timing

    Timing matters because:
    - Midweek games have different crowd dynamics (fewer casual fans)
    - Bank holidays → full stadiums, but home advantage may be diluted
    - Festive congestion → tired squads, unpredictable results
    """
    df = df.copy()

    days        = []
    is_weekend  = []
    is_midweek  = []
    bh_flags    = []
    fest_flags  = []
    signals     = []

    for _, row in df.iterrows():
        dt = row["parsed_date"]
        if pd.isna(dt):
            days.append(np.nan); is_weekend.append(False); is_midweek.append(False)
            bh_flags.append(False); fest_flags.append(False); signals.append(0.0)
            continue

        dow  = dt.dayofweek    # 0=Mon, 5=Sat, 6=Sun
        bh   = is_bank_holiday(dt)
        fest = is_festive_period(dt)
        wknd = dow in (5, 6)
        midw = dow in (1, 2, 3)   # Tue/Wed/Thu

        # Timing disruption signal
        # Base: weekend = 0 (normal), midweek = 0.4
        # Modifier: bank holiday +0.3, festive +0.4
        sig = 0.0
        if midw:   sig += 0.4
        if bh:     sig += 0.3
        if fest:   sig += 0.4
        sig = round(min(sig, 1.0), 4)

        days.append(dow)
        is_weekend.append(wknd)
        is_midweek.append(midw)
        bh_flags.append(bh)
        fest_flags.append(fest)
        signals.append(sig)

    df["day_of_week"]       = days
    df["is_weekend"]        = is_weekend
    df["is_midweek"]        = is_midweek
    df["bank_holiday_flag"] = bh_flags
    df["festive_flag"]      = fest_flags
    df["timing_signal"]     = signals

    return df


# ---------------------------------------------------------------------------
# 6. MOTIVATION INDEX — derived from standings
# ---------------------------------------------------------------------------

# League tier sizes — approximate teams per tier
TIER_SIZES = {
    "E0": 20, "E1": 24, "E2": 24, "E3": 24, "EC": 24,
}

# Promotion/relegation zone sizes per tier
PROMO_SPOTS  = {"E0": 0, "E1": 3, "E2": 3, "E3": 3, "EC": 5}   # E0 = no promotion out of PL
RELEGATE_SPOTS = {"E0": 3, "E1": 3, "E2": 4, "E3": 4, "EC": 1}  # EC = 1 drops to regional


def compute_motivation_index(
    home_pos: Optional[int],
    away_pos: Optional[int],
    home_pts: Optional[int],
    away_pts: Optional[int],
    matches_played: Optional[int],
    tier: str = "E1",
) -> Dict[str, float]:
    """
    Compute motivation signals for both teams based on league standing.

    Returns dict with:
        home_motivation   — 0 (dead rubber) to 1 (title/survival decider)
        away_motivation   — 0 (dead rubber) to 1 (title/survival decider)
        motivation_gap    — home_motivation - away_motivation (-1 to 1)
        dead_rubber_flag  — True if both teams likely have nothing to play for
        six_pointer_flag  — True if both teams are in relegation/promotion battle

    Logic:
    - Early season (< 10 games): all games have equal motivation (0.5)
    - Top zone: promotion motivation (1.0 = in top 3, 0.8 = within 3 pts)
    - Bottom zone: relegation motivation (1.0 = in bottom 3, 0.8 = within 3 pts)
    - Mid-table with no chance of top/bottom: dead rubber (0.1 – 0.3)
    - Both in same zone: six-pointer flag
    """
    # Can't compute without standing data
    if home_pos is None or away_pos is None:
        return {
            "home_motivation":  0.5,
            "away_motivation":  0.5,
            "motivation_gap":   0.0,
            "dead_rubber_flag": False,
            "six_pointer_flag": False,
        }

    n_teams   = TIER_SIZES.get(tier, 22)
    promo     = PROMO_SPOTS.get(tier, 3)
    relegate  = RELEGATE_SPOTS.get(tier, 3)
    played    = matches_played or 0

    def team_motivation(pos: int, pts: int) -> float:
        if played < 10:
            return 0.5   # too early to mean much

        max_possible_pts = pts + (38 - played) * 3 if played < 38 else pts
        total_games = n_teams - 1  # standard season total

        # Promotion zone — top N positions
        if pos <= promo:
            return 1.0
        if pos <= promo + 3:
            return 0.8    # close to automatic

        # Playoff fringe (for leagues with playoffs)
        if tier in ("E1", "E2", "E3", "EC") and pos <= promo + 3 + 3:
            return 0.65   # playoff fringe

        # Relegation zone — bottom N positions
        if pos > n_teams - relegate:
            return 1.0    # in the drop zone
        if pos > n_teams - relegate - 3:
            return 0.85   # one bad run from it

        # Can't make top, can't reach bottom — dead rubber territory
        if played >= 30:
            if pos > promo + 8 and pos < n_teams - relegate - 4:
                return 0.2

        return 0.5   # default — something to play for, just not desperate

    h_mot = team_motivation(home_pos, home_pts or 0)
    a_mot = team_motivation(away_pos, away_pts or 0)

    dead_rubber = h_mot < 0.3 and a_mot < 0.3
    six_pointer = (
        (home_pos <= promo + 3 and away_pos <= promo + 3) or
        (home_pos >= n_teams - relegate - 3 and away_pos >= n_teams - relegate - 3)
    )

    return {
        "home_motivation":  round(h_mot, 3),
        "away_motivation":  round(a_mot, 3),
        "motivation_gap":   round(h_mot - a_mot, 3),
        "dead_rubber_flag": dead_rubber,
        "six_pointer_flag": six_pointer,
    }


def compute_motivation_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add motivation columns to df using position/points data from the engine.
    Requires home_position, away_position, home_points, away_points columns.

    Columns added:
        home_motivation   — 0-1
        away_motivation   — 0-1
        motivation_gap    — -1 to 1 (home advantage in motivation)
        dead_rubber_flag  — bool
        six_pointer_flag  — bool
    """
    df = df.copy()

    if "home_position" not in df.columns:
        df["home_motivation"]  = 0.5
        df["away_motivation"]  = 0.5
        df["motivation_gap"]   = 0.0
        df["dead_rubber_flag"] = False
        df["six_pointer_flag"] = False
        return df

    h_mots, a_mots, gaps, dead, sixp = [], [], [], [], []

    for _, row in df.iterrows():
        # Estimate matches played from date (approximate)
        season_start = pd.to_datetime(f"{row.get('season', '2024')[:4]}-08-01")
        try:
            played = max(0, (row["parsed_date"] - season_start).days // 7)
        except Exception:
            played = 0

        result = compute_motivation_index(
            home_pos=row.get("home_position"),
            away_pos=row.get("away_position"),
            home_pts=row.get("home_points"),
            away_pts=row.get("away_points"),
            matches_played=played,
            tier=row.get("tier", "E1"),
        )
        h_mots.append(result["home_motivation"])
        a_mots.append(result["away_motivation"])
        gaps.append(result["motivation_gap"])
        dead.append(result["dead_rubber_flag"])
        sixp.append(result["six_pointer_flag"])

    df["home_motivation"]  = h_mots
    df["away_motivation"]  = a_mots
    df["motivation_gap"]   = gaps
    df["dead_rubber_flag"] = dead
    df["six_pointer_flag"] = sixp

    return df


# ---------------------------------------------------------------------------
# Combined pipeline function — add all Phase 1 signals at once
# ---------------------------------------------------------------------------

def compute_phase1_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all Phase 1 external signal computations on a dataframe.
    Call this after the standard engine feature pipeline.

    Order matters:
      1. Referee stats (needs rolling history, no lookahead)
      2. Travel load (pure lookup, no state)
      3. Fixture timing (pure date calc, no state)
      4. Motivation (needs position/points from standings)

    Args:
        df: DataFrame that has already been through prepare_dataframe()
            Expects: parsed_date, HomeTeam, AwayTeam, FTR, tier
            Optional: Referee, HY, AY, HF, AF (for card/foul rates)
            Optional: home_position, away_position, home_points, away_points

    Returns:
        df with all Phase 1 signal columns added.
    """
    df = compute_referee_stats(df)
    df = compute_travel_load(df)
    df = compute_fixture_timing(df)
    # Motivation needs position/points — only add if columns present
    if "home_position" in df.columns:
        df = compute_motivation_df(df)
    else:
        df["home_motivation"]  = 0.5
        df["away_motivation"]  = 0.5
        df["motivation_gap"]   = 0.0
        df["dead_rubber_flag"] = False
        df["six_pointer_flag"] = False

    return df


# ---------------------------------------------------------------------------
# Gary context helper — single fixture signal summary
# ---------------------------------------------------------------------------

def get_signal_context(
    home_team: str,
    away_team: str,
    match_date: str,
    tier: str,
    df_history: Optional[pd.DataFrame] = None,
    home_pos: Optional[int] = None,
    away_pos: Optional[int] = None,
    home_pts: Optional[int] = None,
    away_pts: Optional[int] = None,
    matches_played: Optional[int] = None,
    referee: Optional[str] = None,
    ref_home_rate: Optional[float] = None,
) -> dict:
    """
    Build a plain-English signal context dict for Gary.

    This is called by GaryBrain._build_match_flags() to populate
    the external signal fields.

    Returns a dict Gary can use to enrich his briefing:
        travel_km, travel_load, timing_signal, bank_holiday_flag,
        festive_flag, is_midweek, motivation dict, referee_signal,
        plain_english summary strings
    """
    dt = pd.to_datetime(match_date)

    # Travel
    travel_km = get_travel_km(home_team, away_team)
    travel_load = None
    if travel_km is not None:
        travel_load = round(float(np.clip((travel_km - 30) / 370, 0.0, 1.0)), 3)

    # Timing
    bh    = is_bank_holiday(dt)
    fest  = is_festive_period(dt)
    dow   = dt.dayofweek
    midw  = dow in (1, 2, 3)
    timing_signal = min(
        (0.4 if midw else 0.0) + (0.3 if bh else 0.0) + (0.4 if fest else 0.0),
        1.0
    )

    # Motivation
    motivation = compute_motivation_index(
        home_pos=home_pos, away_pos=away_pos,
        home_pts=home_pts, away_pts=away_pts,
        matches_played=matches_played, tier=tier,
    )

    # Referee (use pre-computed stat if available)
    ref_info = None
    if referee and ref_home_rate is not None:
        bias_str = ""
        if ref_home_rate >= 0.55:
            bias_str = f"home bias (H win rate {ref_home_rate:.0%})"
        elif ref_home_rate <= 0.35:
            bias_str = f"low home rate ({ref_home_rate:.0%} — slightly away-friendly)"
        ref_info = {
            "name": referee,
            "home_rate": ref_home_rate,
            "bias_description": bias_str,
        }

    # Human-readable travel description
    travel_description = None
    if travel_km is not None:
        if travel_km < 50:
            travel_description = f"Local derby — {travel_km:.0f}km"
        elif travel_km < 150:
            travel_description = f"Regional trip — {travel_km:.0f}km"
        elif travel_km < 300:
            travel_description = f"Long away trip — {travel_km:.0f}km"
        else:
            travel_description = f"Marathon journey — {travel_km:.0f}km"

    # Timing description
    timing_parts = []
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    timing_parts.append(f"{day_names[dow]} fixture")
    if bh:
        timing_parts.append("bank holiday")
    if fest:
        timing_parts.append("festive period")
    if midw and not bh and not fest:
        timing_parts.append("midweek — lower attendance likely")

    return {
        "travel_km":           travel_km,
        "travel_load":         travel_load,
        "travel_description":  travel_description,
        "timing_signal":       timing_signal,
        "bank_holiday_flag":   bh,
        "festive_flag":        fest,
        "is_midweek":          midw,
        "day_of_week":         day_names[dow],
        "timing_description":  ", ".join(timing_parts),
        "motivation":          motivation,
        "referee":             ref_info,
    }


# ---------------------------------------------------------------------------
# DPOL param slot names — reference list for adding to LeagueParams/EngineParams
# ---------------------------------------------------------------------------
#
# Add these to LeagueParams (edgelab_dpol.py) and EngineParams (edgelab_engine.py):
#
#   # External Signal Layer — Phase 1 (all start at 0, DPOL activates them)
#   w_ref_signal:        float = 0.0   # referee home bias signal weight
#   w_travel_load:       float = 0.0   # away travel distance signal weight
#   w_timing_signal:     float = 0.0   # fixture timing disruption weight
#   w_motivation_gap:    float = 0.0   # home vs away motivation gap weight
#
# In compute_score_differential() (edgelab_engine.py), add:
#   sig_ref      = df["ref_signal"].fillna(0.5)    if "ref_signal"      in df.columns else 0.5
#   sig_travel   = df["travel_load"].fillna(0.0)   if "travel_load"     in df.columns else 0.0
#   sig_timing   = df["timing_signal"].fillna(0.0) if "timing_signal"   in df.columns else 0.0
#   sig_motivate = df["motivation_gap"].fillna(0.0)if "motivation_gap"  in df.columns else 0.0
#
#   # These lines are already commented-in as stubs — just uncomment and add weights:
#   # score_differential += params.w_ref_signal * (sig_ref - 0.5) * 2
#   # score_differential -= params.w_travel_load * sig_travel
#   # score_differential -= params.w_timing_signal * sig_timing
#   # score_differential += params.w_motivation_gap * sig_motivate
#

# ---------------------------------------------------------------------------
# CLI — test signals on a single fixture
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    home  = sys.argv[1] if len(sys.argv) > 1 else "Wigan Athletic"
    away  = sys.argv[2] if len(sys.argv) > 2 else "Leyton Orient"
    date  = sys.argv[3] if len(sys.argv) > 3 else "2026-04-12"
    tier  = sys.argv[4] if len(sys.argv) > 4 else "E2"

    print(f"\n  Signal context: {home} vs {away}  |  {date}  |  {tier}")
    print(f"  {'─'*60}")

    ctx = get_signal_context(
        home_team=home, away_team=away,
        match_date=date, tier=tier,
        home_pos=8, away_pos=14, home_pts=42, away_pts=35,
        matches_played=34,
    )

    print(f"  Travel        : {ctx['travel_description']}  (load={ctx['travel_load']})")
    print(f"  Timing        : {ctx['timing_description']}  (signal={ctx['timing_signal']})")
    print(f"  Bank holiday  : {ctx['bank_holiday_flag']}")
    print(f"  Festive       : {ctx['festive_flag']}")
    print(f"  Motivation    : Home={ctx['motivation']['home_motivation']}  "
          f"Away={ctx['motivation']['away_motivation']}  "
          f"Gap={ctx['motivation']['motivation_gap']}")
    print(f"  Dead rubber   : {ctx['motivation']['dead_rubber_flag']}")
    print(f"  Six-pointer   : {ctx['motivation']['six_pointer_flag']}")

    # Test travel distances for a few known fixtures
    print(f"\n  Travel distances:")
    tests = [
        ("Chelsea", "Arsenal"),
        ("Man City", "Wolves"),
        ("Plymouth", "Newcastle"),
        ("Exeter", "Hartlepool"),
        ("Wigan Athletic", "Leyton Orient"),
    ]
    for h, a in tests:
        km = get_travel_km(h, a)
        if km:
            print(f"    {a:<25} → {h:<20}  {km:.0f} km")
        else:
            print(f"    {a:<25} → {h:<20}  (coords not found)")
