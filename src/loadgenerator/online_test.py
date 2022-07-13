import os
import time
import json
import random
import requests
import itertools

import numpy as np


HOST_URL = os.getenv("FRONTEND_URL", "http://ak-frontend.boutique:80")
LOCUST_URL = os.getenv("LOCUST_URL", "http://0.0.0.0:8089")
# Percentage of variance to add to the number of users selected
GAUSSIAN_NOISE = os.getenv("GAUSSIAN_NOISE_VARIANCE_PERCENTAGE")

SCENARIOS_FOLDER = '/scenarios'

N_USER_DOMAIN = (10, 700)
SPAWN_RATE_DOMAIN = (1.0, 700.0)
DURATION_DOMAIN = (10, 240)  # minutes


def _pick_random_spawn_rate():
    lower, upper = SPAWN_RATE_DOMAIN
    return lower + (random.random() * (upper - lower))


def _pick_duration(is_test_to_be_stopped, n_users):
    # high intensity workloads longs just a few minutes normally
    duration = random.randint(*DURATION_DOMAIN)
    if n_users > 200 or is_test_to_be_stopped:
        while duration > 15:
            duration = random.randint(*DURATION_DOMAIN)
    return duration


def stop_test():
    response = requests.get(f'{LOCUST_URL}/stop')
    print(f'Response is: {str(response.content)}')


def start_test(spawn_rate, n_users):
    data = {'user_count': n_users,
            'spawn_rate': spawn_rate,
            'host': HOST_URL}
    response = requests.post(f'{LOCUST_URL}/swarm', data=data)
    print(f'Response is: {response.json()}')


def random_test():
    print("Starting random test")
    while 1:
        n_users = random.randint(*N_USER_DOMAIN)
        spawn_rate = _pick_random_spawn_rate()
        is_test_to_be_stopped = random.choices([1, 0], (0.01, 0.99))[0]
        duration = _pick_duration(is_test_to_be_stopped, n_users)

        # with 1% probability we stop the test
        if is_test_to_be_stopped:
            print(f"Stopping test for {duration} minutes")
            stop_test()
        else:
            print(f"Starting test with users: {n_users}, "
                  f"spawn_rate: {spawn_rate} for {duration} minutes")
            start_test(spawn_rate, n_users)
        time.sleep(duration * 60)


def run_test(scenario):
    print(f"Starting scenario {scenario}")
    week = 1
    for day in itertools.cycle(range(1, 8)):
        if day == 1:
            print(f'Week {week}')
            week += 1
        print(f"Day {day}")
        for step in scenario:
            step_days = step.get('days', [day])
            if day not in step_days:
                continue
            spawn_rate = step['spawn_rate']
            n_users = step['n_users']
            if GAUSSIAN_NOISE is not None:
                scale = np.sqrt(n_users * (float(GAUSSIAN_NOISE) / 100))
                n_users = int(np.random.normal(n_users, scale=scale))
                if n_users <= 0:
                    print(f"WARNING: number of users {n_users}. Setting to 1")
                    n_users = 1
            duration = step['duration']

            print(f"Starting test with users: {n_users}, "
                  f"spawn_rate: {spawn_rate} for {duration} minutes")
            start_test(spawn_rate, n_users)
            time.sleep(duration * 60)


def run():
    scenario_filename = os.getenv('SCENARIO_JSON')
    if scenario_filename:
        scenario_path = os.path.join(SCENARIOS_FOLDER, scenario_filename)
        try:
            print(f"Opening scenario {scenario_filename} at {scenario_path}")
            with open(scenario_path, 'r') as infile:
                scenario = json.load(infile)
        except json.JSONDecodeError as e:
            print(f'ERROR: Unable to load the json from {scenario_path}. Error was: {e.msg}')
        run_test(scenario)
    else:
        random_test()


if __name__ == '__main__':
    print("Welcome to the online Locust load generator")
    run()
