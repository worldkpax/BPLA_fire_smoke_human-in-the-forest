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

                        Image {
                            id: videoView
                            anchors.fill: parent
                            fillMode: Image.PreserveAspectFit
                            cache: false
                            smooth: true
                            source: "image://video/live"
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

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 12
                            text: "DETECTOR CONTENT"
                            color: "#ffcc66"
                            font.pixelSize: 18
                            z: 6
                        }
                    }

                    // Auto-run detector with fixed confidence
                    Component.onCompleted: {
                        if (app.confidence !== 0.4) app.setConfidence(0.4);
                        if (app.cameraAvailable) app.startDetector();
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

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 12
                            text: "PLANNER CONTENT"
                            color: "#ffcc66"
                            font.pixelSize: 18
                            z: 6
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

                        Text {
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: parent.top
                            anchors.topMargin: 12
                            text: "LOGS CONTENT"
                            color: "#ffcc66"
                            font.pixelSize: 18
                            z: 6
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
        id: importDialog
        title: "Import GeoJSON"
        nameFilters: ["GeoJSON (*.geojson *.json)"]
        onAccepted: {
            app.importGeoJson(fileUrl.toLocalFile());
        }
    }
}
