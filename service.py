# -*- coding: utf-8 -*-

import os
import sys
import urllib.parse
import urllib.request

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = xbmc.translatePath(__addon__.getAddonInfo('path'))
__profile__ = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__resource__ = xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib'))
__temp__ = xbmc.translatePath(os.path.join(__profile__, 'temp'))

sys.path.append(__resource__)

from SUBUtilities import SubsHelper, log, normalizeString, parse_rls_title, clean_title


def search(_item):
    _helper = SubsHelper()
    subtitles_list = _helper.get_subtitle_list(_item)
    if subtitles_list:
        for it in subtitles_list:
            _list_item = xbmcgui.ListItem(label=it["language_name"],
                                          label2=it["filename"],
                                          iconImage=it["rating"],
                                          thumbnailImage=it["language_flag"]
                                          )
            if it["sync"]:
                _list_item.setProperty("sync", "true")
            else:
                _list_item.setProperty("sync", "false")

            if it.get("hearing_imp", False):
                _list_item.setProperty("hearing_imp", "true")
            else:
                _list_item.setProperty("hearing_imp", "false")

            url = "plugin://%s/?action=download&id=%s&filename=%s&language=%s" % (
                __scriptid__, it["id"], it["filename"], it["language_flag"])
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=_list_item, isFolder=False)


def download(_id, language, filename):
    subtitle_list = []
    exts = [".srt", ".sub"]

    filename = os.path.join(__temp__, "%s.srt" % filename)

    _helper = SubsHelper()
    _helper.download(_id, language, filename)

    for file in xbmcvfs.listdir(__temp__)[1]:
        full_path = os.path.join(__temp__, file)
        if os.path.splitext(full_path)[1] in exts:
            subtitle_list.append(full_path)

    return subtitle_list


def get_params(string=""):
    param = []
    if string == "":
        param_string = sys.argv[2]
    else:
        param_string = string

    if len(param_string) >= 2:
        params = param_string
        cleaned_params = params.replace('?', '')
        if params[len(params) - 1] == '/':
            params = params[0:len(params) - 2]
        pairs_of_params = cleaned_params.split('&')
        param = {}
        for i in range(len(pairs_of_params)):
            split_params = pairs_of_params[i].split('=')
            if (len(split_params)) == 2:
                param[split_params[0]] = split_params[1]

    return param


params = get_params()

if params['action'] in ['search', 'manualsearch']:
    log("Version: '%s'" % (__version__,))
    log("Action '%s' called" % (params['action']))

    if params['action'] == 'manualsearch':
        params['searchstring'] = urllib.parse.unquote(params['searchstring'])

    item = {
        'temp': False,
        'rar': False,
        'year': xbmc.getInfoLabel("VideoPlayer.Year"),
        'season': str(xbmc.getInfoLabel("VideoPlayer.Season")),
        'episode': str(xbmc.getInfoLabel("VideoPlayer.Episode")),
        'tvshow': normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle")),
        'title': normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle")),
        'file_original_path': urllib.parse.unquote(xbmc.Player().getPlayingFile()),
        '3let_language': [],
        'preferredlanguage': urllib.parse.unquote(params.get('preferredlanguage', ''))
    }
    item['preferredlanguage'] = xbmc.convertLanguage(item['preferredlanguage'], xbmc.ISO_639_2)

    if item['title'] == "":
        log("VideoPlayer.OriginalTitle not found")
        item['title'] = normalizeString(xbmc.getInfoLabel("VideoPlayer.Title"))  # no original title, get just Title

    if params['action'] == 'manualsearch':
        if item['season'] != '' or item['episode']:
            item['tvshow'] = params['searchstring']
        else:
            item['title'] = params['searchstring']

    for lang in urllib.parse.unquote(params['languages']).split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang, xbmc.ISO_639_2))

    log("Item before cleaning: \n    %s" % item)

    # clean title + tvshow params
    clean_title(item)
    parse_rls_title(item)

    if item['episode'].lower().find("s") > -1:  # Check if season is "Special"
        item['season'] = "0"
        item['episode'] = item['episode'][-1:]

    if item['file_original_path'].find("http") > -1:
        item['temp'] = True

    elif item['file_original_path'].find("rar://") > -1:
        item['rar'] = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

    elif item['file_original_path'].find("stack://") > -1:
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]
    log("%s" % item)
    search(item)


elif params['action'] == 'download':
    # we pickup all our arguments sent from def search()
    subs = download(params['id'], params['language'], params['filename'])
    # we can return more than one subtitle for multi CD versions,
    # for now we are still working out how to handle that in XBMC core
    for sub in subs:
        list_item = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=list_item, isFolder=False)

elif params['action'] == 'login':
    helper = SubsHelper()
    helper.login(True)
    __addon__.openSettings()

xbmcplugin.endOfDirectory(int(sys.argv[1]))  # send end of directory to XBMC
