import asyncio
import logging
from math import ceil

from xcomfort.devices import Shade

from homeassistant.components.cover import (
    CoverEntityFeature,
    DEVICE_CLASS_SHADE,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, VERBOSE
from .hub import XComfortHub

_LOGGER = logging.getLogger(__name__)


def log(msg: str):
    if VERBOSE:
        _LOGGER.info(msg)


# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
# 	vol.Required(CONF_IP_ADDRESS): cv.string,
# 	vol.Required(CONF_AUTH_KEY): cv.string,
# })


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:

    hub = XComfortHub.get_hub(hass, entry)

    devices = hub.devices

    _LOGGER.info(f"Found {len(devices)} xcomfort devices")

    shades = list()
    for device in devices:
        if isinstance(device, Shade):
            _LOGGER.info(f"Adding {device}")
            shade = HASSXComfortShade(hass, hub, device)
            shades.append(shade)

    _LOGGER.info(f"Added {len(shades)} shades")
    async_add_entities(shades)


class HASSXComfortShade(CoverEntity):
    def __init__(self, hass: HomeAssistant, hub: XComfortHub, device: Shade):
        self.hass = hass
        self.hub = hub

        self._device = device
        self._name = device.name
        self._state = None
        self.device_id = device.device_id

        self.device_class = DEVICE_CLASS_SHADE

        self._unique_id = f"shade_{DOMAIN}_{hub.identifier}-{device.device_id}"

    async def async_added_to_hass(self):
        log(f"Added to hass {self._name} ")
        if self._device.state is None:
            log(f"State is null for {self._name}")
        else:
            self._device.state.subscribe(lambda state: self._state_change(state))

    def _state_change(self, state):
        self._state = state

        should_update = self._state is not None

        log(f"State changed {self._name} : {state}")

        if should_update:
            self.schedule_update_ha_state()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Eaton",
            "model": "XXX",
            "sw_version": "Unknown",
            "via_device": self.hub.hub_id,
        }

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._unique_id

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def supported_features(self):
        """Flag supported features."""
        return CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self._device.move_up()
    
    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self._device.move_down()

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self._device.move_stop()

    def update(self):
        pass
