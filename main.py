try:
    from termcolor import cprint
except ImportError:
    print('You didn\'t install termcolor yet. Try "pip3 install termcolor"')
    exit(0)

import requests
import time

appid = '29ff6adee62dc3c1d403996b65b559b1'
cnt_day_forecast = 9
max_rank = 50
min_climate_index = 60
min_temp = 15
max_temp = 24


def info(text):
    cprint(text, 'green')


def error(text):
    cprint(text, 'red')


def request_json(site):
    try:
        response = requests.get(site)
        if response.status_code != requests.codes.ok:
            error('Can\'t download data.')
            response.raise_for_status()
            exit(0)
        else:
            return response.json()
    except requests.ConnectionError:
        error(f'Connection error, can\'t download data from {site}')
        exit(0)


def download_data():
    info('Started downloading Drobinin`s json...')
    cities_data = request_json('http://drobinin.com/lksh/cities.json')
    info('Finished.')
    rank_climate_optimal_cities = []
    for city in cities_data:
        if (city['Rank'] <= max_rank and
                city['Climate Index'] >= min_climate_index):
            rank_climate_optimal_cities.append(city)
    return rank_climate_optimal_cities


def is_not_comfort_temp(city, day):
    return (city['list'][day]['temp']['min'] < min_temp or
            city['list'][day]['temp']['max'] > max_temp)


def get_date(city, day, format):
    return time.strftime(format, time.localtime(city['list'][day]['dt']))


def get_optimal_cities(rank_climate_optimal_cities):
    optimal_cities = {}
    info('Start getting info about cities...')
    for city in rank_climate_optimal_cities:
        info(f'Getting info about {city["City"]}')
        request = (f'http://api.openweathermap.org/data/2.5/forecast/daily' +
                   f'?q={city["City"]}&cnt={cnt_day_forecast}&appid={appid}' +
                   '&units=metric')
        city_data = request_json(request)
        for day in range(cnt_day_forecast):
            day_of_week = get_date(city_data, day, '%a')

            if day_of_week == 'Fri':
                global nearest_days_dates
                nearest_days_dates = {
                    'Friday': get_date(city_data, day, '%d.%m.%y'),
                    'Saturday': get_date(city_data, day + 1, '%d.%m.%y'),
                    'Sunday': get_date(city_data, day + 2, '%d.%m.%y')}

                if (is_not_comfort_temp(city_data, day) or
                        is_not_comfort_temp(city_data, day + 1) or
                        is_not_comfort_temp(city_data, day + 2)):
                    break

                to_export = {'Friday': city_data['list'][day],
                             'Saturday': city_data['list'][day + 1],
                             'Sunday': city_data['list'][day + 2]}

                if len(to_export) > 0:
                    optimal_cities[city['City']] = to_export
                break
    info('Finished.')
    return optimal_cities


def make_html(outf, optimal_cities):
    def get(city, day, param, spec_weather_temp_param):
        if param == 'temp':
            return optimal_cities[city][day][param][spec_weather_temp_param]
        elif param == 'weather':
            return optimal_cities[city][day][param][0][spec_weather_temp_param]
        else:
            return optimal_cities[city][day][param]

    info('Making HTML-file...')
    outf.write('''<!DOCTYPE html>
<html>
<head>
    <title>May Holidays</title>
</head>
<body>

<h1>Optimal Cities for travel</h1>

<style>
    table, td, th {
        border: 1px solid #dddddd;
        text-align: left;
        padding: 8px;
    }
</style>

<table style='width:60%'>''' + f'''
    <tr>
        <th>City</th>
        <th>Weather forecast on Friday {nearest_days_dates['Friday']}</th>
        <th>Weather forecast on Saturday {nearest_days_dates['Saturday']}</th>
        <th>Weather forecast on Sunday {nearest_days_dates['Sunday']}</th>
    </tr>
''')
    for city in optimal_cities:
        outf.write(f'''
    <tr>
        <th> {city} </th>''')
        weekends = ['Friday', 'Saturday', 'Sunday']

        for weekend in weekends:
            outf.write(f'''
            <th>
            Morning temperature: {get(city, weekend, 'temp', 'morn')}&deg;C<br>
            Day temperature: {get(city, weekend, 'temp', 'day')}&deg;C<br>
            Evening temperature: {get(city, weekend, 'temp', 'eve')}&deg;C<br>
            Night temperature: {get(city, weekend, 'temp', 'night')}&deg;C<br>
            Pressure: {get(city, weekend, 'pressure', '')} hPa<br>
            Humidity: {get(city, weekend, 'humidity', '')} %<br>
            Cloudiness: {get(city, weekend, 'clouds', '')} %<br>
            Weather: {get(city, weekend, 'weather', 'main')} <br>
            Wind Speed: {get(city, weekend, 'speed', '')} meter/sec<br>
            </th>''')
        outf.write('''
    </tr>
    ''')

    outf.write('''
</table>

</body>
</html>
''')
    info('Finished.')


def main():
    data = download_data()
    optimal_cities = get_optimal_cities(data)
    with open('optimal_cities_to_travel.html', 'w') as outf:
        make_html(outf, optimal_cities)


if __name__ == '__main__':
    main()
