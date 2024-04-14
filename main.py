from multiprocessing import Process, Queue
from loguru import logger
import sudoku_problem
import time


def setup_logger():
    config = {
        "handlers": [
            {"sink": "file.log", "enqueue": True, "level": "INFO"},
        ],
    }
    logger.configure(**config)


class AttributAgent(Process):
    def __init__(self, agent_id, log_queue, name, connections, constraints, all_domains):
        super(AttributAgent, self).__init__()
        self.agent_id = agent_id  # ID des Agenten
        self.name = name  # Name des Agenten
        self.log_queue = log_queue  # Queue für Log-Nachrichten
        self.connections = connections  # Ein Dictionary von Verbindungen(Pipes) zu anderen Agenten
        self.constraints = constraints  # Dict von Constraints zu anderen Agenten
        self.all_domains = all_domains  # Liste aller möglichen eigenen Domains
        self.nogood_dict = dict()  # Dictionary mit No-goods Key: Constraint-String Value: Liste von no-good Domains
        self.agent_view = dict()  # Dictionary mit den Domains, die der Agent betrachtet

        self.message_handlers = {
            "ok": self.ok,
            "check": self.check,
            "nogood": self.nogood,
            "kill": self.stop,
            "startagent": self.start
        }

    def log(self, message):
        # Sendet Log-Nachrichten an die Log-Queue
        self.log_queue.put(f"Agent {self.agent_id} ({self.name}) - {message}")
        # TODO: Implementieren der Funktion, die Log-Nachrichten an die Log-Queue/Log-Agent sendet

    def send_message(self, recipient_queue, message):
        # Sendet Nachrichten an andere Agenten
        recipient_queue.put((self.agent_id, message))
        # TODO: Implementieren der Funktion, die Nachrichten an andere Agenten sendet

    def receive_message(self, message_data):
        # Behandelt eingehende Nachrichten mithilfe des Dictionaries
        header, message = message_data
        handler = self.message_handlers.get(header)
        if handler:
            handler(message)  # Rufe die zugehörige Funktion auf
        else:
            self.log(f"Received unknown message type: {header} with message: {message}")

    def nogood(self, message):
        # Aktualisiert das Dictionary der No-goods und probiert die Constraints mit einer neuen Domain
        # zu erfüllen ansonsten wird eine "nogood"-Nachricht an den vorherigen Agenten gesendet
        self.agent_view = [domain for domain in self.all_domains if self.is_valid(domain)]
        self.log(f"Updated domains to: {self.agent_view}")
        # TODO: Implementieren der Funktion, die die Domains in nogood schiebt/aktualisiert
        #  und entweder andere Domain überprüft oder an vorherigen Agenten nogood sendet

    def ok(self, message):
        # Bestätigt, dass die Constraints in dem Pfad erfüllt sind
        self.log("Received OK message.")
        # TODO: Funktionalität implemntieren und Konzept überlegen

    def check(self, message):
        # Überprüft, ob es eine Möglichkeit gibt die Constraints zu erfüllen mit
        # den aktuellen Domains-String und fragt die anderen nicht im Domain-String
        # enthaltenen Agenten, ob die Auswahl gültig ist
        if any(domain in self.nogood_dict for domain in self.agent_view):
            self.log("Conflict found in nogood list.")
        else:
            self.log("No conflicts with nogood list.")
    # TODO: Funktion muss noch implementiert werden, dabei geschaut werden ob es eine Domain gibt,
    #  die die bereits gesetzten Constraints erfüllt und entsprechend nachfolgende Agenten anspricht

    def stop(self, message):
        # Beendet den Agenten
        self.log("Received kill message.")
        self.log("Stopping agent.")
        self.join()
        self.kill()

    def startagent(self, message):
        # Startet den Agenten
        self.log("Received start message.")
        self.log("Starting agent.")
        self.solve("")

    def solve(self, domainString):
        # Löst alle Constraints mit den gegebenen Domains und findet valide Lösungsmenge
        fulfillments = []
        assignments = domainString.split(';')
        for assignment in assignments:
            if assignment.strip():  # Überprüfe, ob die Zuweisung leer ist
                var, value = assignment.split('=')
                var = var.strip()  # Entferne vermeintliche Leerzeichen
                value = int(value.strip())  # Konvertiere Wert in Integer

                # Überprüfe, ob die Variable in den Constraints enthalten ist
                if var in self.constraints:
                    constraint_value = self.constraints[var]
                    if value != constraint_value:  # Überprüfe auf Ungleichheit
                        fulfillments.append(value)  # Füge zu den Erfüllungen hinzu
        for domain in self.all_domains:
            if domain not in fulfillments:
                self.agent_view[domainString].append(domain)
    # TODO: Implementieren der Funktion senden von Check an andere Agenten die
    #  Constraint haben aber noch nicht gesetzt sind


    def run(self):
        # Hauptloop des Agenten, um Nachrichten zu empfangen und verarbeiten
        while True:
            message = self.log_queue.get()  # Warten auf eine neue Nachricht
            sender_id, msg = message
            self.log(f"Received message from agent {sender_id}: {msg}")
            self.receive_message(msg)


if __name__ == "__main__":
    setup_logger()
    log_queue = Queue()
    # TODO Initialisierung der Agenten und des Sodoku-Problems und Start-Message an den ersten Agenten senden
