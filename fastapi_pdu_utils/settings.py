day = 0
hour = 0
minute = 2
second_in = 0
# define default step and query function step
step = "2s"
step_func = "30s"

decimal_limit = 3
log = []


SSH_USER = "ubuntu"
SSH_KEY_PATH = "/home/ubuntu/myenv/myenv/ayposKeypair.pem"
STRESS_LEVELS = {
    "low": "stress -c 4 -t 30m",
    "medium": "stress -c 8 -t 30m",
    "high": "stress -c 12 -t 30m"
}
