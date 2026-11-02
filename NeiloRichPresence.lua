-- Neilo DCS Rich Presence v0.1 - independent GameGUI hook. Miku was here
local cb = {}
local active, paused, loading = false, false, false
local started = os.time()
local last = -100
local target = lfs.writedir() .. 'Logs/NeiloRichPresence.json'
local function safe(fn, ...)
    if type(fn) ~= 'function' then return nil end
    local ok, value = pcall(fn, ...)
    if ok then return value end
end
local function writeState()
    local status = loading and 'loading' or (active and 'spectator' or 'menu')
    local aircraft, theatre = '', ''
    if active then
        local current = safe(DCS.getCurrentMission)
        local mission = current and (current.mission or current)
        theatre = (mission and mission.theatre) or ''
        local selfData = Export and safe(Export.LoGetSelfData)
        aircraft = (selfData and selfData.Name) or ''
        if aircraft == '' and safe(DCS.isMultiplayer) then
            local id = safe(net.get_my_player_id)
            local slot = id and safe(net.get_player_info, id, 'slot')
            if slot and tostring(slot) ~= '' and tostring(slot) ~= '0' then
                aircraft = safe(DCS.getUnitProperty, slot, DCS.UNIT_TYPE) or ''
            end
        end
        if aircraft ~= '' then status = 'cockpit' end
    end
    local data = {
        schema = 1, status = status, aircraft = aircraft, theatre = theatre,
        paused = paused, started = started, updated = os.time(),
        multiplayer = safe(DCS.isMultiplayer) == true
    }
    local encoded = net.lua2json(data)
    local file = io.open(target, 'w')
    if file then file:write(encoded); file:close() end
end
local function publish()
    local ok, err = pcall(writeState)
    if not ok and log then log.write('NeiloRichPresence', log.ERROR, tostring(err)) end
end
function cb.onMissionLoadBegin()
    active = false; paused = false; loading = true; publish()
end
function cb.onSimulationStart()
    active = true; paused = false; loading = false; started = os.time(); last = -100; publish()
end
function cb.onSimulationStop()
    active = false; paused = false; loading = false; publish()
end
function cb.onSimulationPause() paused = true; publish() end
function cb.onSimulationResume() paused = false; publish() end
function cb.onSimulationFrame()
    local now = safe(DCS.getRealTime) or os.time()
    if now < last or now - last >= 2 then last = now; publish() end
end
function cb.onPlayerChangeSlot(id)
    if id == safe(net.get_my_player_id) then publish() end
end
DCS.setUserCallbacks(cb)
publish()
