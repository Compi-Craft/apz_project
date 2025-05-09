import consul
import time
consul_client = consul.Consul(host="consul")


def get_members(key):
    data = None
    while data is None:
        index, data = consul_client.kv.get(key)
        time.sleep(5)
    return data['Value'].decode().split(",")


def register_service(service_name, service_id, service_port):
    """Реєстрація сервісу в Consul."""
    consul_client.agent.service.register(
        service_name,
        service_id=service_id,
        port=service_port,
        tags=["api"],
        check=consul.Check.http(f'http://{service_id}:{service_port}/health', interval="10s")
    )

REDIS_SERVERS = get_members('redis/token_servers')
