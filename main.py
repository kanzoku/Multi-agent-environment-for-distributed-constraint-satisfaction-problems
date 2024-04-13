from multiprocessing import Process, Queue
from loguru import logger
import time


def setup_logger():
    config = {
        "handlers": [
            {"sink": "file.log", "enqueue": True, "level": "INFO"},
            # Sie können weitere Sinks hinzufügen, wenn nötig
        ],
    }
    logger.configure(**config)


def agent_attribut(log_queue, agent_id):
    while True:
        message = log_queue.get()  # Warten auf eine neue Nachricht
        if message is None:
            break  # Beenden, wenn die Nachricht None ist
        # Log-Nachricht verarbeiten
        logger.info(f"Agent {agent_id} - {message}")


if __name__ == "__main__":
    setup_logger()
    log_queue = Queue()

    # Agent-Prozesse erstellen
    agents = [Process(target=agent_attribut, args=(log_queue, i)) for i in range(5)]

    # Agent-Prozesse starten
    for agent in agents:
        agent.start()

    # Log-Nachrichten senden
    for _ in range(10):
        log_queue.put("Eine wichtige Nachricht")

    # Agent-Prozesse beenden
    for _ in agents:
        log_queue.put(None)

    # Warten, bis alle Agent-Prozesse beendet sind
    for agent in agents:
        agent.join()