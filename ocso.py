from aiohttp import ClientSession
from datetime import datetime
from maps import get_place_data, Place
from typing import TypedDict
from xml.dom.minidom import Element, parseString
from zoneinfo import ZoneInfo

ACTIVE_CALLS_URL = 'https://www.ocso.com/portals/0/CFS_FEED/activecalls.xml'


class Call(TypedDict):
    description: str
    entry_time: datetime
    incident_number: int
    location: str
    location_data: Place | None
    reporting_district: str
    sector: str
    zone: str


def get_element_data(el: Element, subelement: str) -> str:
    text = ''
    for node in el.getElementsByTagName(subelement)[0].childNodes:
        if node.nodeType == node.TEXT_NODE:
            text += node.data
    return text


def parse_entry_time(call: Element) -> datetime:
    entry_time = get_element_data(call, 'ENTRYTIME')

    entry_time_dt = datetime.strptime(
        entry_time,
        '%m/%d/%Y %I:%M:%S %p',
    )
    entry_time_dt = entry_time_dt.replace(
        tzinfo=ZoneInfo('America/New_York'),
    )

    return entry_time_dt


async def get_active_calls(session: ClientSession) -> list[Call]:
    async with session.get(ACTIVE_CALLS_URL) as request:
        response = await request.read()
    
    document = parseString(response)
    calls_el = document.firstChild
    
    if not calls_el:
        return []

    if not isinstance(calls_el, Element):
        return []

    calls: list[Call] = []

    for call in calls_el.getElementsByTagName('CALL'):
        location_name = get_element_data(call, 'LOCATION')
        location_data = await get_place_data(session, location_name)

        if location_data:
            location_data: Place | None = {'geometry': location_data['geometry']}

        calls.append({
            'description': get_element_data(call, 'DESC'),
            'entry_time': parse_entry_time(call),
            'incident_number': int(call.getAttribute('INCIDENT')),
            'location': location_name,
            'location_data': location_data,
            'reporting_district': get_element_data(call, 'RD'),
            'sector': get_element_data(call, 'SECTOR'),
            'zone': get_element_data(call, 'ZONE'),
        })

    return calls
