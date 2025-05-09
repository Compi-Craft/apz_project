import time
import json
import consul
import os

CONSUL_HOST = os.environ.get("CONSUL_HOST", "consul")
CONSUL_PORT = int(os.environ.get("CONSUL_PORT", 8500))
CONFIG_FILE = os.environ.get("CONFIG_FILE", "/app/config.json")

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def push_to_consul(config):
    c = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
    for key, value in config.items():
        print(f"Pushing {key}: {value}")
        c.kv.put(key, value)

if __name__ == "__main__":
    print("Waiting for Consul to be available...")
    time.sleep(5)
    
    config = load_config()
    push_to_consul(config)
    
    print("All keys pushed to Consul!")