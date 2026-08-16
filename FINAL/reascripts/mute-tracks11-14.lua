-- Mute Tracks 11 to 14

local FIRST_TRACK = 11
local LAST_TRACK = 14

reaper.Undo_BeginBlock()

for track_num = FIRST_TRACK, LAST_TRACK do
    local track = reaper.GetTrack(0, track_num - 1) -- REAPER tracks are 0-indexed

    if track then
        reaper.SetMediaTrackInfo_Value(track, "B_MUTE", 1)
    end
end

reaper.TrackList_AdjustWindows(false)
reaper.UpdateArrange()

reaper.Undo_EndBlock("Mute Tracks 11-14", -1)