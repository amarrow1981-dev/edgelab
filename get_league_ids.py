import requests
import sys

api_key = sys.argv[1]
headers = {'x-apisports-key': api_key}

countries = [
    'France', 'Portugal', 'Turkey', 'Greece', 'Russia', 'Ukraine',
    'Austria', 'Switzerland', 'Czech-Republic', 'Croatia', 'Serbia',
    'Poland', 'Romania', 'Denmark', 'Norway', 'Sweden'
]

for country in countries:
    r = requests.get(
        'https://v3.football.api-sports.io/leagues',
        headers=headers,
        params={'country': country, 'type': 'league'}
    )
    data = r.json()
    leagues = data.get('response', [])
    if leagues:
        print(f'\n{country}:')
        for l in leagues:
            lg = l['league']
            print(f'  {lg["id"]:4d}  {lg["name"]}')
    else:
        print(f'\n{country}: no results')
