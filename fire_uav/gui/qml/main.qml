import QtQuick 2.15
import QtQuick.Window 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Dialogs
import QtWebEngine 1.10
import Qt5Compat.GraphicalEffects

ApplicationWindow {
    id: root
    width: 1440
    height: 860
    visible: true
    title: "fire_uav"
    color: "transparent"

    property real baseSpacing: 16
    property color panelColor: "#111111"
    property color borderColor: "#333333"
    property color textPrimary: "#ffffff"
    property color textMuted: "#aaaaaa"
    property int cardRadius: 18
    property int currentTab: 1
    Item {
        id: sceneLayer
        anchors.fill: parent

        Rectangle { anchors.fill: parent; color: "#000000" }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: baseSpacing / 2

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: currentTab

                // Detector
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Rectangle {
                        anchors.fill: parent
                        radius: cardRadius
                        color: panelColor
                        border.color: borderColor
                        clip: true

                        Item {
                            id: videoSurface
                            anchors.fill: parent

                            Image {
                                id: videoView
                                anchors.fill: parent
                                fillMode: Image.PreserveAspectFit
                                cache: false
                                smooth: true
                                source: app.cameraAvailable ? "image://video/live" : ""
                                visible: app.cameraAvailable
                            }
                        }
                        Connections {
                            target: app
                            function onFrameReady(url) { videoView.source = url; }
                        }

                        Rectangle {
                            anchors.fill: parent
                            color: Qt.rgba(0, 0, 0, 0.7)
                            visible: (!app.cameraAvailable) || videoView.status !== Image.Ready
                            z: 5
                            Text {
                                anchors.centerIn: parent
                                text: "Camera not found"
                                color: textPrimary
                                font.pixelSize: 24
                                font.bold: true
                            }
                        }

                        Item {
                            id: statusBar
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 12
                            width: Math.min(root.width * 0.34, 320)
                            height: navFloating.height
                            z: 7
                            property real highlightOpacity: 0.25
                            property color pillBg: Qt.rgba(1, 1, 1, 0.08)
                            property color pillBorder: Qt.rgba(1, 1, 1, 0.18)
                            property var blurOrigin: {
                                var _x = statusBar.x;
                                var _y = statusBar.y;
                                return statusBar.mapToItem(videoSurface, 0, 0);
                            }

                            ShaderEffectSource {
                                id: statusSlice
                                anchors.fill: parent
                                sourceItem: videoSurface
                                sourceRect: Qt.rect(statusBar.blurOrigin.x, statusBar.blurOrigin.y, statusBar.width, statusBar.height)
                                recursive: true
                                live: true
                                visible: false
                            }

                            FastBlur {
                                id: statusBlur
                                anchors.fill: parent
                                source: statusSlice
                                radius: 16
                                transparentBorder: true
                                z: -3
                            }

                            OpacityMask {
                                anchors.fill: parent
                                source: statusBlur
                                maskSource: Rectangle {
                                    width: statusBar.width
                                    height: statusBar.height
                                    radius: height / 2
                                }
                                z: -2
                            }

                            Rectangle {
                                anchors.fill: parent
                                radius: height / 2
                                color: Qt.rgba(0.08, 0.08, 0.08, 0.35)
                                border.color: Qt.rgba(1, 1, 1, 0.16)
                                border.width: 1
                                z: -1
                            }

                            Rectangle {
                                anchors.fill: parent
                                radius: height / 2
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.12) }
                                    GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.06) }
                                }
                                opacity: statusBar.highlightOpacity
                                Behavior on opacity { NumberAnimation { duration: 120; easing.type: Easing.OutQuad } }
                                z: -0.5
                            }

                            Row {
                                id: statusRow
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 0

                                Repeater {
                                    model: [
                                        { label: "FPS", value: function() { return app.fps.toFixed(1); }, color: textPrimary },
                                        { label: "Latency", value: function() { return app.latencyMs.toFixed(0) + " ms"; }, color: textPrimary },
                                        { label: "Conf", value: function() { return Math.round(app.detectionConfidence * 100) + "%"; }, color: "#7bc6ff" }
                                    ]
                                    delegate: Column {
                                        width: statusRow.width / 3
                                        anchors.verticalCenter: parent.verticalCenter
                                        spacing: 2
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: modelData.label
                                            color: Qt.rgba(1, 1, 1, 0.82)
                                            font.pixelSize: 13
                                            font.family: "Inter"
                                            font.weight: Font.Medium
                                        }
                                        Text {
                                            anchors.horizontalCenter: parent.horizontalCenter
                                            text: modelData.value()
                                            color: modelData.color
                                            font.pixelSize: 15
                                            font.family: "Inter"
                                            font.weight: Font.Medium
                                        }
                                    }
                                }
                            }
                        }

                        // Auto-run detector with fixed confidence
                        Component.onCompleted: {
                            if (app.confidence !== 0.4) app.setConfidence(0.4);
                            if (app.cameraAvailable) app.startDetector();
                        }
                    }
                }

                // Planner
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Rectangle {
                        anchors.fill: parent
                        radius: cardRadius
                        color: panelColor
                        border.color: borderColor
                        clip: true
                        layer.enabled: true
                        layer.samples: 4

                        WebEngineView {
                            id: mapView
                            anchors.fill: parent
                            url: app.mapUrl
                            profile: WebEngineProfile { storageName: "fire-uav"; offTheRecord: true }
                            backgroundColor: "transparent"
                            settings {
                                localContentCanAccessRemoteUrls: true
                                localContentCanAccessFileUrls: true
                                javascriptEnabled: true
                                errorPageEnabled: true
                                webGLEnabled: true
                            }
                            onLoadingChanged: function(loadRequest) {
                                if (loadRequest.status === WebEngineView.LoadSucceededStatus) {
                                    mapOverlay.text = ""
                                    mapView.runJavaScript(app.mapBridgeScript);
                                } else if (loadRequest.status === WebEngineView.LoadFailedStatus || loadRequest.status === WebEngineView.LoadStoppedStatus) {
                                    mapOverlay.text = "Map failed: " + (loadRequest.errorString || "")
                                    console.warn("Map load failed", loadRequest.errorString)
                                } else {
                                    mapOverlay.text = "Map loading..."
                                }
                            }
                            onRenderProcessTerminated: function(terminationStatus, exitCode) {
                                mapOverlay.text = "Map renderer crashed"
                                console.error("WebEngine terminated", terminationStatus, exitCode)
                            }
                            onJavaScriptConsoleMessage: function(level, message, lineNumber, sourceID) {
                                app.handleMapConsole(message);
                                if (message.indexOf("Leaflet failed") !== -1 || message.indexOf("Map instance not found") !== -1) {
                                    mapOverlay.text = message;
                                }
                                if (level === WebEngineView.ErrorMessageLevel) {
                                    console.error("Map JS error", message, lineNumber, sourceID)
                                }
                            }
                        }

                        Item {
                            id: mapControls
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 12
                            width: Math.min(mapRow.implicitWidth + 12, root.width * 0.9)
                            height: 48
                            z: 6
                            property real highlightOpacity: 0.25
                            property var blurOrigin: {
                                var _x = mapControls.x;
                                var _y = mapControls.y;
                                return mapControls.mapToItem(mapView, 0, 0);
                            }
                            property int buttonHeight: height - 12

                            ShaderEffectSource {
                                id: mapSlice
                                anchors.fill: parent
                                sourceItem: mapView
                                sourceRect: Qt.rect(mapControls.blurOrigin.x, mapControls.blurOrigin.y, mapControls.width, mapControls.height)
                                recursive: true
                                live: true
                                opacity: 0.0 // keep texture alive for blur only
                            }

                            FastBlur {
                                id: mapBlur
                                anchors.fill: parent
                                source: mapSlice
                                radius: 16
                                transparentBorder: true
                                z: -3
                            }

                            OpacityMask {
                                anchors.fill: parent
                                source: mapBlur
                                maskSource: Rectangle {
                                    width: mapControls.width
                                    height: mapControls.height
                                    radius: height / 2
                                }
                                z: -2
                            }

                            Rectangle {
                                anchors.fill: parent
                                radius: height / 2
                                color: Qt.rgba(0.08, 0.08, 0.08, 0.35)
                                border.color: Qt.rgba(1, 1, 1, 0.16)
                                border.width: 1
                                z: -1
                            }

                            Rectangle {
                                anchors.fill: parent
                                radius: height / 2
                                gradient: Gradient {
                                    GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.10) }
                                    GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.05) }
                                }
                                opacity: mapControls.highlightOpacity
                                Behavior on opacity { NumberAnimation { duration: 120; easing.type: Easing.OutQuad } }
                                z: -0.5
                            }

                            Row {
                                id: mapRow
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 6
                                anchors.verticalCenter: parent.verticalCenter

                                Component {
                                    id: glassButton
                                    Item {
                                        property string label
                                        property var action
                                        property int minWidth: 96
                                        property real targetScale: 1.0
                                        property bool hovered: false
                                        property bool pressed: false
                                        implicitWidth: Math.max(minWidth, labelText.implicitWidth + 28)
                                        width: implicitWidth
                                        height: mapControls.buttonHeight
                                        scale: targetScale
                                        Behavior on scale { SpringAnimation { spring: 4; damping: 0.38 } }

                                        Rectangle {
                                            anchors.fill: parent
                                            radius: glassBar.radius - 8
                                            color: pressed ? Qt.rgba(0.20, 0.20, 0.20, 0.55)
                                                           : (hovered ? Qt.rgba(0.16, 0.16, 0.16, 0.35)
                                                                      : "transparent")
                                            border.color: "transparent"
                                            Behavior on color { ColorAnimation { duration: 140 } }
                                        }

                                        Text {
                                            id: labelText
                                            anchors.centerIn: parent
                                            text: label
                                            color: (hovered || pressed) ? "#7bc6ff" : textPrimary
                                            font.pixelSize: 13
                                            font.family: "Inter"
                                            font.bold: hovered || pressed
                                            Behavior on color { ColorAnimation { duration: 120 } }
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            onEntered: { hovered = true; mapControls.highlightOpacity = pressed ? 0.34 : 0.30 }
                                            onExited: { hovered = false; mapControls.highlightOpacity = 0.25 }
                                            onPressed: { pressed = true; targetScale = 0.97; mapControls.highlightOpacity = 0.34 }
                                            onCanceled: { pressed = false; targetScale = 1.0; mapControls.highlightOpacity = hovered ? 0.30 : 0.25 }
                                            onReleased: {
                                                if (pressed && containsMouse && action) action();
                                                pressed = false;
                                                targetScale = 1.0;
                                                mapControls.highlightOpacity = hovered ? 0.30 : 0.25;
                                            }
                                        }
                                    }
                                }

                                Loader {
                                    sourceComponent: glassButton
                                    onLoaded: {
                                        item.label = "Generate"
                                        item.minWidth = 110
                                        item.action = function() { app.generatePath(); }
                                    }
                                }
                                Loader {
                                    sourceComponent: glassButton
                                    onLoaded: {
                                        item.label = "Refresh"
                                        item.minWidth = 100
                                        item.action = function() { app.regenerateMap(); }
                                    }
                                }
                                Loader {
                                    sourceComponent: glassButton
                                    onLoaded: {
                                        item.label = "Save QGC"
                                        item.minWidth = 118
                                        item.action = function() { app.savePlan(); }
                                    }
                                }
                                Loader {
                                    sourceComponent: glassButton
                                    onLoaded: {
                                        item.label = "Import GeoJSON"
                                        item.minWidth = 138
                                        item.action = function() { geojsonDialog.open(); }
                                    }
                                }
                                Loader {
                                    sourceComponent: glassButton
                                    onLoaded: {
                                        item.label = "Import KML"
                                        item.minWidth = 110
                                        item.action = function() { kmlDialog.open(); }
                                    }
                                }
                            }
                        }

                        Rectangle {
                            anchors.fill: parent
                            radius: cardRadius
                            color: Qt.rgba(0, 0, 0, 0.55)
                            visible: mapOverlay.text !== ""
                            z: 5
                            Text {
                                id: mapOverlay
                                anchors.centerIn: parent
                                text: "Map loading..."
                                color: textPrimary
                                font.pixelSize: 20
                                font.bold: true
                            }
                        }

                    }
                }

                // Logs
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Rectangle {
                        anchors.fill: parent
                        radius: cardRadius
                        color: panelColor
                        border.color: borderColor
                        clip: true

                        ListView {
                            id: logView
                            anchors.fill: parent
                            model: app.logs
                            delegate: Text {
                                text: modelData
                                color: textPrimary
                                font.pixelSize: 12
                                font.family: "Inter"
                                elide: Text.ElideLeft
                            }
                            onCountChanged: positionViewAtEnd()
                            Connections {
                                target: app
                                function onLogsChanged() { logView.positionViewAtEnd(); }
                            }
                        }

                        Text {
                            anchors.centerIn: parent
                            visible: logView.count === 0
                            text: "No logs yet"
                            color: textMuted
                            font.pixelSize: 16
                            font.bold: true
                            z: 5
                        }
                    }
                }
            }
        }
    }

    // Floating navigation capsule (unchanged)
    Item {
        id: navFloating
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 52
        width: Math.min(root.width * 0.34, 320)
        height: 48
        z: 50
        property real highlightOpacity: 0.25

        ShaderEffectSource {
            id: navSlice
            anchors.fill: parent
            sourceItem: sceneLayer
            opacity: 0.0 // keep texture alive for blur but don't show raw copy to avoid bleed
            live: true
            recursive: true
            sourceRect: Qt.rect(navFloating.x, navFloating.y, navFloating.width, navFloating.height)
        }

        FastBlur {
            id: navBlur
            anchors.fill: parent
            source: navSlice
            radius: 16
            transparentBorder: true
            z: -3
        }

        OpacityMask {
            anchors.fill: parent
            source: navBlur
            maskSource: Rectangle {
                width: navFloating.width
                height: navFloating.height
                radius: height / 2
            }
            z: -2
        }

        Rectangle {
            id: glassBar
            anchors.fill: parent
            radius: height / 2
            color: Qt.rgba(0.08, 0.08, 0.08, 0.35)
            border.color: Qt.rgba(1, 1, 1, 0.16)
            border.width: 1
        }

        Rectangle {
            id: glassHighlight
            anchors.fill: glassBar
            radius: glassBar.radius
            gradient: Gradient {
                GradientStop { position: 0.0; color: Qt.rgba(1, 1, 1, 0.12) }
                GradientStop { position: 1.0; color: Qt.rgba(1, 1, 1, 0.06) }
            }
            opacity: navFloating.highlightOpacity
            Behavior on opacity { NumberAnimation { duration: 120; easing.type: Easing.OutQuad } }
        }

        Row {
            id: navRow
            anchors.fill: parent
            anchors.margins: 6
            spacing: 0

            Component {
                id: navSegment
                Item {
                    property string label
                    property int index: 0
                    readonly property bool selected: currentTab === index
                    width: navRow.width / 3
                    height: navRow.height
                    property real targetScale: 1.0
                    scale: targetScale
                    Behavior on scale { SpringAnimation { spring: 4; damping: 0.38 } }

                    Rectangle {
                        anchors.fill: parent
                        radius: glassBar.radius - 8
                        color: selected ? Qt.rgba(0.2, 0.2, 0.2, 0.7) : "transparent"
                        border.color: selected ? Qt.rgba(1, 1, 1, 0.12) : "transparent"
                        Behavior on color { ColorAnimation { duration: 150 } }
                    }

                    Text {
                        anchors.centerIn: parent
                        text: label
                        color: selected ? "#7bc6ff" : textPrimary
                        font.pixelSize: 13
                        font.family: "Inter"
                        font.bold: selected
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onPressed: {
                            targetScale = 0.97;
                            navFloating.highlightOpacity = 0.32;
                        }
                        onReleased: {
                            targetScale = 1.0;
                            navFloating.highlightOpacity = 0.25;
                        }
                        onCanceled: {
                            targetScale = 1.0;
                            navFloating.highlightOpacity = 0.25;
                        }
                        onClicked: currentTab = index
                    }
                }
            }

            Loader { sourceComponent: navSegment; onLoaded: { item.label = "Detector"; item.index = 0 } }
            Loader { sourceComponent: navSegment; onLoaded: { item.label = "Planner";  item.index = 1 } }
            Loader { sourceComponent: navSegment; onLoaded: { item.label = "Logs";     item.index = 2 } }
        }
    }

    Component.onCompleted: {
        if (!app.cameraAvailable) currentTab = 1;
    }

    FileDialog {
        id: geojsonDialog
        title: "Import GeoJSON"
        nameFilters: ["GeoJSON (*.geojson *.json)"]
        onAccepted: app.importGeoJson(fileUrl.toLocalFile())
    }

    FileDialog {
        id: kmlDialog
        title: "Import KML"
        nameFilters: ["KML (*.kml)"]
        onAccepted: app.importKml(fileUrl.toLocalFile())
    }
}
