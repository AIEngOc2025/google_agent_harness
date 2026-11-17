import http.server
import json
import socketserver
import sys


class MockProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        """
        @definition : traite les requetes POST pour simuler la reponse du modele
        @args/params : aucun (acces via self)
        @return : None
        """
        # lecture des donnees envoyees
        content_length = int(self.headers.get("Content-Length", 0))
        _ = self.rfile.read(content_length)

        # creation de la reponse OpenAI attendue par le probe
        response_payload = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "OK",
                    }
                }
            ]
        }
        body = json.dumps(response_payload).encode("utf-8")

        # envoi de la reponse HTTP 200
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        """
        @definition : traite les requetes GET de verification d'etat
        @args/params : aucun (acces via self)
        @return : None
        """
        # envoi d'un statut OK simple
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        """
        @definition : desactive la journalisation verbeuse sur stdout
        @args/params : format (str), *args
        @return : None
        """
        # filtrage des messages de logs
        pass


def start_server(port: int = 8000) -> None:
    """
    @definition : demarre le serveur proxy mock sur toutes les interfaces
    @args/params : port (int) port d'ecoute
    @return : None
    """
    # configuration de la reutilisation d'adresse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", port), MockProxyHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    start_server(port_arg)
