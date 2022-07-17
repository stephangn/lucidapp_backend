
# Demo des LUCID-APP Backend

Die LUCID-APP ist der Prototyp einer Zollsoftware zur DLT-gestützten Abwicklung von Importprozessen.


## Installation

Ausführen per Docker (vorausgesetzt ist eine aktuelle Docker Installation)

Bauen des Container 

    docker compose build 

Starten des Containers

    docker compose up -d 

Importieren der Testdaten 

    docker-compose exec web python manage.py loaddata database_demo.json


Bei Problemen anzeigen der Server-Logs 

    docker compose logs -f 

Anschließend ist das Backend unter [localhost:8000](http://localhost:8000) erreichbar


## Hinweise 

\* Die in den verlinkten Testdaten sichtbaren Dokumente sind nicht zu sehen. Erst neu angelegte Dokumente sind nicht abrufbar.

\* Mögliche Dokumente sind unter Testdaten abgelegt

\* Nach dem Beenden und löschen des Containers und des Volumes sind die Daten zu Entwicklungszwecken zurückgesetzt

Ein Backup der daten kann erstellt werden 

    docker-compose exec web python manage.py dumpdata --indent 2 > database.json






