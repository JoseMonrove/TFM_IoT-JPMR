import time
import json
import logging
from threading import Lock
import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)

# ---------- credenciales ThingsBoard ----------
TB_TOKEN = "pk7ubsf8pu8xlzwn9gbd"
TB_HOST  = "mqtt.thingsboard.cloud"
TB_PORT  = 1883
TB_TOPIC = "v1/devices/me/telemetry"

_lock = Lock()

_client = mqtt.Client(client_id=f"cm5_{int(time.time())}", protocol=mqtt.MQTTv311)
_client.username_pw_set(TB_TOKEN)

_client.connect(TB_HOST, TB_PORT, keepalive=60)
_client.loop_start()

def publish_telemetry(payload: dict) -> None:
    """Envía un dict como telemetría JSON a ThingsBoard Cloud."""
    try:
        with _lock:
            _client.publish(TB_TOPIC, json.dumps(payload), qos=0, retain=False)
    except Exception:
        log.error("Error publicando en ThingsBoard", exc_info=True)
