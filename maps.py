from aiohttp import ClientSession
from os import getenv
from typing import Any, TypedDict
import re

GOOGLE_MAPS_API_BASE_URL = 'https://maps.googleapis.com/maps/api'
GOOGLE_MAPS_API_KEY = getenv('GOOGLE_MAPS_API_KEY', '')


class PlaceLocation(TypedDict):
    lat: float
    lng: float


class PlaceGeometry(TypedDict):
    location: PlaceLocation


class Place(TypedDict):
    geometry: PlaceGeometry


class GeocodeResponse(TypedDict):
    results: list[Place]
    status: str


# dict of (place name): (place data from OSM)
place_data_cache: dict[str, Place] = {}


def clean_address(text: str) -> str:
    # replace ranges like [123 - 456] with just the first number
    text = re.sub(r'\[(\d+)\s*-\s*\d+\]\s*', r'\1 ', text)

    # remove [UNK]
    text = re.sub(r'\[UNK\]\s*', '', text)

    # format intersection name
    # "N ALAFAYA TRL/E COLONIAL DR" -> "N ALAFAYA TRAIL and E COLONIAL DR"
    text = text.replace('/', ' and ')
    text = text.replace('&', 'and')
    
    # format state route name
    text = re.sub(r'SR\s?(\d+)', r'State Route \1', text)
    
    return text.strip()


async def get_place_data(session: ClientSession, place_name: str, county: str = 'ORANGE') -> Place | None:
    place_name = f'{clean_address(place_name)}, {county} COUNTY'

    if (cached := place_data_cache.get(place_name)):
        return cached

    params = {
        'address': place_name,
        'components': 'country:US|administrative_area:FL',
        'key': GOOGLE_MAPS_API_KEY,
    }

    async with session.get(GOOGLE_MAPS_API_BASE_URL + '/geocode/json', params=params) as request:
        response: GeocodeResponse = await request.json()

        if len(response['results']) == 0:
            return None
        
        place = response['results'][0]
        place_data_cache[place_name] = place

        return place
