#!/usr/bin/env python
"""

This runner is controlled by evennia.py and should normally not be
 launched directly.  It manages the two main Evennia processes (Server
 and Portal) and most importanly runs a passive, threaded loop that
 makes sure to restart Server whenever it shuts down.

Since twistd does not allow for returning an optional exit code we
need to handle the current reload state for server and portal with
flag-files instead. The files, one each for server and portal either
contains True or False indicating if the process should be restarted
upon returning, or not. A process returning != 0 will always stop, no
matter the value of this file.

"""
import os  
import sys
from optparse import OptionParser
from subprocess import Popen, call
import Queue, thread, subprocess

#
# System Configuration
# 


SERVER_PIDFILE = "server.pid"
PORTAL_PIDFILE = "portal.pid"

SERVER_RESTART = "server.restart"
PORTAL_RESTART = "portal.restart"

# Set the Python path up so we can get to settings.py from here.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'game.settings'

# i18n
from django.utils.translation import ugettext as _

if not os.path.exists('settings.py'):

    print _("No settings.py file found. Run evennia.py to create it.")
    sys.exit()
                     
# Get the settings
from django.conf import settings

# Setup access of the evennia server itself
SERVER_PY_FILE = os.path.join(settings.SRC_DIR, 'server/server.py')
PORTAL_PY_FILE = os.path.join(settings.SRC_DIR, 'server/portal.py')

# Get logfile names
SERVER_LOGFILE = settings.SERVER_LOG_FILE
PORTAL_LOGFILE = settings.PORTAL_LOG_FILE

# Add this to the environmental variable for the 'twistd' command.
currpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if 'PYTHONPATH' in os.environ:
    os.environ['PYTHONPATH'] += (":%s" % currpath)
else:
    os.environ['PYTHONPATH'] = currpath

TWISTED_BINARY = 'twistd' 
if os.name == 'nt':
    TWISTED_BINARY = 'twistd.bat'
    err = False 
    try:
        import win32api  # Test for for win32api
    except ImportError:
        err = True 
    if not os.path.exists(TWISTED_BINARY):
        err = True 
    if err:
        print _("Twisted binary for Windows is not ready to use. Please run evennia.py.")
        sys.exit()

# Functions 

def set_restart_mode(restart_file, flag=True):
    """
    This sets a flag file for the restart mode. 
    """    
    f = open(restart_file, 'w')
    f.write(str(flag))
    f.close()

def get_restart_mode(restart_file):
    """
    Parse the server/portal restart status
    """
    if os.path.exists(restart_file):
        flag = open(restart_file, 'r').read()
        return flag == "True"
    return False 

def get_pid(pidfile):
    """
    Get the PID (Process ID) by trying to access
    an PID file. 
    """
    pid = None 
    if os.path.exists(pidfile):
        f = open(pidfile, 'r')
        pid = f.read()
    return pid 

def cycle_logfile(logfile):
    """
    Move the old log files to <filename>.old

    """    
    logfile_old = logfile + '.old'
    if os.path.exists(logfile):
        # Cycle the old logfiles to *.old
        if os.path.exists(logfile_old):
            # E.g. Windows don't support rename-replace
            os.remove(logfile_old)
        os.rename(logfile, logfile_old)

    logfile = settings.HTTP_LOG_FILE.strip()
    logfile_old = logfile + '.old'
    if os.path.exists(logfile):
        # Cycle the old logfiles to *.old
        if os.path.exists(logfile_old):
            # E.g. Windows don't support rename-replace
            os.remove(logfile_old)
        os.rename(logfile, logfile_old)    


# Start program management 

SERVER = None
PORTAL = None 

def start_services(server_argv, portal_argv):
    """
    This calls a threaded loop that launces the Portal and Server
    and then restarts them when they finish. 
    """
    global SERVER, PORTAL 

    processes = Queue.Queue()

    def server_waiter(queue):                
        try: 
            rc = Popen(server_argv).wait()
        except Exception, e:
            print _("Server process error: %(e)s") % {'e': e}
        queue.put(("server_stopped", rc)) # this signals the controller that the program finished

    def portal_waiter(queue):                
        try: 
            rc = Popen(portal_argv).wait()
        except Exception, e:
            print _("Portal process error: %(e)s") % {'e': e}
        queue.put(("portal_stopped", rc)) # this signals the controller that the program finished
                    
    if server_argv:
        # start server as a reloadable thread 
        SERVER = thread.start_new_thread(server_waiter, (processes, ))

    if portal_argv: 
        if get_restart_mode(PORTAL_RESTART):
            # start portal as interactive, reloadable thread 
            PORTAL = thread.start_new_thread(portal_waiter, (processes, ))
        else:
            # normal operation: start portal as a daemon; we don't care to monitor it for restart
            PORTAL = Popen(portal_argv)
            if not SERVER:
                # if portal is daemon and no server is running, we have no reason to continue to the loop.
                return 

    # Reload loop 
    while True:
        
        # this blocks until something is actually returned.
        message, rc = processes.get()                    

        # restart only if process stopped cleanly
        if message == "server_stopped" and int(rc) == 0 and get_restart_mode(SERVER_RESTART):
            print _("Evennia Server stopped. Restarting ...")            
            SERVER = thread.start_new_thread(server_waiter, (processes, ))
            continue 

        # normally the portal is not reloaded since it's run as a daemon.
        if message == "portal_stopped" and int(rc) == 0 and get_restart_mode(PORTAL_RESTART):
            print _("Evennia Portal stopped in interactive mode. Restarting ...")
            PORTAL = thread.start_new_thread(portal_waiter, (processes, ))                            
            continue 
        break 

# Setup signal handling

def main():
    """
    This handles the command line input of the runner (it's most often called by evennia.py)
    """
    
    parser = OptionParser(usage="%prog [options] start",
                          description=_("This runner should normally *not* be called directly - it is called automatically from the evennia.py main program. It manages the Evennia game server and portal processes an hosts a threaded loop to restart the Server whenever it is stopped (this constitues Evennia's reload mechanism)."))
    parser.add_option('-s', '--noserver', action='store_true', 
                      dest='noserver', default=False,
                      help=_('Do not start Server process'))
    parser.add_option('-p', '--noportal', action='store_true', 
                      dest='noportal', default=False,
                      help=_('Do not start Portal process'))
    parser.add_option('-i', '--iserver', action='store_true', 
                      dest='iserver', default=False,
                      help=_('output server log to stdout instead of logfile'))
    parser.add_option('-d', '--iportal', action='store_true', 
                      dest='iportal', default=False,
                      help=_('output portal log to stdout. Does not make portal a daemon.'))
    options, args = parser.parse_args()

    if not args or args[0] != 'start':
        # this is so as to not be accidentally launched.
        parser.print_help()
        sys.exit()

    # set up default project calls 
    server_argv = [TWISTED_BINARY, 
                   '--nodaemon',
                   '--logfile=%s' % SERVER_LOGFILE,
                   '--pidfile=%s' % SERVER_PIDFILE, 
                   '--python=%s' % SERVER_PY_FILE]
    portal_argv = [TWISTED_BINARY,
                   '--logfile=%s' % PORTAL_LOGFILE,
                   '--pidfile=%s' % PORTAL_PIDFILE, 
                   '--python=%s' % PORTAL_PY_FILE]    
    # Server 
    
    pid = get_pid(SERVER_PIDFILE)
    if pid and not options.noserver:
            print _("\nEvennia Server is already running as process %(pid)s. Not restarted.") % {'pid': pid}
            options.noserver = True
    if options.noserver:
        server_argv = None 
    else:
        set_restart_mode(SERVER_RESTART, True)
        if options.iserver:
            # don't log to server logfile
            del server_argv[2]
            print _("\nStarting Evennia Server (output to stdout).")
        else:
            print _("\nStarting Evennia Server (output to server logfile).")
        cycle_logfile(SERVER_LOGFILE)

    # Portal 

    pid = get_pid(PORTAL_PIDFILE)
    if pid and not options.noportal:
        print _("\nEvennia Portal is already running as process %(pid)s. Not restarted.") % {'pid': pid}    
        options.noportal = True             
    if options.noportal:
        portal_argv = None 
    else:
        if options.iportal:
            # make portal interactive
            portal_argv[1] = '--nodaemon'
            PORTAL_INTERACTIVE = True                     
            set_restart_mode(PORTAL_RESTART, True)
            print _("\nStarting Evennia Portal in non-Daemon mode (output to stdout).")
        else:
            set_restart_mode(PORTAL_RESTART, False)
            print _("\nStarting Evennia Portal in Daemon mode (output to portal logfile).")            
        cycle_logfile(PORTAL_LOGFILE)

    # Windows fixes (Windows don't support pidfiles natively)
    if os.name == 'nt':
        if server_argv:
            del server_argv[-2]
        if portal_argv:
            del portal_argv[-2]

    # Start processes
    start_services(server_argv, portal_argv)
          
if __name__ == '__main__':
    from src.utils.utils import check_evennia_dependencies
    if check_evennia_dependencies():
        main()