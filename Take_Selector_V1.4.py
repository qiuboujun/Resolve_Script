# Zachary Korpi, Jimmy Qiu
import os
import re
import sys
import math
import time

def GetResolve():
    try:
    # The PYTHONPATH needs to be set correctly for this import statement to work.
    # An alternative is to import the DaVinciResolveScript by specifying absolute path (see ExceptionHandler logic)
        import DaVinciResolveScript as bmd
    except ImportError:
        if sys.platform.startswith("darwin"):
            expectedPath="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/"
        elif sys.platform.startswith("win") or sys.platform.startswith("cygwin"):
            import os
            expectedPath=os.getenv('PROGRAMDATA') + "\\Blackmagic Design\\DaVinci Resolve\\Support\\Developer\\Scripting\\Modules\\"
        elif sys.platform.startswith("linux"):
            expectedPath="/opt/resolve/Developer/Scripting/Modules/"

        # check if the default path has it...
        print("Unable to find module DaVinciResolveScript from $PYTHONPATH - trying default locations")
        try:
            import imp
            bmd = imp.load_source('DaVinciResolveScript', expectedPath+"DaVinciResolveScript.py")
        except ImportError:
            # No fallbacks ... report error:
            print("Unable to find module DaVinciResolveScript - please ensure that the module DaVinciResolveScript is discoverable by python")
            print("For a default DaVinci Resolve installation, the module is expected to be located in: "+expectedPath)
            sys.exit()

    return bmd.scriptapp("Resolve")

resolve = app.GetResolve()
fu = bmd.scriptapp('Fusion')
ui = app.UIManager
disp = bmd.UIDispatcher(ui)
pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject()
tl = proj.GetCurrentTimeline()
marker_color = ['All','Blue','Cyan','Green','Yellow','Red','Pink','Purple','Fuchsia','Rose','Lavender','Sky','Mint','Lemon','Sand','Cocoa','Cream']
refresher = '1'
framerate = 24

def getresolve(app='Resolve'):
    dr = bmd.scriptapp(app)
    return dr

def _exit(ev):
    disp.ExitLoop()

def this_timeline():
    return proj.GetCurrentTimeline()

def read_all_marker():
    mks = this_timeline().GetMarkers()
    print(mks)
    return mks

def read_timeline_startTC():
    tc = this_timeline().GetStartFrame()
    print(tc)
    return tc

def merge_two_dicts(x, y):
    z =x.copy()
    z.update(y)
    return z

def frames_to_timecode(total_frames, frame_rate, drop):     ##credits to Manne Ohrstrom and Shotgun Software Inc.
    """
    Method that converts frames to SMPTE timecode.
    
    :param total_frames: Number of frames
    :param frame_rate: frames per second
    :param drop: true if time code should drop frames, false if not
    :returns: SMPTE timecode as string, e.g. '01:02:12:32' or '01:02:12;32'
    """
    if drop and frame_rate not in [29.97, 59.94]:
        raise NotImplementedError("Time code calculation logic only supports drop frame "
                                  "calculations for 29.97 and 59.94 fps.")

    # for a good discussion around time codes and sample code, see
    # http://andrewduncan.net/timecodes/

    # round fps to the nearest integer
    # note that for frame rates such as 29.97 or 59.94,
    # we treat them as 30 and 60 when converting to time code
    # then, in some cases we 'compensate' by adding 'drop frames',
    # e.g. jump in the time code at certain points to make sure that
    # the time code calculations are roughly right.
    #
    # for a good explanation, see
    # https://documentation.apple.com/en/finalcutpro/usermanual/index.html#chapter=D%26section=6
    fps_int = int(round(frame_rate))

    if drop:
        # drop-frame-mode
        # add two 'fake' frames every minute but not every 10 minutes
        #
        # example at the one minute mark:
        #
        # frame: 1795 non-drop: 00:00:59:25 drop: 00:00:59;25
        # frame: 1796 non-drop: 00:00:59:26 drop: 00:00:59;26
        # frame: 1797 non-drop: 00:00:59:27 drop: 00:00:59;27
        # frame: 1798 non-drop: 00:00:59:28 drop: 00:00:59;28
        # frame: 1799 non-drop: 00:00:59:29 drop: 00:00:59;29
        # frame: 1800 non-drop: 00:01:00:00 drop: 00:01:00;02
        # frame: 1801 non-drop: 00:01:00:01 drop: 00:01:00;03
        # frame: 1802 non-drop: 00:01:00:02 drop: 00:01:00;04
        # frame: 1803 non-drop: 00:01:00:03 drop: 00:01:00;05
        # frame: 1804 non-drop: 00:01:00:04 drop: 00:01:00;06
        # frame: 1805 non-drop: 00:01:00:05 drop: 00:01:00;07
        #
        # example at the ten minute mark:
        #
        # frame: 17977 non-drop: 00:09:59:07 drop: 00:09:59;25
        # frame: 17978 non-drop: 00:09:59:08 drop: 00:09:59;26
        # frame: 17979 non-drop: 00:09:59:09 drop: 00:09:59;27
        # frame: 17980 non-drop: 00:09:59:10 drop: 00:09:59;28
        # frame: 17981 non-drop: 00:09:59:11 drop: 00:09:59;29
        # frame: 17982 non-drop: 00:09:59:12 drop: 00:10:00;00
        # frame: 17983 non-drop: 00:09:59:13 drop: 00:10:00;01
        # frame: 17984 non-drop: 00:09:59:14 drop: 00:10:00;02
        # frame: 17985 non-drop: 00:09:59:15 drop: 00:10:00;03
        # frame: 17986 non-drop: 00:09:59:16 drop: 00:10:00;04
        # frame: 17987 non-drop: 00:09:59:17 drop: 00:10:00;05

        # calculate number of drop frames for a 29.97 std NTSC
        # workflow. Here there are 30*60 = 1800 frames in one
        # minute

        FRAMES_IN_ONE_MINUTE = 1800 - 2

        FRAMES_IN_TEN_MINUTES = (FRAMES_IN_ONE_MINUTE * 10) - 2

        ten_minute_chunks = total_frames / FRAMES_IN_TEN_MINUTES
        one_minute_chunks = total_frames % FRAMES_IN_TEN_MINUTES

        ten_minute_part = 18 * ten_minute_chunks
        one_minute_part = 2 * ((one_minute_chunks - 2) / FRAMES_IN_ONE_MINUTE)

        if one_minute_part < 0:
            one_minute_part = 0

        # add extra frames
        total_frames += ten_minute_part + one_minute_part

        # for 60 fps drop frame calculations, we add twice the number of frames
        if fps_int == 60:
            total_frames = total_frames * 2

        # time codes are on the form 12:12:12;12
        smpte_token = ";"

    else:
        # time codes are on the form 12:12:12:12
        smpte_token = ":"

    # now split our frames into time code
    hours = int(total_frames / (3600 * fps_int))
    minutes = int(total_frames / (60 * fps_int) % 60)
    seconds = int(total_frames / fps_int % 60)
    frames = int(total_frames % fps_int)
    return "%02d:%02d:%02d%s%02d" % (hours, minutes, seconds, smpte_token, frames) # usage example print frames_to_timecode(123214, 24, False)

def get_all_timeline_items():
    TimelineConca = []
    TimelineDict = dict()
    for i in range(1, trackcount + 1):
        TimelineItem = this_timeline().GetItemListInTrack("video", i)
        TimelineConca = TimelineConca + TimelineItem
    for item in TimelineConca:
        enable_check = item.GetClipEnabled()
        if enable_check == True:    
            frameID = item.GetStart()
            TimelineDictItem = {frameID: item}
            TimelineDict = merge_two_dicts(TimelineDict, TimelineDictItem)
    TimelineDict = OrderedDict(sorted(TimelineDict.items()))
    return TimelineDict

def read_all_timeline_clips(ev):
    itm['tree'].Clear()
    global refresher
    refresher = '1'
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Name'
    mrk.Text[2] = 'Record In'
    mrk.Text[3] = 'Record Out'
    mrk.Text[4] = 'Takes'
    itm['tree'].SetHeaderItem(mrk)

    itm['tree'].ColumnCount = 5

    itm['tree'].ColumnWidth[0] = 75
    itm['tree'].ColumnWidth[1] = 200
    itm['tree'].ColumnWidth[2] = 100
    itm['tree'].ColumnWidth[3] = 100
    itm['tree'].ColumnWidth[4] = 50

    trackcount = this_timeline().GetTrackCount("video")
    i = 0
    TimelineDict = get_all_timeline_items()
    if itm['takes_only'].Checked == True:
        for frameID in TimelineDict:
            item = TimelineDict[frameID]
            enable_check = item.GetClipEnabled()
            takes_count = item.GetTakesCount()
            if enable_check == True and takes_count > 1:
                i= i + 1
                mrk.Text[1] = 'Reel Name'
                mrk.Text[5] = 'Date Added'
                itm['tree'].ColumnCount = 6
                itm['tree'].ColumnWidth[5] = 200
                itRow = itm['tree'].NewItem()
                itRow.Text[0] = str(i)
                itRow.Text[1] = str(item.GetMediaPoolItem().GetClipProperty('Reel Name'))
                itRow.Text[2] = str(frames_to_timecode(item.GetStart(), framerate, False))
                itRow.Text[3] = str(frames_to_timecode(item.GetEnd(), framerate, False))
                itRow.Text[4] = str(takes_count)
                itRow.Text[5] = str(item.GetMediaPoolItem().GetClipProperty('Date Added'))
                itm['tree'].AddTopLevelItem(itRow)
        itm['tree'].SortByColumn(2, "AscendingOrder")
    else:
        for frameID in TimelineDict:
            item = TimelineDict[frameID]
            enable_check = item.GetClipEnabled()
            if enable_check == True:
                i= i + 1
                itRow = itm['tree'].NewItem()
                itRow.Text[0] = str(i)
                itRow.Text[1] = item.GetName()
                itRow.Text[2] = str(frames_to_timecode(item.GetStart(), framerate, False))
                itRow.Text[3] = str(frames_to_timecode(item.GetEnd(), framerate, False))
                itRow.Text[4] = str(item.GetTakesCount())
                itm['tree'].AddTopLevelItem(itRow)
        itm['tree'].SortByColumn(2, "AscendingOrder")

def get_nearest_less_element(d, k):
    k = int(k)
    nearest = max(key for key in map(int, d.keys()) if key <= k)
    return nearest

def take_index_dict(current_clip):
    index_count = current_clip.GetTakesCount()
    take_conca = {}
    for i in range(1, index_count + 1):
        take_info = {i:current_clip.GetTakeByIndex(i)}
        take_conca = merge_two_dicts(take_conca, take_info)
    take_conca = OrderedDict(reversed(sorted(take_conca.items())))
    return take_conca

def read_current_take(current_clip, take_index):
    itm['current_tree'].UpdatesEnabled = False
    itm['current_tree'].Clear()
    crt = itm['current_tree'].NewItem()
    crt.Text[0] = 'ID'
    crt.Text[1] = 'Clip Name'
    crt.Text[2] = 'Record In'
    crt.Text[3] = 'Record Out'
    crt.Text[4] = 'Takes'
    crt.Text[5] = 'Date Added'
    itm['current_tree'].SetHeaderItem(crt)
    itm['current_tree'].ColumnCount = 6

    itm['current_tree'].ColumnWidth[0] = 50
    itm['current_tree'].ColumnWidth[1] = 200
    itm['current_tree'].ColumnWidth[2] = 100
    itm['current_tree'].ColumnWidth[3] = 100
    itm['current_tree'].ColumnWidth[4] = 50
    itm['current_tree'].ColumnWidth[5] = 150
    Take_Dict = take_index_dict(current_clip)
    i = 0
    for takeID in Take_Dict:
        item_dict = Take_Dict[takeID]
        item = item_dict['mediaPoolItem']
        #startframe = item_dict['startFrame']

        crtRow = itm['current_tree'].NewItem()
        i= i + 1
        crtRow.Text[0] = str(i)
        crtRow.Text[1] = str(item.GetClipProperty('Clip Name'))
        crtRow.Text[2] = str(frames_to_timecode(current_clip.GetStart(), framerate, False))
        crtRow.Text[3] = str(frames_to_timecode(current_clip.GetEnd(), framerate, False))
        crtRow.Text[4] = str(current_clip.GetTakesCount())
        crtRow.Text[5] = str(item.GetClipProperty('Date Added'))
        if takeID == take_index:
            for n in range(0, 6):
                crtRow.BackgroundColor[n] = { 'R':99/255, 'G':99/255, 'B':99/255, 'A':0.5 }
        itm['current_tree'].AddTopLevelItem(crtRow)
    itm['current_tree'].UpdatesEnabled = True

def _show_takes(ev):
    current_clip = tl.GetCurrentVideoItem()
    current_take = int(current_clip.GetSelectedTakeIndex())
    read_current_take(current_clip, current_take)
    itm['show_take'].Hidden = True

def _previous_take(ev):
    current_clip = tl.GetCurrentVideoItem()
    current_takes_available = int(current_clip.GetTakesCount())
    current_take = int(current_clip.GetSelectedTakeIndex())
    if current_takes_available > 0:
        if current_take <= current_takes_available and current_take > 1:
            select_take = current_clip.SelectTakeByIndex(current_take - 1)
            take_index = current_take - 1
            read_current_take(current_clip, take_index)
        elif current_take == 1:
            select_take = current_clip.SelectTakeByIndex(1)
            take_index = 1
            read_current_take(current_clip, take_index)
        else:
            pass

def _next_take(ev):
    current_clip = tl.GetCurrentVideoItem()
    current_takes_available = int(current_clip.GetTakesCount())
    current_take = int(current_clip.GetSelectedTakeIndex())
    if current_takes_available > 0:
        if current_take < current_takes_available:
            select_take = current_clip.SelectTakeByIndex(current_take + 1)
            take_index = current_take + 1
            read_current_take(current_clip, take_index)
        elif current_take == current_takes_available:
            select_take = current_clip.SelectTakeByIndex(current_takes_available)
            take_index = current_takes_available
            read_current_take(current_clip, take_index)
        else:
            pass

def _double_click(ev):
    print(str(ev['item'].Text[0]))
    x = str(ev['item'].Text[0])
    current_clip = tl.GetCurrentVideoItem()
    current_takes_available = int(current_clip.GetTakesCount())
    current_clip.SelectTakeByIndex(current_takes_available-(int(x)-1))
    read_current_take(current_clip, int(current_clip.GetSelectedTakeIndex()))

def read_marker_color(color_filter):
    itm['tree'].Clear()
    global refresher
    refresher = '0'
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Clip Name'
    mrk.Text[2] = 'Timecode'
    mrk.Text[3] = 'Takes'
    mrk.Text[4] = 'Color'
    mrk.Text[5] = 'Name'
    mrk.Text[6] = 'Notes'
    itm['tree'].SetHeaderItem(mrk)

    itm['tree'].ColumnCount = 7

    itm['tree'].ColumnWidth[0] = 50
    itm['tree'].ColumnWidth[1] = 150
    itm['tree'].ColumnWidth[2] = 75
    itm['tree'].ColumnWidth[3] = 50
    itm['tree'].ColumnWidth[4] = 60
    itm['tree'].ColumnWidth[5] = 100
    itm['tree'].ColumnWidth[6] = 150
    start_tc = read_timeline_startTC()
    all_marker = read_all_marker()
    all_marker = OrderedDict(sorted(all_marker.items()))
    i = 0
    TimelineDict = get_all_timeline_items()
    for mk_frameId in all_marker:
        marker_list = []
        mk = all_marker[mk_frameId]
        frame = mk_frameId + start_tc
        nearest = get_nearest_less_element(TimelineDict, frame)
        clipname = str(TimelineDict[nearest].GetName())
        takes_count = TimelineDict[nearest].GetTakesCount()
        color = str(mk['color'])
        duration = int(mk['duration'])
        note = str(mk['note'])
        name = str(mk['name'])
        customData = mk['customData']
        if itm['takes_only'].Checked == True:
            if color == color_filter or color_filter == 'All' and takes_count > 1:
                 i= i + 1
                 marker_list = [mk_frameId, color, duration, note, name, customData, clipname, takes_count]
                 itRow = itm['tree'].NewItem()
                 itRow.Text[0] = str(i)
                 itRow.Text[1] = str(marker_list[6])
                 itRow.Text[2] = str(frames_to_timecode(int(marker_list[0])+start_tc, framerate, False))
                 itRow.Text[3] = str(marker_list[7])
                 itRow.Text[4] = str(marker_list[1])
                 itRow.Text[5] = str(marker_list[4])
                 itRow.Text[6] = str(marker_list[3])
                 itm['tree'].AddTopLevelItem(itRow)
                 print (marker_list)
            itm['tree'].SortByColumn(2, "AscendingOrder")
        else:
            if color == color_filter or color_filter == 'All':
                 i= i + 1
                 marker_list = [mk_frameId, color, duration, note, name, customData, clipname, takes_count]
                 itRow = itm['tree'].NewItem()
                 itRow.Text[0] = str(i)
                 itRow.Text[1] = str(marker_list[6])
                 itRow.Text[2] = str(frames_to_timecode(int(marker_list[0])+start_tc, framerate, False))
                 itRow.Text[3] = str(marker_list[7])
                 itRow.Text[4] = str(marker_list[1])
                 itRow.Text[5] = str(marker_list[4])
                 itRow.Text[6] = str(marker_list[3])
                 itm['tree'].AddTopLevelItem(itRow)
                 print (marker_list)
            itm['tree'].SortByColumn(2, "AscendingOrder")

def _read_timeline_items():
    trackcount = this_timeline().GetTrackCount("video")
    TimelineItem = []
    for i in range(1, trackcount + 1):
        TimelineItem = TimelineItem.extend(this_timeline().GetItemListInTrack("video", i))

def _clicked(ev):
    print(str(ev['item'].Text[2]))
    x = str(ev['item'].Text[2])
    this_timeline().SetCurrentTimecode(x) 

def _selected(ev):
    selected_item = itm['tree'].SelectedItems()
    return selected_item

def _apply_filter(ev):
    color = itm['color_list'].CurrentText
    read_marker_color(color)

def _refresh_filter(ev):
    color = itm['color_list'].CurrentText
    if refresher == '0':
        read_marker_color(color)
    if refresher == '1':
        read_all_timeline_clips(ev)

def main_ui(ui):
    window01 = ui.VGroup({"Spacing": 10,},[
        ui.HGroup({"Spacing": 10, "Weight": 7,},[ 
            ui.Tree({
                    'ID': 'tree',
                    'SortingEnabled': True,
                    'SelectionMode': 'ExtendedSelection',
                    'Events': {
                              'ItemDoubleClicked': True,
                              'ItemClicked': True}}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 5,},[ 
            ui.Tree({
                    'ID': 'current_tree',
                    'SortingEnabled': True,
                    'SelectionMode': 'ExtendedSelection',
                    'Events': {
                              'ItemDoubleClicked': True,
                              'ItemClicked': True}
                                                   }),
        ]),
        ui.HGroup({"Spacing": 7, "Weight": 0,},[
            ui.Label({ "ID": "filter_text","Text": "Marker Filter Color","Weight": 0}),
            ui.ComboBox({ "ID": "color_list","Weight": 2}),
            ui.VGap({"Weight": 2}),
            ui.Button({ "ID": "filter_color", "Text": "Apply","Weight": 0}),
            ui.Button({ "ID": "reset_filter", "Text": "Show All","Weight": 0}),
            ui.Button({ "ID": "refresh", "Text": "Refresh","Weight": 0}),
        ]),
        ui.HGroup({"Spacing": 7, "Weight": 0,},[
            ui.CheckBox({ "ID": "takes_only", "Text": "Only show clips with multiple takes", "Weight": 0}),
            ui.VGap({"Weight": 2}),
            ui.CheckBox({ 
			"ID": "show_take", 
			"Text": "Auto Track Takes",
			"Weight": 1,
			"AutoRepeat": True,
			"AutoRepeatInterval": 1500,
			"AutoRepeatDelay": 2000,
			"Down": True,
                        'Events': {
                              'Toggled': True,
                              'SetDown': True,
                              'SetAutoRepeat': True,
                              'Update': True,}}),
            ui.Button({ "ID": "previous_take", "Text": "Previous Take","Weight": 0}),
            ui.Button({ "ID": "next_take", "Text": "Next Take","Weight": 0}),
        ])
        ])
    return window01

if __name__ == '__main__':

    window_01 = main_ui(ui)

    dlg = disp.AddWindow({ 
                        "WindowTitle": "Take Selector V1.4", 
                        "ID": "MyWin", 
                        'WindowFlags': {
                              'Window': True,
                              'WindowStaysOnTopHint': True,
                               },
                        'Events': {
                              'ContextMenu': True,
                              'FocusOut': True,
                              'Close': True},
                        "Geometry": [ 
                                    800, 700, 
                                    700, 430
                         ],
                        },
    window_01)

    itm = dlg.GetItems()

    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Name'
    mrk.Text[2] = 'Record In'
    mrk.Text[3] = 'Record Out'
    mrk.Text[4] = 'Takes'
    itm['tree'].SetHeaderItem(mrk)
    itm['tree'].ColumnCount = 5

    itm['tree'].ColumnWidth[0] = 75
    itm['tree'].ColumnWidth[1] = 200
    itm['tree'].ColumnWidth[2] = 100
    itm['tree'].ColumnWidth[3] = 100
    itm['tree'].ColumnWidth[4] = 50

    crt = itm['current_tree'].NewItem()
    crt.Text[0] = 'ID'
    crt.Text[1] = 'Reel Name'
    crt.Text[2] = 'Record In'
    crt.Text[3] = 'Record Out'
    crt.Text[4] = 'Takes'
    crt.Text[5] = 'Date Added'
    itm['current_tree'].SetHeaderItem(crt)
    itm['current_tree'].ColumnCount = 6

    itm['current_tree'].ColumnWidth[0] = 75
    itm['current_tree'].ColumnWidth[1] = 200
    itm['current_tree'].ColumnWidth[2] = 100
    itm['current_tree'].ColumnWidth[3] = 100
    itm['current_tree'].ColumnWidth[4] = 50
    itm['current_tree'].ColumnWidth[5] = 200

    trackcount = this_timeline().GetTrackCount("video")
    i = 0
    TimelineDict = get_all_timeline_items()
    if itm['takes_only'].Checked == True:
        for frameID in TimelineDict:
            item = TimelineDict[frameID]
            enable_check = item.GetClipEnabled()
            takes_count = item.GetTakesCount()
            if enable_check == True and takes_count > 1:
                i= i + 1
                mrk.Text[1] = 'Reel Name'
                mrk.Text[5] = 'Date Added'
                itm['tree'].ColumnCount = 6
                itm['tree'].ColumnWidth[5] = 200
                itRow = itm['tree'].NewItem()
                itRow.Text[0] = str(i)
                itRow.Text[1] = item.GetMediaPoolItem().GetClipProperty('Reel Name')
                itRow.Text[2] = str(frames_to_timecode(item.GetStart(), framerate, False))
                itRow.Text[3] = str(frames_to_timecode(item.GetEnd(), framerate, False))
                itRow.Text[4] = str(takes_count)
                itRow.Text[5] = str(item.GetMediaPoolItem().GetClipProperty('Date Added'))
                itm['tree'].AddTopLevelItem(itRow)
        itm['tree'].SortByColumn(2, "AscendingOrder")
    else:
        for frameID in TimelineDict:
            item = TimelineDict[frameID]
            enable_check = item.GetClipEnabled()
            if enable_check == True:
                i= i + 1
                itRow = itm['tree'].NewItem()
                itRow.Text[0] = str(i)
                itRow.Text[1] = item.GetName()
                itRow.Text[2] = str(frames_to_timecode(item.GetStart(), framerate, False))
                itRow.Text[3] = str(frames_to_timecode(item.GetEnd(), framerate, False))
                itRow.Text[4] = str(item.GetTakesCount())
                itm['tree'].AddTopLevelItem(itRow)
        itm['tree'].SortByColumn(2, "AscendingOrder")

    itm['color_list'].AddItems(marker_color)

    dlg.On.filter_color.Clicked = _apply_filter
    dlg.On.reset_filter.Clicked = read_all_timeline_clips
    dlg.On.refresh.Clicked = _refresh_filter
    dlg.On.current_tree.ItemDoubleClicked = _double_click
    dlg.On.previous_take.Clicked = _previous_take
    dlg.On.next_take.Clicked = _next_take
    dlg.On.show_take.Toggled = _show_takes
    dlg.On.tree.ItemDoubleClicked = _clicked
    dlg.On.tree.ItemClicked = _selected
    dlg.On.MyWin.Close = _exit

    dlg.Show()
    disp.RunLoop()
    dlg.Hide()

