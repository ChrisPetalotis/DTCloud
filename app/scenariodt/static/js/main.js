function menuDrop() {
	document.getElementById("myDropdown").classList.toggle("show")
}

window.onclick = function (event) {
	if (!event.target.matches(".dropbtn")) {
		var dropdowns = document.getElementsByClassName("dropdown-content")
		var i
		for (i = 0; i < dropdowns.length; i++) {
			var openDropdown = dropdowns[i]
			if (openDropdown.classList.contains("show")) {
				openDropdown.classList.remove("show")
			}
		}
	}
}

// Set up web socket connection with server
const webSocketProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"
const wsEndpoint = `${webSocketProtocol}//${window.location.host}/ws/notifications/`
const socket = new WebSocket(wsEndpoint)

// Captures incoming messages via web socket connection
socket.addEventListener("message", event => {
	const messageData = JSON.parse(event.data)
	console.log("Received notification:", messageData.message) // Log the received message
	showNotification(messageData.message)
})

function showNotification(notificationHTML) {
	const notificationsContainer = document.getElementById("notifications")

	// Create a new alert div
	const alertDiv = document.createElement("div")
	alertDiv.classList.add(
		"alert",
		"alert-dismissible",
		"alert-primary",
		"fade",
		"show",
		"mb-0"
	)
	alertDiv.setAttribute("role", "alert")
	alertDiv.innerHTML = notificationHTML

	// Create the close button
	const closeButton = document.createElement("button")
	closeButton.setAttribute("type", "button")
	closeButton.classList.add("close")
	closeButton.setAttribute("data-dismiss", "alert")
	closeButton.setAttribute("aria-label", "Close")

	const closeSign = document.createElement("span")
	closeSign.setAttribute("aria-hidden", "true")
	closeSign.innerHTML = "&times;"
	closeButton.append(closeSign)

	alertDiv.appendChild(closeButton)

	notificationsContainer.appendChild(alertDiv)
}

socket.onopen = event => {
	console.log("WebSocket connection opened!")
}

socket.onclose = event => {
	console.log("WebSocket connection closed!")
}
