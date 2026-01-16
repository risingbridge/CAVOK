from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from datetime import timedelta, datetime, timezone
from email.utils import parsedate_to_datetime
import logging
import async_timeout
from avwx import Metar, Taf

from .const import DOMAIN, USER_AGENT

# Vi har ingen plattformer (sensorer) ennå
PLATFORMS: list[str] = ["sensor"]

LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:  # Legacy
    # Gammelt oppsett - returner bare True. Brukes hvis integrasjonen legges til via configuration.yaml, og det
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    icao = entry.data["icao"]
    LOGGER.debug(f"Starting CAVOK for airport: {icao}")

    STANDARD_INTERVAL = timedelta(minutes=10)

    async def get_api_data():
        session = async_get_clientsession(hass)
        url = "https://api.met.no/weatherapi/tafmetar/1.0/"
        params = {"icao": icao, "content": "metar", "content_type": "text/plain"}
        headers = {"User-Agent": USER_AGENT}
        try:
            async with async_timeout.timeout(10):
                response = await session.get(url, params=params, headers=headers)
                LOGGER.debug("Fetching new data from met.api.no")
                if response.status == 404:
                    debug_url_str = f"{url}?icao={params['icao']}&content={params['content']}&content_type={params['content_type']}"
                    LOGGER.debug(f"🚀 Sender request til: {debug_url_str}")
                    raise UpdateFailed("Error 404, wrong airport?")
                response.raise_for_status()

                # Expires-logikken
                expires_header = response.headers.get("Expires")
                if expires_header:
                    try:
                        expire_time = parsedate_to_datetime(expires_header)
                        now_time = datetime.now(timezone.utc)
                        delay_time = expire_time - now_time
                        if delay_time.total_seconds() < 60:
                            new_interval = timedelta(minutes=2)
                        else:
                            new_interval = delay_time
                        coordinator.update_interval = new_interval
                        LOGGER.debug(f"CAVOK Update Time: {new_interval}")
                    except Exception:
                        coordinator.update_interval = STANDARD_INTERVAL
                # Behandle data
                raw_text = await response.text()
                stripped_text = raw_text.strip()

                if not stripped_text:
                    raise UpdateFailed("Empty response from Met.no")
                lines = stripped_text.splitlines()
                result = lines[-1]
                LOGGER.debug(f"Fetched raw data: {result}")
                try:
                    metar_object = await hass.async_add_executor_job(
                        Metar.from_report, result
                    )
                    LOGGER.debug(f"Parsing of METAR OK: {metar_object.summary}")
                except Exception as e:
                    LOGGER.error(f"Error parsing METAR: {e}")
                    metar_object = None
                return_data = {
                    "raw_metar": result,
                    "metar_object": metar_object,
                    "fetch_time": datetime.now(timezone.utc),
                    "expires": expires_header,
                }
                return return_data
        except Exception as err:
            LOGGER.exception("Connection to API failed")
            raise UpdateFailed(
                f"Error with connecting to API: {err} - {type(err).__name__}"
            )

    coordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=f"CAVOK {icao}",
        update_method=get_api_data,
        update_interval=STANDARD_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
