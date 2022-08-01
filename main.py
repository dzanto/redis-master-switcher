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
KUBECONFIG = os.getenv('KUBECONFIG', '/code/config/kubeconfig')

logging.info('load kube config')
config.load_kube_config(config_file=KUBECONFIG)
# config.load_incluster_config()
v1 = client.CoreV1Api()

external_name = ""

while True:
    sentinel = Sentinel([(SENTINEL_NAME, SENTINEL_PORT)], socket_timeout=0.5)
    try:
        redis_master_name = sentinel.discover_master(MASTER_SET_NAME)[0]
        logging.info(f'redis_master_name is {redis_master_name}')
    except Exception as e:
        logging.info(e)
    
    services_list = v1.list_namespaced_service(namespace = NAMESPACE)

    service_exist = False
    for service in services_list.items:
        # logging.info(service.metadata.name)
        if SERVICE_NAME == service.metadata.name:
            service_exist = True

    if service_exist == True:
        service = v1.read_namespaced_service(name = SERVICE_NAME, namespace = NAMESPACE)
        external_name = service.spec.external_name
        logging.info(f'Service ExternalName is {external_name}')

    if service_exist == False:
        logging.info(f'Update service {SERVICE_NAME}')
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
        continue

    if redis_master_name != external_name:
        logging.info(f'Update service {SERVICE_NAME}')
        service_metadata = client.V1ObjectMeta(name=SERVICE_NAME)
        service_spec = client.V1ServiceSpec(type="ExternalName", external_name=redis_master_name)
        service_body = client.V1Service(
            metadata=service_metadata,
            spec=service_spec,
            kind='Service',
            api_version='v1'
            )
        try:
            service = v1.patch_namespaced_service(name=SERVICE_NAME,namespace=NAMESPACE, body=service_body)
        except Exception as e:
            logging.info(e)

    sleep (20)



# redis_master_name = "redis-bitnami-node-1.redis-bitnami-headless.test.svc.cluster.local"
# namespace = "test"
# service_name = "redis-bitnami-master"

