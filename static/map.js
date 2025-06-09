let map

const markers = {
    ocfr: [],
    ocso: [],
    scso: [],
}

const tooltips = {
    ocfr: [],
    ocso: [],
    scso: [],
}

const showMarkers = {
    ocfr: true,
    ocso: true,
    scso: true,
}

/*
    change display state of markers and tooltips by agency.
    true -> show
    false -> hide
    undefined -> whatever state was previously stored
    { ocfr, ocso, scso, updateState }
*/
function refreshMarkers(data) {
    for (const agency of Object.keys(markers))
        for (const marker of markers[agency])
            marker.setMap((data[agency] ?? showMarkers[agency]) ? map : null)

    for (const agency of Object.keys(markers))
        for (const tooltip of tooltips[agency])
            tooltip.setMap((data[agency] ?? showMarkers[agency]) ? map : null)

    if (data.updateState)
        for (const agency  of Object.keys(showMarkers))
            showMarkers[agency] = data[agency] ?? showMarkers[agency]
}

// fetch from API
async function getActiveCalls() {
    const req = await fetch('/active-calls')
    return await req.json()
}

// whether the FAB menu is visible
function isFabMenuVisible() {
    return document.getElementById('fab-menu').style.display !== 'none'
}

// change the display state of the FAB menu
function setFabMenuVisible(isVisible) {
    document.getElementById('fab-menu').style.display = isVisible ? '' : 'none'
}

async function main() {
    // import libraries

    const { Map } = await google.maps.importLibrary('maps')
    const { AdvancedMarkerElement, PinElement } = await google.maps.importLibrary('marker')

    // tooltip class

    class TooltipOverlay extends google.maps.OverlayView {
        constructor(position, call) {
            super()
            this.position = position
            this.call = call
            this.div = null
        }

        onAdd() {
            this.div = document.createElement('div')
            this.div.className = 'tooltip'

            // set z-index based on recency

            const timeAgo = Math.round(this.call.time_ago_duration.as('minutes'))
            this.div.style.zIndex = 100000 + timeAgo

            // set background color based on recency

            let bgColor

            if (timeAgo < -30)
                bgColor = `rgba(150,150,150,${timeAgo / -240}`
            else
                bgColor = `rgba(255,0,0,${(.5 - (timeAgo / -60))}`

            this.div.innerHTML = `
            <div class="tooltip-overlay" style="background:${bgColor})">
            <span class="tooltip-description">${this.call.description}</span>
            <span class="tooltip-location">${this.call.location}</span>
            <span class="tooltip-time-ago">${this.call.time_ago}</span>
            </div>`

            const panes = this.getPanes()
            panes.floatPane.appendChild(this.div)
        }

        draw() {
            if (!this.div) return

            const point = this.getProjection().fromLatLngToDivPixel(this.position)
            if (point) {
                this.div.style.left = `${point.x + 17}px`
                this.div.style.top = `${point.y - 37}px`
            }
        }

        onRemove() {
            if (this.div) {
                this.div.remove()
                this.div = null
            }
        }
    }

    // init map

    map = new Map(document.getElementById('map'), {
        zoom: 12,
        center: { lat: 28.5667416, lng: -81.4255644 },
        mapId: "MAP",
    })

    // center on orange county

    const bounds = new google.maps.LatLngBounds(
        { lat: 28.3468891, lng: -81.658612 },
        { lat: 28.78619, lng: -80.862908 },
    )

    map.fitBounds(bounds)

    async function refreshMap() {
        // fetch calls

        const calls = await getActiveCalls()
        console.log(calls)

        // find longest ago reporting time

        let longestTimeAgo = 0

        for (const agency of Object.keys(calls))
            for (const call of calls[agency]) {
                const entryTimeDateTime = luxon.DateTime.fromISO(call.entry_time)

                call.time_ago = entryTimeDateTime.toRelative()
                call.time_ago_duration = entryTimeDateTime.diff(luxon.DateTime.now())

                if (call.time_ago_duration < longestTimeAgo)
                    longestTimeAgo = call.time_ago_duration
            }

        // remove any existing markers and tooltips

        refreshMarkers({ ocfr: false, ocso: false, scso: false, updateState: false })

        for (const agency of Object.keys(markers))
            markers[agency] = []

        for (const agency of Object.keys(tooltips))
            tooltips[agency] = []

        // create markers

        for (const call of calls.ocfr) {
            // set pin glyph
            const glyph = document.createElement('img')
            glyph.className = 'pin-glyph'
            glyph.src = '/ocfr_logo.png'

            const pinEl = new PinElement({
                background: '#b40208',
                borderColor: '#d9ba32',
                glyph,
            })

            // create marker
            const marker = new AdvancedMarkerElement({
                content: pinEl.element,
                position: { lat: call.lat, lng: call.lng },
                title: '',
            })

            // create tooltip
            const tooltip = new TooltipOverlay(
                new google.maps.LatLng(call.lat, call.lng),
                call,
            )

            markers.ocfr.push(marker)
            tooltips.ocfr.push(tooltip)
        }

        for (const call of calls.ocso) {
            const position = call.location_data.geometry.location

            // set pin glyph
            const glyph = document.createElement('img')
            glyph.className = 'pin-glyph'
            glyph.src = '/ocso_logo.png'

            const pinEl = new PinElement({
                background: '#336034',
                borderColor: '#ede3c5',
                glyph,
            })

            // create marker
            const marker = new AdvancedMarkerElement({
                content: pinEl.element,
                position,
                title: '',
            })

            // create tooltip
            const tooltip = new TooltipOverlay(
                new google.maps.LatLng(position.lat, position.lng),
                call,
            )

            markers.ocso.push(marker)
            tooltips.ocso.push(tooltip)
        }

        for (const call of calls.scso) {
            const position = call.location_data.geometry.location

            // set pin glyph
            const glyph = document.createElement('img')
            glyph.className = 'pin-glyph'
            glyph.src = '/scso_logo.png'

            const pinEl = new PinElement({
                background: '#0c6134',
                borderColor: '#f4c474',
                glyph,
            })

            // create marker
            const marker = new AdvancedMarkerElement({
                content: pinEl.element,
                position,
                title: '',
            })

            // create tooltip
            const tooltip = new TooltipOverlay(
                new google.maps.LatLng(position.lat, position.lng),
                call,
            )

            markers.scso.push(marker)
            tooltips.scso.push(tooltip)
        }

        refreshMarkers({ ocfr: undefined, ocso: undefined, scso: undefined, updateState: false })
    }

    setInterval(refreshMap, 60_000)

    await refreshMap()
}

main()
