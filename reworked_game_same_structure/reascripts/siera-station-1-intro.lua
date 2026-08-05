-- Jump to Marker 8 and play for a fixed duration.
-- Then mute Tracks 11–16 and loop Region 1.

local MARKER_ID = 8
local REGION_ID = 1
local PLAY_DURATION = 45 -- seconds

local FIRST_MUTE_TRACK = 11
local LAST_MUTE_TRACK = 16

--------------------------------------------------
-- Find a marker or region by displayed ID number
--------------------------------------------------

local function find_marker_or_region(target_id, want_region)
    local index = 0

    while true do
        local retval,
              is_region,
              position,
              region_end,
              name,
              displayed_id =
            reaper.EnumProjectMarkers3(0, index)

        if retval == 0 then
            break
        end

        if is_region == want_region
            and displayed_id == target_id then

            return position, region_end
        end

        index = index + 1
    end

    return nil, nil
end

--------------------------------------------------
-- Mute Tracks 11–16
--------------------------------------------------

local function mute_tracks()
    for track_number = FIRST_MUTE_TRACK, LAST_MUTE_TRACK do
        -- REAPER track indexes start from 0
        local track = reaper.GetTrack(0, track_number - 1)

        if track then
            reaper.SetMediaTrackInfo_Value(
                track,
                "B_MUTE",
                1
            )
        end
    end

    reaper.TrackList_AdjustWindows(false)
    reaper.UpdateArrange()
end

--------------------------------------------------
-- Find Marker 8 and Region 1
--------------------------------------------------

local marker_position =
    find_marker_or_region(MARKER_ID, false)

local region_start, region_end =
    find_marker_or_region(REGION_ID, true)

if not marker_position then
    reaper.ShowMessageBox(
        "Marker 8 could not be found.",
        "Script Error",
        0
    )
    return
end

if not region_start or not region_end then
    reaper.ShowMessageBox(
        "Region 1 could not be found.",
        "Script Error",
        0
    )
    return
end

--------------------------------------------------
-- Start at Marker 8
--------------------------------------------------

-- Disable repeat during the Marker 8 section
reaper.GetSetRepeat(0)

-- Move to Marker 8
reaper.SetEditCurPos(
    marker_position,
    true,
    true
)

-- Start playback
reaper.OnPlayButton()

local start_time = reaper.time_precise()

--------------------------------------------------
-- Wait, then switch to Region 1
--------------------------------------------------

local function wait_then_loop_region()
    local elapsed =
        reaper.time_precise() - start_time

    if elapsed < PLAY_DURATION then
        reaper.defer(wait_then_loop_region)
        return
    end

    -- Mute Tracks 11–16
    mute_tracks()

    -- Set Region 1 as the loop range
    reaper.GetSet_LoopTimeRange(
        true,
        true,
        region_start,
        region_end,
        false
    )

    -- Turn repeat on
    reaper.GetSetRepeat(1)

    -- Jump to the start of Region 1
    -- seekplay=true means playback continues from the new location
    reaper.SetEditCurPos(
        region_start,
        true,
        true
    )
end

wait_then_loop_region()