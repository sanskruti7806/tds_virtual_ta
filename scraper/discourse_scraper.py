import requests
import json
from datetime import datetime

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in"

def fetch_post(post_id):
    url = f"{BASE_URL}/posts/{post_id}.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def scrape_discourse(start_id=100000, end_id=101000, output_file="data/discourse_posts.json"):
    posts = []

    for pid in range(start_id, end_id):
        post_data = fetch_post(pid)
        if post_data and "raw" in post_data:
            post_date = post_data.get("created_at", "")
            if "2025-01" <= post_date[:7] <= "2025-04":
                posts.append({
                    "id": pid,
                    "date": post_date,
                    "content": post_data["raw"],
                    "topic_id": post_data["topic_id"]
                })
        if pid % 50 == 0:
            print(f"Checked up to post {pid}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(posts)} posts to {output_file}")

if __name__ == "__main__":
    scrape_discourse()
