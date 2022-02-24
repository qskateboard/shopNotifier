script_name("ShopNotifier")
script_author("pSkateboard")
script_description("Advanced trade utility")
script_version('0.0.2')

local ev = require("samp.events")
local copas = require 'copas'
local http = require 'copas.http'
local lanes = require('lanes').configure()
local requests = require('requests')

encoding         = require("encoding")
encoding.default = 'CP1251'
u8 = encoding.UTF8
host = "http://127.0.0.1:5000"

function encodeUrl(str)
    str = str:gsub(' ', '%+')
    str = str:gsub('\n', '%%0A')
    return u8:encode(str, 'CP1251')
end

function urlencode(str)
   if (str) then
      str = string.gsub (str, "\n", "\r\n")
      str = string.gsub (str, "([^%w ])",
         function (c) return string.format ("%%%02X", string.byte(c)) end)
      str = string.gsub (str, " ", "+")
   end
   return str
end


function main()
	autoupdate(string.format("%s/api/updates", host), "[ShopNotifier]", host)
	repeat wait(0) until isSampAvailable()
	sampAddChatMessage("{FF0000}[ShopNotifier] {FFFFFF}Скрипт успешно запущен! Уведомления активированы.", -1)
	sampRegisterChatCommand('atest', function()
		send_to_panel("sell", "Платиновая рулетка", "1 шт", "470000", sampGetPlayerNickname(0), tostring(getPlayerMoney(playerHandle)))
	end)
	sampRegisterChatCommand('lcatch', function()
		status = not status
		if status then
			sampAddChatMessage("{FF0000}[ShopNotifier]{FFFFFF} Скрипт включен...", -1)
		else
			sampAddChatMessage("{FF0000}[ShopNotifier]{FFFFFF} Скрипт выключен...", -1)
		end
	end)
	while true do
		wait(0)
	end
end

function send_to_panel(order_type, item_name, item_count, item_price, player_name, balance)
	local result, id = sampGetPlayerIdByCharHandle(playerPed)
	local url = string.format("%s/api/%s/new_item", host, sampGetPlayerNickname(id))
	local body = {item_name = urlencode(u8:encode(item_name, 'CP1251')), item_count = urlencode(u8:encode(item_count, 'CP1251')), item_price = item_price, order_type = order_type, balance = balance, player_name = player_name}
	async_http_request('POST', url, {params = body}, function(result) end)
end


function ev.onServerMessage(color, text)
	local bItem, bCount, bNickname, bPrice = text:match("^Вы купили (.+) %((.+)%.%) у игрока (.+) за %$(%d+)")
	if bItem and bCount and bNickname and bPrice then
		send_to_panel("buy", bItem, bCount, bPrice, bNickname, tostring(getPlayerMoney(playerHandle)))
	end

	local sNickname, sItem, sCount, sPrice = text:match("^(.+) купил у вас (.+) %((.+)%.%), вы получили %$(%d+) от продажи %(комиссия 4 процент%(а%)%)")
	if sItem and sCount and sNickname and sPrice then
		send_to_panel("sell", sItem, sCount, sPrice, sNickname, tostring(getPlayerMoney(playerHandle)))
	end
end


function sumFormat(a)
    local b, e = ('%d'):format(a):gsub('^%-', '')
    local c = b:reverse():gsub('%d%d%d', '%1.')
    local d = c:reverse():gsub('^%.', '')
    return (e == 1 and '-' or '')..d
end


function ev.onShowDialog(dialogId)
	if dialogId == 3010 and status then
		sampSendDialogResponse(dialogId, 1, 0, 0)
		sampAddChatMessage("{FF0000}[AC]{FFFFFF} Вы поймали {ffb400}лавку!", -1)
		local result, id = sampGetPlayerIdByCharHandle(playerPed)
		local url = string.format("%s/api/alert/custom/%s?type=rent", host, sampGetPlayerNickname(id))
		local body = {type = "rent"}
		async_http_request('GET', url, nil, function(result) end)
	end
end

function ev.onSetObjectMaterialText(ev, data)
	local Object = sampGetObjectHandleBySampId(ev)
	if doesObjectExist(Object) and getObjectModel(Object) == 18663 and string.find(data.text, "(.-) {30A332}Свободная!") then
		if get_distance(Object) and status then
			lua_thread.create(press_key)
		end
	end
end

function press_key()
	setGameKeyState(21, 256)
end


function get_distance(Object)
	local result, posX, posY, posZ = getObjectCoordinates(Object)
	if result then
		if doesObjectExist(Object) then
			local pPosX, pPosY, pPosZ = getCharCoordinates(PLAYER_PED)
			local distance = (math.abs(posX - pPosX)^2 + math.abs(posY - pPosY)^2)^0.5
			local posX, posY = convert3DCoordsToScreen(posX, posY, posZ)
			if round(distance, 2) <= 0.9 then
				return true
			end
		end
	end
	return false
end

function round(x, n)
    n = math.pow(10, n or 0)
    x = x * n
    if x >= 0 then x = math.floor(x + 0.5) else x = math.ceil(x - 0.5) end
    return x / n
end

function autoupdate(json_url, prefix, url)
  local dlstatus = require('moonloader').download_status
  local json = getWorkingDirectory() .. '\\'..thisScript().name..'-version.json'
  if doesFileExist(json) then os.remove(json) end
  downloadUrlToFile(json_url, json,
    function(id, status, p1, p2)
      if status == dlstatus.STATUSEX_ENDDOWNLOAD then
        if doesFileExist(json) then
          local f = io.open(json, 'r')
          if f then
            local info = decodeJson(f:read('*a'))
            updatelink = info.url
            updateversion = info.latest
            f:close()
            os.remove(json)
            if updateversion ~= thisScript().version then
              lua_thread.create(function(prefix)
                local dlstatus = require('moonloader').download_status
                local color = -1
                sampAddChatMessage((prefix..'Обнаружено обновление. Пытаюсь обновиться c '..thisScript().version..' на '..updateversion), color)
                wait(250)
                downloadUrlToFile(updatelink, thisScript().path,
                  function(id3, status1, p13, p23)
                    if status1 == dlstatus.STATUS_DOWNLOADINGDATA then
                      print(string.format('Загружено %d из %d.', p13, p23))
                    elseif status1 == dlstatus.STATUS_ENDDOWNLOADDATA then
                      print('Загрузка обновления завершена.')
                      sampAddChatMessage((prefix..'Обновление завершено!'), color)
                      goupdatestatus = true
                      lua_thread.create(function() wait(500) thisScript():reload() end)
                    end
                    if status1 == dlstatus.STATUSEX_ENDDOWNLOAD then
                      if goupdatestatus == nil then
                        sampAddChatMessage((prefix..'Обновление прошло неудачно. Запускаю устаревшую версию..'), color)
                        update = false
                      end
                    end
                  end
                )
                end, prefix
              )
            else
              update = false
              print('v'..thisScript().version..': Обновление не требуется.')
            end
          end
        else
          print('v'..thisScript().version..': Не могу проверить обновление. Смиритесь или проверьте самостоятельно на '..url)
          update = false
        end
      end
    end
  )
  while update ~= false do wait(100) end
end

function async_http_request(method, url, args, resolve, reject)
    local request_lane = lanes.gen('*', {package = {path = package.path, cpath = package.cpath}}, function()
        local requests = require 'requests'
        local ok, result = pcall(requests.request, method, url, args)
        if ok then
            result.json, result.xml = nil, nil -- cannot be passed through a lane
            return true, result
        else
            return false, result -- return error
        end
    end)
    if not reject then reject = function() end end
    lua_thread.create(function()
        local lh = request_lane()
        while true do
            local status = lh.status
            if status == 'done' then
                local ok, result = lh[1], lh[2]
                if ok then resolve(result) else reject(result) end
                return
            elseif status == 'error' then
                return reject(lh[1])
            elseif status == 'killed' or status == 'cancelled' then
                return reject(status)
            end
            wait(0)
        end
    end)
end
