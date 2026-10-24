# Bereitet das von Capacitor erzeugte iOS-Projekt für TestFlight vor (läuft auf dem Mac in der Cloud, nach `npx cap add ios`).
# Mikrofon-Text, Exportregel, nur Hochformat am iPhone, Audio so, dass Musik aus anderen Apps weiterläuft (und Vibrationen trotz Mikro spürbar sind),
# App-Symbol, gemeinsames Build-Schema. Ändert nur Dateien in ios/.
import plistlib, re, shutil, sys, uuid
from pathlib import Path

root = Path(__file__).resolve().parent.parent
app = root / 'ios' / 'App'
info_p = app / 'App' / 'Info.plist'
info = plistlib.loads(info_p.read_bytes())
info['CFBundleDisplayName'] = 'Riff'
info['CFBundleDevelopmentRegion'] = 'de'
info['NSMicrophoneUsageDescription'] = 'Riff hört zu, was du auf der Gitarre spielst – nur zum Erkennen, nichts wird gespeichert.'
info['ITSAppUsesNonExemptEncryption'] = False
info['UIRequiredDeviceCapabilities'] = ['arm64']
info['UISupportedInterfaceOrientations'] = ['UIInterfaceOrientationPortrait']
info['UIStatusBarStyle'] = 'UIStatusBarStyleLightContent'
info_p.write_bytes(plistlib.dumps(info))

# Audio: Mikro und Wiedergabe gleichzeitig, andere Apps (Spotify, Apple Music) spielen weiter, Ton aus dem Lautsprecher
ad = app / 'App' / 'AppDelegate.swift'
src = ad.read_text()
if 'AVAudioSession' not in src:
    src = src.replace('import Capacitor', 'import Capacitor\nimport AVFoundation', 1)
    src = src.replace('// Override point for customization after application launch.',
        '// Mikro + Wiedergabe zugleich; Musik aus anderen Apps läuft weiter (Mitspielen)\n'
        '        try? AVAudioSession.sharedInstance().setCategory(.playAndRecord, mode: .default, options: [.mixWithOthers, .defaultToSpeaker, .allowBluetoothA2DP])\n'
        '        try? AVAudioSession.sharedInstance().setActive(true)\n'
        '        // Ohne das schweigt das Taptic Engine, solange das Mikro läuft (Stimmgerät: kleine Vibrationen)\n'
        '        try? AVAudioSession.sharedInstance().setAllowHapticsAndSystemSoundsDuringRecording(true)', 1)
    assert 'AVAudioSession.sharedInstance().setCategory' in src, 'AppDelegate-Muster nicht gefunden'
    ad.write_text(src)

# App-Symbol (1024 px, ohne Transparenz)
icons = app / 'App' / 'Assets.xcassets' / 'AppIcon.appiconset'
shutil.copy(root / 'ios-ci' / 'icon-1024.png', icons / 'AppIcon-512@2x.png')

# Gemeinsames Schema „App", damit xcodebuild es in der Cloud sicher findet
pbx = (app / 'App.xcodeproj' / 'project.pbxproj').read_text()
m = re.search(r'(\w{24}) /\* App \*/ = \{\s*isa = PBXNativeTarget;', pbx)
assert m, 'App-Ziel nicht gefunden'
tid = m.group(1)
schemes = app / 'App.xcodeproj' / 'xcshareddata' / 'xcschemes'
schemes.mkdir(parents=True, exist_ok=True)
ref = f'''<BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="{tid}" BuildableName="App.app" BlueprintName="App" ReferencedContainer="container:App.xcodeproj"></BuildableReference>'''
(schemes / 'App.xcscheme').write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="1600" version="1.7">
  <BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES">
    <BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES">{ref}</BuildActionEntry></BuildActionEntries>
  </BuildAction>
  <LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.DebuggerFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" debugServiceExtension="internal" allowLocationSimulation="YES">
    <BuildableProductRunnable runnableDebuggingMode="0">{ref}</BuildableProductRunnable>
  </LaunchAction>
  <ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"></ArchiveAction>
</Scheme>
''')
print('iOS-Projekt vorbereitet: Info.plist, AppDelegate (Audio), Symbol, Schema', tid)
