"""Windows display-language detection, independent of region/keyboard settings."""
import ctypes
from ctypes import wintypes
import locale
import sys

KEYS = ('cockpit','paused','mission','spectator','menu','prepare','loading','waiting','unavailable','solo','multi')
ROWS = {
'en': ('Flying {aircraft}','Paused — {aircraft}','Mission','Spectating / selecting aircraft','In the menus','Preparing for flight','Loading mission','Waiting for flight data','Map unavailable','Single player','Multiplayer'),
'fr': ('Aux commandes du {aircraft}','En pause — {aircraft}','Mission','Spectateur / choix de l’appareil','Dans les menus','Préparation du vol','Chargement de la mission','En attente des données de vol','Carte indisponible','Solo','Multijoueur'),
'de': ('Im Cockpit: {aircraft}','Pausiert — {aircraft}','Mission','Zuschauer / Flugzeugauswahl','Im Hauptmenü','Flugvorbereitung','Mission wird geladen','Warten auf Flugdaten','Karte nicht verfügbar','Einzelspieler','Mehrspieler'),
'es': ('Pilotando {aircraft}','En pausa — {aircraft}','Misión','Espectador / selección de aeronave','En los menús','Preparando el vuelo','Cargando misión','Esperando datos de vuelo','Mapa no disponible','Un jugador','Multijugador'),
'it': ('Ai comandi di {aircraft}','In pausa — {aircraft}','Missione','Spettatore / selezione velivolo','Nei menu','Preparazione al volo','Caricamento missione','In attesa dei dati di volo','Mappa non disponibile','Giocatore singolo','Multigiocatore'),
'pt': ('Pilotando {aircraft}','Em pausa — {aircraft}','Missão','Espectador / seleção de aeronave','Nos menus','Preparação do voo','Carregando missão','Aguardando dados de voo','Mapa indisponível','Um jogador','Multijogador'),
'ru': ('За штурвалом {aircraft}','Пауза — {aircraft}','Миссия','Наблюдение / выбор самолёта','В меню','Подготовка к полёту','Загрузка миссии','Ожидание данных полёта','Карта недоступна','Одиночная игра','Сетевая игра'),
'ar': ('قيادة {aircraft}','متوقف مؤقتًا — {aircraft}','المهمة','مشاهدة / اختيار الطائرة','في القوائم','الاستعداد للطيران','تحميل المهمة','في انتظار بيانات الرحلة','الخريطة غير متاحة','لعب فردي','لعب جماعي'),
'ja': ('{aircraft}を操縦中','一時停止中 — {aircraft}','ミッション','観戦 / 機体選択','メニュー画面','飛行準備中','ミッション読み込み中','飛行データを待機中','マップ情報なし','シングルプレイ','マルチプレイ'),
'ko': ('{aircraft} 조종 중','일시 정지 — {aircraft}','임무','관전 / 기체 선택','메뉴 화면','비행 준비 중','임무 불러오는 중','비행 데이터 대기 중','지도 정보 없음','싱글 플레이','멀티플레이'),
'zh-hans': ('正在驾驶 {aircraft}','已暂停 — {aircraft}','任务','观战 / 选择飞机','主菜单','准备飞行','正在加载任务','等待飞行数据','地图不可用','单人游戏','多人游戏'),
'zh-hant': ('正在駕駛 {aircraft}','已暫停 — {aircraft}','任務','觀戰 / 選擇飛機','主選單','準備飛行','正在載入任務','等待飛行資料','地圖無法使用','單人遊戲','多人遊戲'),
}
TEXT = {lang: dict(zip(KEYS, values)) for lang, values in ROWS.items()}
MAPS = {'Caucasus':'Caucasus','Syria':'Syria','PersianGulf':'Persian Gulf','Nevada':'Nevada',
        'MarianaIslands':'Mariana Islands','SinaiMap':'Sinai','TheChannel':'The Channel',
        'Normandy':'Normandy','Falklands':'South Atlantic','Kola':'Kola','Afghanistan':'Afghanistan'}
LOCAL_MAPS = {
'fr': {'Caucasus':'Caucase','Syria':'Syrie','PersianGulf':'Golfe Persique','MarianaIslands':'Mariannes','SinaiMap':'Sinaï','TheChannel':'La Manche','Normandy':'Normandie','Falklands':'Atlantique Sud'},
'de': {'Caucasus':'Kaukasus','Syria':'Syrien','PersianGulf':'Persischer Golf','MarianaIslands':'Marianen','TheChannel':'Ärmelkanal','Normandy':'Normandie','Falklands':'Südatlantik'},
'es': {'Caucasus':'Cáucaso','Syria':'Siria','PersianGulf':'Golfo Pérsico','MarianaIslands':'Islas Marianas','SinaiMap':'Sinaí','TheChannel':'Canal de la Mancha','Normandy':'Normandía','Falklands':'Atlántico Sur'},
'ru': {'Caucasus':'Кавказ','Syria':'Сирия','PersianGulf':'Персидский залив','Nevada':'Невада','MarianaIslands':'Марианские острова','SinaiMap':'Синай','TheChannel':'Ла-Манш','Normandy':'Нормандия','Falklands':'Южная Атлантика','Kola':'Кольский полуостров','Afghanistan':'Афганистан'},
'ar': {'Caucasus':'القوقاز','Syria':'سوريا','PersianGulf':'الخليج العربي','Nevada':'نيفادا','MarianaIslands':'جزر ماريانا','SinaiMap':'سيناء','TheChannel':'القنال الإنجليزي','Normandy':'نورماندي','Falklands':'جنوب الأطلسي','Kola':'كولا','Afghanistan':'أفغانستان'},
}

def language_for(tag):
    tag = str(tag or '').lower().replace('_','-')
    if tag.startswith('zh'):
        return 'zh-hant' if any(x in tag.split('-') for x in ('hant','tw','hk','mo')) else 'zh-hans'
    primary = tag.split('-')[0]
    return primary if primary in TEXT else 'en'

def windows_display_tag():
    if sys.platform != 'win32':
        return 'en'
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    try:
        fn = kernel.GetUserPreferredUILanguages
        fn.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.ULONG), wintypes.LPWSTR, ctypes.POINTER(wintypes.ULONG)]
        fn.restype = wintypes.BOOL
        count, size = wintypes.ULONG(), wintypes.ULONG()
        if fn(8, ctypes.byref(count), None, ctypes.byref(size)) and 0 < size.value < 32768:
            buf = ctypes.create_unicode_buffer(size.value)
            if fn(8, ctypes.byref(count), buf, ctypes.byref(size)) and buf.value:
                return buf.value
    except (OSError, AttributeError):
        pass
    try:
        kernel.GetUserDefaultUILanguage.restype = wintypes.WORD
        return locale.windows_locale.get(kernel.GetUserDefaultUILanguage(), 'en')
    except (OSError, AttributeError):
        return 'en'

def detect_language(override='auto'):
    return language_for(windows_display_tag() if override == 'auto' else override)

def map_name(value, lang):
    return LOCAL_MAPS.get(lang, {}).get(value, MAPS.get(value, value))
