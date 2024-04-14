from multiprocessing import Process, Queue
from loguru import logger
import sudoku_problem
import time


def setup_logger():
    config = {
        "handlers": [
            {"sink": "file.log", "enqueue": True, "level": "INFO"},
            # Sie können weitere Sinks hinzufügen, wenn nötig
        ],
    }
    logger.configure(**config)


class AttributAgent:
    def __init__(self, agent_id, log_queue, name, connections):
        self.agent_id = agent_id  # ID des Agenten
        self.name = name  # Name des Agenten
        self.log_queue = log_queue  # Queue für Log-Nachrichten
        self.connections = connections  # Ein Dictionary von Verbindungen zu anderen Agenten
        self.constraints = []  # Liste von Constraints zu anderen Agenten
        self.all_domains = []  # Liste aller möglichen eigenen Domains
        self.nogood_dict = []  # Dictionary mit No-goods Key: Constraint-String Value: Liste von no-good Domains

        self.message_handlers = {
            "ok": self.ok,
            "check": self.check,
            "nogood": self.nogood,
            "None": self.stop
        }

    def log(self, message):
        # Sendet Log-Nachrichten an die Log-Queue
        self.log_queue.put(f"Agent {self.agent_id} ({self.name}) - {message}")

    def send_message(self, recipient_queue, message):
        # Sendet Nachrichten an andere Agenten
        recipient_queue.put((self.agent_id, message))

    def receive_message(self, message):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        handler = self.message_handlers.get(message)
        if handler:
            handler()  # Rufe die zugehörige Funktion auf
        else:
            self.log(f"Received unknown message type: {message}")

    def update_domains(self):
        # Aktualisiert die Liste der validen Domains
        self.agent_view = [domain for domain in self.all_domains if self.is_valid(domain)]
        self.log(f"Updated domains to: {self.agent_view}")


    def check(self):
        # Überprüft, ob es eine Möglichkeit gibt die Constraints zu erfüllen mit
        # den aktuellen Domains-String und fragt die anderen nicht im Domain-String
        # enthaltenen Agenten, ob die Auswahl gültig ist
        if any(domain in self.nogood_list for domain in self.agent_view):
            self.log("Conflict found in nogood list.")
        else:
            self.log("No conflicts with nogood list.")

    def run(self):
        # Hauptloop des Agenten, um Nachrichten zu empfangen
        while True:
            message = self.log_queue.get()  # Warten auf eine neue Nachricht
            if message is None:
                self.log("Stopping agent.")
                break  # Beenden, wenn die Nachricht None ist
            sender_id, msg = message
            self.log(f"Received message from agent {sender_id}: {msg}")
            self.receive_message(msg)


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
