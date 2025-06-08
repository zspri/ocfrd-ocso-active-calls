let map

let frMarkers = []
let frTooltips = []

let soMarkers = []
let soTooltips = []

let showSoMarkers = true
let showFrMarkers = true

/*
    change display state of markers and tooltips by agency.
    true -> show
    false -> hide
    undefined -> whatever state was previously stored
*/
function refreshMarkers(fr, so) {
    for (const marker of frMarkers) {
        marker.setMap((fr ?? showFrMarkers) ? map : null)
    }

    for (const tooltip of frTooltips) {
        tooltip.setMap((fr ?? showFrMarkers) ? map : null)
    }

    for (const marker of soMarkers) {
        marker.setMap((so ?? showSoMarkers) ? map : null)
    }

    for (const tooltip of soTooltips) {
        tooltip.setMap((so ?? showSoMarkers) ? map : null)
    }

    showFrMarkers = fr ?? showFrMarkers
    showSoMarkers = so ?? showSoMarkers
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

        for (const call of calls.fr) {
            const entryTimeDateTime = luxon.DateTime.fromISO(call.entry_time)

            call.time_ago = entryTimeDateTime.toRelative()
            call.time_ago_duration = entryTimeDateTime.diff(luxon.DateTime.now())

            if (call.time_ago_duration < longestTimeAgo)
                longestTimeAgo = call.time_ago_duration
        }

        for (const call of calls.so) {
            const entryTimeDateTime = luxon.DateTime.fromISO(call.entry_time)

            call.time_ago = entryTimeDateTime.toRelative()
            call.time_ago_duration = entryTimeDateTime.diff(luxon.DateTime.now())

            if (call.time_ago_duration < longestTimeAgo)
                longestTimeAgo = call.time_ago_duration
        }

        // remove any existing markers and tooltips

        for (const marker of frMarkers)
            marker.setMap(null)

        for (const tooltip of frTooltips)
            tooltip.setMap(null)

        for (const marker of soMarkers)
            marker.setMap(null)

        for (const tooltip of soTooltips)
            tooltip.setMap(null)

        frMarkers = []
        frTooltips = []

        soMarkers = []
        soTooltips = []

        // create markers

        for (const call of calls.fr) {
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

            frMarkers.push(marker)
            frTooltips.push(tooltip)
        }

        for (const call of calls.so) {
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

            soMarkers.push(marker)
            soTooltips.push(tooltip)
        }

        refreshMarkers(undefined, undefined)
    }

    setInterval(refreshMap, 60_000)

    await refreshMap()
}

main()
