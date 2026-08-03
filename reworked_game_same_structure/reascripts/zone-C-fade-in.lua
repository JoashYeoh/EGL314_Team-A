local track_num = 22
local track = reaper.GetTrack(0, track_num-1)    -- track 20 (in this case)

if not track then return end

local fade_time = 1.0     -- Fade in duration
local end_db = 0          -- Fade to 0 dB (unity gain)

-- Start from silence
reaper.SetMediaTrackInfo_Value(track, "D_VOL", 0)

local start_db = -150     -- Effectively silent
local start_time = reaper.time_precise()

function Fade()
    local t = (reaper.time_precise() - start_time) / fade_time

    if t >= 1 then
        reaper.SetMediaTrackInfo_Value(track, "D_VOL", 10^(end_db / 20))
        return
    end

    local db = start_db + (end_db - start_db) * t
    local gain = 10^(db / 20)

    reaper.SetMediaTrackInfo_Value(track, "D_VOL", gain)

    reaper.defer(Fade)
end

Fade()