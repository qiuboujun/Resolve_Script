#Jimmy Qiu
import os
import re
import sys
import math
import time
from datetime import date

class RefreshManager:
    def __init__(self):
        self.current_mode = 'all'

    def set_refresh_all(self):
        self.current_mode = 'all'

    def set_refresh_filtered(self):
        self.current_mode = 'filtered'

    def set_refresh_search(self):
        self.current_mode = 'search'

    def get_current_mode(self):
        return self.current_mode

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
ui = app.UIManager
disp = bmd.UIDispatcher(ui)
pm = resolve.GetProjectManager()
proj = pm.GetCurrentProject()
framerate = proj.GetSetting('timelineFrameRate')
print(framerate)
tl = proj.GetCurrentTimeline()
marker_color = ['All','Blue','Cyan','Green','Yellow','Red','Pink','Purple','Fuchsia','Rose','Lavender','Sky','Mint','Lemon','Sand','Cocoa','Cream']
filter_options = ['Marker', 'Flag', 'Clip Color']
clip_color = ['All','Orange','Apricot','Yellow','Lime','Olive','Green','Teal','Navy','Blue','Purple','Violet','Pink','Tan','Beige','Brown','Chocolate']
flag_color = ['','Blue','Cyan','Green','Yellow','Red','Pink','Purple','Fuchsia','Rose','Lavender','Sky','Mint','Lemon','Sand','Cocoa','Cream']
refresh_manager = RefreshManager()
refresh_manager.set_refresh_all()
# Initialize boolean flags
flags = {
    'goodtake': False,
    'colorist_reviewed': False,
    'continuity_reviewed': False,
    'goodtake_filter': False,
    'colorist_reviewed_filter': False,
    'continuity_reviewed_filter': False
}
TimelineDict = {}
child_dict = {}

def toggle_flag(flag_name):
    def wrapper(ev):
        global flags
        flags[flag_name] = not flags[flag_name]
    return wrapper

@toggle_flag('goodtake')
def goodtake_bool(ev):
    pass

@toggle_flag('goodtake_filter')
def goodtake_filter(ev):
    pass

@toggle_flag('colorist_reviewed')
def coloristreviewed(ev):
    pass

@toggle_flag('colorist_reviewed_filter')
def coloristreviewed_filter(ev):
    pass

@toggle_flag('continuity_reviewed')
def continuityreviewed(ev):
    pass

@toggle_flag('continuity_reviewed_filter')
def continuityreviewed_filter(ev):
    pass

def this_timeline():
    return proj.GetCurrentTimeline()

def read_all_marker():
    mks = this_timeline().GetMarkers()
    print(mks)
    return mks

def read_all_flag():
    TimelineDict = get_all_timeline_items()
    flags = dict()
    for frameID in TimelineDict:
        item = TimelineDict[frameID]
        try:
            check = item.GetFlagList()
            if check:
                clip_flags = item.GetFlagList()
                flags = merge_two_dicts(flags, {frameID:item})
        except:
            pass
    print(flags)
    return flags

def read_all_clipcolor():
    TimelineDict = get_all_timeline_items()
    cc = dict()
    for frameID in TimelineDict:
        item = TimelineDict[frameID]
        try:
            check = item.GetClipColor()
            if check:
                clip_flags = item.GetClipColor()
                cc = merge_two_dicts(cc, {frameID:item})
        except:
            pass
    print(cc)
    return cc

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


def frame_to_index(i):
    lenth = len(str(max(read_all_marker().keys())))
    b = int(math.pow(10, int(lenth)))
    o = str(b+int(i))[1:]
    return o

def version_count(item):
    ver_list = item.GetVersionNameList(1)
    ver_count = ''
    try:
        ver_count = len(ver_list)
    except Exception:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        del exc_type, exc_value, exc_traceback
    return ver_count

def read_all_timeline_clips(ev):
    itm['tree'].Clear()
    refresh_manager.set_refresh_all()
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Name'
    mrk.Text[2] = 'Record In'
    mrk.Text[3] = 'Record Out'
    mrk.Text[4] = 'Version Num'
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
            itRow.Text[4] = str(version_count(item))
            itm['tree'].AddTopLevelItem(itRow)
    itm['tree'].SortByColumn(2, "AscendingOrder")

def get_nearest_less_element(d, k):
    k = int(k)
    try:
        nearest = max(key for key in map(int, d.keys()) if key <= k)
    except ValueError:
        pass
    return nearest

def read_marker_color(color_filter):
    itm['tree'].Clear()
    refresh_manager.set_refresh_filtered()
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Clip Name'
    mrk.Text[2] = 'Timecode'
    mrk.Text[3] = 'Color'
    mrk.Text[4] = 'Name'
    mrk.Text[5] = 'Notes'
    itm['tree'].SetHeaderItem(mrk)

    itm['tree'].ColumnCount = 6

    itm['tree'].ColumnWidth[0] = 50
    itm['tree'].ColumnWidth[1] = 150
    itm['tree'].ColumnWidth[2] = 75
    itm['tree'].ColumnWidth[3] = 60
    itm['tree'].ColumnWidth[4] = 100
    itm['tree'].ColumnWidth[5] = 150
    start_tc = read_timeline_startTC()
    all_marker = read_all_marker()
    all_marker = OrderedDict(sorted(all_marker.items()))
    i = 0
    for mk_frameId in all_marker:
        marker_list = []
        mk = all_marker[mk_frameId]
        frame = mk_frameId + start_tc
        print(start_tc, mk_frameId)
        nearest = get_nearest_less_element(TimelineDict, frame)
        clipname = str(TimelineDict[nearest].GetName())
        color = str(mk['color'])
        duration = int(mk['duration'])
        note = str(mk['note'])
        name = str(mk['name'])
        customData = mk['customData']
        if color == color_filter or color_filter == 'All':
             i= i + 1
             marker_list = [mk_frameId, color, duration, note, name, customData, clipname]
             itRow = itm['tree'].NewItem()
             itRow.Text[0] = str(i)
             itRow.Text[1] = str(marker_list[6])
             itRow.Text[2] = str(frames_to_timecode(int(marker_list[0])+start_tc, framerate, False))
             itRow.Text[3] = str(marker_list[1])
             itRow.Text[4] = str(marker_list[4])
             itRow.Text[5] = str(marker_list[3])
             itm['tree'].AddTopLevelItem(itRow)
        itm['tree'].SortByColumn(2, "AscendingOrder")

def read_flag_color(color_filter):
    itm['tree'].Clear()
    refresh_manager.set_refresh_filtered()
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Clip Name'
    mrk.Text[2] = 'Timecode'
    mrk.Text[3] = 'Color'

    itm['tree'].SetHeaderItem(mrk)

    itm['tree'].ColumnCount = 4

    itm['tree'].ColumnWidth[0] = 50
    itm['tree'].ColumnWidth[1] = 250
    itm['tree'].ColumnWidth[2] = 75
    itm['tree'].ColumnWidth[3] = 60

    start_tc = read_timeline_startTC()
    all_flag = read_all_flag()
    all_flag = OrderedDict(sorted(all_flag.items()))
    i = 0
    for flag_frameId in all_flag:
        flag_list = []
        fg = all_flag[flag_frameId].GetFlagList()
        clipname = str(all_flag[flag_frameId].GetName())

        if color_filter in fg or color_filter == 'All':
             i= i + 1
             flag_list = [flag_frameId, fg, clipname]
             itRow = itm['tree'].NewItem()
             itRow.Text[0] = str(i)
             itRow.Text[1] = str(flag_list[2])
             itRow.Text[2] = str(frames_to_timecode(int(flag_list[0]), framerate, False))
             itRow.Text[3] = str(', '.join(flag_list[1]))

             itm['tree'].AddTopLevelItem(itRow)
        itm['tree'].SortByColumn(2, "AscendingOrder")

def read_clip_color(color_filter):
    itm['tree'].Clear()
    refresh_manager.set_refresh_filtered()
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Clip Name'
    mrk.Text[2] = 'Timecode'
    mrk.Text[3] = 'Color'

    itm['tree'].SetHeaderItem(mrk)

    itm['tree'].ColumnCount = 4

    itm['tree'].ColumnWidth[0] = 50
    itm['tree'].ColumnWidth[1] = 250
    itm['tree'].ColumnWidth[2] = 75
    itm['tree'].ColumnWidth[3] = 60

    start_tc = read_timeline_startTC()
    all_clipcolor = read_all_clipcolor()
    all_clipcolor = OrderedDict(sorted(all_clipcolor.items()))
    i = 0
    for clip_frameId in all_clipcolor:
        clip_list = []
        cp = all_clipcolor[clip_frameId].GetClipColor()
        clipname = str(all_clipcolor[clip_frameId].GetName())

        if color_filter in cp or color_filter == 'All':
             i= i + 1
             clip_list = [clip_frameId, cp, clipname]
             itRow = itm['tree'].NewItem()
             itRow.Text[0] = str(i)
             itRow.Text[1] = str(clip_list[2])
             itRow.Text[2] = str(frames_to_timecode(int(clip_list[0]), framerate, False))
             itRow.Text[3] = str(clip_list[1])

             itm['tree'].AddTopLevelItem(itRow)
        itm['tree'].SortByColumn(2, "AscendingOrder")

def convert_marker_color(color_filter):
    start_tc = read_timeline_startTC()
    all_marker = read_all_marker()
    all_marker = OrderedDict(sorted(all_marker.items()))
    i = 0
    for mk_frameId in all_marker:
        marker_list = []
        mk = all_marker[mk_frameId]
        frame = mk_frameId + start_tc
        print(start_tc, mk_frameId)
        nearest = get_nearest_less_element(TimelineDict, frame)
        clipname = str(TimelineDict[nearest].GetName())
        color = str(mk['color'])
        duration = int(mk['duration'])
        note = str(mk['note'])
        name = str(mk['name'])
        customData = mk['customData']
        if color == color_filter:
             i= i + 1
             marker_list = [mk_frameId, color, duration, note, name, customData, clipname]
             if marker_list[3] != '':
                 _edit_metadata('Comments', marker_list[3], TimelineDict[nearest])

def add_markers(frameId, color, name, note, duration, customData=''):
    o = this_timeline().AddMarker(frameId, color, name, note, duration, customData)
    return o

def convert_comment_to_marker(color_filter):
    start_tc = read_timeline_startTC()
    TimelineDict = get_all_timeline_items()
    name = str(date.today())
    for frameID in TimelineDict:
        timelineitem = TimelineDict[frameID]
        media_item = timelineitem.GetMediaPoolItem()
        get_setting = ''
        try:
            get_setting = media_item.GetMetadata('Comments')
        except Exception:
            sys.exc_clear()
        if get_setting != '':
            new_marker_tc = (timelineitem.GetStart() + timelineitem.GetEnd())/2 - start_tc
            marker = this_timeline().AddMarker(int(new_marker_tc), color_filter, name, get_setting, 1, '')
            print(int(new_marker_tc), color_filter, name, get_setting)

def _read_timeline_items():
    trackcount = this_timeline().GetTrackCount("video")
    TimelineItem = []
    for i in range(1, trackcount + 1):
        TimelineItem = TimelineItem.extend(this_timeline().GetItemListInTrack("video", i))

def _clicked(ev):
    print(str(ev['item'].Text[2]))
    x = str(ev['item'].Text[2])
    this_timeline().SetCurrentTimecode(x) 

def _clicked_mediafolder(ev):
    global child_dict
    x = str(ev['item'].Text[0])
    for foldername in child_dict:
        if foldername == x:
            folder_item = child_dict[foldername]
            folder_clips = folder_item.GetClipList()
    #for items in folder_clips:
        #print(items)

def list_folder_clips(selected_item):
    global child_dict
    i = 0
    all_clips_list = []
    #print(child_dict)
    itm['tree'].Clear()
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Name'
    mrk.Text[2] = 'Record In'
    mrk.Text[3] = 'Record Out'
    mrk.Text[4] = 'Version Num'
    itm['tree'].SetHeaderItem(mrk)
    itm['tree'].ColumnCount = 5

    itm['tree'].ColumnWidth[0] = 75
    itm['tree'].ColumnWidth[1] = 200
    itm['tree'].ColumnWidth[2] = 100
    itm['tree'].ColumnWidth[3] = 100
    itm['tree'].ColumnWidth[4] = 50
    TimelineDict = get_all_timeline_items()
    new_timeline_dict = {}
    for frameID in TimelineDict:
        try:
            timelineitem_dict = {TimelineDict[frameID].GetMediaPoolItem().GetName():TimelineDict[frameID]}
            new_timeline_dict = merge_two_dicts(new_timeline_dict, timelineitem_dict)
        except Exception:
            sys.exc_clear()
    for folder in selected_item:
        ui_item = selected_item[folder].Text[0]
        parent_folder_name = selected_item[folder].Parent().Text[0]
        for foldername in child_dict:
            parent_folder = child_dict[foldername]
            for parent in parent_folder:
                parent_name = parent_folder[parent]
                if foldername == ui_item and parent_name == parent_folder_name: 
                    folder_item = parent
                    folder_clips = folder_item.GetClipList()
                    for items in folder_clips:
                         for timelineitem_name in new_timeline_dict:
                             item_name = items.GetName()
                             if item_name == timelineitem_name:
                                 timelineitem = new_timeline_dict[timelineitem_name]
                                 i= i + 1
                                 itRow = itm['tree'].NewItem()
                                 itRow.Text[0] = str(i)
                                 itRow.Text[1] = str(timelineitem_name)
                                 itRow.Text[2] = str(frames_to_timecode(timelineitem.GetStart(), framerate, False))
                                 itRow.Text[3] = str(frames_to_timecode(timelineitem.GetEnd(), framerate, False))
                                 itRow.Text[4] = str(version_count(timelineitem))
                                 itm['tree'].AddTopLevelItem(itRow)
                    itm['tree'].SortByColumn(2, "AscendingOrder")
                    all_clips_list = all_clips_list + folder_clips
    return all_clips_list

def _selection(ev):
    selected_item = folderitm['FolderTreeNested'].SelectedItems()
    #print(selected_item)
    all_clips = list_folder_clips(selected_item)
    #print(all_clips)

def _selected(ev):
    selected_item = itm['tree'].SelectedItems()
    return selected_item

def _get_selected_timelineitem(ev):
    selected_item = _selected(ev)
    item_list = []
    TimelineConca = dict()
    TimelineDict = dict()
    for item in selected_item:
        timeline_item = selected_item[item]
        item_name = timeline_item.Text[1]
        item_list.append(item_name)
    print(item_list)
    TimelineDict = get_all_timeline_items()
    for frameID in TimelineDict:
        item = TimelineDict[frameID]
        try:
            mediapool_name = item.GetName()
        except Exception:
            sys.exc_clear()
        if mediapool_name in item_list:
            TimelineConca = merge_two_dicts(TimelineConca, {frameID:item})
    return TimelineConca

def _get_flagged_timelineitem(ev):
    TimelineConca = dict()
    TimelineDict = get_all_timeline_items()
    flag_color = itm['flag_color_list'].CurrentText
    for frameID in TimelineDict:
        item = TimelineDict[frameID]
        try:
            item_flagcolor = item.GetFlagList()
        except Exception:
            sys.exc_clear()
        if flag_color in item_flagcolor:
            TimelineConca = merge_two_dicts(TimelineConca, {frameID:item})
    return TimelineConca

def _edit_metadata(key, metadataValue, item):
    media_item = item.GetMediaPoolItem()
    set_setting = media_item.SetMetadata(key, metadataValue)

def _edit_metadata_text(key, metadataValue, item):
    media_item = item.GetMediaPoolItem()
    old_data = media_item.GetMetadata(key)
    new_data = old_data + ', ' + metadataValue
    set_setting = media_item.SetMetadata(key, new_data)

def _match_metadata(key, metadataValue, item):
    media_item = item.GetMediaPoolItem()
    get_setting = ''
    try:
        get_setting = media_item.GetMetadata(key)
    except Exception:
        sys.exc_clear()
    if metadataValue.lower() in get_setting.lower():
        matched = 1
    else:
        matched = 0
    return matched

def _apply_filter(ev):
    color = itm['color_list'].CurrentText
    if itm['filter_list'].CurrentText == 'Marker':
        read_marker_color(color)
    if itm['filter_list'].CurrentText == 'Flag':
        read_flag_color(color)
    if itm['filter_list'].CurrentText == 'Clip Color':
        read_clip_color(color)

def _refresh_filter(ev):
    current_mode = refresh_manager.get_current_mode()
    if current_mode == 'all':
        read_all_timeline_clips(ev)
    elif current_mode == 'filtered':
        _apply_filter(ev)
    elif current_mode == 'search':
        search_source_clipname(ev)
    else:
        print("Unknown refresh mode")

def _filter_metadata(ev):
    global meta
    itm['tree'].Clear()

    mrk = itm['tree'].NewItem()
    headers = ['ID', 'Name', 'Record In', 'Record Out', 'Version Num']
    for i, header in enumerate(headers):
        mrk.Text[i] = header
    itm['tree'].SetHeaderItem(mrk)
    itm['tree'].ColumnCount = len(headers)
    column_widths = [75, 200, 100, 100, 50]
    for i, width in enumerate(column_widths):
        itm['tree'].ColumnWidth[i] = width

    TimelineDict = get_all_timeline_items()
    
    # Define metadata fields and their corresponding UI elements
    metadata_fields = {
        'Description': metaitm['description_text'].PlainText,
        'Comments': metaitm['comments_text'].PlainText,
        'Keywords': metaitm['keywords_text'].PlainText,
        'Good Take': (metaitm['good_take_bool'].Checked, goodtake_filter),
        'VFX Notes': metaitm['vfx_notes_text'].PlainText,
        'Colorist Notes': metaitm['colorist_notes_text'].PlainText,
        'Colorist Reviewed': (metaitm['colorist_reviewed_bool'].Checked, coloristreviewed_filter),
        'Continuity Reviewed': (metaitm['continuity_reviewed_bool'].Checked, continuityreviewed_filter),
        'Reviewers Notes': metaitm['reviewers_notes_text'].PlainText,
        'Send to': metaitm['send_to_text'].PlainText
    }

    i = 0
    for frameID, timelineitem in TimelineDict.items():
        if all(_check_metadata(field, value, timelineitem) for field, value in metadata_fields.items()):
            if timelineitem.GetClipEnabled():
                i += 1
                itRow = itm['tree'].NewItem()
                itRow.Text[0] = str(i)
                itRow.Text[1] = timelineitem.GetName()
                itRow.Text[2] = str(frames_to_timecode(timelineitem.GetStart(), framerate, False))
                itRow.Text[3] = str(frames_to_timecode(timelineitem.GetEnd(), framerate, False))
                itRow.Text[4] = str(version_count(timelineitem))
                itm['tree'].AddTopLevelItem(itRow)

    itm['tree'].SortByColumn(2, "AscendingOrder")
    _reset_meta(metaitm)
    _exit(ev)

def _check_metadata(field, value, timelineitem):
    if isinstance(value, tuple):  # For boolean fields with a filter
        return not value[1] or _match_metadata(field, bool_to_int(value[0]), timelineitem)
    elif value:  # For text fields
        return _match_metadata(field, value, timelineitem)
    return True  # If the field is empty, don't filter on it
def _search_source_clipname(ev):
    clipname = itm['search'].Text
    print(clipname)
    itm['tree'].Clear()
    refresh_manager.set_refresh_search()
    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Name'
    mrk.Text[2] = 'Record In'
    mrk.Text[3] = 'Record Out'
    mrk.Text[4] = 'Version Num'
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
    for frameID in TimelineDict:
        item = TimelineDict[frameID]
        mediapool_name = ''
        if itm['source_clip'].Checked == True:
            try:
                mediapool_name = item.GetMediaPoolItem().GetName()
            except Exception:
                sys.exc_clear()
        else:
            try:
                mediapool_name = item.GetName()
            except Exception:
                sys.exc_clear()
        enable_check = item.GetClipEnabled()
        if enable_check == True:
            name_check = bool(re.search(clipname, mediapool_name, re.IGNORECASE))
            if name_check == True:
                i= i + 1
                itRow = itm['tree'].NewItem()
                itRow.Text[0] = str(i)
                itRow.Text[1] = item.GetName()
                itRow.Text[2] = str(frames_to_timecode(item.GetStart(), framerate, False))
                itRow.Text[3] = str(frames_to_timecode(item.GetEnd(), framerate, False))
                itRow.Text[4] = str(version_count(item))
                itm['tree'].AddTopLevelItem(itRow)
    itm['tree'].SortByColumn(2, "AscendingOrder")

def disable_current_clip(ev):
    vid = tl.GetCurrentVideoItem()
    test = vid.GetClipEnabled()
    track_list = {}
    trackcount = this_timeline().GetTrackCount("video")
    for i in range(1, trackcount + 1):
        track_test = tl.GetIsTrackLocked("video", i)
        track_list = merge_two_dicts(track_list, {i:track_test})
        if track_test == True:
            tl.SetTrackLock("video", i, False)
    if test == True:    
        clip = vid.SetClipEnabled(False)
    else:
        clip = vid.SetClipEnabled(True)
    for i in track_list:
        track = track_list[i]
        if track == True:
            tl.SetTrackLock("video", i, True)

def bool_to_int(value):
    return '1' if value else '0'

def _reset(cmenuitm):
    global selected_items, flags
    cmenuitm['good_take_bool'].SetChecked(False)
    cmenuitm['colorist_reviewed_bool'].SetChecked(False)
    cmenuitm['continuity_reviewed_bool'].SetChecked(False)
    cmenuitm['description_text'].Clear()
    cmenuitm['comments_text'].Clear()
    cmenuitm['keywords_text'].Clear()
    cmenuitm['vfx_notes_text'].Clear()
    cmenuitm['colorist_notes_text'].Clear()
    cmenuitm['reviewers_notes_text'].Clear()
    cmenuitm['send_to_text'].Clear()
    if itm['flag_color_list'].CurrentText != '':
        for item in selected_items:
            timelineitem = selected_items[item]
            timelineitem.ClearFlags(itm['flag_color_list'].CurrentText)
    update_progress(0)
    # Reset all flags to False
    for key in flags:
        flags[key] = False

def _reset_meta(metaitm):
    global flags
    metaitm['good_take_bool'].SetChecked(False)
    metaitm['colorist_reviewed_bool'].SetChecked(False)
    metaitm['continuity_reviewed_bool'].SetChecked(False)
    metaitm['description_text'].Clear()
    metaitm['comments_text'].Clear()
    metaitm['keywords_text'].Clear()
    metaitm['vfx_notes_text'].Clear()
    metaitm['colorist_notes_text'].Clear()
    metaitm['reviewers_notes_text'].Clear()
    metaitm['send_to_text'].Clear()
    # Reset all flags to False
    for key in flags:
        flags[key] = False

def _batch_metadata(ev):
    global selected_items, flags, cmenuitm, cmenu

    # Collect metadata from UI
    metadata = {
        'Description': cmenuitm['description_text'].PlainText,
        'Comments': cmenuitm['comments_text'].PlainText,
        'Keywords': cmenuitm['keywords_text'].PlainText,
        'VFX Notes': cmenuitm['vfx_notes_text'].PlainText,
        'Colorist Notes': cmenuitm['colorist_notes_text'].PlainText,
        'Reviewers Notes': cmenuitm['reviewers_notes_text'].PlainText,
        'Send to': cmenuitm['send_to_text'].PlainText,
        'Good Take': cmenuitm['good_take_bool'].Checked,
        'Colorist Reviewed': cmenuitm['colorist_reviewed_bool'].Checked,
        'Continuity Reviewed': cmenuitm['continuity_reviewed_bool'].Checked
    }

    step = 130 / len(selected_items)
    print(f"Processing {len(selected_items)} items")
    cmenuitm['CMenu'].UpdatesEnabled = True

    for i, (item, timelineitem) in enumerate(selected_items.items(), 1):
        if metadata['Description']:
            _edit_metadata('Description', metadata['Description'], timelineitem)
        if metadata['Comments']:
            _edit_metadata('Comments', metadata['Comments'], timelineitem)
        if metadata['Keywords']:
            _edit_metadata_text('Keywords', metadata['Keywords'], timelineitem)
        if metadata['VFX Notes']:
            _edit_metadata('VFX Notes', metadata['VFX Notes'], timelineitem)
        if metadata['Colorist Notes']:
            _edit_metadata('Colorist Notes', metadata['Colorist Notes'], timelineitem)
        if metadata['Reviewers Notes']:
            _edit_metadata('Reviewers Notes', metadata['Reviewers Notes'], timelineitem)
        if metadata['Send to']:
            _edit_metadata('Send to', metadata['Send to'], timelineitem)
        if flags['goodtake']:
            _edit_metadata('Good Take', bool_to_int(metadata['Good Take']), timelineitem)
        if flags['colorist_reviewed']:
            _edit_metadata('Colorist Reviewed', bool_to_int(metadata['Colorist Reviewed']), timelineitem)
        if flags['continuity_reviewed']:
            _edit_metadata('Continuity Reviewed', bool_to_int(metadata['Continuity Reviewed']), timelineitem)
        
        update_progress(i * step)

    _reset(cmenuitm)
    _exit(ev)
    cmenu.Hide()

def get_all_timeline_items():
    TimelineConca = []
    TimelineDict = dict()
    for i in range(1, trackcount + 1):
        TimelineItem = this_timeline().GetItemListInTrack("video", i)
        TimelineConca = TimelineConca + TimelineItem
    for item in TimelineConca:
        enable_check = item.GetClipEnabled()
        name_check = item.GetMediaPoolItem()
        if enable_check == True and name_check:
            frameID = item.GetStart()
            TimelineDictItem = {frameID: item}
            TimelineDict = merge_two_dicts(TimelineDict, TimelineDictItem)
    TimelineDict = OrderedDict(sorted(TimelineDict.items()))
    return TimelineDict

def _updateproress(ev):
    global cmenu, cmenuitm
    label = cmenuitm['SplashProgress']
    label.Resize([ev['Progress'] * 3, 2])
    label['StyleSheet'] = "background-color: rgb(102, 211, 39);"
    disp.ExitLoop()

def update_progress(progress):
    global cmenu, cmenuitm
    label = cmenuitm['SplashProgress']
    app.UIManager.QueueEvent(cmenuitm['CMenu'], "UpdateProgress", {'Progress':progress})
    disp.RunLoop()
    #cmenuitm['SplashProgress'].Update()

def _click_comments(ev):
    convert_marker_color(convitm['color_conv_list'].CurrentText)

def _click_markers(ev):
    convert_comment_to_marker(convitm['color_conv_list'].CurrentText)

def _exit(ev):
    disp.ExitLoop()

def _call_context(ev):
    global cmenu , selected_items, cmenuitm
    position = ev['GlobalPos']
    selected_items = _get_selected_timelineitem(ev)
    x = int(position[1])
    y = int(position[2])
    window_detect = ui.FindWindows('CMenu')
    if len(window_detect) == 0:
        cmenu = disp.AddWindow({ 
                        "WindowTitle": "Edit Metadata", 
                        "ID": "CMenu", 
                        'WindowFlags': {
                              'Window': True,
                              'WindowStaysOnTopHint': True,
                               },
                        "Events": { 
                                   'UpdateProgress': True,
                                   'UpdatesEnabled': True,
                                   'Close': True},
                        "Geometry": [ 
                                    x, y-500, 
                                    450, 700],
                                            },
        window_02)

        cmenuitm= cmenu.GetItems()
        cmenu.On.good_take_bool.Clicked = goodtake_bool
        cmenu.On.colorist_reviewed_bool.Clicked = coloristreviewed
        cmenu.On.continuity_reviewed_bool.Clicked = continuityreviewed
        cmenu.On.batch_metadata.Clicked = _batch_metadata
        cmenu.On.cancel_metadata.Clicked = _exit
        cmenu.On.CMenu.UpdateProgress =  _updateproress
        cmenu.On.CMenu.Close = _exit
        cmenu.Show()
        disp.RunLoop()
        cmenu.Hide()
    else:
        cmenu.Show()
        disp.RunLoop()
        cmenu.Hide()

def _call_context_buttom(ev):
    global cmenu, cmenuitm, selected_items
    selected_items = _get_flagged_timelineitem(ev)
    window_detect = ui.FindWindows('CMenu')
    if itm['flag_color_list'].CurrentText == '':
        window_detect = 1
    if len(window_detect) == 0:
        cmenu = disp.AddWindow({ 
                        "WindowTitle": "Edit Metadata", 
                        "ID": "CMenu", 
                        'WindowFlags': {
                              'Window': True,
                              'WindowStaysOnTopHint': True,
                               },
                        "Events": { 
                                   'UpdateProgress': True,
                                   'UpdatesEnabled': True,
                                   'Close': True},
                        "Geometry": [ 
                                    200, 800, 
                                    450, 700],
                                            },
        window_02)

        cmenuitm= cmenu.GetItems()
        cmenu.On.good_take_bool.Clicked = goodtake_bool
        cmenu.On.colorist_reviewed_bool.Clicked = coloristreviewed
        cmenu.On.continuity_reviewed_bool.Clicked = continuityreviewed
        cmenu.On.batch_metadata.Clicked = _batch_metadata
        cmenu.On.cancel_metadata.Clicked = _exit
        cmenu.On.CMenu.UpdateProgress =  _updateproress
        cmenu.On.CMenu.Close = _exit
        cmenu.Show()
        disp.RunLoop()
        cmenu.Hide()
    else:
        cmenu.Show()
        disp.RunLoop()
        cmenu.Hide()

def _call_metadata(ev):
    global meta, metaitm
    meta = disp.AddWindow({ 
                        "WindowTitle": "Metadata Filter", 
                        "ID": "MetaWin", 
                        'WindowFlags': {
                              'Window': True,
                              'WindowStaysOnTopHint': True,
                               },
                        "Geometry": [ 
                                    1000, 600, 
                                    450, 700
                         ],
                        },
    window_03)

    metaitm = meta.GetItems()
    meta.On.good_take_bool.Clicked = goodtake_filter
    meta.On.colorist_reviewed_bool.Clicked = coloristreviewed_filter
    meta.On.continuity_reviewed_bool.Clicked = continuityreviewed_filter
    meta.On.search_metadata.Clicked = _filter_metadata
    meta.On.cancel_metadata.Clicked = _exit
    meta.On.MetaWin.Close = _exit
    meta.Show()
    disp.RunLoop()
    meta.Hide()

def _call_convert(ev):
    global conv, convitm
    conv = disp.AddWindow({ 
                        "WindowTitle": "Convert Markers", 
                        "ID": "ConvWin", 
                        'WindowFlags': {
                              'Window': True,
                              'WindowStaysOnTopHint': True,
                               },
                        "Geometry": [ 
                                    1000, 400, 
                                    700, 100
                         ],
                        },
    window_05)

    convitm = conv.GetItems()
    convitm['color_conv_list'].AddItems(flag_color)
    conv.On.ConvWin.Close = _exit
    conv.On.marker_to_comment.Clicked = _click_comments
    conv.On.comment_to_marker.Clicked = _click_markers
    conv.Show()
    disp.RunLoop()
    conv.Hide()

def get_folderid(foldername):
    mp = proj.GetMediaPool()
    root_folder = mp.GetRootFolder()
    subfolder_list = fast_scandir_list(root_folder)
    folder_dict = {}
    for i in subfolder_list:
        folder_dict = merge_two_dicts(folder_dict, {i.GetName():i})
    found_folder = [value for key, value in folder_dict.iteritems() if foldername.lower() in key.lower()]
    return found_folder

def fast_scandir_list(dirname):
    subfolders_list = dirname.GetSubFolderList()
    for dirname in list(subfolders_list):
        subfolders_list.extend(fast_scandir_list(dirname))
    return subfolders_list
    
def fast_scandir(dirname, parent_item):
    subfolders = dirname.GetSubFolderList()
    global child_dict
    for dirname in list(subfolders):
        child_item = ''
        folderitm['FolderTreeNested'].AddTopLevelItem(parent_item)
        child_item = folderitm['FolderTreeNested'].NewItem()
        child_item.Text[0] = dirname.GetName()
        dname = dirname.GetName()
        diritem = {}
        diritem= {dirname:parent_item.Text[0]}
        dictionary = {}
        dictionary = {dname:diritem}
        child_dict = merge_two_dicts(child_dict, dictionary)
        parent_item.AddChild(child_item)
        parent_item.Expanded = True
        folderitm['FolderTreeNested'].SortByColumn(0, "AscendingOrder")
        try:
            fast_scandir(dirname, child_item)
        except:
            pass

def find_items(text):
    search = folderitm['FolderTreeNested'].FindItems(text, {
		'MatchExactly': False,
		'MatchFixedString': False,
		'MatchContains': True,
		'MatchStartsWith': False,
		'MatchEndsWith': False,
		'MatchCaseSensitive': False,
		'MatchRegExp':False,
		'MatchWrap': False,
		'MatchRecursive': True,
	}, 0)
    return search

def get_all_items():
    items = folderitm['FolderTreeNested'].FindItems("*", {
		'MatchExactly': False,
		'MatchFixedString': False,
		'MatchContains': True,
		'MatchStartsWith': False,
		'MatchEndsWith': False,
		'MatchWildcard': True,
		'MatchCaseSensitive': False,
		'MatchRegExp':False,
		'MatchWrap': False,
		'MatchRecursive': True,
	}, 0)
    return items

def _search(ev):
    text = folderitm['description_text'].Text
    if text == '':
        _test_subfolder(ev)
    if text != '':
        folderitm['FolderTreeNested'].UpdatesEnabled = False
        for i in get_all_items():
            item = get_all_items()[i]
            if item.Hidden == False:
                item.Hidden = True
        for i in find_items(text):
            foundItem = find_items(text)[i]
            foundItem.Hidden = False
            foundItem.Expanded = True
            print(foundItem)
            n = 0
            parentItem = foundItem.Parent()
            parentItem.Hidden = False
            parentItem.Expanded = True
            print(parentItem)
            for n in range(10000):
                n = n + 1
                try:
                    parentItem = parentItem.Parent()
                    parentItem.Hidden = False
                    parentItem.Expanded = True
                except:
                    pass
    folderitm['FolderTreeNested'].UpdatesEnabled = True

def getpath(nested_dict, value):
    listofKeys = []
    for i in nested_dict.keys():
        for j in nested_dict[i].values():
            if value in j:
                if i not in listofKeys:
                    listofKeys.append(i)
    return listofKeys

def _test_subfolder_firsttime(ev):
    mp = proj.GetMediaPool()
    root_folder = mp.GetRootFolder()
    parent_item = folderitm['FolderTreeNested'].NewItem()
    parent_item.Text[0] = 'Master'
    parent_item.Expanded = True
    folderitm['FolderTreeNested'].Clear()
    fast_scandir(root_folder, parent_item)
    folderui.Show()
    disp.RunLoop()
    folderui.Hide()

def _test_subfolder(ev):
    mp = proj.GetMediaPool()
    root_folder = mp.GetRootFolder()
    parent_item = folderitm['FolderTreeNested'].NewItem()
    parent_item.Text[0] = 'Master'
    parent_item.Expanded = True
    folderitm['FolderTreeNested'].Clear()
    fast_scandir(root_folder, parent_item)

def _set_color(ev):
    if itm['filter_list'].CurrentText == 'Marker' or itm['filter_list'].CurrentText == 'Flag':
        itm['color_list'].Clear()
        itm['color_list'].AddItems(marker_color)
    if itm['filter_list'].CurrentText == 'Clip Color':
        itm['color_list'].Clear()
        itm['color_list'].AddItems(clip_color)

def main_ui(ui):
    window01 = ui.VGroup({"Spacing": 10,},[
        ui.HGroup({"Spacing": 4, "Weight": 0,},[
            ui.Label({ "ID": "filter_text","Text": "Filter type: ","Weight": 0}),
            ui.ComboBox({ "ID": "filter_list","Weight": 2}),
            ui.Label({ "ID": "filter_color_text","Text": "Color: ","Weight": 0}),
            ui.ComboBox({ "ID": "color_list","Weight": 1}),
            ui.HGap({"Weight": 1}),
            ui.Button({ "ID": "filter_color", "Text": "Apply","Weight": 0}),
            ui.Button({ "ID": "reset_filter", "Text": "Show All","Weight": 0}),
            ui.Button({ "ID": "refresh", "Text": "Refresh","Weight": 0}),
            ui.Button({ "ID": "convert_comments", "Text": "Convert","Weight": 0}),
        ]),
        ui.HGroup({"Spacing": 4, "Weight": 1,},[ 
            ui.Tree({
                    'ID': 'tree',
                    'SortingEnabled': 'true',
                    'SelectionMode': 'ExtendedSelection',
                    'Events': {
                              'ItemDoubleClicked': True,
                              'ItemClicked': True}}),
        ]),
        ui.HGroup({"Spacing": 7, "Weight": 0,},[
            ui.Label({ "ID": "metadata_color_text","Text": "Metadata Flag Color","Weight": 0}),
            ui.ComboBox({ "ID": "flag_color_list","Weight": 0}),
            ui.VGap({"Weight": 5}),
            ui.Button({ "ID": "edit_metadata", "Text": "Edit metadata","Weight": 0}),
            ui.Button({ "ID": "metadata_filter", "Text": "Search metadata","Weight": 0}),
        ]),
        ui.HGroup({"Spacing": 7, "Weight": 0,},[
            ui.Button({ "ID": "disenable", "Text": "Disable/Enable Clip","Weight": 0}),
            ui.Button({ "ID": "media_browser", "Text": "Media browser","Weight": 0}),
            ui.VGap({"Weight": 2}),
            ui.LineEdit({ "ID": "search", "Events": {'ReturnPressed': True}, "Weight": 1}),
            ui.CheckBox({ "ID": "source_clip", "Text": "Source name", "Weight": 0}),
        ])
        ])
    return window01

def convert_ui(ui):
    window05 = ui.VGroup({"Spacing": 10,},[
        ui.HGroup({"Spacing": 4, "Weight": 0,},[
            ui.Label({ "ID": "marker_color","Text": "Marker Color","Weight": 0}),
            ui.ComboBox({ "ID": "color_conv_list","Weight": 1}),
            ui.VGap({"Weight": 2}),
            ui.Button({ "ID": "marker_to_comment", "Text": "Convert Marker Notes to Comments","Weight": 0}),
            ui.Button({ "ID": "comment_to_marker", "Text": "Convert Comments to Marker Notes","Weight": 0}),
        ]),
        ])
    return window05

def folder_ui(ui):
    window04 = ui.VGroup({"Spacing": 10,},[
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.LineEdit({ "ID": "description_text","Weight": 1, "PlaceholderText": "Search folder name...", 'Events': {'ReturnPressed': True}}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 1,},[
            ui.VGroup({"Spacing": 10, "Weight": 1,},[
                ui.Tree({
                    'ID': 'FolderTreeNested',
                    'HeaderHidden': True,
                    'Weight': 1,
                    'SelectionMode': 'ExtendedSelection',
                     
                    'Events': {
                              'ItemDoubleClicked': True,
                              'ItemClicked': True,
                              'ItemsExpandable': True,
                              'ItemSelectionChanged': True}})
           ]),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Button({ "ID": "test", "Text": "Refresh","Weight": 0}),
            ui.VGap({"Weight": 1}),
            ui.Button({ "ID": "folder_close", "Text": "Close","Weight": 0}),
        ]),
        ])
    return window04

def context_ui(ui):
    window02 = ui.VGroup({"Spacing": 10,},[
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "description","Text": "Description","Weight": 1}),
            ui.TextEdit({ "ID": "description_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "comments","Text": "Comments","Weight": 1}),
            ui.TextEdit({ "ID": "comments_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "keywords","Text": "Keywords","Weight": 1}),
            ui.TextEdit({ "ID": "keywords_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "good_take","Text": "Good Take","Weight": 1}),
            ui.CheckBox({ "ID": "good_take_bool","Weight": 1}),
            ui.VGap(),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "vfx_notes","Text": "VFX Notes","Weight": 1}),
            ui.TextEdit({ "ID": "vfx_notes_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "colorist_notes","Text": "Colorist Notes","Weight": 1}),
            ui.TextEdit({ "ID": "colorist_notes_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "colorist_reviewed","Text": "Colorist Reviewed","Weight": 1}),
            ui.CheckBox({ "ID": "colorist_reviewed_bool","Weight": 1}),
            ui.VGap(),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "continuity_reviewed","Text": "Continuity Reviewed","Weight": 1}),
            ui.CheckBox({ "ID": "continuity_reviewed_bool","Weight": 1}),
            ui.VGap(),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "reviewers_notes","Text": "Reviewers Notes","Weight": 1}),
            ui.TextEdit({ "ID": "reviewers_notes_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "send_to","Text": "Send to","Weight": 1}),
            ui.TextEdit({ "ID": "send_to_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Button({ "ID": "batch_metadata", "Text": "Apply Changes","Weight": 1}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Button({ "ID": "cancel_metadata", "Text": "Cancel","Weight": 1}),
        ]),
        ui.HGroup({"Spacing": 5, "Weight": 0,},[
            ui.Label({ "ID": "SplashProgress", "Events" : {'UpdatesEnabled': True}, "StyleSheet": "max-height: 1px; background-color: rgb(40, 40, 46);"}),
        ])
        ])
    return window02

def metadata_ui(ui):
    window03 = ui.VGroup({"Spacing": 10,},[
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "description","Text": "Description","Weight": 1}),
            ui.TextEdit({ "ID": "description_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "comments","Text": "Comments","Weight": 1}),
            ui.TextEdit({ "ID": "comments_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "keywords","Text": "Keywords","Weight": 1}),
            ui.TextEdit({ "ID": "keywords_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "good_take","Text": "Good Take","Weight": 1}),
            ui.CheckBox({ "ID": "good_take_bool","Weight": 1}),
            ui.VGap(),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "vfx_notes","Text": "VFX Notes","Weight": 1}),
            ui.TextEdit({ "ID": "vfx_notes_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "colorist_notes","Text": "Colorist Notes","Weight": 1}),
            ui.TextEdit({ "ID": "colorist_notes_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "colorist_reviewed","Text": "Colorist Reviewed","Weight": 1}),
            ui.CheckBox({ "ID": "colorist_reviewed_bool","Weight": 1}),
            ui.VGap(),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "continuity_reviewed","Text": "Continuity Reviewed","Weight": 1}),
            ui.CheckBox({ "ID": "continuity_reviewed_bool","Weight": 1}),
            ui.VGap(),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "reviewers_notes","Text": "Reviewers Notes","Weight": 1}),
            ui.TextEdit({ "ID": "reviewers_notes_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Label({ "ID": "send_to","Text": "Send to","Weight": 1}),
            ui.TextEdit({ "ID": "send_to_text","Weight": 2}),
        ]),
        ui.HGroup({"Spacing": 10, "Weight": 0,},[
            ui.Button({ "ID": "search_metadata", "Text": "Search","Weight": 1}),
        ]),
        ui.HGroup({"Spacing": 5, "Weight": 0,},[
            ui.Button({ "ID": "cancel_metadata", "Text": "Cancel","Weight": 1}),
        ])
        ])
    return window03

if __name__ == '__main__':

    window_01 = main_ui(ui)
    window_02 = context_ui(ui)
    window_03 = metadata_ui(ui)
    window_04 = folder_ui(ui)
    window_05 = convert_ui(ui)

    dlg = disp.AddWindow({ 
                        "WindowTitle": "Edit Index v4.1", 
                        "ID": "MyWin", 
                        'WindowFlags': {
                              'Window': True,
                              'WindowStaysOnTopHint': True,
                               },
                        'Events': {
                              'ContextMenu': True,
                              'Close': True},
                        "Geometry": [ 
                                    800, 700, 
                                    750, 360
                         ],
                        },
    window_01)

    folderui = disp.AddWindow({ 
                        "WindowTitle": "Media Browser", 
                        "ID": "FolderWin", 
                        'WindowFlags': {
                              'Window': True,
                              'WindowStaysOnTopHint': True,
                               },
                        "Geometry": [ 
                                    1600, 700, 
                                    350, 600
                         ],
                        },
    window_04)

    folderitm = folderui.GetItems()
    folderui.On.FolderWin.Close = _exit
    folderui.On.test.Clicked = _test_subfolder
    folderui.On.folder_close.Clicked = _exit
    folderui.On.description_text.ReturnPressed = _search
    folderui.On.FolderTreeNested.ItemDoubleClicked = _clicked
    folderui.On.FolderTreeNested.ItemSelectionChanged = _selection

    itm = dlg.GetItems()

    mrk = itm['tree'].NewItem()
    mrk.Text[0] = 'ID'
    mrk.Text[1] = 'Name'
    mrk.Text[2] = 'Record In'
    mrk.Text[3] = 'Record Out'
    mrk.Text[4] = 'Versions'
    itm['tree'].SetHeaderItem(mrk)
    itm['search'].PlaceholderText = 'Search clipname...'
    itm['tree'].ColumnCount = 5

    itm['tree'].ColumnWidth[0] = 75
    itm['tree'].ColumnWidth[1] = 200
    itm['tree'].ColumnWidth[2] = 100
    itm['tree'].ColumnWidth[3] = 100
    itm['tree'].ColumnWidth[4] = 50

    trackcount = this_timeline().GetTrackCount("video")
    i = 0
    TimelineDict = get_all_timeline_items()
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
            itRow.Text[4] = str(version_count(item))
            itm['tree'].AddTopLevelItem(itRow)
    itm['tree'].SortByColumn(2, "AscendingOrder")

    itm['color_list'].AddItems(marker_color)
    itm['filter_list'].AddItems(filter_options)
    itm['flag_color_list'].AddItems(flag_color)

    dlg.On.context.Clicked = _call_context
    dlg.On.convert_comments.Clicked = _call_convert
    dlg.On.filter_color.Clicked = _apply_filter
    dlg.On.reset_filter.Clicked = read_all_timeline_clips
    dlg.On.refresh.Clicked = _refresh_filter
    dlg.On.filter_list.CurrentIndexChanged = _set_color
    dlg.On.media_browser.Clicked = _test_subfolder_firsttime
    dlg.On.edit_metadata.Clicked = _call_context_buttom
    dlg.On.disenable.Clicked = disable_current_clip
    dlg.On.search.ReturnPressed = _search_source_clipname
    dlg.On.tree.ItemDoubleClicked = _clicked
    dlg.On.tree.ItemClicked = _selected
    dlg.On.metadata_filter.Clicked = _call_metadata
    dlg.On.MyWin.ContextMenu = _call_context
    dlg.On.MyWin.Close = _exit
    dlg.Show()
    disp.RunLoop()
    dlg.Hide()

