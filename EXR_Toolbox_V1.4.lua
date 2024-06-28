-- created by Jimmy Qiu

function check_embedded_mattes(exr_path)
      local exr = EXRIO()
      exr:ReadOpen(exr_path, -1) -- filename, frame
      assert(exr:ReadHeader())
      add_text = ''
      for part = 1, exr.NumParts do
         part_count = 1
         part_text = ''
         if (exr.NumParts > 1) then
            part_text = "  Part: "..select(2, exr:GetAttribute(part, "name")).."\n"
            part_count = part_count + 1
         end
         channel_count = 0
         channel_text = ''
         for _, channel in ipairs(exr:GetChannels(part)) do
            channel_text = channel_text .. "    Channel: "..channel.Name.."\n"
            channel_count = channel_count + 1
         end
         add_text = add_text .. part_text .. channel_text.."\n"
      end
      combined_text = filename_text .. add_text
      assert(exr:Close())
   end

function TableConcat(x, y)
    z = {}
    n = 0
    for _, v in ipairs(x) do n=n+1; z[n]=v end
    for _, v in ipairs(y) do n=n+1; z[n]=v end
return z
end

function clip_table(folderlist)
    n = {}
    for k, v in ipairs(folderlist) do
        clip = v:GetClipList()
        n = TableConcat(n, clip)
    end
    print(n)
return n
end

function GetFileExtension(file)
    file = file:match "[^.]+$"
    file = string.lower(file)
    return file
end

function addZeros(Id, length)
    Id = tostring(Id)
    local Id = string.rep('0', length-#Id)..Id
    return Id
end

function searchSubfolders(folder)
    local subfolders = {}
    local subfolderList = folder:GetSubFolderList()
    for i, subfolder in ipairs(subfolderList) do
        subfolders[#subfolders + 1] = subfolder
        local subsubfolders = searchSubfolders(subfolder)
        for j, subsubfolder in ipairs(subsubfolders) do
            subfolders[#subfolders + 1] = subsubfolder
        end
    end
    return subfolders
end

function travelsing_dir(current_folder)
    currentfolder_cliplist = current_folder:GetClipList()
    local clip_tree = {}
    table.move(currentfolder_cliplist, 1, #currentfolder_cliplist, #clip_tree + 1, clip_tree)
    subfolders_list = searchSubfolders(current_folder)
    for _, subfolder in pairs(subfolders_list) do
        subfolder_clips = subfolder:GetClipList()
        table.move(subfolder_clips, 1, #subfolder_clips, #clip_tree + 1, clip_tree)
    end
    return clip_tree
end

function exr_clip_check(mediapoolitem)
    local filename = mediapoolitem:GetClipProperty("File Path")
    check = GetFileExtension(filename)
    if string.match(filename, "%b[-") == nil then
        check = 'bad'
    end
    if check ~= "bad" then
        local mediapoolitemtype = filename
        filename_text = clip_count .. ". " .. mediapoolitem:GetName().."\n"
        path = mediapoolitemtype
        firstframe = string.match(string.match(path, "%b[-"), "%d+")
        lastframe = string.match(string.match(path, "%b-]"), "%d+")
        if #firstframe == #lastframe then
            check_padding = #firstframe
            local framenumber = tonumber(firstframe) + math.floor((tonumber(lastframe)-tonumber(firstframe))/2)
            local new_framenumber = addZeros(framenumber, check_padding)
            path = string.gsub(path, "%b[]", new_framenumber)
        else
            local framenumber = tonumber(firstframe) + math.floor((tonumber(lastframe)-tonumber(firstframe))/2)
            path = string.gsub(path, "%b[]", framenumber)
        end
    end
    return path
end

   function search()
      currentfolder = mp:GetCurrentFolder()
      combined_textall = ''
      allfolder_cliplist = travelsing_dir(currentfolder)
      clip_count = 1
      for _, mediapoolitem in ipairs(allfolder_cliplist) do
             local clip_path = exr_clip_check(mediapoolitem)
             local extension = string.lower(string.sub(clip_path, -3))
             if extension ~= "exr" then
                 print("skipping non-exr file:" .. clip_path)
                 goto continue
             end
             clip_count = clip_count + 1
             check_embedded_mattes(clip_path)
             combined_textall = combined_textall .. combined_text
             ::continue::
      end
      itm.exrdetail.Text = combined_textall
   end

   function add_flag()
      color = itm.flag.CurrentText
      currentfolder = mp:GetCurrentFolder()
      allfolder_cliplist = travelsing_dir(currentfolder)

      for _, mediapoolitem in ipairs(allfolder_cliplist) do
             clip_count = _
             local clip_path = exr_clip_check(mediapoolitem)
             check_embedded_mattes(clip_path)
             if (channel_count > 4) then
                mediapoolitem:AddFlag(color)
             end
             if itm.search_alpha.Checked == true then
                 if (channel_count > 3) then
                    mediapoolitem:AddFlag(color)
                 end
             end
             if (part_count > 1) then
                mediapoolitem:AddFlag(color)
             end
      end
   end

   function clear_flag()
      color = itm.flag.CurrentText
      currentfolder = mp:GetCurrentFolder()
      allfolder_cliplist = travelsing_dir(currentfolder)
      for _, mediapoolitem in ipairs(allfolder_cliplist) do
             clip_count = _
             local clip_path = exr_clip_check(mediapoolitem)
             check_embedded_mattes(clip_path)
             if (channel_count > 4) then
                mediapoolitem:ClearFlags(color)
             end
             if itm.search_alpha.Checked == true then
                 if (channel_count > 3) then
                    mediapoolitem:ClearFlags(color)
                 end
             end
             if (part_count > 1) then
                mediapoolitem:ClearFlags(color)
             end
      end
   end

   flag_color = {'Blue','Cyan','Green','Yellow','Red','Pink','Purple','Fuchsia','Rose','Lavender','Sky','Mint','Lemon','Sand','Cocoa','Cream'}
   resolve = Resolve()
   pm = resolve:GetProjectManager()
   proj = pm:GetCurrentProject()
   ms = resolve:GetMediaStorage()
   mp = proj:GetMediaPool()
   local ui = app.UIManager
   local disp = bmd.UIDispatcher(ui)
   local width,height = 800,600
   win = disp:AddWindow({
     ID = 'exrio',
     WindowTitle = 'EXR ToolBox v1.4',
     WindowFlags = {
           Window = true,
           WindowStaysOnTopHint = true,
           },
     Geometry = {100, 100, width, height},
     ui:VGroup
     {
       ID = 'root',
       Spacing = 10, Weight = 0,
       -- Add your GUI elements here:
       -- Flag color
       ui:Label{
         ID = 'flaglabel',
         Weight = 0,
         Text = 'Flag Color', 
         Alignment = {AlignLeft = true, AlignTop = true},
       },
       ui:HGroup {
       Spacing = 10, Weight = 0,
       ui:ComboBox{
         ID = 'flag',
         Weight = 2
       },
       ui.HGap({Weight = 2}),
       -- button
       ui:Button{ Text = 'List', ID = 'search', Weight = 0},
       -- button
       ui:Button{ Text = 'Apply', ID = 'applyflag', Weight = 0 },
      -- button
       ui:Button{ Text = 'Clear', ID = 'clearflag', Weight = 0 },
       },
       ui:HGroup {
       Spacing = 10, Weight = 0,
       ui:CheckBox { Text = 'Check If Mattes in Alpha Channel', ID = 'search_alpha', Weight = 0},
       },
       ui:HGroup {
       Spacing = 10, Weight = 3,
       -- Description
       ui:TextEdit{
         Weight = 3,
         ID = 'exrdetail',
         ReadOnly = false,
         Font = ui:Font{
           Family = 'Droid Sans Mono',
           -- Family = 'Tahoma',
           StyleName = 'Regular',
           PixelSize = 15,
           MonoSpaced = true,
           StyleStrategy = {ForceIntegerMetrics = true},
         },
       },
       },
      },
   })
   -- Add your GUI element based event functions here:
   itm = win:GetItems()
   itm.flag:AddItems(flag_color)

   function win.On.search.Clicked(ev)
      search()
   end
   function win.On.applyflag.Clicked(ev)
      add_flag()
   end
   function win.On.clearflag.Clicked(ev)
      clear_flag()
   end
   -- The window was closed
   function win.On.exrio.Close(ev)
      disp:ExitLoop()
   end
   win:Show()
   disp:RunLoop()
   win:Hide()
