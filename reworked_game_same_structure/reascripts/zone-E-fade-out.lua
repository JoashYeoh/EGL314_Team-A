local track_num = 24
local track = reaper.GetTrack(0, track_num-1)    -- track 20 (in this case)

if not track then return end

local fade_time = 2.0   -- duration of fade
local start_gain = reaper.GetMediaTrackInfo_Value(track, "D_VOL")
local start_db = 20 * math.log(start_gain, 10)
local end_db = -150      -- effectively silent

local start_time = reaper.time_precise()

function Fade()
    local t = (reaper.time_precise() - start_time) / fade_time

    if t >= 1 then
        reaper.SetMediaTrackInfo_Value(track, "D_VOL", 0)
        return
    end

    local db = start_db + (end_db - start_db) * t
    local gain = 10^(db / 20)

    reaper.SetMediaTrackInfo_Value(track, "D_VOL", gain)

    reaper.defer(Fade)
end

Fade()