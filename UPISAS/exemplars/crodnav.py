import logging
from pathlib import Path
from UPISAS.exemplar import Exemplar

logging.getLogger().setLevel(logging.INFO)

class CrowdnavFAS2024(Exemplar):
    def __init__(self, auto_start=False):
        crowdnav_docker_kwargs = {
            "name": "crowdnav",
            "build": {"context": "./crowdnav", "dockerfile": "Dockerfile"},
            "depends_on": ["kafka"],
            "networks": ["fas-net"],
            "volumes": {"csvexchangevolume": {"bind": "/app/data/", "mode": "rw"}},
        }

        super().__init__(
            api_url=None,
            docker_kwargs=crowdnav_docker_kwargs,
            auto_start=auto_start
        )

    def start_run(self):
        self.exemplar_container.exec_run(
            cmd="python app.py",
            detach=True
        )


class Kafka(Exemplar):
    def __init__(self, auto_start=False):
        kafka_docker_kwargs = {
            "name": "kafka",
            "image": "spotify/kafka",
            "environment": {
                "ADVERTISED_HOST": "kafka",
                "ADVERTISED_PORT": "9092"
            },
            "networks": ["fas-net"]
        }

        super().__init__(
            api_url=None,
            docker_kwargs=kafka_docker_kwargs,
            auto_start=auto_start
        )

    def start_run(self):
        logging.info("Kafka container is running.")


class HTTPServer(Exemplar):
    def __init__(self, auto_start=False):
        http_server_docker_kwargs = {
            "name": "http-server",
            "build": {"context": "./api", "dockerfile": "Dockerfile"},
            "depends_on": ["kafka"],
            "networks": ["fas-net"],
            "ports": {"8080": "8080"}
        }

        super().__init__(
            api_url="http://localhost:8080",
            docker_kwargs=http_server_docker_kwargs,
            auto_start=auto_start
        )

    def start_run(self):
        self.exemplar_container.exec_run(
            cmd="node server.js",
            detach=True
        )


if __name__ == "__main__":
    kafka = Kafka(auto_start=True)
    crowdnav = CrowdnavFAS2024(auto_start=True)
    http_server = HTTPServer(auto_start=True)

    kafka.start_run()
    crowdnav.start_run()
    http_server.start_run()
