import os
import logging
from time import sleep
from redis import Sentinel
from kubernetes import client, config

logging.basicConfig(
    level=logging.DEBUG, 
    format="%(created)f %(asctime)s.%(msecs)03d [%(process)d] "
        "[%(name)s::%(module)s:%(funcName)s:%(lineno)d] "
        "%(levelname)s: %(message)s"
)

SENTINEL_NAME = os.getenv('SENTINEL_NAME', 'localhost')
SENTINEL_PORT = int(os.getenv('SENTINEL_PORT', 26379))
MASTER_SET_NAME = os.getenv('MASTER_SET_NAME', 'mymaster')
# сменить тест на default
NAMESPACE = os.getenv('NAMESPACE', 'test')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'redis-bitnami-master')

logging.info('load kube config')
config.load_kube_config()
v1 = client.CoreV1Api()

while True:
    sentinel = Sentinel([(SENTINEL_NAME, SENTINEL_PORT)], socket_timeout=0.5)
    try:
        redis_master_name = sentinel.discover_master(MASTER_SET_NAME)
        logging.info(f'redis_master_name is {redis_master_name[0]}')
    except Exception as e:
        logging.info(e)
    
    service = v1.read_namespaced_service(name = SERVICE_NAME, namespace = NAMESPACE)
    external_name = service.spec.external_name
    logging.info(f'Service ExternalName is {external_name}')

    if redis_master_name != external_name:
        logging.info(f'Change ExternalName')
        service_metadata = client.V1ObjectMeta(name=SERVICE_NAME)
        service_spec = client.V1ServiceSpec(type="ExternalName", external_name=redis_master_name)
        service_body = client.V1Service(
            metadata=service_metadata,
            spec=service_spec,
            kind='Service',
            api_version='v1'
            )

        try:
            service = v1.create_namespaced_service(namespace=NAMESPACE, body=service_body)
        except Exception as e:
            logging.info(e)

    sleep (5)



# redis_master_name = "redis-bitnami-node-1.redis-bitnami-headless.test.svc.cluster.local"
# namespace = "test"
# service_name = "redis-bitnami-master"

