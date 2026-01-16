from typing import Any
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, VERSION


class CavokConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        # Hvis brukeren trykker "Send Inn"
        if user_input is not None:
            icao_code = user_input["icao"].upper()

            return self.async_create_entry(
                title=f"CAVOK: {icao_code}", data={"icao": icao_code}
            )
        # Hvis ikke brukeren har trykket "Send Inn", vis skjemaet
        data_schema = vol.Schema(
            {
                vol.Required("icao", default="ENGM"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)
