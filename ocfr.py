from aiohttp import ClientSession
from base64 import b64decode
from Crypto.Cipher import AES
from hashlib import md5
from orjson import loads
from typing import Any, TypedDict

ACTIVE_CALLS_URL = 'https://api.pulsepoint.org/v1/webapp?resource=incidents&agencyid=65060'
ACTIVE_CALLS_PASSWORD = 'tombrady5rings'.encode('utf-8')


class Call(TypedDict):
    description: str
    entry_time: str
    lat: float
    lng: float
    location: str


class CallRaw(TypedDict):
    CallReceivedDateTime: str
    Latitude: str
    Longitude: str
    FullDisplayAddress: str
    PulsePointIncidentCallType: str


class CallType(TypedDict):
    id: str
    description: str
    category: str


class CryptoJSResponse(TypedDict):
    ct: str
    iv: str
    s: str


# sourced from https://web.pulsepoint.org/@pulsepoint-web-common/src/models/CallType.ts
call_types: list[CallType] = [
    {"id": "AA", "description": "Auto Aid", "category": "Aid"},
    {"id": "MU", "description": "Mutual Aid", "category": "Aid"},
    {"id": "ST", "description": "Strike Team/Task Force", "category": "Aid"},
    {"id": "AC", "description": "Aircraft Crash", "category": "Aircraft"},
    {"id": "AE", "description": "Aircraft Emergency", "category": "Aircraft"},
    {"id": "AES", "description": "Aircraft Emergency Standby", "category": "Aircraft"},
    {"id": "LZ", "description": "Landing Zone", "category": "Aircraft"},
    {"id": "AED", "description": "AED Alarm", "category": "Alarm"},
    {"id": "OA", "description": "Alarm", "category": "Alarm"},
    {"id": "CMA", "description": "Carbon Monoxide", "category": "Alarm"},
    {"id": "FA", "description": "Fire Alarm", "category": "Alarm"},
    {"id": "MA", "description": "Manual Alarm", "category": "Alarm"},
    {"id": "SD", "description": "Smoke Detector", "category": "Alarm"},
    {"id": "TRBL", "description": "Trouble Alarm", "category": "Alarm"},
    {"id": "WFA", "description": "Waterflow Alarm", "category": "Alarm"},
    {"id": "FL", "description": "Flooding", "category": "Assist"},
    {"id": "LR", "description": "Ladder Request", "category": "Assist"},
    {"id": "LA", "description": "Lift Assist", "category": "Assist"},
    {"id": "PA", "description": "Police Assist", "category": "Assist"},
    {"id": "PS", "description": "Public Service", "category": "Assist"},
    {"id": "SH", "description": "Sheared Hydrant", "category": "Assist"},
    {"id": "EX", "description": "Explosion", "category": "Explosion"},
    {"id": "PE", "description": "Pipeline Emergency", "category": "Explosion"},
    {"id": "TE", "description": "Transformer Explosion", "category": "Explosion"},
    {"id": "AF", "description": "Appliance Fire", "category": "Fire"},
    {"id": "CHIM", "description": "Chimney Fire", "category": "Fire"},
    {"id": "CF", "description": "Commercial Fire", "category": "Fire"},
    {"id": "WSF", "description": "Confirmed Structure Fire", "category": "Fire"},
    {"id": "WVEG", "description": "Confirmed Vegetation Fire", "category": "Fire"},
    {"id": "CB", "description": "Controlled Burn/Prescribed Fire", "category": "Fire"},
    {"id": "ELF", "description": "Electrical Fire", "category": "Fire"},
    {"id": "EF", "description": "Extinguished Fire", "category": "Fire"},
    {"id": "FIRE", "description": "Fire", "category": "Fire"},
    {"id": "FULL", "description": "Full Assignment", "category": "Fire"},
    {"id": "IF", "description": "Illegal Fire", "category": "Fire"},
    {"id": "MF", "description": "Marine Fire", "category": "Fire"},
    {"id": "OF", "description": "Outside Fire", "category": "Fire"},
    {"id": "PF", "description": "Pole Fire", "category": "Fire"},
    {"id": "GF", "description": "Refuse/Garbage Fire", "category": "Fire"},
    {"id": "RF", "description": "Residential Fire", "category": "Fire"},
    {"id": "SF", "description": "Structure Fire", "category": "Fire"},
    {"id": "TF", "description": "Tank Fire", "category": "Fire"},
    {"id": "VEG", "description": "Vegetation Fire", "category": "Fire"},
    {"id": "VF", "description": "Vehicle Fire", "category": "Fire"},
    {"id": "WF", "description": "Confirmed Fire", "category": "Fire"},
    {"id": "WCF", "description": "Confirmed Commercial Fire", "category": "Fire"},
    {"id": "WRF", "description": "Confirmed Residential Fire", "category": "Fire"},
    {"id": "BT", "description": "Bomb Threat", "category": "Hazard"},
    {"id": "EE", "description": "Electrical Emergency", "category": "Hazard"},
    {"id": "EM", "description": "Emergency", "category": "Hazard"},
    {"id": "ER", "description": "Emergency Response", "category": "Hazard"},
    {"id": "GAS", "description": "Gas Main", "category": "Hazard"},
    {"id": "HC", "description": "Hazardous Condition", "category": "Hazard"},
    {"id": "HMR", "description": "Hazardous Materials Response", "category": "Hazard"},
    {"id": "TD", "description": "Tree Down", "category": "Hazard"},
    {"id": "WE", "description": "Water Emergency", "category": "Hazard"},
    {"id": "AI", "description": "Arson Investigation", "category": "Investigation"},
    {"id": "FWI", "description": "Fireworks Investigation", "category": "Investigation"},
    {"id": "HMI", "description": "Hazmat Investigation", "category": "Investigation"},
    {"id": "INV", "description": "Investigation", "category": "Investigation"},
    {"id": "OI", "description": "Odor Investigation", "category": "Investigation"},
    {"id": "SI", "description": "Smoke Investigation", "category": "Investigation"},
    {"id": "CL", "description": "Commercial Lockout", "category": "Lockout"},
    {"id": "LO", "description": "Lockout", "category": "Lockout"},
    {"id": "RL", "description": "Residential Lockout", "category": "Lockout"},
    {"id": "VL", "description": "Vehicle Lockout", "category": "Lockout"},
    {"id": "CP", "description": "Community Paramedicine", "category": "Medical"},
    {"id": "IFT", "description": "Interfacility Transfer", "category": "Medical"},
    {"id": "ME", "description": "Medical Emergency", "category": "Medical"},
    {"id": "MCI", "description": "Multi Casualty", "category": "Medical"},
    {"id": "EQ", "description": "Earthquake", "category": "Natural Disaster"},
    {"id": "FLW", "description": "Flood Warning", "category": "Natural Disaster"},
    {"id": "TOW", "description": "Tornado Warning", "category": "Natural Disaster"},
    {"id": "TSW", "description": "Tsunami Warning", "category": "Natural Disaster"},
    {"id": "WX", "description": "Weather Incident", "category": "Natural Disaster"},
    {"id": "AR", "description": "Animal Rescue", "category": "Rescue"},
    {"id": "CR", "description": "Cliff Rescue", "category": "Rescue"},
    {"id": "CSR", "description": "Confined Space Rescue", "category": "Rescue"},
    {"id": "ELR", "description": "Elevator Rescue", "category": "Rescue"},
    {"id": "EER", "description": "Elevator/Escalator Rescue", "category": "Rescue"},
    {"id": "IR", "description": "Ice Rescue", "category": "Rescue"},
    {"id": "IA", "description": "Industrial Accident", "category": "Rescue"},
    {"id": "RES", "description": "Rescue", "category": "Rescue"},
    {"id": "RR", "description": "Rope Rescue", "category": "Rescue"},
    {"id": "SC", "description": "Structural Collapse", "category": "Rescue"},
    {"id": "TR", "description": "Technical Rescue", "category": "Rescue"},
    {"id": "TNR", "description": "Trench Rescue", "category": "Rescue"},
    {"id": "USAR", "description": "Urban Search and Rescue", "category": "Rescue"},
    {"id": "VS", "description": "Vessel Sinking", "category": "Rescue"},
    {"id": "WR", "description": "Water Rescue", "category": "Rescue"},
    {"id": "TCP", "description": "Collision Involving Pedestrian", "category": "Vehicle"},
    {"id": "TCS", "description": "Collision Involving Structure", "category": "Vehicle"},
    {"id": "TCT", "description": "Collision Involving Train", "category": "Vehicle"},
    {"id": "TCE", "description": "Expanded Traffic Collision", "category": "Vehicle"},
    {"id": "RTE", "description": "Railroad/Train Emergency", "category": "Vehicle"},
    {"id": "TC", "description": "Traffic Collision", "category": "Vehicle"},
    {"id": "PLE", "description": "Powerline Emergency", "category": "Wires"},
    {"id": "WA", "description": "Wires Arching", "category": "Wires"},
    {"id": "WD", "description": "Wires Down", "category": "Wires"},
    {"id": "WDA", "description": "Wires Down/Arcing", "category": "Wires"},
    {"id": "BP", "description": "Burn Permit", "category": "Other"},
    {"id": "CA", "description": "Community Activity", "category": "Other"},
    {"id": "FW", "description": "Fire Watch", "category": "Other"},
    {"id": "MC", "description": "Move-up/Cover", "category": "Other"},
    {"id": "NO", "description": "Notification", "category": "Other"},
    {"id": "STBY", "description": "Standby", "category": "Other"},
    {"id": "TEST", "description": "Test", "category": "Other"},
    {"id": "TRNG", "description": "Training", "category": "Other"},
    {"id": "NEWS", "description": "News", "category": "Alert"},
    {"id": "CERT", "description": "CERT", "category": "Alert"},
    {"id": "DISASTER", "description": "Disaster", "category": "Alert"},
    {"id": "UNK", "description": "Unknown Call Type", "category": "Unknown"}
]


async def get_active_calls(session: ClientSession) -> list[Call]:
    async with session.get(ACTIVE_CALLS_URL) as request:
        response: CryptoJSResponse = await request.json()
    
    # decode response body
    ct = b64decode(response['ct'])
    iv = bytes.fromhex(response['iv'])
    salt = bytes.fromhex(response['s'])

    # derive key, discard IV since we've already got it
    key, _ = evp_bytes_to_key(ACTIVE_CALLS_PASSWORD, salt, 32, 16)

    # decrypt
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_plaintext = cipher.decrypt(ct)

    # remove PKCS#7 padding
    pad_len = padded_plaintext[-1]
    plaintext = padded_plaintext[:-pad_len].decode("utf-8")

    # plaintext is a JSON-encoded string,
    # so parse once to get string, then again to get array
    data: dict[str, Any] = loads(loads(plaintext))
    data_calls: list[CallRaw] = data['incidents']['active']

    active_calls: list[Call] = []

    for call in data_calls:
        description = get_call_type(call["PulsePointIncidentCallType"])['description'].upper()

        active_calls.append({
            'description': description,
            'entry_time': call['CallReceivedDateTime'],
            'lat': float(call['Latitude']),
            'lng': float(call['Longitude']),
            'location': call['FullDisplayAddress'].split(',')[0],
        })

    return active_calls


# EVP_BytesToKey implementation (same as OpenSSL and CryptoJS)
def evp_bytes_to_key(password: bytes, salt: bytes, key_len: int, iv_len: int):
    d = b''
    while len(d) < key_len + iv_len:
        d_i = md5(d[-16:] + password + salt) if d else md5(password + salt)
        d += d_i.digest()
    return d[:key_len], d[key_len:key_len+iv_len]


def get_call_type(t: str) -> CallType:
    for call_type in call_types:
        if call_type['id'] == t:
            return call_type
        
    return call_types[-1]
