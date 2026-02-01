import requests
import json
import time
import os
import uuid
from datetime import datetime

# Configuration
# Inside GitHub Actions service containers, localhost ports are mapped
GREEN_URL = "http://localhost:8000"
PURPLE_URL = "http://localhost:8001" 

# Use the Env Var for flexibility, else use the hardcoded ID we just setup
# This Agent ID is for the PURPLE agent (the one being tested)
PARTICIPANT_ID = os.environ.get("AGENT_ID", "019c17ab-21f2-78a3-a404-24054d5c73b8")

def run_benchmark():
    print(f"🚀 Starting Benchmark for Participant: {PARTICIPANT_ID}")
    
    # Wait for services to be ready
    for i in range(12): # Wait up to 60s
        try:
            requests.get(f"{GREEN_URL}/health")
            requests.get(f"{PURPLE_URL}/health")
            print("✅ Services are up!")
            break
        except:
            print(f"⏳ Waiting for services... ({i*5}s)")
            time.sleep(5)
            
    # 1. Get Challenges
    try:
        resp = requests.get(f"{GREEN_URL}/challenges")
        challenges = resp.json()
        print(f"✅ Found {len(challenges)} challenges.")
    except Exception as e:
        print(f"❌ Failed to reach Green Agent: {e}")
        return

    # 2. Iterate and Solve
    samples = []
    total_score = 0
    total_sim = 0
    passed_count = 0
    
    for chal in challenges:
        cid = chal["id"]
        
        # Get Code from Green
        try:
            details = requests.get(f"{GREEN_URL}/challenges/{cid}").json()
            vuln_code = list(details["files"].values())[0] # Take first file
        except: continue

        # Solve via Purple
        try:
            p_resp = requests.post(f"{PURPLE_URL}/solve", json={"task": "vulnerable.py", "content": vuln_code})
            fixed_code = p_resp.json()["response"]
        except:
            fixed_code = vuln_code # Fail closed

        # Submit to Green
        try:
            submission = {
                "challenge_id": cid,
                "agent_id": PARTICIPANT_ID,
                "patched_files": {"vulnerable.py": fixed_code}
            }
            result = requests.post(f"{GREEN_URL}/submit", json=submission).json()
            
            # Extract Metrics
            sec_score = result.get("security_score", 0.0)
            sim_score = result.get("similarity_score", 0.0)
            is_sec = result.get("is_secure", False)
            
            if is_sec: passed_count += 1
            total_score += sec_score
            total_sim += sim_score
            
            # Record Sample
            samples.append({
                "challenge_id": cid,
                "status": "success" if is_sec else "failure",
                "is_secure": is_sec,
                "security_score": sec_score,
                "similarity_score": sim_score,
                "functional_tests_passed": result.get("functional_tests_passed", False),
                "duration_ms": 1000 # Mock duration
            })
            
            print(f"  Result {cid}: Secure={is_sec}, Score={sec_score:.2f}")
            
        except Exception as e:
            print(f"  ❌ Error processing {cid}: {e}")

    # 3. Generate Final JSON (Nested Format)
    count = len(challenges)
    final_json = {
        "participants": {
            "agent": PARTICIPANT_ID
        },
        "results": [
            {
                "metrics": {
                    "total_challenges": count,
                    "security_score_avg": total_score / count if count else 0,
                    "similarity_score_avg": total_sim / count if count else 0,
                    "functional_tests_passed": passed_count,
                    "challenges_attempted": count
                },
                "samples": samples
            }
        ]
    }
    
    # Save to file
    out_dir = "results" 
    os.makedirs(out_dir, exist_ok=True)
    filename = f"Avayam_AutoRun_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(f"{out_dir}/{filename}", "w") as f:
        json.dump(final_json, f, indent=2)
        
    print(f"✅ Saved results to {out_dir}/{filename}")

if __name__ == "__main__":
    run_benchmark()
