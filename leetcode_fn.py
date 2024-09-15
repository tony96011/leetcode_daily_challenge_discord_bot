import requests
import time
from datetime import datetime, timedelta, timezone
import json
import logging

BASE_URL = "https://alfa-leetcode-api.onrender.com"
json_file = 'user_data.json'

logging.basicConfig(filename='leetcode_daily.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_user_data():
    with open(json_file, 'r') as file:
        return json.load(file)

def save_user_data(data):
    with open(json_file, 'w') as file:
        json.dump(data, file, indent=4)
        
def get_recent_24h_ac_submissions(submission_list):
    current_utc_time = datetime.now(timezone.utc)
    midnight_utc = current_utc_time.replace(hour=0, minute=0, second=0, microsecond=0)
    one_day_ago = midnight_utc - timedelta(days=1)

    recent_submissions = []
    for submission in submission_list:
        submission_time = int(submission.get('timestamp', 0))
        submission_time_utc = datetime.utcfromtimestamp(submission_time).replace(tzinfo=timezone.utc)
        
        if one_day_ago <= submission_time_utc <= current_utc_time:
            recent_submissions.append({
                'title': submission.get('title'),
                'statusDisplay': submission.get('statusDisplay'),
                'timestamp': submission_time_utc.strftime('%Y-%m-%d %H:%M:%S')
            })
    return recent_submissions

def extract_daily_problem_info(daily_problem):
    problem_info = {
        "questionLink": daily_problem["questionLink"],
        "date": daily_problem["date"],
        "questionTitle": daily_problem["questionTitle"],
        "difficulty": daily_problem["difficulty"],
    }
    return problem_info

def get_daily_problem():
    url = f"{BASE_URL}/daily"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"in get_daily_problem(), Failed to get daily problem: {response.status_code}")
        return None
    
def get_profile(username):
    url = f"{BASE_URL}/{username}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"in get_profile(), Failed to get profile for {username}: {response.status_code}")
        return None

def get_accepted_submissions(username):
    url = f"{BASE_URL}/{username}/acSubmission"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"in get_accepted_submissions(), Failed to get accepted submissions for {username}: {response.status_code}")
        return None

def get_user_daily_status(username, problem_info):   
    profile = get_profile(username)
    if profile:
        logging.info(f"Profile for {username}: {json.dumps(profile, indent=4)}")
    
        submissions = get_accepted_submissions(username)
        submission_list = submissions.get('submission', [])
    
        recent_ac_submissions = get_recent_24h_ac_submissions(submission_list)
        logging.info(f"Recent 24-hour submissions for {username}: {recent_ac_submissions}")
        flag = False
        for ac_submission in recent_ac_submissions:
            if ac_submission['title'] == problem_info['questionTitle']:
                flag = True
                logging.info(f"{username} finished the daily challenge.")
                return True
        if flag == False:
            logging.info(f"{username} has not finished the daily challenge.")
            return False

if __name__ == "__main__":
    user_data = load_user_data()
    daily_problem = get_daily_problem()
    if daily_problem:
        daily_problem_info = extract_daily_problem_info(daily_problem)
        logging.info(f"Daily problem info: {daily_problem_info}")
    else:
        logging.warning("No daily problem data available.")
        
    for username, details in user_data.items():
        user_data[username]['daily_completed'] = get_user_daily_status(username, daily_problem_info)
        logging.info(f"User {username} finished problem {daily_problem_info['questionTitle']}: {user_data[username]['daily_completed']}\n\n")
    save_user_data(user_data)