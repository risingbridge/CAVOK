from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import DEGREE, UnitOfTemperature, UnitOfSpeed
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, VERSION


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    icao = entry.data["icao"]
    async_add_entities(
        [
            CavokMetarSensor(coordinator, icao),
            CavokWindSpeedSensor(coordinator, icao),
            CavokWindDirectionSensor(coordinator, icao),
            CavokTemperatureSensor(coordinator, icao),
            CavokDewpointSensor(coordinator, icao),
            CavokMetarTimestamp(coordinator, icao),
        ]
    )


class CavokEntity(CoordinatorEntity, SensorEntity):
    # Baseklassen som grupperer de andre klassene
    def __init__(self, coordinator, icao):
        super().__init__(coordinator)
        self.icao = icao
        # Device Info kobler ralle de andre klassene sammen
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, icao)},
            name=f"CAVOK: {icao}",
            manufacturer="Met.no",
            model="METAR Weather Station",
            sw_version=VERSION,
            configuration_url=f"https://metar-taf.com/metar/{icao}",
        )


class CavokMetarSensor(CavokEntity):
    def __init__(self, coordinator, icao):
        super().__init__(coordinator, icao)
        self.icao = icao

        self._attr_unique_id = f"{icao}_metar_raw"

        self._attr_name = f"{icao} METAR"

        self._attr_icon = "mdi:eye"

    @property
    def native_value(self):
        if self.coordinator.data:
            return self.coordinator.data["raw_metar"]
        return None

    @property
    def extra_state_attributes(self):
        if self.coordinator.data:
            fetch_time = self.coordinator.data["fetch_time"]
            expires = self.coordinator.data["expires"]
        else:
            fetch_time = None
        return {"last_update": fetch_time, "source": "Met.no", "Expires": expires}


class CavokMetarTimestamp(CavokEntity):
    def __init__(self, coordinator, icao):
        super().__init__(coordinator, icao)
        self._attr_unique_id = f"{icao}_time"
        self._attr_name = f"{icao} Time"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        metar_object = self.coordinator.data.get("metar_object")
        if metar_object is None or metar_object.data is None:
            return None
        if metar_object.data.time and metar_object.data.time.dt:
            return metar_object.data.time.dt
        return None


class CavokWindSpeedSensor(CavokEntity):
    def __init__(self, coordinator, icao):
        super().__init__(coordinator, icao)
        self._attr_unique_id = f"{icao}_wind_speed"
        self._attr_name = f"{icao} Wind Speed"
        self._attr_icon = "mdi:weather-windy"
        self._attr_native_unit_of_measurement = UnitOfSpeed.KNOTS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        metar_object = self.coordinator.data.get("metar_object")
        if metar_object is None or metar_object.data is None:
            return None
        if metar_object and metar_object.data.wind_speed:
            return metar_object.data.wind_speed.value
        return None


class CavokWindDirectionSensor(CavokEntity):
    def __init__(self, coordinator, icao):
        super().__init__(coordinator, icao)
        self._attr_unique_id = f"{icao}_wind_direction"
        self._attr_name = f"{icao} Wind Direction"
        self._attr_device_class = SensorDeviceClass.WIND_DIRECTION
        self._attr_native_unit_of_measurement = DEGREE

    @property
    def native_value(self):
        metar_object = self.coordinator.data.get("metar_object")
        if metar_object is None or metar_object.data is None:
            return None
        if metar_object.data.wind_direction.repr == "VRB":
            return None
        if metar_object and metar_object.data.wind_direction:
            return metar_object.data.wind_direction.value
        return None


class CavokTemperatureSensor(CavokEntity):
    def __init__(self, coordinator, icao):
        super().__init__(coordinator, icao)
        self._attr_unique_id = f"{icao}_temp_sensor"
        self._attr_name = f"{icao} Temperature"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        metar_object = self.coordinator.data.get("metar_object")
        if metar_object is None or metar_object.data is None:
            return None
        if metar_object.data.temperature:
            return metar_object.data.temperature.value
        return None


class CavokDewpointSensor(CavokEntity):
    def __init__(self, coordinator, icao):
        super().__init__(coordinator, icao)
        self._attr_unique_id = f"{icao}_dewpoint_sensor"
        self._attr_name = f"{icao} Dew Point"
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        metar_object = self.coordinator.data.get("metar_object")
        if metar_object is None or metar_object.data is None:
            return None
        if metar_object.data.dewpoint:
            return metar_object.data.dewpoint.value
        return None
