""" Code to run icloud photo display """
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app
from src.pages import home_page
from src.pages import photo_page
from src.pages import sync_status
from src.pages import settings_page
from src.helpers.settings import Settings
from src.helpers.metrics import Metrics
from src.helpers.icloud import ICloud
from src.helpers.sync_thread import SyncHandler

app = Flask(__name__)
configs = Settings("/icloudpd", "configs.json")
prom_metrics = Metrics()
icloud_helper = ICloud(configs, prom_metrics)
sync_handler = SyncHandler(configs, icloud_helper)

home_page.add_home_page(app, prom_metrics, configs)
photo_page.add_photo_page(app, prom_metrics, configs)
sync_status.add_sync_status_pages(app, icloud_helpe, icloud_helperr)
settings_page.add_settings_pages(app, prom_metrics, configs)

# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})