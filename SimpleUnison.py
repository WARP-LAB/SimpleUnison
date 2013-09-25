#
# Sublime 2 plugin for quick sync with destination over SSH using Unison
#
# @copyleft (cl) 2013 WARP
# @version 0.0.1
# @licence GPL
# @link http://www.warp.lv/
#

import sublime, sublime_plugin
import subprocess
import threading
import re
import sys
import glob
import os
import json
from pprint import pprint


def loadUnisonSettings(settingpath):
    with open(settingpath) as data_file:    
        data = json.load(data_file)
    return data

def runUnison(cmd):
    #print cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while (True):
        retcode = p.poll()
        line    = p.stdout.readline()
        yield line.decode('utf-8')
        if (retcode is not None):
            break

  
class WarpThreadedUnison(threading.Thread):
    def __init__(self, _settings, _projFolder):
        self.settings    = _settings
        self.projFolder  = _projFolder
        threading.Thread.__init__(self)

    def run(self):
        ignoreStrComp = "-ignore \"Name {"

        for ignore in self.settings["warpunison"][0]["ignores"]:
            ignoreStrComp+=str(ignore)+','

        ignoreStrComp+='._.DS_Store' #default in
        ignoreStrComp += "}\" "

        unisonMode = "-batch " if (int(self.settings["warpunison"][0]["opts"][0]["batch"]) == 1) else "-auto "

        remoteHost = str(self.settings["warpunison"][0]["connection"][0]["host"])
        remotePort = str(self.settings["warpunison"][0]["connection"][0]["port"])
        remoteUser = str(self.settings["warpunison"][0]["connection"][0]["username"])
        remotePath = str(self.settings["warpunison"][0]["connection"][0]["remotepath"])

    #cmd = 'rsync --progress -vv -az --update ' + deleteIfNotLocal + excludeStrComp + deleteExcluded + self.projFolder + '/ ' + '-e \'ssh -p ' + remotePort + '\' ' + remoteUser + '@' + remoteHost + ':' + remotePath
        
        cmd = 'unison -ui text ' + unisonMode + ignoreStrComp + self.projFolder + ' ' +  'ssh://'+ remoteUser + '@' + remoteHost + ':' + remotePort + '/' + remotePath
                
        print "WARPUNISON | start"
        print cmd
        
        for line in runUnison(cmd):
            print line,

        print "WARPUNISON | done"

        if ( int(self.settings["warpunison"][0]["connection"][0]["openuri"]) == 1):
            os.system('open \'' + str(self.settings["warpunison"][0]["connection"][0]["remoteuri"]) + '\'')


class WarpUnisonCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        #self.window.active_view().insert(edit, 0, "inview")
        print "WARPUNISON | starting"
        currWindow = self.view.window()
        folders = currWindow.folders()
        foldersLen = len(folders)
        if (foldersLen > 1):
            print "WARPUNISON | more than one folder at project top level found, aborting"
            for folder in folders:
                print folder
            print "WARPUNISON | abort"
            return
        elif (foldersLen == 0):
            print "WARPUNISON | there must be one top level directory, aborting"
            return
        else:
            projFolder = str(folders[0])
            print "WARPUNISON | project folder: " + projFolder;
            #find project file
            projFileSearch = glob.glob(projFolder+'/*.sublime-project')
            if (len(projFileSearch) != 1):
                "WARPUNISON | no sublime-project file found in top directory" 
                return
            projFilePath =  str(projFileSearch[0])
            print "WARPUNISON | project file: " + projFilePath

            settings = loadUnisonSettings(projFilePath)
            #pprint(settings)

            if ( str(settings["folders"][0]["path"]) != str(projFolder) ):
                print "WARPUNISON | physical folder differs from sublime-project path entry (under folders)! aborting"
                return

            WarpThreadedUnison(settings, projFolder).start()



