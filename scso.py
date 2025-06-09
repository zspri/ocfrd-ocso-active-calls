from aiohttp import ClientSession
from bs4 import BeautifulSoup, Tag
from datetime import datetime
from maps import get_place_data, Place
from typing import TypedDict
from zoneinfo import ZoneInfo

ACTIVE_CALLS_URL = 'https://www.seminolesheriff.org/ACS'


class Call(TypedDict):
    description: str
    entry_time: datetime
    location: str
    location_data: Place | None


async def get_active_calls(session: ClientSession) -> list[Call]:
    async with session.get(ACTIVE_CALLS_URL) as request:
        response = await request.text()

    soup = BeautifulSoup(response, 'html.parser')
    tbody = soup.select('main table tbody')

    if not tbody:
        return []
    
    tbody = tbody[0]

    calls: list[Call] = []

    for tr in tbody.children:
        if not isinstance(tr, Tag):
            continue

        tds = [c for c in tr.children if isinstance(c, Tag)]
        
        entry_time = tds[1].get_text()
        entry_time_dt = datetime.strptime(
            entry_time,
            '%m/%d/%Y %I:%M:%S %p',
        )
        entry_time_dt = entry_time_dt.replace(
            tzinfo=ZoneInfo('America/New_York'),
        )

        description = tds[2].get_text().upper()

        location = tds[3].get_text() + ', ' + tds[4].get_text()
        location_data = await get_place_data(session, location, 'SEMINOLE')

        calls.append({
            'description': description,
            'entry_time': entry_time_dt,
            'location': location,
            'location_data':  location_data,
        })

    return calls
