-- Jump to Marker 9, play for a set duration, then pause

local MARKER_ID = 9
local PLAY_DURATION = 72   -- seconds

--------------------------------------------------
-- Find Marker 9
--------------------------------------------------

local marker_pos = nil
local i = 0

while true do
    local retval, is_region, pos, rgnend, name, markrgnindexnumber =
        reaper.EnumProjectMarkers3(0, i)

    if retval == 0 then break end

    if not is_region and markrgnindexnumber == MARKER_ID then
        marker_pos = pos
        break
    end

    i = i + 1
end

if not marker_pos then
    reaper.ShowMessageBox("Marker 9 not found.", "Error", 0)
    return
end

--------------------------------------------------
-- Jump to marker and play
--------------------------------------------------

reaper.SetEditCurPos(marker_pos, true, true)
reaper.OnPlayButton()

local start_time = reaper.time_precise()

--------------------------------------------------
-- Wait then pause
--------------------------------------------------

function Wait()

    if (reaper.time_precise() - start_time) >= PLAY_DURATION then
        reaper.OnPauseButton()
        return
    end

    reaper.defer(Wait)
end

Wait()